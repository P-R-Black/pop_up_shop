from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from decimal import Decimal
from django.utils.timezone import now
from pop_up_finance.models import PopUpFinance
from pop_up_auction.models import (
    PopUpProduct, 
    PopUpCategory, 
    PopUpBrand, 
    PopUpProductType,
)
from pop_up_order.models import PopUpCustomerOrder
from pop_accounts.models import PopUpCustomerProfile

from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_staff_user)

from django.contrib.auth import get_user_model

User = get_user_model()


class TestPopUpFinanceModel(TestCase):
    """Test suite for PopUpFinance model"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
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
            acquisition_cost=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        # Create test order
        self.order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User1',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-001',
            billing_status=True
        )

    def test_create_finance_record(self):
        """Test creating a basic finance record"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            fees=Decimal('10.00'),
            payment_method='stripe'
        )
        
        self.assertEqual(finance.order, self.order)
        self.assertEqual(finance.product, self.product)
        self.assertEqual(finance.reserve_price, Decimal('200.00'))
        self.assertEqual(finance.final_price, Decimal('215.00'))
        self.assertEqual(finance.fees, Decimal('10.00'))
        self.assertEqual(finance.payment_method, 'stripe')
        self.assertFalse(finance.is_disputed)
        self.assertFalse(finance.is_refunded)

    def test_finance_default_values(self):
        """Test that default values are set correctly"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertEqual(finance.fees, Decimal('0.00'))
        self.assertEqual(finance.refunded_amount, Decimal('0.00'))
        self.assertEqual(finance.profit, Decimal('0.00'))
        self.assertFalse(finance.is_disputed)
        self.assertFalse(finance.is_refunded)

    def test_one_to_one_relationship_with_order(self):
        """Test that one order can only have one finance record"""
        PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        # Attempting to create another finance record for same order should fail
        with self.assertRaises(IntegrityError):
            PopUpFinance.objects.create(
                order=self.order,
                product=self.product,
                reserve_price=Decimal('200.00'),
                final_price=Decimal('220.00'),
                payment_method='paypal'
            )

    def test_calculate_revenue_no_refund(self):
        """Test revenue calculation without refunds"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            fees=Decimal('10.00'),
            payment_method='stripe'
        )
        
        revenue = finance.calculate_revenue()
        self.assertEqual(revenue, Decimal('215.00'))

    def test_calculate_revenue_with_refund(self):
        """Test revenue calculation with partial refund"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            refunded_amount=Decimal('50.00'),
            fees=Decimal('10.00'),
            payment_method='stripe'
        )
        
        revenue = finance.calculate_revenue()
        self.assertEqual(revenue, Decimal('165.00'))

    def test_calculate_revenue_full_refund(self):
        """Test revenue calculation with full refund"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            refunded_amount=Decimal('215.00'),
            fees=Decimal('10.00'),
            payment_method='stripe',
            is_refunded=True
        )
        
        revenue = finance.calculate_revenue()
        self.assertEqual(revenue, Decimal('0.00'))

    def test_calculate_profit_no_fees_no_refund(self):
        """Test profit calculation with no fees or refunds"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            fees=Decimal('0.00'),
            payment_method='stripe'
        )
        
        profit = finance.calculate_profit()
        # 215 (final) - 0 (refund) - 0 (fees) - 200 (reserve) = 15
        self.assertEqual(profit, Decimal('15.00'))

    def test_calculate_profit_with_fees(self):
        """Test profit calculation with fees"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            fees=Decimal('10.00'),
            payment_method='stripe'
        )
        
        profit = finance.calculate_profit()
        # 215 (final) - 0 (refund) - 10 (fees) - 200 (reserve) = 5
        self.assertEqual(profit, Decimal('5.00'))

    def test_calculate_profit_with_refund(self):
        """Test profit calculation with partial refund"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            refunded_amount=Decimal('50.00'),
            fees=Decimal('10.00'),
            payment_method='stripe'
        )
        
        profit = finance.calculate_profit()
        # (215 - 50) - 10 - 200 = -45
        self.assertEqual(profit, Decimal('-45.00'))

    def test_calculate_profit_full_refund(self):
        """Test profit calculation with full refund results in loss"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            refunded_amount=Decimal('215.00'),
            fees=Decimal('10.00'),
            payment_method='stripe',
            is_refunded=True
        )
        
        profit = finance.calculate_profit()
        # (215 - 215) - 10 - 200 = -210
        self.assertEqual(profit, Decimal('-210.00'))

    def test_calculate_profit_high_fees(self):
        """Test profit calculation where fees exceed margin"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            fees=Decimal('20.00'),
            payment_method='stripe'
        )
        
        profit = finance.calculate_profit()
        # 215 - 0 - 20 - 200 = -5 (loss)
        self.assertEqual(profit, Decimal('-5.00'))

    def test_payment_methods(self):
        """Test different payment methods can be stored"""
        payment_methods = ['stripe', 'paypal', 'venmo', 'apple pay', 'google pay', 'crypto']
        
        for idx, method in enumerate(payment_methods):
            # Create new order for each finance record
            order = PopUpCustomerOrder.objects.create(
                user=self.user,
                full_name='Test User1',
                email='test@example.com',
                address1='123 Test St',
                postal_code='12345',
                city='Test City',
                state='TS',
                total_paid=Decimal('215.00'),
                order_key=f'TEST-ORDER-{idx}',
                billing_status=True
            )
            
            finance = PopUpFinance.objects.create(
                order=order,
                product=self.product,
                reserve_price=Decimal('200.00'),
                final_price=Decimal('215.00'),
                payment_method=method
            )
            
            self.assertEqual(finance.payment_method, method)

    def test_disputed_order(self):
        """Test marking an order as disputed"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            fees=Decimal('10.00'),
            payment_method='stripe',
            is_disputed=True
        )
        
        self.assertTrue(finance.is_disputed)

    def test_refunded_order(self):
        """Test marking an order as refunded"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            refunded_amount=Decimal('215.00'),
            payment_method='stripe',
            is_refunded=True
        )
        
        self.assertTrue(finance.is_refunded)
        self.assertEqual(finance.refunded_amount, Decimal('215.00'))

    def test_timestamps(self):
        """Test that timestamps are set automatically"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertIsNotNone(finance.sold_at)
        self.assertIsNotNone(finance.updated_at)
        self.assertLessEqual(finance.sold_at, finance.updated_at)

    def test_updated_at_changes(self):
        """Test that updated_at changes when record is modified"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        original_updated = finance.updated_at
        
        # Modify the record
        finance.fees = Decimal('15.00')
        finance.save()
        
        finance.refresh_from_db()
        self.assertGreater(finance.updated_at, original_updated)

    def test_cascade_delete_with_order(self):
        """Test that finance record is deleted when order is deleted"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        finance_id = finance.id
        self.order.delete()
        
        # Finance record should be deleted
        with self.assertRaises(PopUpFinance.DoesNotExist):
            PopUpFinance.objects.get(id=finance_id)

    def test_cascade_delete_with_product(self):
        """Test that finance record is deleted when product is deleted"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        finance_id = finance.id
        self.product.delete()
        
        # Finance record should be deleted
        with self.assertRaises(PopUpFinance.DoesNotExist):
            PopUpFinance.objects.get(id=finance_id)

    def test_multiple_products_different_orders(self):
        """Test creating finance records for different orders"""
        order2 = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name='Test User1',
            email='test@example.com',
            address1='123 Test St',
            postal_code='12345',
            city='Test City',
            state='TS',
            total_paid=Decimal('215.00'),
            order_key='TEST-ORDER-002',
            billing_status=True
        )
        
        finance1 = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),
            payment_method='stripe'
        )
        
        finance2 = PopUpFinance.objects.create(
            order=order2,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('210.00'),
            payment_method='paypal'
        )
        
        self.assertEqual(PopUpFinance.objects.count(), 2)
        self.assertNotEqual(finance1.order, finance2.order)

    def test_decimal_precision(self):
        """Test that decimal values maintain precision"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('199.99'),
            final_price=Decimal('214.99'),
            fees=Decimal('10.50'),
            refunded_amount=Decimal('25.25'),
            payment_method='stripe'
        )
        
        self.assertEqual(finance.reserve_price, Decimal('199.99'))
        self.assertEqual(finance.final_price, Decimal('214.99'))
        self.assertEqual(finance.fees, Decimal('10.50'))
        self.assertEqual(finance.refunded_amount, Decimal('25.25'))

    def test_verbose_names(self):
        """Test model verbose names"""
        self.assertEqual(str(PopUpFinance._meta.verbose_name), 'PopUp Finance')
        self.assertEqual(str(PopUpFinance._meta.verbose_name_plural), 'PopUp Finances')

    def test_auction_win_scenario(self):
        """Test finance record for auction win"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('250.00'),  # Won auction at higher price
            fees=Decimal('12.50'),
            payment_method='stripe'
        )
        
        profit = finance.calculate_profit()
        # 250 - 0 - 12.50 - 200 = 37.50
        self.assertEqual(profit, Decimal('37.50'))

    def test_buy_now_scenario(self):
        """Test finance record for buy now purchase"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('200.00'),
            final_price=Decimal('215.00'),  # Buy now price
            fees=Decimal('10.00'),
            payment_method='stripe'
        )
        
        profit = finance.calculate_profit()
        # 215 - 0 - 10 - 200 = 5
        self.assertEqual(profit, Decimal('5.00'))

    def test_zero_values(self):
        """Test handling of zero values"""
        finance = PopUpFinance.objects.create(
            order=self.order,
            product=self.product,
            reserve_price=Decimal('0.00'),
            final_price=Decimal('0.00'),
            fees=Decimal('0.00'),
            refunded_amount=Decimal('0.00'),
            payment_method='comp'  # Complimentary item
        )
        
        self.assertEqual(finance.calculate_revenue(), Decimal('0.00'))
        self.assertEqual(finance.calculate_profit(), Decimal('0.00'))