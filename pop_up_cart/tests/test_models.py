from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.timezone import now
from django.utils import timezone as django_timezone
from datetime import timedelta
from pop_up_cart.models import PopUpCartItem, ProcurementCartItem
from pop_up_bot.models import ScheduledRelease, ProcurementServiceRequest
from pop_up_auction.models import PopUpProduct, PopUpCategory, PopUpProductType, PopUpBrand
from pop_up_auction.tests.conftest import (create_test_user)
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()



def create_scheduled_release(product, sku='AJ1-001', days_from_now=10):
    return ScheduledRelease.objects.create(
        product=product,
        sku=sku,
        release_date=django_timezone.now() + django_timezone.timedelta(days=days_from_now),
        retail_price=Decimal('180.00'),
        search_method='direct_url',
        status='scheduled',
    )
 
 
def create_procurement_service_request(user, scheduled_release, size="Men's 10"):
    return ProcurementServiceRequest.objects.create(
        user=user,
        scheduled_release=scheduled_release,
        size=size,
        service_fee=Decimal('15.00'),
        fee_paid_at=django_timezone.now(),
        status='pending',
        strategy='fastest',
    )
 

"""
Tests for PopUpCartItem model
1. TestPopUpCartItemModel
2. ProcurementCartItemModelTest
"""



class TestPopUpCartItemModel(TestCase):
    """
    Comprehensive test suite for PopUpCartItem model covering:
    - Model creation and defaults
    - Field validations
    - Unique constraints
    - Relationships (user and product)
    - String representation
    - Model methods and properties
    - Edge cases
    """

    def setUp(self):
        """Set up test fixtures for each test method."""
        
        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
        )
        self.other_user, self.other_user_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User2", "10", "female"
        )
        
        # Create category
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        
        # Create brand
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        
        # Create product type
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )
        
        # Create test products
        self.product1 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            slug='jordan-4-military-blue',
            buy_now_price=Decimal('215.00'),
            retail_price=Decimal('215.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        self.product2 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            retail_price=Decimal('180.00'),
            inventory_status='in_inventory',
            is_active=True
        )

    # ==================== Model Creation Tests ====================
    
    def test_create_cart_item_with_defaults(self):
        """Test creating a cart item with default values."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        self.assertIsNotNone(cart_item.id)
        self.assertEqual(cart_item.user, self.user)
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.quantity, 1)  # Default quantity
        self.assertFalse(cart_item.auction_locked)  # Default False
        self.assertFalse(cart_item.buy_now)  # Default False
        self.assertIsNotNone(cart_item.added_at)

    def test_create_cart_item_with_custom_quantity(self):
        """Test creating a cart item with custom quantity."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=3
        )
        
        self.assertEqual(cart_item.quantity, 3)

    def test_create_cart_item_with_auction_locked_true(self):
        """Test creating a cart item with auction_locked=True."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            auction_locked=True
        )
        
        self.assertTrue(cart_item.auction_locked)

    def test_create_cart_item_with_buy_now_true(self):
        """Test creating a cart item with buy_now=True."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            buy_now=True
        )
        
        self.assertTrue(cart_item.buy_now)

    def test_create_cart_item_all_fields(self):
        """Test creating a cart item with all fields specified."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=5,
            auction_locked=True,
            buy_now=True
        )
        
        self.assertEqual(cart_item.quantity, 5)
        self.assertTrue(cart_item.auction_locked)
        self.assertTrue(cart_item.buy_now)

    # ==================== Field Validation Tests ====================
    
    def test_quantity_must_be_positive(self):
        """Test that quantity must be a positive integer."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=10
        )
        
        self.assertEqual(cart_item.quantity, 10)
        self.assertGreater(cart_item.quantity, 0)

    def test_quantity_zero_allowed(self):
        """Test that quantity of 0 is technically allowed by PositiveBigIntegerField."""
        # Note: PositiveBigIntegerField allows 0
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=0
        )
        
        self.assertEqual(cart_item.quantity, 0)

    def test_added_at_auto_set(self):
        """Test that added_at is automatically set on creation."""
        before_time = now()
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        after_time = now()
        
        self.assertIsNotNone(cart_item.added_at)
        self.assertGreaterEqual(cart_item.added_at, before_time)
        self.assertLessEqual(cart_item.added_at, after_time)

    def test_added_at_not_updated_on_save(self):
        """Test that added_at doesn't change when model is saved again."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=1
        )
        
        original_added_at = cart_item.added_at
        
        # Update quantity and save
        cart_item.quantity = 2
        cart_item.save()
        cart_item.refresh_from_db()
        
        self.assertEqual(cart_item.added_at, original_added_at)

    # ==================== Unique Constraint Tests ====================
    
    def test_unique_together_constraint(self):
        """Test that user-product combination must be unique."""
        # Create first cart item
        PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            PopUpCartItem.objects.create(
                user=self.user,
                product=self.product1
            )

    def test_same_product_different_users_allowed(self):
        """Test that same product can be in different users' carts."""
        cart_item1 = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        cart_item2 = PopUpCartItem.objects.create(
            user=self.other_user,
            product=self.product1
        )
        
        self.assertNotEqual(cart_item1.id, cart_item2.id)
        self.assertEqual(cart_item1.product, cart_item2.product)
        self.assertNotEqual(cart_item1.user, cart_item2.user)

    def test_different_products_same_user_allowed(self):
        """Test that same user can have multiple products in cart."""
        cart_item1 = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        cart_item2 = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product2
        )
        
        self.assertNotEqual(cart_item1.id, cart_item2.id)
        self.assertNotEqual(cart_item1.product, cart_item2.product)
        self.assertEqual(cart_item1.user, cart_item2.user)

    # ==================== Relationship Tests ====================
    
    def test_user_foreign_key_relationship(self):
        """Test the foreign key relationship to User model."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        # Access user from cart item
        self.assertEqual(cart_item.user, self.user)
        self.assertEqual(cart_item.user.email, "test@example.com")
        
        # Access cart items from user (reverse relationship)
        user_cart_items = PopUpCartItem.objects.filter(user=self.user)
        self.assertEqual(user_cart_items.count(), 1)
        self.assertEqual(user_cart_items.first(), cart_item)


    def test_product_foreign_key_relationship(self):
        """Test the foreign key relationship to PopUpProduct model."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        # Access product from cart item
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.product.product_title, 'Air Jordan 4')
        
        # Access cart items from product (reverse relationship)
        product_cart_items = PopUpCartItem.objects.filter(product=self.product1)
        self.assertEqual(product_cart_items.count(), 1)
        self.assertEqual(product_cart_items.first(), cart_item)


    def test_cascade_delete_user(self):
        """Test that deleting a user deletes their cart items."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        cart_item_id = cart_item.id

        # Delete profile first (because of PROTECT)
        self.user.popupcustomerprofile.delete()

        # Now delete user
        self.user.hard_delete()

        self.assertFalse(
            PopUpCartItem.objects.filter(id=cart_item_id).exists()
        )

        
        # # Use hard_delete() instead of delete() since User has soft delete
        # self.user.hard_delete()
        
        # # Cart item should be deleted
        # self.assertFalse(
        #     PopUpCartItem.objects.filter(id=cart_item_id).exists(),
        #     "Cart item should be deleted when user is hard deleted"
        # )
    
    def test_soft_delete_user_keeps_cart_items(self):
        """Test that soft deleting a user keeps their cart items."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        cart_item_id = cart_item.id
        
        # Soft delete user (regular delete())
        self.user.delete()
        
        # User should be soft deleted
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)
        
        # Cart item should still exist (user wasn't hard deleted)
        self.assertTrue(
            PopUpCartItem.objects.filter(id=cart_item_id).exists(),
            "Cart item should remain when user is soft deleted"
        )



    def test_cascade_delete_product(self):
        """Test that deleting a product deletes related cart items."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        cart_item_id = cart_item.id
        
        # Delete product
        self.product1.delete()
        
        # Cart item should be deleted
        with self.assertRaises(PopUpCartItem.DoesNotExist):
            PopUpCartItem.objects.get(id=cart_item_id)

    # ==================== String Representation Tests ====================
    
    def test_str_representation(self):
        """Test the __str__ method returns expected format."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=2
        )
        
        expected_str = f"{self.user}'s cart: Air Jordan 4 Retro Military Blue 2"
        self.assertEqual(str(cart_item), expected_str)

    def test_str_representation_single_quantity(self):
        """Test __str__ with quantity of 1."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=1
        )
        
        expected_str = f"{self.user}'s cart: Air Jordan 4 Retro Military Blue 1"
        self.assertEqual(str(cart_item), expected_str)

    # ==================== Query and Filter Tests ====================
    
    def test_filter_by_user(self):
        """Test filtering cart items by user."""
        PopUpCartItem.objects.create(user=self.user, product=self.product1)
        PopUpCartItem.objects.create(user=self.user, product=self.product2)
        PopUpCartItem.objects.create(user=self.other_user, product=self.product1)
        
        user_items = PopUpCartItem.objects.filter(user=self.user)
        
        self.assertEqual(user_items.count(), 2)
        for item in user_items:
            self.assertEqual(item.user, self.user)

    def test_filter_by_product(self):
        """Test filtering cart items by product."""
        PopUpCartItem.objects.create(user=self.user, product=self.product1)
        PopUpCartItem.objects.create(user=self.other_user, product=self.product1)
        PopUpCartItem.objects.create(user=self.user, product=self.product2)
        
        product_items = PopUpCartItem.objects.filter(product=self.product1)
        
        self.assertEqual(product_items.count(), 2)
        for item in product_items:
            self.assertEqual(item.product, self.product1)

    def test_filter_by_auction_locked(self):
        """Test filtering cart items by auction_locked status."""
        PopUpCartItem.objects.create(
            user=self.user, product=self.product1, auction_locked=True
        )
        PopUpCartItem.objects.create(
            user=self.user, product=self.product2, auction_locked=False
        )
        
        locked_items = PopUpCartItem.objects.filter(auction_locked=True)
        
        self.assertEqual(locked_items.count(), 1)
        self.assertTrue(locked_items.first().auction_locked)

    def test_filter_by_buy_now(self):
        """Test filtering cart items by buy_now status."""
        PopUpCartItem.objects.create(
            user=self.user, product=self.product1, buy_now=True
        )
        PopUpCartItem.objects.create(
            user=self.user, product=self.product2, buy_now=False
        )
        
        buy_now_items = PopUpCartItem.objects.filter(buy_now=True)
        
        self.assertEqual(buy_now_items.count(), 1)
        self.assertTrue(buy_now_items.first().buy_now)

    def test_order_by_added_at(self):
        """Test ordering cart items by added_at timestamp."""
        item1 = PopUpCartItem.objects.create(user=self.user, product=self.product1)
        item2 = PopUpCartItem.objects.create(user=self.user, product=self.product2)
        
        items = PopUpCartItem.objects.filter(user=self.user).order_by('added_at')
        
        self.assertEqual(items[0], item1)
        self.assertEqual(items[1], item2)

    # ==================== Edge Cases ====================
    
    def test_very_large_quantity(self):
        """Test cart item with very large quantity."""
        large_quantity = 999999
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=large_quantity
        )
        
        self.assertEqual(cart_item.quantity, large_quantity)

    def test_both_auction_locked_and_buy_now_true(self):
        """Test cart item with both auction_locked and buy_now set to True."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            auction_locked=True,
            buy_now=True
        )
        
        self.assertTrue(cart_item.auction_locked)
        self.assertTrue(cart_item.buy_now)

    def test_update_quantity(self):
        """Test updating the quantity of an existing cart item."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=1
        )
        
        cart_item.quantity = 5
        cart_item.save()
        cart_item.refresh_from_db()
        
        self.assertEqual(cart_item.quantity, 5)

    def test_update_auction_locked_flag(self):
        """Test updating the auction_locked flag."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            auction_locked=False
        )
        
        cart_item.auction_locked = True
        cart_item.save()
        cart_item.refresh_from_db()
        
        self.assertTrue(cart_item.auction_locked)

    def test_update_buy_now_flag(self):
        """Test updating the buy_now flag."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            buy_now=False
        )
        
        cart_item.buy_now = True
        cart_item.save()
        cart_item.refresh_from_db()
        
        self.assertTrue(cart_item.buy_now)

    # ==================== Multiple Items Tests ====================
    
    def test_user_with_multiple_cart_items(self):
        """Test a user with multiple items in their cart."""
        item1 = PopUpCartItem.objects.create(user=self.user, product=self.product1, quantity=2)
        item2 = PopUpCartItem.objects.create(user=self.user, product=self.product2, quantity=3)
        
        user_items = PopUpCartItem.objects.filter(user=self.user)
        
        self.assertEqual(user_items.count(), 2)
        
        total_quantity = sum(item.quantity for item in user_items)
        self.assertEqual(total_quantity, 5)

    def test_delete_single_cart_item(self):
        """Test deleting a single cart item doesn't affect others."""
        item1 = PopUpCartItem.objects.create(user=self.user, product=self.product1)
        item2 = PopUpCartItem.objects.create(user=self.user, product=self.product2)
        
        item1.delete()
        
        remaining_items = PopUpCartItem.objects.filter(user=self.user)
        self.assertEqual(remaining_items.count(), 1)
        self.assertEqual(remaining_items.first(), item2)

    def test_clear_user_cart(self):
        """Test clearing all items from a user's cart."""
        PopUpCartItem.objects.create(user=self.user, product=self.product1)
        PopUpCartItem.objects.create(user=self.user, product=self.product2)
        
        # Clear cart
        PopUpCartItem.objects.filter(user=self.user).delete()
        
        remaining_items = PopUpCartItem.objects.filter(user=self.user)
        self.assertEqual(remaining_items.count(), 0)

    # ==================== Meta Options Tests ====================
    
    def test_meta_unique_together(self):
        """Test that Meta unique_together is enforced."""
        cart_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1
        )
        
        # Verify the unique_together constraint
        self.assertIn(('user', 'product'), PopUpCartItem._meta.unique_together)

    # ==================== Business Logic Tests ====================
    
    def test_cart_item_represents_user_intent(self):
        """Test that cart item correctly represents user's purchase intent."""
        # Regular cart item
        regular_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=1,
            auction_locked=False,
            buy_now=False
        )
        
        # Buy now item (immediate purchase)
        buy_now_item = PopUpCartItem.objects.create(
            user=self.other_user,
            product=self.product2,
            quantity=1,
            buy_now=True
        )
        
        # Auction item (locked for auction)
        auction_item = PopUpCartItem.objects.create(
            user=self.user,
            product=self.product2,
            quantity=1,
            auction_locked=True
        )
        
        # Verify different purchase types
        self.assertFalse(regular_item.buy_now)
        self.assertFalse(regular_item.auction_locked)
        
        self.assertTrue(buy_now_item.buy_now)
        
        self.assertTrue(auction_item.auction_locked)



 
class TestProcurementCartItemModel(TestCase):
    """Tests for ProcurementCartItem model"""
 
    def setUp(self):
        self.user, self.profile = create_test_user(
            'buyer@example.com', 'testpass!23', 'Jane', 'Buyer', '10', 'female'
        )
 
        self.product_type = PopUpProductType.objects.create(
            name='Shoe', slug='shoe'
        )
        self.category = PopUpCategory.objects.create(
            name='Basketball', slug='basketball'
        )
        self.brand = PopUpBrand.objects.create(
            name='Nike', slug='nike'
        )
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='aj1-chicago',
            retail_price=Decimal('180.00'),
            inventory_status='anticipated',
            is_active=True,
        )
        self.scheduled_release = create_scheduled_release(self.product)
        self.psr = create_procurement_service_request(self.user, self.scheduled_release)
 
    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
 
    def test_can_create_procurement_cart_item(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
            fee_amount=Decimal('15.00'),
        )
        self.assertIsNotNone(item.pk)
        self.assertEqual(ProcurementCartItem.objects.count(), 1)
 
    def test_id_is_uuid(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.assertIsInstance(item.id, uuid.UUID)
 
    def test_default_fee_amount_is_fifteen(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.assertEqual(item.fee_amount, Decimal('15.00'))
 
    def test_added_at_set_automatically(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.assertIsNotNone(item.added_at)
 
    # ------------------------------------------------------------------
    # OneToOne constraint
    # ------------------------------------------------------------------
 
    def test_one_to_one_with_procurement_service_request(self):
        """Each ProcurementServiceRequest can only have one cart item."""
        ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ProcurementCartItem.objects.create(
                user=self.user,
                procurement_service_request=self.psr,
            )
 
    # ------------------------------------------------------------------
    # Cascade delete
    # ------------------------------------------------------------------
 
    def test_deleting_psr_deletes_cart_item(self):
        """Primary cascade path: PSR deleted → cart item deleted."""
        ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.psr.delete()
        self.assertEqual(ProcurementCartItem.objects.count(), 0)
    
    def test_soft_deleting_user_does_not_delete_cart_item(self):
        """
        User.delete() is a soft delete (sets deleted_at, keeps the DB row).
        The cart item must survive so the order history stays intact.
        """
        ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.user.delete()  # soft delete — row stays, deleted_at is set
    
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.deleted_at)           # user is soft-deleted
        self.assertEqual(ProcurementCartItem.objects.count(), 1)  # cart item survives
    
    def test_hard_deleting_user_requires_profile_deletion_first(self):
        """
        Hard deletion of a user is blocked by PopUpCustomerProfile (PROTECT).
        This test documents that constraint so future devs don't hit it by surprise.
        """
        from django.db.models.deletion import ProtectedError
    
        ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        with self.assertRaises(ProtectedError):
            self.user.hard_delete()
 
 
    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
 
    def test_display_title_contains_product_title(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.assertIn('Air Jordan 1', item.display_title)
        self.assertIn('Procurement', item.display_title)
 
    def test_display_subtitle_contains_size(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        self.assertIn("Men's 10", item.display_subtitle)
 
    def test_price_property_equals_fee_amount(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
            fee_amount=Decimal('15.00'),
        )
        self.assertEqual(item.price, Decimal('15.00'))
 
    def test_total_price_property_equals_fee_amount(self):
        """Qty is always 1 for procurement items, so total == fee."""
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
            fee_amount=Decimal('15.00'),
        )
        self.assertEqual(item.total_price, Decimal('15.00'))
 
    # ------------------------------------------------------------------
    # __str__
    # ------------------------------------------------------------------
 
    def test_str_contains_user_and_product(self):
        item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
        )
        result = str(item)
        self.assertIn('Air Jordan 1', result)
        self.assertIn(self.user.email, result)
 
    # ------------------------------------------------------------------
    # Multiple users / same release
    # ------------------------------------------------------------------
 
    def test_multiple_users_can_have_cart_item_for_same_release(self):
        user2, _ = create_test_user(
            'buyer2@example.com', 'testpass!23', 'John', 'Smith', '11', 'male'
        )
        psr2 = create_procurement_service_request(
            user2, self.scheduled_release, size="Men's 11"
        )
        item1 = ProcurementCartItem.objects.create(
            user=self.user, procurement_service_request=self.psr
        )
        item2 = ProcurementCartItem.objects.create(
            user=user2, procurement_service_request=psr2
        )
        self.assertEqual(ProcurementCartItem.objects.count(), 2)
        self.assertNotEqual(item1.pk, item2.pk)