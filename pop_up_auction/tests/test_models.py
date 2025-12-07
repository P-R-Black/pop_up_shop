from django.forms import ValidationError
from django.test import TestCase
from pop_accounts.models import (PopUpCustomerProfile, PopUpBid)
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, 
                            PopUpProductType, PopUpProductSpecification, WinnerReservation,
                            PopUpProductSpecificationValue, PopUpProductImage)

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime 

from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta
from freezegun import freeze_time
from unittest.mock import patch
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def create_test_user(email, password, first_name, last_name, shoe_size, size_gender, **kwargs):
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        **kwargs
    )
    profile = PopUpCustomerProfile.objects.get(user=user)    
    profile.shoe_size = shoe_size
    profile.size_gender = size_gender
    profile.save()


    return user, profile


"""
Tests In Order
 1.  TestPopUpBrandModel
 2.  TestPopUpCategoryModel
 3.  TestPopUpTypesModel
 4.  TestPopUpProductModel
 5.  TestPopUpProductSpecificationModel
 6.  TestPopUpProductSpecificationValueModel
 7.  TestPopUpProductImageModel
 8.  TestWinnerReservationModel
"""

class TestPopUpBrandModel(TestCase):
    def setUp(self):
        self.brand_one = PopUpBrand.objects.create(name='Nike', slug='nike')
        self.brand_two = PopUpBrand.objects.create(name='Fear of God', slug='fear-of-god')

    
    def test_brand_mode_entry(self):
        """
        Test Brand model data insertion/types field attributes
        """
        brand_one = self.brand_one
        brand_two = self.brand_two
        self.assertTrue(isinstance(brand_one, PopUpBrand))
        self.assertTrue(isinstance(brand_two, PopUpBrand))


class TestPopUpCategoryModel(TestCase):

    def setUp(self):
        self.data_one = PopUpCategory.objects.create(name='Jordan 11', slug='jordan-11')
        self.data_two = PopUpCategory.objects.create(name='Collectable', slug='collectable')
    
    def test_category_model_entry(self):
        """
        Test Category model data insertion/types.field attributes
        """
        data_one = self.data_one
        data_two = self.data_two
        self.assertTrue(isinstance(data_one, PopUpCategory))
        self.assertTrue(isinstance(data_two, PopUpCategory))


class TestPopUpTypesModel(TestCase):

    def setUp(self):
        self.data_one = PopUpProductType.objects.create(name='shoe', slug='shoe')
        self.data_two = PopUpProductType.objects.create(name='gaming system', slug='gaming-system')
    
    def test_type_model_entry(self):
        """
        Test Type model data insertion/types field attributes
        """
        data_one = self.data_one
        data_two = self.data_two
        self.assertTrue(isinstance(data_one, PopUpProductType))
        self.assertEqual(str(data_one), 'shoe')

        self.assertTrue(isinstance(data_two, PopUpProductType))
        self.assertEqual(str(data_two), 'gaming system')
    

class PopUpProductModelTest(TestCase):
    """Comprehensive test suite for PopUpProduct model"""

    def setUp(self):
        """Create test data"""
        # Create required foreign key objects
        self.product_type = PopUpProductType.objects.create(
            name="Sneakers",
            slug="sneakers"
        )
        self.category = PopUpCategory.objects.create(
            name="Jordan 3",
            slug="jordan-3"
        )
        self.brand = PopUpBrand.objects.create(
            name="Jordan",
            slug="jordan"
        )
        
        # Create user for winner tests
        self.user, self.profile_user = create_test_user('winner@example.com', 'testPass!23', 'Test', 'User', '9', 'male')
        self.user.is_active = True
        self.user.save()



    # ========================================
    # BASIC CRUD TESTS
    # ========================================     

    def test_create_product(self):
        """Test creating a basic product"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            is_active=True
        )
        
        self.assertEqual(product.product_title, "Jordan 3 Retro")
        self.assertEqual(product.retail_price, Decimal("150.00"))
        self.assertTrue(product.is_active)

    def test_slug_auto_generated(self):
        """Test that slug is automatically generated from product_title"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro OG",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(product.slug, "jordan-3-retro-og")

    def test_slug_unique_on_duplicate_titles(self):
        """Test that duplicate titles get unique slugs"""
        product1 = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        product2 = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(product1.slug, "jordan-3-retro")
        self.assertEqual(product2.slug, "jordan-3-retro-1")

    def test_str_representation(self):
        """Test __str__ method"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(str(product), "Jordan 3 Retro")

    def test_inventory_status_default(self):
        """Test default inventory status"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(product.inventory_status, "anticipated")

    # ========================================
    # AUCTION STATUS TESTS
    # ========================================
    
    def test_auction_status_upcoming(self):
        """Test auction status when auction hasn't started"""
        auction_start = django_timezone.now() + timedelta(days=7)
        auction_end = django_timezone.now() + timedelta(days=14)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.auction_status, "Upcoming")

    def test_auction_status_ongoing(self):
        """Test auction status during auction"""
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.auction_status, "Ongoing")

    def test_auction_status_ended(self):
        """Test auction status after auction ends"""
        auction_start = django_timezone.now() - timedelta(days=14)
        auction_end = django_timezone.now() - timedelta(days=7)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.auction_status, "Ended")

    def test_auction_status_not_available(self):
        """Test auction status when no dates are set"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(product.auction_status, "Not Available")

    # ========================================
    # AUCTION DURATION TESTS
    # ========================================
    
    def test_auction_duration_calculation(self):
        """Test auction duration calculation"""
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6, hours=5)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        duration = product.auction_duration
        self.assertIsNotNone(duration)
        self.assertEqual(duration["days"], 6)
        self.assertGreaterEqual(duration["hours"], 0)
        self.assertLessEqual(duration["hours"], 23)

    def test_auction_duration_none_when_no_dates(self):
        """Test auction duration returns None when dates not set"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertIsNone(product.auction_duration)

    # ========================================
    # BUY NOW TESTS
    # ========================================
    
    def test_is_buy_now_available_true(self):
        """Test buy now is available during buy now period"""
        buy_now_start = django_timezone.now() - timedelta(days=1)
        buy_now_end = django_timezone.now() + timedelta(days=6)
        auction_start = django_timezone.now() + timedelta(days=7)
        auction_end = django_timezone.now() + timedelta(days=14)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            buy_now_start=buy_now_start,
            buy_now_end=buy_now_end,
            auction_start_date=auction_start,
            auction_end_date=auction_end,
            bought_now=False
        )
        
        self.assertTrue(product.is_buy_now_available)

    def test_is_buy_now_available_false_after_bought(self):
        """Test buy now not available after purchase"""
        buy_now_start = django_timezone.now() - timedelta(days=1)
        buy_now_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            buy_now_start=buy_now_start,
            buy_now_end=buy_now_end,
            bought_now=True
        )
        
        self.assertFalse(product.is_buy_now_available)

    def test_is_buy_now_available_false_during_auction(self):
        """Test buy now not available during auction phase"""
        buy_now_start = django_timezone.now() - timedelta(days=8)
        buy_now_end = django_timezone.now() - timedelta(days=2)
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            buy_now_start=buy_now_start,
            buy_now_end=buy_now_end,
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertFalse(product.is_buy_now_available)

    def test_complete_buy_now_purchase(self):
        """Test completing a buy now purchase"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            inventory_status="in_inventory"
        )
        
        product.complete_buy_now_purchase(self.user)
        
        self.assertEqual(product.inventory_status, "sold_out")
        self.assertTrue(product.bought_now)
        self.assertTrue(product.auction_finalized)
        self.assertEqual(product.winner, self.user)
        self.assertIsNotNone(product.auction_end_date)

    def test_buy_now_must_end_before_auction(self):
        """Test validation that buy now must end before auction"""
        buy_now_start = django_timezone.now() + timedelta(days=1)
        buy_now_end = django_timezone.now() + timedelta(days=10)  # After auction starts!
        auction_start = django_timezone.now() + timedelta(days=7)
        auction_end = django_timezone.now() + timedelta(days=14)
        
        product = PopUpProduct(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            buy_now_start=buy_now_start,
            buy_now_end=buy_now_end,
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        with self.assertRaises(ValidationError):
            product.clean()

    # ========================================
    # AUCTION PHASE TESTS
    # ========================================
    
    def test_is_auction_phase_true(self):
        """Test auction phase is true during auction"""
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertTrue(product.is_auction_phase())

    def test_is_auction_phase_false_before_start(self):
        """Test auction phase is false before start"""
        auction_start = django_timezone.now() + timedelta(days=7)
        auction_end = django_timezone.now() + timedelta(days=14)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertFalse(product.is_auction_phase())

    def test_is_auction_phase_false_after_end(self):
        """Test auction phase is false after end"""
        auction_start = django_timezone.now() - timedelta(days=14)
        auction_end = django_timezone.now() - timedelta(days=7)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertFalse(product.is_auction_phase())

    # ========================================
    # RESERVATION TESTS
    # ========================================
    
    def test_is_reserved_expired_true(self):
        """Test reservation is expired"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            reserved_until= django_timezone.now() - timedelta(hours=1)
        )
        
        self.assertTrue(product.is_reserved_expired())

    def test_is_reserved_expired_false(self):
        """Test reservation is not expired"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            reserved_until= django_timezone.now() + timedelta(hours=1)
        )
        
        self.assertFalse(product.is_reserved_expired())

    def test_is_reserved_expired_none(self):
        """Test reservation expiry when no reservation"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertFalse(product.is_reserved_expired())

    # ========================================
    # CART AVAILABILITY TESTS
    # ========================================
    
    def test_can_be_added_to_cart_in_inventory(self):
        """Test product can be added to cart when in inventory"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            inventory_status="in_inventory"
        )
        
        self.assertTrue(product.can_be_added_to_cart())

    def test_can_be_added_to_cart_reserved_expired(self):
        """Test product can be added when reservation expired"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            inventory_status="reserved",
            reserved_until= django_timezone.now() - timedelta(hours=1)
        )
        
        self.assertTrue(product.can_be_added_to_cart())

    def test_cannot_be_added_to_cart_reserved_active(self):
        """Test product cannot be added when actively reserved"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            inventory_status="reserved",
            reserved_until= django_timezone.now() + timedelta(hours=1)
        )
        
        self.assertFalse(product.can_be_added_to_cart())

    def test_cannot_be_added_to_cart_sold_out(self):
        """Test product cannot be added when sold out"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            inventory_status="sold_out"
        )
        
        self.assertFalse(product.can_be_added_to_cart())

    # ========================================
    # DISPLAY PRICE TESTS
    # ========================================
    
    def test_display_price_bought_now(self):
        """Test display price when bought via buy now"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            bought_now=True
        )
        
        self.assertEqual(product.display_price(), Decimal("230.00"))

    def test_display_price_during_buy_now(self):
        """Test display price during buy now period"""
        buy_now_start = django_timezone.now() - timedelta(days=1)
        buy_now_end = django_timezone.now() + timedelta(days=6)
        auction_start = django_timezone.now() + timedelta(days=7)
        auction_end = django_timezone.now() + timedelta(days=14)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            buy_now_price=Decimal("230.00"),
            buy_now_start=buy_now_start,
            buy_now_end=buy_now_end,
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.display_price(), Decimal("230.00"))

    def test_display_price_during_auction_with_bid(self):
        """Test display price shows highest bid during auction"""
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            reserve_price=Decimal("100.00"),
            current_highest_bid=Decimal("180.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.display_price(), Decimal("180.00"))

    def test_display_price_during_auction_no_bid(self):
        """Test display price shows reserve during auction with no bids"""
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            reserve_price=Decimal("100.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.display_price(), Decimal("100.00"))

    def test_display_price_default_retail(self):
        """Test display price defaults to retail"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(product.display_price(), Decimal("150.00"))

    # ========================================
    # FINALIZE AUCTION TESTS
    # ========================================
    
    def test_finalize_auction_with_bids(self):
        """Test finalizing auction with bids"""
        auction_start = django_timezone.now() - timedelta(days=7)
        auction_end = django_timezone.now() - timedelta(days=1)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        # Create profile and bid
        PopUpBid.objects.create(
            customer=self.profile_user,
            product=product,
            amount=Decimal("180.00")
        )
        
        product.finalize_auction()
        
        self.assertTrue(product.auction_finalized)
        self.assertEqual(product.winner, self.user)
        self.assertEqual(product.inventory_status, "in_inventory")

    def test_finalize_auction_no_bids(self):
        """Test finalizing auction with no bids"""
        auction_start = django_timezone.now() - timedelta(days=7)
        auction_end = django_timezone.now() - timedelta(days=1)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        product.finalize_auction()
        
        self.assertTrue(product.auction_finalized)
        self.assertIsNone(product.winner)

    def test_finalize_auction_already_bought(self):
        """Test finalize auction does nothing if already bought"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            bought_now=True,
            winner=self.user
        )
        
        original_winner = product.winner
        product.finalize_auction()
        
        # Should not change anything
        self.assertEqual(product.winner, original_winner)

    # ========================================
    # SALE OUTCOME TESTS
    # ========================================
    
    def test_sale_outcome_bought_now(self):
        """Test sale outcome when bought via buy now"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            bought_now=True
        )
        
        self.assertEqual(product.sale_outcome, "Bought Now")

    def test_sale_outcome_auction_finalized_with_winner(self):
        """Test sale outcome when auction ended with winner"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_finalized=True,
            winner=self.user
        )
        
        self.assertEqual(
            product.sale_outcome,
            "Auction Finalized - Winner Pending Purchase"
        )

    def test_sale_outcome_auction_finalized_no_winner(self):
        """Test sale outcome when auction ended with no bids"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_finalized=True,
            winner=None
        )
        
        self.assertEqual(
            product.sale_outcome,
            "Auction Ended - No Bids"
        )

    def test_sale_outcome_returns_auction_status(self):
        """Test sale outcome returns auction status when not finalized"""
        auction_start = django_timezone.now() - timedelta(days=1)
        auction_end = django_timezone.now() + timedelta(days=6)
        
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            auction_start_date=auction_start,
            auction_end_date=auction_end
        )
        
        self.assertEqual(product.sale_outcome, "Ongoing")

    # ========================================
    # ADDITIONAL FIELD TESTS
    # ========================================
    
    def test_bid_count_default(self):
        """Test bid count defaults to 0"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertEqual(product.bid_count, 0)

    def test_timestamps_auto_populate(self):
        """Test that timestamps are auto-populated"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00")
        )
        
        self.assertIsNotNone(product.created_at)
        self.assertIsNotNone(product.updated_at)

    def test_get_absolute_url(self):
        """Test get_absolute_url method"""
        product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            slug="jordan-3-retro",
            retail_price=Decimal("150.00")
        )
        
        expected_url = f"/auction/product/{product.slug}/"
        # This depends on your URL configuration
        # Adjust the assertion based on your actual URL pattern
        self.assertIn(product.slug, product.get_absolute_url())



class TestPopUpProductSpecificationModel(TestCase):

    def setUp(self):
        self.product_type = PopUpProductType.objects.create(name='Shoe', slug='shoe')

    def test_specification_creation(self):
        spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='Color'
        )
        self.assertEqual(spec.name, 'Color')
        self.assertEqual(spec.product_type.name, 'Shoe')
        self.assertTrue(isinstance(spec, PopUpProductSpecification))
        self.assertEqual(str(spec), 'Color')

    def test_specification_unique_constraint(self):
        PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='Size'
        )
        with self.assertRaises(Exception):
            # Should raise an IntegrityError due to unique_together
            PopUpProductSpecification.objects.create(
                product_type=self.product_type,
                name='Size'
            )

class TestPopUpProductSpecificationValueModel(TestCase):
    def setUp(self):
        self.product_type = PopUpProductType.objects.create(name='Shoe', slug='shoe')
        self.category = PopUpCategory.objects.create(name='Sneakers', slug='sneakers')
        self.brand = PopUpBrand.objects.create(name='Nike', slug='nike')

        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            product_title="Nike Air Max",
            secondary_product_title="Limited Edition",
            description="Comfortable and stylish",
            slug="nike-air-max",
            retail_price="120.00",
            buy_now_price="190.00",
            brand=self.brand,
            auction_start_date=now(),
            auction_end_date=now() + timedelta(days=5),
            inventory_status="in_inventory",
            bid_count=0,
            reserve_price="0.00",
            is_active=True,
        )

        self.specification = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name="Color"
        )

    def test_specification_value_creation(self):
        value = PopUpProductSpecificationValue.objects.create(
            product=self.product,
            specification=self.specification,
            value="Red"
        )

        self.assertEqual(value.value, "Red")
        self.assertEqual(value.product.product_title, "Nike Air Max")
        self.assertEqual(value.specification.name, "Color")
        self.assertEqual(str(value), "Red")


class TestPopUpProductImageModel(TestCase):
    """Test suite for PopUpProductImage model"""

    def setUp(self):
        """Create test data"""
        # Create required foreign key objects
        self.product_type = PopUpProductType.objects.create(
            name="Sneakers"
        )
        self.category = PopUpCategory.objects.create(
            name="Athletic Shoes",
            slug="athletic-shoes"
        )
        self.brand = PopUpBrand.objects.create(
            name="Nike"
        )
        
        # Create product
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Test Sneakers",
            slug="test-sneakers",
            retail_price=Decimal("200.00"),
            is_active=True
        )

    

    def test_create_product_image_with_uploaded_file(self):
        """Test creating a product image with uploaded file"""
        # Create a simple test image file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image,
            alt_text="Test image"
        )
        
        self.assertEqual(product_image.product, self.product)
        self.assertIsNotNone(product_image.image)
        self.assertEqual(product_image.alt_text, "Test image")

    def test_create_product_image_with_url(self):
        """Test creating a product image with external URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            alt_text="External image"
        )
        
        self.assertEqual(product_image.image_url, "https://example.com/image.jpg")
        self.assertEqual(product_image.alt_text, "External image")

    def test_is_feature_default_false(self):
        """Test that is_feature defaults to False"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertFalse(product_image.is_feature)

    def test_set_feature_image(self):
        """Test setting an image as featured"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            is_feature=True
        )
        
        self.assertTrue(product_image.is_feature)

    def test_multiple_images_per_product(self):
        """Test that a product can have multiple images"""
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg",
            is_feature=True
        )
        img2 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg"
        )
        img3 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image3.jpg"
        )
        
        self.assertEqual(self.product.product_image.count(), 3)
        self.assertIn(img1, self.product.product_image.all())
        self.assertIn(img2, self.product.product_image.all())
        self.assertIn(img3, self.product.product_image.all())

    def test_cascade_delete_product_deletes_images(self):
        """Test that deleting product deletes its images"""
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg"
        )
        img2 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg"
        )
        
        product_id = self.product.id
        self.product.delete()
        
        # Images should be deleted
        self.assertEqual(PopUpProductImage.objects.filter(product_id=product_id).count(), 0)

    def test_get_image_url_with_uploaded_file(self):
        """Test get_image_url returns uploaded file"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image
        )
        
        # Should return the actual URL of the uploaded file
        self.assertEqual(product_image.get_image_url(), product_image.image.url)


    def test_get_image_url_with_external_url(self):
        """get_image_url returns image_url when no file is uploaded."""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            alt_text="Test",
        )

        self.assertEqual(
            product_image.get_image_url(),
            "https://example.com/image.jpg"
        )



    def test_get_image_url_fallback_to_default(self):
        """Test get_image_url returns default when no image or URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image= '',
        )
        
        expected_default = settings.STATIC_URL + 'images/default.png'
        self.assertEqual(product_image.get_image_url(), expected_default)


    def test_resolved_image_url_property(self):
        """Test resolved_image_url property"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(
            product_image.resolved_image_url,
            product_image.get_image_url()
        )

    def test_str_representation_with_uploaded_image(self):
        """Test __str__ with uploaded image"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image
        )
        
        # Should return the image URL
        str_repr = str(product_image)
        self.assertIn('test_image', str_repr)

    def test_str_representation_with_external_url(self):
        """Test __str__ with external URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(str(product_image), "https://example.com/image.jpg")

    def test_str_representation_with_no_image(self):
        """Test __str__ when no image or URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product
        )
        
        self.assertEqual(str(product_image), "No Image")

    def test_alt_text_optional(self):
        """Test that alt_text is optional"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertIsNone(product_image.alt_text)

    def test_alt_text_max_length(self):
        """Test alt_text respects max_length"""
        long_alt_text = "A" * 255
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            alt_text=long_alt_text
        )
        
        self.assertEqual(len(product_image.alt_text), 255)

    def test_timestamps_auto_populate(self):
        """Test that created_at and updated_at auto-populate"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertIsNotNone(product_image.created_at)
        self.assertIsNotNone(product_image.updated_at)

    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        original_updated_at = product_image.updated_at
        
        # Update the image
        product_image.alt_text = "Updated alt text"
        product_image.save()
        
        self.assertNotEqual(product_image.updated_at, original_updated_at)
        self.assertGreater(product_image.updated_at, original_updated_at)

    def test_filter_featured_images(self):
        """Test filtering for featured images"""
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg",
            is_feature=True
        )
        img2 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg",
            is_feature=False
        )
        img3 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image3.jpg",
            is_feature=True
        )
        
        featured_images = self.product.product_image.filter(is_feature=True)
        self.assertEqual(featured_images.count(), 2)
        self.assertIn(img1, featured_images)
        self.assertIn(img3, featured_images)
        self.assertNotIn(img2, featured_images)

    def test_get_featured_image(self):
        """Test getting the first featured image"""
        PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg",
            is_feature=False
        )
        featured = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg",
            is_feature=True
        )
        
        first_featured = self.product.product_image.filter(is_feature=True).first()
        self.assertEqual(first_featured, featured)

    def test_related_name_product_image(self):
        """Test the related_name 'product_image' works correctly"""
        PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        # Access via related_name
        self.assertEqual(self.product.product_image.count(), 1)

    def test_image_priority_uploaded_over_url(self):
        """Test that uploaded image takes priority over external URL"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image,
            image_url="https://example.com/image.jpg"
        )
        
        # Should return uploaded image, not URL
        self.assertEqual(product_image.get_image_url(), product_image.image.url)

    def test_default_image_path(self):
        """Test default image is set correctly"""
        product_image = PopUpProductImage.objects.create(
            product=self.product
        )
        
        # Check that default exists in the path
        expected_default = settings.STATIC_URL + 'images/default.png'
        self.assertEqual(product_image.get_image_url(), expected_default)


    def test_uploaded_file_takes_priority_over_url(self):
        """Local uploaded image overrides the external image URL."""
        image = SimpleUploadedFile(
            "local.jpg", b"fake-content", content_type="image/jpeg"
        )

        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image,
            image_url="https://example.com/remote.jpg"
        )

        self.assertEqual(product_image.get_image_url(), product_image.image.url)


    def test_multiple_products_same_image_url(self):
        """Test that different products can use the same external URL"""
        product2 = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Another Sneaker",
            slug="another-sneaker",
            retail_price=Decimal("150.00")
        )
        
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/shared-image.jpg"
        )
        img2 = PopUpProductImage.objects.create(
            product=product2,
            image_url="https://example.com/shared-image.jpg"
        )
        
        self.assertEqual(img1.image_url, img2.image_url)
        self.assertNotEqual(img1.product, img2.product)



class TestWinnerReservationModel(TestCase):
    """Test suite for WinnerReservation model"""

    def setUp(self):
        """Create test data"""
        # Create user
        self.user = User.objects.create_user(
            email="winner@example.com",
            password="testpass123",
            first_name="Winner",
            last_name="User"
        )
        
        self.user.is_active = True
        self.user.save()
        
        # Create another user for duplicate tests
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )
        self.user2.is_active = True
        self.user2.save()
        
        # Create required foreign key objects
        self.product_type = PopUpProductType.objects.create(name="Sneakers")
        self.category = PopUpCategory.objects.create(name="Athletic", slug="athletic")
        self.brand = PopUpBrand.objects.create(name="Nike")
        
        # Create product
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Test Sneakers",
            slug="test-sneakers",
            retail_price=Decimal("200.00"),
            reserve_price=Decimal("150.00"),
            is_active=True
        )
        
        # Create another product for testing
        self.product2 = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Another Sneaker",
            slug="another-sneaker",
            retail_price=Decimal("180.00")
        )

    def test_create_winner_reservation(self):
        """Test creating a winner reservation"""
        expires_at = django_timezone.now() + timedelta(hours=48)
        
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=expires_at
        )
        
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.product, self.product)
        self.assertEqual(reservation.expires_at, expires_at)
        self.assertFalse(reservation.is_paid)
        self.assertFalse(reservation.is_expired)
        self.assertFalse(reservation.notification_sent)


    def test_reserved_at_auto_populated(self):
        """Test that reserved_at is automatically set"""
        before = django_timezone.now()
        
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        after = django_timezone.now()
        
        self.assertIsNotNone(reservation.reserved_at)
        self.assertGreaterEqual(reservation.reserved_at, before)
        self.assertLessEqual(reservation.reserved_at, after)


    def test_expires_at_48_hours_from_now(self):
        """Test setting expiration to 48 hours from now"""
        now = django_timezone.now()
        expires_at = now + timedelta(hours=48)
        
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=expires_at
        )
        
        # Check that expires_at is approximately 48 hours from now
        time_diff = reservation.expires_at - now
        self.assertAlmostEqual(
            time_diff.total_seconds(),
            48 * 3600,
            delta=5  # Allow 5 seconds tolerance
        )

    def test_is_paid_default_false(self):
        """Test that is_paid defaults to False"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        self.assertFalse(reservation.is_paid)
        self.assertIsNone(reservation.paid_at)

    def test_mark_as_paid(self):
        """Test marking reservation as paid"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        paid_time = django_timezone.now()
        reservation.is_paid = True
        reservation.paid_at = paid_time
        reservation.save()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_paid)
        self.assertEqual(reservation.paid_at, paid_time)

    def test_is_expired_default_false(self):
        """Test that is_expired defaults to False"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        self.assertFalse(reservation.is_expired)

    def test_mark_as_expired(self):
        """Test marking reservation as expired (simulating background task)"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() - timedelta(hours=1)  # Already expired
        )
        
        # Simulate background task marking as expired
        reservation.is_expired = True
        reservation.save()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_expired)

    def test_notification_sent_default_false(self):
        """Test that notification_sent defaults to False"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        self.assertFalse(reservation.notification_sent)

    def test_mark_notification_as_sent(self):
        """Test marking notification as sent"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        reservation.notification_sent = True
        reservation.save()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.notification_sent)

    def test_reminder_flags_default_false(self):
        """Test that reminder flags default to False"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        self.assertFalse(reservation.reminder_24hr_sent)
        self.assertFalse(reservation.reminder_1hr_sent)

    def test_mark_24hr_reminder_sent(self):
        """Test marking 24-hour reminder as sent"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        reservation.reminder_24hr_sent = True
        reservation.save()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.reminder_24hr_sent)
        self.assertFalse(reservation.reminder_1hr_sent)

    def test_mark_1hr_reminder_sent(self):
        """Test marking 1-hour reminder as sent"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        reservation.reminder_1hr_sent = True
        reservation.save()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.reminder_1hr_sent)
        self.assertFalse(reservation.reminder_24hr_sent)

    def test_unique_together_constraint(self):
        """Test that same product and user can't have duplicate reservations"""
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            WinnerReservation.objects.create(
                user=self.user,
                product=self.product,
                expires_at=django_timezone.now() + timedelta(hours=48)
            )

    def test_same_user_different_products(self):
        """Test that same user can have reservations for different products"""
        reservation1 = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        reservation2 = WinnerReservation.objects.create(
            user=self.user,
            product=self.product2,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        self.assertEqual(WinnerReservation.objects.filter(user=self.user).count(), 2)
        self.assertNotEqual(reservation1.product, reservation2.product)

    def test_same_product_different_users(self):
        """Test that different users can have reservations for same product (sequential wins)"""
        # First user wins, pays, reservation can be deleted
        reservation1 = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        reservation1.is_paid = True
        reservation1.save()
        
        # After first user's reservation is handled, second user can win
        reservation1.delete()  # Simulating cleanup after payment
        
        reservation2 = WinnerReservation.objects.create(
            user=self.user2,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        self.assertNotEqual(reservation2.user, self.user)

    def test_cascade_delete_user(self):
        """Test that deleting user deletes reservation"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        reservation_id = reservation.id
        self.user.hard_delete()
        
        self.assertFalse(
            WinnerReservation.objects.filter(id=reservation_id).exists()
        )

    def test_cascade_delete_product(self):
        """Test that deleting product deletes reservation"""
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        reservation_id = reservation.id
        self.product.delete()
        
        self.assertFalse(
            WinnerReservation.objects.filter(id=reservation_id).exists()
        )

    def test_filter_unpaid_reservations(self):
        """Test filtering unpaid reservations"""
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48),
            is_paid=False
        )
        
        WinnerReservation.objects.create(
            user=self.user2,
            product=self.product2,
            expires_at=django_timezone.now() + timedelta(hours=48),
            is_paid=True
        )
        
        unpaid = WinnerReservation.objects.filter(is_paid=False)
        self.assertEqual(unpaid.count(), 1)

    def test_filter_expired_reservations(self):
        """Test filtering expired reservations"""
        # Create expired reservation
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() - timedelta(hours=1),
            is_expired=True
        )
        
        # Create active reservation
        WinnerReservation.objects.create(
            user=self.user2,
            product=self.product2,
            expires_at=django_timezone.now() + timedelta(hours=48),
            is_expired=False
        )
        
        expired = WinnerReservation.objects.filter(is_expired=True)
        self.assertEqual(expired.count(), 1)

    def test_filter_reservations_needing_24hr_reminder(self):
        """Test finding reservations that need 24-hour reminder"""
        # Expires in ~24 hours, reminder not sent
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=24),
            reminder_24hr_sent=False
        )
        
        # Expires in ~24 hours, reminder already sent
        WinnerReservation.objects.create(
            user=self.user2,
            product=self.product2,
            expires_at=django_timezone.now() + timedelta(hours=24),
            reminder_24hr_sent=True
        )
        
        needs_reminder = WinnerReservation.objects.filter(
            reminder_24hr_sent=False,
            expires_at__lte=django_timezone.now() + timedelta(hours=25),
            expires_at__gte=django_timezone.now() + timedelta(hours=23)
        )
        
        self.assertEqual(needs_reminder.count(), 1)

    def test_filter_reservations_needing_1hr_reminder(self):
        """Test finding reservations that need 1-hour reminder"""
        # Expires in ~1 hour, reminder not sent
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=1),
            reminder_1hr_sent=False
        )
        
        # Expires in ~1 hour, reminder already sent
        WinnerReservation.objects.create(
            user=self.user2,
            product=self.product2,
            expires_at=django_timezone.now() + timedelta(hours=1),
            reminder_1hr_sent=True
        )
        
        needs_reminder = WinnerReservation.objects.filter(
            reminder_1hr_sent=False,
            expires_at__lte=django_timezone.now() + timedelta(hours=2),
            expires_at__gte=django_timezone.now()
        )
        
        self.assertEqual(needs_reminder.count(), 1)

    def test_payment_workflow(self):
        """Test complete payment workflow"""
        # Create reservation
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48)
        )
        
        # Initial state
        self.assertFalse(reservation.is_paid)
        self.assertIsNone(reservation.paid_at)
        
        # User pays
        payment_time = django_timezone.now()
        reservation.is_paid = True
        reservation.paid_at = payment_time
        reservation.save()
        
        # Verify payment recorded
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_paid)
        self.assertEqual(reservation.paid_at, payment_time)
        self.assertFalse(reservation.is_expired)

    def test_expiration_workflow(self):
        """Test complete expiration workflow"""
        # Create reservation that expires soon
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(minutes=1)
        )
        
        # Initial state
        self.assertFalse(reservation.is_expired)
        
        # Simulate background task checking expiration
        if django_timezone.now() > reservation.expires_at:
            reservation.is_expired = True
            reservation.save()
        
        # For this test, manually mark as expired
        reservation.is_expired = True
        reservation.save()
        
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_expired)

    def test_get_user_active_reservations(self):
        """Test getting all active reservations for a user"""
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48),
            is_expired=False,
            is_paid=False
        )
        
        WinnerReservation.objects.create(
            user=self.user,
            product=self.product2,
            expires_at=django_timezone.now() + timedelta(hours=48),
            is_expired=True,  # Expired
            is_paid=False
        )
        
        active_reservations = WinnerReservation.objects.filter(
            user=self.user,
            is_expired=False,
            is_paid=False
        )
        
        self.assertEqual(active_reservations.count(), 1)


# coverage report | gets coverage report
# coverage html | gets coverage report in html. open index.html file in htmlcov directory
# run --omit='*/venv/*' manage.py test | command to run test