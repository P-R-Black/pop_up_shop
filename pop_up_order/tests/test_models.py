from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from decimal import Decimal
from django.utils.timezone import now
import unittest
from datetime import timedelta
import uuid
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from pop_up_auction.models import (
    PopUpProduct, 
    PopUpCategory, 
    PopUpBrand, 
    PopUpProductType,
)
from pop_up_coupon.models import PopUpCoupon
from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerAddress
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_staff_user)
from django.contrib.auth import get_user_model

User = get_user_model()



class TestPopUpCustomerOrderModel(TestCase):
    """Test suite for PopUpCustomerOrder model"""

    def setUp(self):
        """Set up test data"""
        # Create user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create category, brand, and product type
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        
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
            secondary_product_title='Chicago',
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            retail_price=Decimal('180.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        # Create customer address
        self.shipping_address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="Test City",
            state="Oklahoma",
            postcode="12345",
            default=True,
            is_default_shipping=True,
            # is_default_billing=is_default_billing
        )


        self.billing_address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="Test City",
            state="Oklahoma",
            postcode="12345",
            default=True
            )

    def test_create_order(self):
        """Test creating a basic order"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001',
            billing_status=True
        )
        
        self.assertIsNotNone(order.id)
        self.assertIsInstance(order.id, uuid.UUID)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.full_name, 'Test User')
        self.assertEqual(order.total_paid, Decimal('215.00'))
        self.assertTrue(order.billing_status)

    def test_order_uuid_auto_generated(self):
        """Test that order ID is automatically generated as UUID"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )
        
        self.assertIsInstance(order.id, uuid.UUID)
        self.assertIsNotNone(order.id)

    def test_order_default_values(self):
        """Test default values for order fields"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )
        
        self.assertFalse(order.billing_status)
        self.assertEqual(order.discount, 0)
        self.assertIsNone(order.coupon)
        self.assertEqual(order.payment_data_id, '')

    def test_order_with_addresses(self):
        """Test order with shipping and billing addresses"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001',
            shipping_address=self.shipping_address,
            billing_address=self.billing_address
        )
        
        self.assertEqual(order.shipping_address, self.shipping_address)
        self.assertEqual(order.billing_address, self.billing_address)

    @unittest.skip("Coupon")
    def test_order_with_coupon(self):
        """Test order with coupon and discount"""
        coupon = PopUpCoupon.objects.create(
            code='SAVE10',
            discount_percentage=10,
            is_active=True
        )
        
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('193.50'),
            order_key='TEST-ORDER-001',
            coupon=coupon,
            discount=10
        )
        
        self.assertEqual(order.coupon, coupon)
        self.assertEqual(order.discount, 10)

    def test_discount_validation_min_value(self):
        """Test discount cannot be negative"""
        with self.assertRaises(ValidationError):
            order = PopUpCustomerOrder(
                user=self.user,
                full_name='Test User',
                email='test@example.com',
                address1='123 Test St',
                postal_code='12345',
                city='Test City',
                state='TS',
                total_paid=Decimal('215.00'),
                order_key='TEST-ORDER-001',
                discount=-5
            )
            order.full_clean()

    def test_discount_validation_max_value(self):
        """Test discount cannot exceed 100"""
        with self.assertRaises(ValidationError):
            order = PopUpCustomerOrder(
                user=self.user,
                full_name='Test User',
                email='test@example.com',
                address1='123 Test St',
                postal_code='12345',
                city='Test City',
                state='TS',
                total_paid=Decimal('215.00'),
                order_key='TEST-ORDER-001',
                discount=150
            )
            order.full_clean()

    def test_order_timestamps(self):
        """Test that timestamps are set automatically"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )
        
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)
        self.assertLessEqual(order.created_at, order.updated_at)

    def test_order_str_representation(self):
        """Test string representation of order"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )
        
        self.assertEqual(str(order), f"Order {order.id}")

    def test_order_ordering(self):
        """Test that orders are ordered by created_at descending"""
        order1 = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )
        
        order2 = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('180.00'),
            order_key='TEST-ORDER-002'
        )
        
        orders = PopUpCustomerOrder.objects.all()
        self.assertEqual(orders[0], order2)
        self.assertEqual(orders[1], order1)

    def test_get_total_cost_no_discount(self):
        """Test get_total_cost with no discount"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('395.00'),
            order_key='TEST-ORDER-001'
        )
        
        # Add order items
        PopUpOrderItem.objects.create(
            order=order,
            product=self.product1,
            product_title=self.product1.product_title,
            secondary_product_title=self.product1.secondary_product_title,
            price=Decimal('215.00'),
            quantity=1
        )
        
        PopUpOrderItem.objects.create(
            order=order,
            product=self.product2,
            product_title=self.product2.product_title,
            secondary_product_title=self.product2.secondary_product_title,
            price=Decimal('180.00'),
            quantity=1
        )
        
        total = order.get_total_cost()
        self.assertEqual(total, Decimal('395.00'))

    def test_get_total_cost_with_discount(self):
        """Test get_total_cost with discount applied"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('355.50'),
            order_key='TEST-ORDER-001',
            discount=10
        )
        
        # Add order items
        PopUpOrderItem.objects.create(
            order=order,
            product=self.product1,
            product_title=self.product1.product_title,
            price=Decimal('215.00'),
            quantity=1
        )
        
        PopUpOrderItem.objects.create(
            order=order,
            product=self.product2,
            product_title=self.product2.product_title,
            price=Decimal('180.00'),
            quantity=1
        )
        
        total = order.get_total_cost()
        # (215 + 180) * 0.9 = 355.50
        self.assertEqual(total, Decimal('355.50'))

    def test_get_total_cost_empty_order(self):
        """Test get_total_cost with no items"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('0.00'),
            order_key='TEST-ORDER-001'
        )
        
        total = order.get_total_cost()
        self.assertEqual(total, Decimal('0.00'))

    def test_cascade_delete_user(self):
        """Test that orders are deleted when user is deleted"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )
        
        order_id = order.id
        self.user.hard_delete()        
        
        with self.assertRaises(PopUpCustomerOrder.DoesNotExist):
            PopUpCustomerOrder.objects.get(id=order_id)

    # def test_set_null_on_address_delete(self):
    #     """Test that address fields are set to null when address is deleted"""
    #     order = PopUpCustomerOrder.objects.create(
    #         user=self.user,
    #         full_name='Test User',
    #         email='test@example.com',
    #         address1='123 Test St',
    #         postal_code='12345',
    #         city='Test City',
    #         state='TS',
    #         total_paid=Decimal('215.00'),
    #         order_key='TEST-ORDER-001',
    #         shipping_address=self.shipping_address
    #     )

        
    #     self.shipping_address.delete()
    #     order.save()
    #     order.refresh_from_db()
        
    #     self.assertIsNone(order.shipping_address)

    def test_optional_fields_blank(self):
        """Test that optional fields can be blank"""
        order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
            # address2, apartment_suite_number, phone all blank
        )
        
        self.assertIsNone(order.address2)
        self.assertEqual(order.apartment_suite_number, '')
        self.assertIsNone(order.phone)

    def test_verbose_names(self):
        """Test model verbose names"""
        self.assertEqual(
            str(PopUpCustomerOrder._meta.verbose_name), 
            'Pop Up Customer Order'
        )
        self.assertEqual(
            str(PopUpCustomerOrder._meta.verbose_name_plural), 
            'Pop Up Customer Orders'
        )


class TestPopUpOrderItemModel(TestCase):
    """Test suite for PopUpOrderItem model"""

    def setUp(self):
        """Set up test data"""
        # Create user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create category, brand, and product type
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )
        
        # Create test product
        self.product = PopUpProduct.objects.create(
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
        
        # Create test order
        self.order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001'
        )

    def test_create_order_item(self):
        """Test creating a basic order item"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            size='9',
            color='Military Blue',
            price=Decimal('215.00'),
            quantity=1
        )
        
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.product_title, 'Air Jordan 4')
        self.assertEqual(item.price, Decimal('215.00'))
        self.assertEqual(item.quantity, 1)

    def test_order_item_default_quantity(self):
        """Test default quantity is 1"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00')
        )
        
        self.assertEqual(item.quantity, 1)

    def test_order_item_denormalized_fields(self):
        """Test that product details are denormalized at purchase time"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            size='9',
            color='Military Blue',
            price=Decimal('215.00'),
            quantity=1
        )
        
        # Change product title
        self.product.product_title = 'Air Jordan 4 Updated'
        self.product.save()
        
        # Order item should still have original title
        item.refresh_from_db()
        self.assertEqual(item.product_title, 'Air Jordan 4')
        self.assertNotEqual(item.product_title, self.product.product_title)

    def test_get_cost_single_quantity(self):
        """Test get_cost with quantity of 1"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        self.assertEqual(item.get_cost(), Decimal('215.00'))

    def test_get_cost_multiple_quantity(self):
        """Test get_cost with multiple quantities"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=3
        )
        
        self.assertEqual(item.get_cost(), Decimal('645.00'))

    def test_order_item_str_representation(self):
        """Test string representation of order item"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            price=Decimal('215.00'),
            quantity=1
        )
        
        expected = f"Air Jordan 4 Retro Military Blue: Product id: {item.id}"
        self.assertEqual(str(item), expected)

    def test_order_item_str_no_secondary_title(self):
        """Test string representation without secondary title"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        expected = f"Air Jordan 4 None: Product id: {item.id}"
        self.assertEqual(str(item), expected)

    def test_cascade_delete_order(self):
        """Test that order items are deleted when order is deleted"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        item_id = item.id
        self.order.delete()
        
        with self.assertRaises(PopUpOrderItem.DoesNotExist):
            PopUpOrderItem.objects.get(id=item_id)

    def test_cascade_delete_product(self):
        """Test that order items are deleted when product is deleted"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        item_id = item.id
        self.product.delete()
        
        with self.assertRaises(PopUpOrderItem.DoesNotExist):
            PopUpOrderItem.objects.get(id=item_id)

    def test_multiple_items_per_order(self):
        """Test adding multiple items to one order"""
        product2 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            slug='jordan-1',
            buy_now_price=Decimal('180.00'),
            retail_price=Decimal('180.00'),
            inventory_status='in_inventory'
        )
        
        item1 = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        item2 = PopUpOrderItem.objects.create(
            order=self.order,
            product=product2,
            product_title='Air Jordan 1',
            price=Decimal('180.00'),
            quantity=2
        )
        
        self.assertEqual(self.order.items.count(), 2)
        self.assertIn(item1, self.order.items.all())
        self.assertIn(item2, self.order.items.all())

    def test_order_item_optional_fields(self):
        """Test that size, color, and secondary title can be blank"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        self.assertIsNone(item.secondary_product_title)
        self.assertIsNone(item.size)
        self.assertIsNone(item.color)

    def test_order_item_decimal_precision(self):
        """Test that price maintains decimal precision"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('214.99'),
            quantity=2
        )
        
        self.assertEqual(item.price, Decimal('214.99'))
        self.assertEqual(item.get_cost(), Decimal('429.98'))

    def test_order_item_ordering(self):
        """Test that order items are ordered by order descending"""
        order2 = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('180.00'),
            order_key='TEST-ORDER-002'
        )
        
        item1 = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        item2 = PopUpOrderItem.objects.create(
            order=order2,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        items = PopUpOrderItem.objects.all()
        self.assertEqual(items[0], item1)
        self.assertEqual(items[1], item2)

    def test_related_name_items(self):
        """Test accessing order items via related name"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        self.assertEqual(self.order.items.count(), 1)
        self.assertEqual(self.order.items.first(), item)

    def test_related_name_order_items(self):
        """Test accessing product's order items via related name"""
        item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=1
        )
        
        self.assertEqual(self.product.order_items.count(), 1)
        self.assertEqual(self.product.order_items.first(), item)

    def test_verbose_names(self):
        """Test model verbose names"""
        self.assertEqual(
            str(PopUpOrderItem._meta.verbose_name), 
            'PopUp Order Item'
        )
        self.assertEqual(
            str(PopUpOrderItem._meta.verbose_name_plural), 
            'PopUp Order Items'
        )

    # def test_zero_quantity_not_allowed(self):
    #     """Test that quantity must be positive"""
    #     with self.assertRaises(IntegrityError):
    #         PopUpOrderItem.objects.create(
    #             order=self.order,
    #             product=self.product,
    #             product_title='Air Jordan 4',
    #             price=Decimal('215.00'),
    #             quantity=0
    #         )

    def test_total_cost_calculation_integration(self):
        """Test integration between order items and order total cost"""
        # Create multiple items
        PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 4',
            price=Decimal('215.00'),
            quantity=2
        )
        
        PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_title='Air Jordan 1',
            price=Decimal('180.00'),
            quantity=1
        )
        
        # Total should be (215 * 2) + (180 * 1) = 610
        total = self.order.get_total_cost()
        self.assertEqual(total, Decimal('610.00'))