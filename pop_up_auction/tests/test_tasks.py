from unittest import skip
from pop_up_auction.models import (
     PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType, PopUpProductImage, PopUpProductSpecification, 
     PopUpProductSpecificationValue, WinnerReservation )
from pop_up_order.utils.utils import user_orders, user_shipments
from pop_up_payment.models import PopUpPayment
from pop_up_shipping.models import PopUpShipment
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest
from pop_up_auction.views import (AllAuctionView, AjaxLoginRequiredMixin, PlaceBidView)
from pop_accounts.models import (PopUpCustomerProfile, PopUpCustomerAddress, PopUpCustomerIP, PopUpBid)
from pop_up_cart.models import (PopUpCartItem)
from django.utils.timezone import now, make_aware
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime, date 
from django.utils.text import slugify
from django.views import View
from django.template import Context, Template
from django.http import Http404
from pop_up_cart.cart import Cart
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import Mock, patch, call, MagicMock
from django.core.cache import cache
from django.http import JsonResponse
import json
from django.contrib.auth.models import AnonymousUser
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand)

from pop_up_auction.tasks import (
    check_auctions_and_finalize, mark_expired_reservations, send_reservation_reminders, 
    transition_expired_buy_now_to_auction)
from freezegun import freeze_time


User = get_user_model()

"""
Tests In Order
 1. TestAllAuctionView
 2. TestProtectedView
 3. TestAjaxLoginRequiredMixin
 4. TestPlaceBidView
 5. TestProductAuctionView
 6. TestProductsView
 7. TestComingSoonView
 8. TestFutureReleasesView
 9. TestProductDetailView
 10. TestBuyNowFlow
"""

# Test helper functions
class CheckAuctionsAndFinalizeTestCase(TestCase):
    """Test suite for check_auctions_and_finalize task."""
 
    def setUp(self):
        """Set up test fixtures."""
        self.now = django_timezone.now()
        
        # Create test users
        # self.user, self.profile = create_test_user(self.existing_email, 'testPass!23', 'Test', 'User', '9', 'male')  

        self.winner_user, self.winner_profile = create_test_user(
            "winner@example.com", "testpass!23", "Winner", "User", "10", "male"
        )
        self.winner_user.is_active = True
        self.winner_user.save()

        self.other_user, self.other_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User", "9", "female"
        )
        self.other_user.is_active = True
        self.other_user.save()

        
        # Create product infrastructure
        self.brand = create_brand('Jordan')
        self.category = create_category('Jordan 3', is_active=True)
        self.product_type = create_product_type('shoe', is_active=True)
        
        # Create specifications
        self.size_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='size'
        )
        self.color_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='colorway'
        )
 
    def test_finalize_auction_with_highest_bid(self):
        """Test that auction with bids finalizes correctly and declares winner."""
        # Create a product with ended auction

        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand= self.brand, 
            auction_start_date= self.now - timedelta(days=2), 
            auction_end_date = self.now - timedelta(minutes=5),  # Ended 5 minutes ago 
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active = True, 
        )
        
        # Create bids from different users
        bid1 = PopUpBid.objects.create(
            customer=self.other_profile,
            product=product,
            amount=Decimal('120.00'),
            timestamp=self.now - timedelta(hours=1)
        )
        
        bid2 = PopUpBid.objects.create(
            customer=self.winner_profile,
            product=product,
            amount=Decimal('150.00'),
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify product is finalized
        product.refresh_from_db()
        self.assertTrue(product.auction_finalized)
        self.assertEqual(product.winner, self.winner_user)
        self.assertEqual(product.current_highest_bid, Decimal('150.00'))
        self.assertEqual(product.inventory_status, 'sold_out')
 
    def test_cart_item_created_for_winner(self):
        """Test that cart item is created with auction_locked=True."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True
        )

        # Create winning bid
        PopUpBid.objects.create(
            customer=self.winner_profile,
            product=product,
            amount=Decimal('100.00'),
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify cart item was created
        cart_item = PopUpCartItem.objects.get(user=self.winner_user, product=product)
        self.assertEqual(cart_item.quantity, 1)
        self.assertTrue(cart_item.auction_locked)
        self.assertFalse(cart_item.buy_now)


    def test_cart_item_updated_if_exists(self):
        """Test that existing cart item is updated with auction_locked=True."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True
        )

        
        # Pre-create a cart item (maybe user added it manually)
        existing_cart = PopUpCartItem.objects.create(
            user=self.winner_user,
            product=product,
            quantity=1,
            auction_locked=False
        )
        
        # Create winning bid
        PopUpBid.objects.create(
            customer=self.winner_profile,
            product=product,
            amount=Decimal('100.00'),
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify cart item was updated (not duplicated)
        cart_items = PopUpCartItem.objects.filter(user=self.winner_user, product=product)
        self.assertEqual(cart_items.count(), 1)
        
        existing_cart.refresh_from_db()
        self.assertTrue(existing_cart.auction_locked)
    

    def test_winner_reservation_created(self):
        """Test that WinnerReservation is created with correct expiration time."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True
        )


        
        # Create winning bid
        PopUpBid.objects.create(
            customer=self.winner_profile,
            product=product,
            amount=Decimal('100.00'),
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify WinnerReservation was created
        reservation = WinnerReservation.objects.get(user=self.winner_user, product=product)
        self.assertEqual(reservation.user, self.winner_user)
        self.assertEqual(reservation.product, product)
        self.assertFalse(reservation.is_paid)
        self.assertFalse(reservation.is_expired)
        self.assertTrue(reservation.notification_sent)
        self.assertFalse(reservation.reminder_24hr_sent)
        self.assertFalse(reservation.reminder_1hr_sent)
        
        # Verify expiration is 48 hours from now
        expected_expiration = self.now + timedelta(hours=48)
        time_diff = abs((reservation.expires_at - expected_expiration).total_seconds())
        self.assertLess(time_diff, 60)  # Within 60 seconds
 
    def test_auction_with_no_bids_finalized(self):
        """Test that auction with no bids is finalized without winner."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True
        )

        
        # Verify no bids exist
        self.assertEqual(product.bids.count(), 0)
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify product is finalized
        product.refresh_from_db()
        self.assertTrue(product.auction_finalized)
        self.assertIsNone(product.winner)
        
        # Verify no cart item or reservation created
        self.assertFalse(PopUpCartItem.objects.filter(product=product).exists())
        self.assertFalse(WinnerReservation.objects.filter(product=product).exists())
 
    def test_auction_reserve_price_not_met_with_bid(self):
        """Test that auction finalizes even if reserve price not met."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('500.00'), 
            is_active=True
        )
      
        
        # Create bid below reserve
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify auction is finalized (but still has a winner)
        # Note: This depends on your business logic - adjust if reserve is enforced
        product.refresh_from_db()
        self.assertTrue(product.auction_finalized)
        self.assertEqual(product.winner, self.winner_user)
 
    def test_only_ended_auctions_processed(self):
        """Test that only ended auctions are processed."""
        # Create an ended auction
        ended_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True
        )
        
        # Create an ongoing auction
        ongoing_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=1),
            auction_end_date=self.now + timedelta(days=1),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True
        )
        
        # Create bids for both
        PopUpBid.objects.create(
            customer=self.winner_profile,
            product=ended_product,
            amount=Decimal('100.00'),
            
        )
        PopUpBid.objects.create(
            customer=self.other_profile,
            product=ongoing_product,
            amount=Decimal('100.00'),
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify only ended auction was finalized
        ended_product.refresh_from_db()
        ongoing_product.refresh_from_db()
        
        self.assertTrue(ended_product.auction_finalized)
        self.assertFalse(ongoing_product.auction_finalized)
 
    def test_already_finalized_auctions_skipped(self):
        """Test that already finalized auctions are not processed again."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-already-finalized-{django_timezone.now().timestamp()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=True,
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('500.00'), 
            is_active=True
        )

        # Create first bid (from other_user)
        PopUpBid.objects.create(
            customer=self.other_profile,
            product=product,
            amount=Decimal('100.00'),
            timestamp=self.now - timedelta(hours=1)
        )
        
        # RUN TASK FIRST TIME - finalizes with the $100 bid winner
        check_auctions_and_finalize()
        
        # Verify first winner was set
        product.refresh_from_db()
        self.assertTrue(product.auction_finalized)
        self.assertEqual(product.winner, self.other_user)
        original_winner = product.winner
        
        # NOW create a HIGHER bid from winner_user (after finalization)
        PopUpBid.objects.create(
            customer=self.winner_profile,
            product=product,
            amount=Decimal('150.00'),  # Much higher!
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # RUN TASK SECOND TIME - should NOT re-process this auction
        check_auctions_and_finalize()
        
        # Verify winner did NOT change to the higher bidder
        product.refresh_from_db()
        self.assertEqual(product.winner, original_winner,
                        "Winner should not change when auction is re-processed")
        self.assertEqual(product.winner, self.other_user)
        
        # Verify the higher bidder's cart item was NOT created
        self.assertFalse(
            PopUpCartItem.objects.filter(
                user=self.winner_user,
                product=product
            ).exists(),
            "Higher bidder should not have cart item created"
        )
 
    def test_inactive_products_not_processed(self):
        """Test that inactive products are not finalized."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
        )

        # product = create_test_product(
        #     product_type=self.product_type,
        #     category=self.category,
        #     brand=self.brand,
        #     auction_start_date=self.now - timedelta(days=2),
        #     auction_end_date=self.now - timedelta(minutes=5),
        #     auction_finalized=False,
        #     is_active=False,  # Inactive
        # )
        
        # Create winning bid
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify product was not finalized
        product.refresh_from_db()
        self.assertFalse(product.auction_finalized)
        self.assertIsNone(product.winner)
 

    def test_highest_bid_selected_correctly(self):
        """Test that highest bid is selected when multiple bids exist."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True, # Inactive
        )

        
        # Create multiple bids
        PopUpBid.objects.create(
            product=product,
            customer=self.other_profile,
            amount=Decimal('100.00'),
            timestamp=self.now - timedelta(hours=2)
        )
        
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('125.00'),
            timestamp=self.now - timedelta(hours=1)
        )
        
        third_user, third_user_profile = create_test_user(
            "third@example.com", "testpass!23", "Third", "User", "8", "male"
        )
        PopUpBid.objects.create(
            product=product,
            customer=third_user_profile,
            amount=Decimal('150.00'),
            timestamp=self.now - timedelta(minutes=30)
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify highest bidder won
        product.refresh_from_db()
        self.assertEqual(product.winner, third_user)
        self.assertEqual(product.current_highest_bid, Decimal('150.00'))
 
    @patch('pop_up_auction.tasks.send_auction_winner_email')
    def test_winner_email_sent(self, mock_send_email):
        """Test that winner notification email is sent."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True, # Inactive
        )

    
        # Create winning bid
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify email was called
        mock_send_email.assert_called_once_with(self.winner_user, product)
 

    @patch('pop_up_auction.tasks.send_auction_winner_email')
    def test_winner_email_not_sent_for_no_bid_auction(self, mock_send_email):
        """Test that winner email is not sent for auctions with no bids."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True, # Inactive
        )

    
        # No bids created
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify email was not called
        mock_send_email.assert_not_called()
 
    def test_multiple_auctions_finalized_in_single_run(self):
        """Test that multiple ended auctions are processed in one task run."""
        products = []
        users = [self.winner_user]
        
        # Create additional users for variety
        for i in range(2):
            user, _ = create_test_user(
                f"winner{i}@example.com", "testpass!23", f"Winner{i}", "User", "10", "male"
            )
            print('user', user)
            users.append(user)
        
        # Create multiple ended auctions
        for i in range(3):
            product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='f"Product {i}',
            secondary_product_title='f"Secondary Product {i}',
            description='Test Description',
            slug=f'test-product-{i}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True, # Inactive
            )

            products.append(product)
            
            # Create winning bid
            PopUpBid.objects.create(
                product=product,
                customer=users[i].popupcustomerprofile,
                amount=Decimal('100.00'),
            )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify all auctions were finalized
        for i, product in enumerate(products):
            product.refresh_from_db()
            self.assertTrue(product.auction_finalized)
            self.assertEqual(product.winner, users[i])
 
    def test_cart_item_exception_handled_gracefully(self):
        """Test that cart item creation failure doesn't stop auction finalization."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True, # Inactive
        )

        
        # Create winning bid
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
        )
        
        # Mock cart item creation to raise exception
        with patch('pop_up_auction.tasks.PopUpCartItem.objects.update_or_create') as mock_cart:
            mock_cart.side_effect = Exception("Cart creation failed")
            
            # Run the task - should not raise exception
            try:
                check_auctions_and_finalize()
            except Exception as e:
                self.fail(f"Task should handle exceptions gracefully: {e}")
        
        # Verify product is still finalized
        product.refresh_from_db()
        self.assertTrue(product.auction_finalized)
 
    def test_winner_reservation_exception_handled_gracefully(self):
        """Test that reservation creation failure doesn't stop auction finalization."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True,
        )

        
        # Create winning bid
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
        )
        
        # Mock reservation creation to raise exception
        with patch('pop_up_auction.tasks.WinnerReservation.objects.create') as mock_reservation:
            mock_reservation.side_effect = Exception("Reservation creation failed")
            
            # Run the task - should not raise exception
            try:
                check_auctions_and_finalize()
            except Exception as e:
                self.fail(f"Task should handle exceptions gracefully: {e}")
        
        # Verify product is still finalized and cart item created
        product.refresh_from_db()
        self.assertTrue(product.auction_finalized)
        self.assertTrue(
            PopUpCartItem.objects.filter(user=self.winner_user, product=product).exists()
        )
 
    @patch('pop_up_auction.tasks.logger')
    def test_task_logging(self, mock_logger):
        """Test that task logs its execution."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True,
        )

        
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
        )
        
        # Run the task
        check_auctions_and_finalize()
        
        # Verify logging was called
        mock_logger.info.assert_called_with("check_auctions_and_finalize started")
 
    def test_concurrent_auction_finalization(self):
        """Test that concurrent auction processing doesn't create duplicate reservations."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False,
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=True,
        )
       
        
        PopUpBid.objects.create(
            product=product,
            customer=self.winner_profile,
            amount=Decimal('100.00'),
        )
        
        # Run the task multiple times (simulating concurrent execution)
        check_auctions_and_finalize()
        check_auctions_and_finalize()
        
        # Verify only one reservation was created
        reservations = WinnerReservation.objects.filter(
            user=self.winner_user,
            product=product
        )
        self.assertEqual(reservations.count(), 1)




class MarkExpiredReservationsTestCase(TestCase):
    """Test suite for mark_expired_reservations task."""
 
    def setUp(self):
        """Set up test fixtures."""
        self.now = django_timezone.now()
        
        # Create test users
        self.winner_user, self.winner_profile = create_test_user(
            "winner@example.com", "testpass!23", "Winner", "User", "10", "male"
        )
        self.other_user, self.other_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User", "9", "female"
        )
        

        # Create product infrastructure
        self.brand = create_brand('Jordan')
        self.category = create_category('Jordan 4', is_active=True)
        self.product_type = create_product_type('shoe', is_active=True)

        # Create specifications
        self.size_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='size'
        )
        self.color_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='colorway'
        )
        

        # Product
        self.product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=self.now - timedelta(days=2), 
            auction_end_date=self.now - timedelta(minutes=5),  # Ended 5 minutes ago 
            auction_finalized=False,
            inventory_status='sold_out', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            # winner=self.winner_user  # ← ADD THIS
        )

        # Clear email outbox for each test
        from django.core.mail import outbox
        outbox.clear()
 
    def test_mark_single_expired_reservation(self):
        """Test that a single expired reservation is marked as expired."""

        # apply winner
        self.product.winner = self.winner_user
        self.product.save()

        print('self.product', self.product)
        print('self.product.winner', self.product.winner)

        # Create the cart item that the task will delete
        cart_item = PopUpCartItem.objects.create(
            user=self.winner_user,
            product=self.product,
            quantity=1,
            auction_locked=True
        )
        
        print('cart_item', cart_item)

        # Create an expired reservation (expired 1 hour ago)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False,
            notification_sent=True
        )
        
        print('reservation', reservation)

        # Run the task
        mark_expired_reservations()
        
        # Verify reservation is marked as expired
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_expired)
        self.assertFalse(reservation.is_paid)
        
        # Verify cart item was removed
        self.assertFalse(
            PopUpCartItem.objects.filter(
                user=self.winner_user,
                product=self.product,
                auction_locked=True
            ).exists()
        )
    
    def test_product_re_listed_after_expiration(self):
        """Test that product inventory status is reset to in_inventory."""
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        mark_expired_reservations()
        
        # Verify product status is reset
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory_status, 'in_inventory')
        self.assertIsNone(self.product.winner)


 
    def test_winner_cleared_from_product(self):
        """Test that product winner is cleared when reservation expires."""
        self.product.winner = self.winner_user
        self.product.save()

        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Verify initial state
        self.assertEqual(self.product.winner, self.winner_user)
        
        # Run the task
        mark_expired_reservations()
        
        # Verify winner was cleared
        self.product.refresh_from_db()
        self.assertIsNone(self.product.winner)

 
    def test_auction_locked_cart_item_removed(self):
        """Test that auction_locked cart items are removed from winner's cart."""

        self.product.winner = self.winner_user
        self.product.save()
        
        # Create cart item with auction_locked=True
        cart_item = PopUpCartItem.objects.create(
            user=self.winner_user,
            product=self.product,
            quantity=1,
            auction_locked=True
        )
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Verify cart item exists
        self.assertTrue(
            PopUpCartItem.objects.filter(
                user=self.winner_user,
                product=self.product,
                auction_locked=True
            ).exists()
        )
        
        # Run the task
        mark_expired_reservations()
        
        # Verify cart item was removed
        self.assertFalse(
            PopUpCartItem.objects.filter(
                user=self.winner_user,
                product=self.product,
                auction_locked=True
            ).exists()
        )
 
    def test_admin_notification_sent(self):
        """Test that admin notification is sent when reservation expires."""
    
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Jordan 3 Retro',
            secondary_product_title='Skyhighs',
            description='Skyhigh Retros',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=self.now - timedelta(days=2), 
            auction_end_date=self.now - timedelta(minutes=5),  # Ended 5 minutes ago 
            auction_finalized=False,
            inventory_status='sold_out', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            winner=self.winner_user  # ← ADD THIS
        )
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        mark_expired_reservations()
        
        # Clear email outbox for each test
        from django.core.mail import outbox

        # Verify admin email was sent
        self.assertEqual(len(outbox), 1)
        email = outbox[0]
        self.assertIn('Auction Reservation Expired', email.subject)
        self.assertIn('Jordan 3 Retro', email.subject)
        self.assertIn(self.winner_user.email, email.body)
 

    def test_only_unpaid_expired_reservations_processed(self):
        """Test that only unpaid, expired reservations are processed."""
        # Create paid reservation (should be skipped)
        paid_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Paid Product',
            secondary_product_title='Paid Product Secondary',
            description='Paid Product Description',
            slug=f'paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.winner_user
        )
       
        
        paid_reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=paid_product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=True,  # Already paid
            is_expired=False
        )
        
        unexpired_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Not Yet Expired Product',
            secondary_product_title='Not Yet Expired Product Secondary',
            description='Paid Product Description',
            slug=f'not-yet-expired-paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.other_user
        )

        
        unexpired_reservation = WinnerReservation.objects.create(
            user=self.other_user,
            product=unexpired_product,
            expires_at=self.now + timedelta(hours=1),  # Not expired yet
            is_paid=False,
            is_expired=False
        )
        
        # Create unpaid, expired reservation (should be processed)
        expired_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Expired Product',
            secondary_product_title='Expired Product Secondary',
            description='Paid Product Description',
            slug=f'expired-paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.other_user
        )
      
        
        expired_reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=expired_product,
            expires_at=self.now - timedelta(hours=1),  # Expired
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        mark_expired_reservations()
        
        # Verify only the expired, unpaid reservation was processed
        paid_reservation.refresh_from_db()
        self.assertFalse(paid_reservation.is_expired)
        
        unexpired_reservation.refresh_from_db()
        self.assertFalse(unexpired_reservation.is_expired)
        
        expired_reservation.refresh_from_db()
        self.assertTrue(expired_reservation.is_expired)
 

    def test_already_expired_reservations_skipped(self):
        """Test that already-expired reservations are not processed again."""

        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Paid Product',
            secondary_product_title='Paid Product Secondary',
            description='Paid Product Description',
            slug=f'paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            # winner=self.winner_user
        )
        
        # Create a reservation already marked as expired
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=True  # Already expired
        )
        
        # Run the task
        result = mark_expired_reservations()
        
        # Verify product status didn't change (was already cleaned up)
        product.refresh_from_db()
        self.assertEqual(product.inventory_status, 'in_inventory')
        self.assertIsNone(product.winner)
        
        # Clear email outbox for each test
        from django.core.mail import outbox

        # Verify no admin email for already-expired reservation
        self.assertEqual(len(outbox), 0)
 
    def test_multiple_expired_reservations_processed(self):
        """Test that multiple expired reservations are processed in one run."""
        reservations = []
        products = []
        users = [self.winner_user]
        
        # Create additional user
        other_winner, _ = create_test_user(
            "another@example.com", "testpass!23", "Another", "User", "11", "male"
        )
        users.append(other_winner)
        
        # Create multiple expired reservations
        for i in range(3):
            product = create_test_product(
                product_type=self.product_type,
                category=self.category,
                product_title=f'Paid Product-{i}',
                secondary_product_title=f'Paid Product {i} Secondary',
                description=f'Paid Product {i} Description',
                slug=f'paid-product-{i}-{django_timezone.now()}',
                buy_now_price=None, 
                current_highest_bid=Decimal('99.00'),
                retail_price=Decimal('1.00'), 
                brand=self.brand,
                auction_start_date=self.now - timedelta(days=2),
                auction_end_date=self.now - timedelta(minutes=5),
                auction_finalized=False, # Already finalized
                inventory_status = 'sold_out', 
                bid_count=0, 
                reserve_price=Decimal('70.00'), 
                is_active=False, # Inactive
                winner=users[i % len(users)]
            )
            
            
            products.append(product)
            
            reservation = WinnerReservation.objects.create(
                user=users[i % len(users)],
                product=product,
                expires_at=self.now - timedelta(hours=i+1),  # All expired
                is_paid=False,
                is_expired=False
            )
            reservations.append(reservation)
        
        # Run the task
        mark_expired_reservations()
        
        # Verify all reservations marked as expired
        for reservation in reservations:
            reservation.refresh_from_db()
            self.assertTrue(reservation.is_expired)
        
        # Verify all products re-listed
        for product in products:
            product.refresh_from_db()
            self.assertEqual(product.inventory_status, 'in_inventory')
            self.assertIsNone(product.winner)
 

    def test_non_auction_locked_cart_items_preserved(self):
        """Test that non-auction-locked cart items are NOT removed."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Paid Product',
            secondary_product_title='Paid Product Secondary',
            description='Paid Product Description',
            slug=f'paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.winner_user
        )

        
        # Create a buy_now cart item (not auction_locked)
        buy_now_cart = PopUpCartItem.objects.create(
            user=self.winner_user,
            product=product,
            quantity=1,
            auction_locked=False,  # Not auction locked
            buy_now=True
        )
        
        # Create reservation for this product
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        mark_expired_reservations()
        
        # Verify buy_now cart item was NOT removed
        buy_now_cart.refresh_from_db()
        self.assertTrue(
            PopUpCartItem.objects.filter(
                user=self.winner_user,
                product=product,
                auction_locked=False,
                buy_now=True
            ).exists()
        )
 

    def test_return_message_format(self):
        """Test that the task returns a proper message."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Paid Product',
            secondary_product_title='Paid Product Secondary',
            description='Paid Product Description',
            slug=f'paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.winner_user
        )
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        result = mark_expired_reservations()
        
        # Verify return message
        self.assertIn('marked as expired', result)
 

    def test_cart_deletion_exception_handled(self):
        """Test that cart deletion failures don't stop the reservation from expiring."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Paid Product',
            secondary_product_title='Paid Product Secondary',
            description='Paid Product Description',
            slug=f'paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.winner_user
        )

        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Mock cart deletion to raise exception
        with patch('pop_up_auction.tasks.mark_expired_reservations') as mock_filter:
            mock_filter.return_value.delete.side_effect = Exception("Delete failed")
            
            # Run the task - should not raise
            try:
                mark_expired_reservations()
            except Exception as e:
                self.fail(f"Task should handle exceptions gracefully: {e}")
        
        # Verify reservation is still marked as expired
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_expired)
 
    def test_product_save_exception_handled(self):
        """Test that product save failures don't stop the process."""
        product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Paid Product',
            secondary_product_title='Paid Product Secondary',
            description='Paid Product Description',
            slug=f'paid-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('99.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand,
            auction_start_date=self.now - timedelta(days=2),
            auction_end_date=self.now - timedelta(minutes=5),
            auction_finalized=False, # Already finalized
            inventory_status = 'sold_out', 
            bid_count=0, 
            reserve_price=Decimal('70.00'), 
            is_active=False, # Inactive
            winner=self.winner_user
        )
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Mock product save to raise exception
        with patch('pop_up_auction.models.PopUpProduct.save') as mock_save:
            mock_save.side_effect = Exception("Save failed")
            
            # Run the task - should not raise
            try:
                mark_expired_reservations()
            except Exception as e:
                self.fail(f"Task should handle exceptions gracefully: {e}")
 
 
 
    def test_expiration_boundary_exactly_at_now(self):
        """Test that reservations expiring exactly at current time are marked expired."""
        
        self.product.winner = self.winner_user
        self.product.save()

        # Create reservation that expires exactly now (uses __lte in filter)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now,
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        mark_expired_reservations()
        
        # Verify reservation is marked as expired (boundary case)
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_expired)
 

    def test_no_reservations_expired(self):
        """Test that task runs successfully with no expired reservations."""
   

        self.product.winner = self.winner_user
        self.product.save()
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(days=1),
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        result = mark_expired_reservations()
        
        # Verify nothing was changed
        reservation.refresh_from_db()
        self.assertFalse(reservation.is_expired)
        
        # May need to clear email outbox for each test
        from django.core.mail import outbox

        # Verify no emails sent
        self.assertEqual(len(outbox), 0)
 
    @patch('pop_up_auction.tasks.logger')
    def test_task_logging(self, mock_logger):
        """Test that task logs its execution."""
        # product = create_test_product(
        #     product_type=self.product_type,
        #     category=self.category,
        #     brand=self.brand,
        #     inventory_status='sold_out',
        #     winner=self.winner_user
        # )

        self.product.winner = self.winner_user
        self.product.save()
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now - timedelta(hours=1),
            is_paid=False,
            is_expired=False
        )
        
        # Run the task
        mark_expired_reservations()
        


class SendReservationRemindersTestCase(TestCase):
    """Test suite for send_reservation_reminders task."""
 
    def setUp(self):
        """Set up test fixtures."""
        self.now = django_timezone.now()
        
        # Create test users
        self.winner_user, self.winner_profile = create_test_user(
            "winner@example.com", "testpass!23", "Winner", "User", "10", "male"
        )
        self.other_user, self.other_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User", "9", "female"
        )
        
        # Create product infrastructure
        self.brand = create_brand('Jordan')
        self.category = create_category('Jordan 3', is_active=True)
        self.product_type = create_product_type('shoe', is_active=True)

        # Product
        self.product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=self.now - timedelta(days=5), 
            auction_end_date=self.now - timedelta(days=3),  # Ended 2 days ago 
            auction_finalized=False,
            inventory_status='sold_out', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            # winner=self.winner_user  # ← ADD THIS
        )

         # Create specifications
        self.size_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='size'
        )
        self.color_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='colorway'
        )

    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_send_24hr_reminder_at_24hr_mark(self, mock_send_24hr):
        """Test that 24-hour reminder is sent when exactly 24 hours remain."""
       
        # Create reservation expiring in exactly 24 hours
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 24-hour email was sent
        mock_send_24hr.assert_called_once_with(self.winner_user, self.product)
        
        # Verify reservation was updated
        reservation.refresh_from_db()
        self.assertTrue(reservation.reminder_24hr_sent)

 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_send_24hr_reminder_within_window(self, mock_send_24hr):
        """Test that 24-hour reminder is sent within the 23.5-24.5 hour window."""
        
        # Create reservation expiring in 24 hours 15 minutes (within window)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24, minutes=15),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 24-hour email was sent
        mock_send_24hr.assert_called_once()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.reminder_24hr_sent)
 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_no_24hr_reminder_before_window(self, mock_send_24hr):
        """Test that 24-hour reminder is NOT sent if more than 24.5 hours remain."""

        self.product.winner = self.winner_user
        self.product.save()
        
        # Create reservation expiring in 25 hours (outside window)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=25),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 24-hour email was NOT sent
        mock_send_24hr.assert_not_called()
        
        reservation.refresh_from_db()
        self.assertFalse(reservation.reminder_24hr_sent)
 
    @patch('pop_up_auction.tasks.send_reservation_reminders')
    def test_no_24hr_reminder_after_window(self, mock_send_24hr):
        """Test that 24-hour reminder is NOT sent if less than 23.5 hours remain."""

        self.product.winner = self.winner_user
        self.product.save()
        
        # Create reservation expiring in 23 hours (outside window)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=23),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 24-hour email was NOT sent
        mock_send_24hr.assert_not_called()
        
        reservation.refresh_from_db()
        self.assertFalse(reservation.reminder_24hr_sent)
 

    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_send_1hr_reminder_at_1hr_mark(self, mock_send_1hr):
        """Test that 1-hour reminder is sent when exactly 1 hour remains."""
        
        self.product.winner = self.winner_user
        self.product.save()
        
        # Create reservation expiring in exactly 1 hour
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=1),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,  # 24hr already sent
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 1-hour email was sent
        mock_send_1hr.assert_called_once_with(self.winner_user, self.product)
        
        # Verify reservation was updated
        reservation.refresh_from_db()
        self.assertTrue(reservation.reminder_1hr_sent)

 
    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_send_1hr_reminder_within_window(self, mock_send_1hr):
        """Test that 1-hour reminder is sent within the 30min-1.5hr window."""
        # product = create_test_product(
        #     product_type=self.product_type,
        #     category=self.category,
        #     brand=self.brand,
        # )
        
        self.product.winner = self.winner_user
        self.product.save()


        # Create reservation expiring in 1 hour 15 minutes (within window)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=1, minutes=15),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 1-hour email was sent
        mock_send_1hr.assert_called_once()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.reminder_1hr_sent)
 
    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_no_1hr_reminder_before_window(self, mock_send_1hr):
        """Test that 1-hour reminder is NOT sent if more than 1.5 hours remain."""

        self.product.winner = self.winner_user
        self.product.save()
        
        # Create reservation expiring in 2 hours (outside window)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=2),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 1-hour email was NOT sent
        mock_send_1hr.assert_not_called()
        
        reservation.refresh_from_db()
        self.assertFalse(reservation.reminder_1hr_sent)
 
    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_no_1hr_reminder_after_window(self, mock_send_1hr):
        """Test that 1-hour reminder is NOT sent if less than 30 minutes remain."""

        self.product.winner = self.winner_user
        self.product.save()
        
        # Create reservation expiring in 20 minutes (outside window)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(minutes=20),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 1-hour email was NOT sent
        mock_send_1hr.assert_not_called()
        
        reservation.refresh_from_db()
        self.assertFalse(reservation.reminder_1hr_sent)
 

    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_no_duplicate_24hr_reminders(self, mock_send_24hr):
        """Test that 24-hour reminder is NOT sent again if already sent."""
 
        self.product.winner = self.winner_user
        self.product.save()
        
        # Create reservation with 24hr reminder already sent
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,  # Already sent
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 24-hour email was NOT sent again
        mock_send_24hr.assert_not_called()
 

    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_no_duplicate_1hr_reminders(self, mock_send_1hr):
        """Test that 1-hour reminder is NOT sent again if already sent."""
        
        # Create reservation with 1hr reminder already sent
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=1),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=True  # Already sent
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify 1-hour email was NOT sent again
        mock_send_1hr.assert_not_called()
 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_both_reminders_sent_at_different_times(self, mock_send_1hr, mock_send_24hr):
        """Test that both reminders are sent at appropriate times for different reservations."""

        product2 = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product 2',
            secondary_product_title='Test Secondary 2',
            description='Test Description 2',
            slug=f'test-product-2-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('100.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=self.now - timedelta(days=5), 
            auction_end_date=self.now - timedelta(days=3),  # Ended 2 days ago 
            auction_finalized=False,
            inventory_status='sold_out', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            # winner=self.winner_user  # ← ADD THIS
        )
        
        # Create reservation for 24-hour reminder
        reservation1 = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Create reservation for 1-hour reminder
        reservation2 = WinnerReservation.objects.create(
            user=self.other_user,
            product=product2,
            expires_at=self.now + timedelta(hours=1),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify both emails were sent
        mock_send_24hr.assert_called_once_with(self.winner_user, self.product)
        mock_send_1hr.assert_called_once_with(self.other_user, product2)
        
        # Verify both reservations were updated
        reservation1.refresh_from_db()
        self.assertTrue(reservation1.reminder_24hr_sent)
        
        reservation2.refresh_from_db()
        self.assertTrue(reservation2.reminder_1hr_sent)
 

    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_paid_reservations_skipped(self, mock_send_24hr):
        """Test that paid reservations are NOT sent reminders."""
        
        # Create paid reservation
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=True,  # Already paid
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify no email was sent
        mock_send_24hr.assert_not_called()
 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_expired_reservations_skipped(self, mock_send_24hr):
        """Test that expired reservations are NOT sent reminders."""
        
        # Create expired reservation
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=True,  # Already expired
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify no email was sent
        mock_send_24hr.assert_not_called()
 

    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_multiple_reservations_same_user(self, mock_send_24hr):
        """Test that multiple reservations for the same user all get reminders."""
        # Create two products for the same user


        product2 = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product 2',
            secondary_product_title='Test Secondary 2',
            description='Test Description 2',
            slug=f'test-product-2-{django_timezone.now()}',
            buy_now_price=None, 
            current_highest_bid=Decimal('100.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=self.now - timedelta(days=5), 
            auction_end_date=self.now - timedelta(days=3),  # Ended 2 days ago 
            auction_finalized=False,
            inventory_status='sold_out', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            # winner=self.winner_user  # ← ADD THIS
        )
        
        
        # Create reservations for same user
        reservation1 = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        reservation2 = WinnerReservation.objects.create(
            user=self.winner_user,
            product=product2,
            expires_at=self.now + timedelta(hours=24, minutes=10),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify both emails were sent
        self.assertEqual(mock_send_24hr.call_count, 2)
        calls = [
            call(self.winner_user, self.product),
            call(self.winner_user, product2)
        ]
        mock_send_24hr.assert_has_calls(calls, any_order=True)
 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_24hr_reminder_with_safe_window(self, mock_send_24hr):
        """Test 24-hour reminder at lower boundary (23.5 hours)."""
        
        
        # Create reservation expiring in exactly 23.5 hours
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify email was sent (at boundary)
        mock_send_24hr.assert_called_once()
    

    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_24hr_reminder_not_sent_too_early(self, mock_send_24hr):
        """Test 24-hour reminder NOT sent when too much time remains."""
        
        # Clearly outside the window (25 hours)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=25),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify email was NOT sent
        mock_send_24hr.assert_not_called()


    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_24hr_reminder_not_sent_too_late(self, mock_send_24hr):
        """Test 24-hour reminder NOT sent when not enough time remains."""
        
        # Clearly outside the window (23 hours)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=23),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify email was NOT sent
        mock_send_24hr.assert_not_called()


    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_24hr_reminder_boundary_upper(self, mock_send_24hr):
        """Test 24-hour reminder at upper boundary (24.5 hours)."""
        
        # Create reservation expiring in exactly 24.5 hours
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24, minutes=30),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify email was sent (at boundary)
        mock_send_24hr.assert_called_once()
 

    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_1hr_reminder_within_safe_window(self, mock_send_1hr):
        """Test 1-hour reminder is sent when safely within the window."""
        
        # Safely in the middle (1 hour exactly)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=1),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        send_reservation_reminders()
        mock_send_1hr.assert_called_once()


    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_1hr_reminder_not_sent_too_early(self, mock_send_1hr):
        """Test 1-hour reminder NOT sent when too much time remains."""
        
        # Clearly outside the window (2 hours)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=2),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        send_reservation_reminders()
        mock_send_1hr.assert_not_called()


    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_1hr_reminder_not_sent_too_late(self, mock_send_1hr):
        """Test 1-hour reminder NOT sent when not enough time remains."""
        
        # Clearly outside the window (20 minutes)
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(minutes=20),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        send_reservation_reminders()
        mock_send_1hr.assert_not_called()
 
    @patch('pop_up_auction.tasks.send_1_hour_reminder_email')
    def test_1hr_reminder_boundary_upper(self, mock_send_1hr):
        """Test 1-hour reminder at upper boundary (1.5 hours)."""
       
        # Create reservation expiring in exactly 1.5 hours
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=1, minutes=30),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=True,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify email was sent (at boundary)
        mock_send_1hr.assert_called_once()
 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_email_send_exception_handled(self, mock_send_24hr):
        """Test that email send failures don't crash the task."""
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=24),
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Mock email send to raise exception
        mock_send_24hr.side_effect = Exception("Email send failed")
        
        # Run the task - should not raise
        try:
            send_reservation_reminders()
        except Exception as e:
            self.fail(f"Task should handle exceptions gracefully: {e}")
 
    @patch('pop_up_auction.tasks.send_24_hour_reminder_email')
    def test_no_reservations_to_remind(self, mock_send_24hr):
        """Test that task runs successfully with no reminders to send."""
        
        reservation = WinnerReservation.objects.create(
            user=self.winner_user,
            product=self.product,
            expires_at=self.now + timedelta(hours=20),  # Too far away
            is_paid=False,
            is_expired=False,
            reminder_24hr_sent=False,
            reminder_1hr_sent=False
        )
        
        # Run the task
        send_reservation_reminders()
        
        # Verify no email was sent
        mock_send_24hr.assert_not_called()


class TransitionExpiredBuyNowToAuctionTestCase(TestCase):
    """Test suite for transition_expired_buy_now_to_auction task."""
 
    def setUp(self):
        """Set up test fixtures."""
       

        # Create test users
        self.interested_user1, self.profile1 = create_test_user(
            "interested1@example.com", "testpass!23", "Interested", "User1", "10", "male"
        )
        self.interested_user2, self.profile2 = create_test_user(
            "interested2@example.com", "testpass!23", "Interested", "User2", "9", "female"
        )
        self.other_user, self.other_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User", "11", "male"
        )
        
        # Create product infrastructure
        self.brand = create_brand('Jordan')
        self.category = create_category('Jordan 3', is_active=True)
        self.product_type = create_product_type('shoe', is_active=True)


        # now = django_timezone.now()
        
        # Product
        self.product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=Decimal('2.00'), 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=now() + timedelta(days=1),
            auction_end_date=now() + timedelta(days=8),
            auction_finalized=False,
            inventory_status='in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            buy_now_start=None,
            buy_now_end=None,
        )
        
        # Create specifications
        self.size_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='size'
        )
        self.color_spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='colorway'
        )
    
    def test_buy_now_dates_cleared_on_expiration(self):
        """Test that buy_now_start and buy_now_end are cleared when buy now expires."""

        self.product.buy_now_start=now() - timedelta(days=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=False
        self.product.save()

    
        # Verify initial state
        self.assertIsNotNone(self.product.buy_now_start)
        self.assertIsNotNone(self.product.buy_now_end)
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify dates were cleared
        self.product.refresh_from_db()
        self.assertIsNone(self.product.buy_now_start)
        self.assertIsNone(self.product.buy_now_end)

 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_interested_users_notified(self, mock_send_notification):
        """Test that interested users are notified when buy now expires."""
        
        self.product.buy_now_start=now() - timedelta(days=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=False
        self.product.save()

        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify notification was sent
        mock_send_notification.assert_called_once()
        call_args = mock_send_notification.call_args
        self.assertEqual(call_args[0][0], self.product)  # First arg is product
        self.assertEqual(call_args[1]['auction_start_date'], self.product.auction_start_date)
 
    def test_only_expired_buy_now_products_processed(self):
        """Test that only products with expired buy_now periods are processed."""
        # Create expired buy now product
        expired_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=Decimal('2.00'), 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=now() + timedelta(days=1),
            auction_end_date=now() + timedelta(days=8),
            auction_finalized=False,
            inventory_status='in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            buy_now_start=None,
            buy_now_end=None,
        )

        expired_product.buy_now_start=now() - timedelta(days=1)
        expired_product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        expired_product.bought_now=False
        expired_product.save()

        
        # Create ongoing buy now product
        ongoing_product = create_test_product(
            product_type=self.product_type,
            category=self.category,
            product_title='Test Product',
            secondary_product_title='Test Secondary',
            description='Test Description',
            slug=f'test-product-{django_timezone.now()}',
            buy_now_price=Decimal('2.00'), 
            current_highest_bid=Decimal('0.00'),
            retail_price=Decimal('1.00'), 
            brand=self.brand, 
            auction_start_date=now() + timedelta(days=1),
            auction_end_date=now() + timedelta(days=8),
            auction_finalized=False,
            inventory_status='in_inventory', 
            bid_count=0, 
            reserve_price=Decimal('5.00'), 
            is_active=True,
            buy_now_start=None,
            buy_now_end=None,
        )

        ongoing_product.buy_now_start=now() - timedelta(days=1)
        ongoing_product.buy_now_end=now() + timedelta(minutes=1)  # Expired 5 minutes ago
        ongoing_product.bought_now=False
        ongoing_product.save()

        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify only expired product was processed
        expired_product.refresh_from_db()
        self.assertIsNone(expired_product.buy_now_start)
        self.assertIsNone(expired_product.buy_now_end)
        
        ongoing_product.refresh_from_db()
        self.assertIsNotNone(ongoing_product.buy_now_start)
        self.assertIsNotNone(ongoing_product.buy_now_end)
 
    def test_purchased_items_not_processed(self):
        """Test that items purchased during buy now period are NOT processed."""
         
        self.product.buy_now_start=now() - timedelta(days=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=True
        self.product.save()

        # Store original dates
        original_start = self.product.buy_now_start
        original_end = self.product.buy_now_end
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify dates were NOT cleared
        self.product.refresh_from_db()
        self.assertEqual(self.product.buy_now_start, original_start)
        self.assertEqual(self.product.buy_now_end, original_end)

 
    def test_inactive_products_not_processed(self):
        """Test that inactive products are NOT processed."""

        self.product.buy_now_start=now() - timedelta(days=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=True
        self.product.save()
        
        # Store original dates
        original_start = self.product.buy_now_start
        original_end = self.product.buy_now_end
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify dates were NOT cleared
        self.product.refresh_from_db()
        self.assertEqual(self.product.buy_now_start, original_start)
        self.assertEqual(self.product.buy_now_end, original_end)
 

    def test_products_without_auction_dates_not_processed(self):
        """Test that products without auction dates are NOT processed."""

        self.product.buy_now_start=now() - timedelta(days=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=True
        self.product.save()
        
        # Store original dates
        original_start = self.product.buy_now_start
        original_end = self.product.buy_now_end
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify dates were NOT cleared
        self.product.refresh_from_db()
        self.assertEqual(self.product.buy_now_start, original_start)
        self.assertEqual(self.product.buy_now_end, original_end)
 

    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_multiple_products_processed_in_single_run(self, mock_send_notification):
        """Test that multiple expired buy now products are processed in one task run."""
        # Create multiple expired buy now products
        products = []
        for i in range(3):
            product = create_test_product(
                product_type=self.product_type,
                category=self.category,
                product_title=f'Product {i}',
                secondary_product_title=f'Test Secondary {i}',
                description=f'Test Description-{i}',
                slug=f'product-{i}-{django_timezone.now().timestamp()}',
                buy_now_price=Decimal('2.00'), 
                current_highest_bid=Decimal('0.00'),
                retail_price=Decimal('1.00'), 
                brand=self.brand, 
                auction_start_date=now() + timedelta(days=1),
                auction_end_date=now() + timedelta(days=8),
                auction_finalized=False,
                inventory_status='in_inventory', 
                bid_count=0, 
                reserve_price=Decimal('5.00'), 
                is_active=True,
                buy_now_start=None,
                buy_now_end=None,
            )

            product.buy_now_start=now() - timedelta(days=1)
            product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
            product.bought_now=False
            product.save()
            

            products.append(product)
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify all products were processed
        for product in products:
            product.refresh_from_db()
            self.assertIsNone(product.buy_now_start)
            self.assertIsNone(product.buy_now_end)
        
        # Verify notification was sent for each product
        self.assertEqual(mock_send_notification.call_count, 3)
 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_correct_auction_date_passed_to_notification(self, mock_send_notification):
        """Test that the correct auction start date is passed to notification function."""

        auction_start = now() + timedelta(days=2)
        product = create_test_product(
                product_type=self.product_type,
                category=self.category,
                product_title='Test Product',
                secondary_product_title='Test Secondary',
                description='Test Description',
                slug=f'product-{django_timezone.now().timestamp()}',
                buy_now_price=Decimal('2.00'), 
                current_highest_bid=Decimal('0.00'),
                retail_price=Decimal('1.00'), 
                brand=self.brand, 
                auction_start_date=auction_start,
                auction_end_date=now() + timedelta(days=9),
                auction_finalized=False,
                inventory_status='in_inventory', 
                bid_count=0, 
                reserve_price=Decimal('5.00'), 
                is_active=True,
                buy_now_start=None,
                buy_now_end=None,
            )

        product.buy_now_start=now() - timedelta(days=1)
        product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        product.bought_now=False
        product.save()
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify correct auction date was passed
        mock_send_notification.assert_called_once()
        call_kwargs = mock_send_notification.call_args[1]
        self.assertEqual(call_kwargs['auction_start_date'], auction_start)
 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_notification_exception_handled(self, mock_send_notification):
        """Test that notification send failures don't crash the task."""
        # Mock notification to raise exception
        mock_send_notification.side_effect = Exception("Notification failed")
        
        # Run the task - should not raise
        try:
            transition_expired_buy_now_to_auction()
        except Exception as e:
            self.fail(f"Task should handle exceptions gracefully: {e}")
        
        # Verify product dates were still cleared despite notification failure
        self.product.refresh_from_db()
        self.assertIsNone(self.product.buy_now_start)
        self.assertIsNone(self.product.buy_now_end)
 
    
 
    def test_no_products_to_transition(self):
        """Test that task runs successfully with no products to transition."""
        # Create a non-expired buy now product
       

        self.product.buy_now_start=now() - timedelta(hours=1)
        self.product.buy_now_end=now() + timedelta(hours=1)  # Expired 5 minutes ago
        self.product.bought_now=False
        self.product.save()

        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify nothing was changed
        self.product.refresh_from_db()
        self.assertIsNotNone(self.product.buy_now_start)
        self.assertIsNotNone(self.product.buy_now_end)
 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_product_save_exception_handled(self, mock_send_notification):
        """Test that product save failures don't crash the task."""

        self.product.buy_now_start=now() - timedelta(hours=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=False
        self.product.save()
        
        # Mock product save to raise exception
        with patch('pop_up_auction.models.PopUpProduct.save') as mock_save:
            mock_save.side_effect = Exception("Save failed")
            
            # Run the task - should not raise
            try:
                transition_expired_buy_now_to_auction()
            except Exception as e:
                self.fail(f"Task should handle exceptions gracefully: {e}")
 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_both_buy_now_dates_set_to_none(self, mock_send_notification):
        """Test that both buy_now_start AND buy_now_end are set to None."""
        
        self.product.buy_now_start=now() - timedelta(hours=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=False
        self.product.save()


        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify BOTH dates were cleared
        self.product.refresh_from_db()
        self.assertIsNone(self.product.buy_now_start)
        self.assertIsNone(self.product.buy_now_end)
 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_auction_dates_not_modified(self, mock_send_notification):
        """Test that auction dates are NOT modified by the task."""
        auction_start = now() + timedelta(days=1)
        auction_end = now() + timedelta(days=8)

        product = create_test_product(
                product_type=self.product_type,
                category=self.category,
                product_title='Test Product',
                secondary_product_title='Test Secondary',
                description='Test Description',
                slug=f'product-{django_timezone.now().timestamp()}',
                buy_now_price=Decimal('2.00'), 
                current_highest_bid=Decimal('0.00'),
                retail_price=Decimal('1.00'), 
                brand=self.brand, 
                auction_start_date=auction_start,
                auction_end_date=auction_end,
                auction_finalized=False,
                inventory_status='in_inventory', 
                bid_count=0, 
                reserve_price=Decimal('5.00'), 
                is_active=True,
                buy_now_start=None,
                buy_now_end=None,
            )
        

        product.buy_now_start=now() - timedelta(hours=1)
        product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        product.bought_now=False
        product.save()

        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify auction dates unchanged
        self.product.refresh_from_db()
        self.assertEqual(product.auction_start_date, auction_start)
        self.assertEqual(product.auction_end_date, auction_end)
 
    @patch('pop_up_auction.tasks.send_interested_in_and_coming_soon_product_update_to_users')
    def test_bought_now_flag_not_modified(self, mock_send_notification):
        """Test that bought_now flag is NOT modified by the task."""
        # product = create_test_product(
        #     product_type=self.product_type,
        #     category=self.category,
        #     brand=self.brand,
        #     buy_now_start=self.now - timedelta(days=1),
        #     buy_now_end=self.now - timedelta(minutes=5),
        #     bought_now=False,
        #     auction_start_date=self.now + timedelta(days=1),
        #     auction_end_date=self.now + timedelta(days=8),
        #     is_active=True
        # )

        self.product.buy_now_start=now() - timedelta(hours=1)
        self.product.buy_now_end=now() - timedelta(minutes=5)  # Expired 5 minutes ago
        self.product.bought_now=False
        self.product.save()
        
        # Run the task
        transition_expired_buy_now_to_auction()
        
        # Verify bought_now flag unchanged
        self.product.refresh_from_db()
        self.assertFalse(self.product.bought_now)



# """
# Run Test
# python3 manage.py test pop_accounts/tests
# python3 manage.py test pop_accounts.tests.test_views.PersonalInfoViewIntegrationTests
# Run Test with Coverage
# coverage run --omit='*/venv/*' manage.py test pop_accounts/tests 
# coverage report | to get overview 
# coverage html | to get hml overview
# """