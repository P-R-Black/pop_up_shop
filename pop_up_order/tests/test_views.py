from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from decimal import Decimal
from unittest.mock import patch, MagicMock
import unittest
import stripe
import json
import uuid
from pop_up_cart.models import PopUpCartItem
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from pop_up_payment.models import PopUpPayment
from pop_up_shipping.models import PopUpShipment
from pop_up_finance.models import PopUpFinance
from pop_up_auction.models import (
    PopUpProduct, PopUpCategory, PopUpBrand, 
    PopUpProductType, WinnerReservation,
    PopUpProductSpecification, PopUpProductSpecificationValue
)

from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerAddress
from pop_up_cart.cart import Cart
from django.utils.timezone import now, make_aware
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime, date 
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_staff_user)

User = get_user_model()



def create_test_address(customer, first_name, last_name, address_line, address_line2, 
                       apartment_suite_number, town_city, state, postcode, 
                       delivery_instructions, default=True, is_default_shipping=False,
                       is_default_billing=False):
    
    """Helper function to create customer address"""
    return PopUpCustomerAddress.objects.create(
        customer=customer,
        first_name=first_name,
        last_name=last_name,
        address_line=address_line,
        address_line2=address_line2,
        apartment_suite_number=apartment_suite_number,
        town_city=town_city,
        state=state,
        postcode=postcode,
        delivery_instructions=delivery_instructions,
        default=default,
        is_default_shipping=is_default_shipping,
        is_default_billing=is_default_billing
    )


class TestCreateOrderAfterPaymentView(TestCase):
    """Test suite for CreateOrderAfterPaymentView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.url = reverse('pop_up_order:create_after_payment')  # Update with your URL name
        
        # Create user and profile
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create addresses
        self.shipping_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 Test St",
            address_line2="",
            apartment_suite_number="",
            town_city="Test City",
            state="Oklahoma",
            postcode="12345",
            delivery_instructions="Leave at door",
            default=True,
            is_default_shipping=True,
            is_default_billing=False
        )
        
        self.billing_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Billing Ave",
            address_line2="",
            apartment_suite_number="Apt 2",
            town_city="Billing City",
            state="Texas",
            postcode="67890",
            delivery_instructions="",
            default=False,
            is_default_shipping=False,
            is_default_billing=True
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
        
        # Create product specifications
        self.size_spec = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='size'
        )
        
        self.colorway_spec = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='colorway'
        )
        
        self.product_sex_spec = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='product_sex'
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
            reserve_price=Decimal('200.00'),
            inventory_status='reserved',
            is_active=True
        )
        
        # Add product specifications
        PopUpProductSpecificationValue.objects.create(
            product=self.product,
            specification=self.size_spec,
            value='9'
        )
        
        PopUpProductSpecificationValue.objects.create(
            product=self.product,
            specification=self.colorway_spec,
            value='Military Blue'
        )
        
        PopUpProductSpecificationValue.objects.create(
            product=self.product,
            specification=self.product_sex_spec,
            value='Male'
        )
        
        # Login user
        self.client.force_login(self.user)
        
        # Clear mail outbox
        mail.outbox = []

    def _get_valid_payload(self):
        """Helper to create valid request payload"""
        return {
            'payment_data_id': 'pi_test_123456789',
            'payment_method': 'stripe',
            'order_key': f'ORDER-{uuid.uuid4()}',
            'user_id': str(self.user.id),
            'total_paid': '215.00',
            'email': 'test@example.com',
            'address1': '123 Test St',
            'address2': '',
            'postal_code': '12345',
            'apartment_suite_number': '',
            'city': 'Test City',
            'state': 'Oklahoma',
            'phone': '<span class="phone-display">555-1234</span>',
            'shippingAddressId': str(self.shipping_address.id),
            'billingAddressId': str(self.billing_address.id),
            'discount': 0,
        }

    def _add_product_to_cart(self):
        """Helper to add product to session cart"""
        
        # For authenticated users, create PopUpCartItem in database
        PopUpCartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=1,
            auction_locked=False,
            buy_now=True  # Set to True since product is 'reserved'
        )

    @patch('pop_up_order.views.stripe.Customer.create')
    @patch('pop_up_order.views.stripe.PaymentIntent.retrieve')
    @patch('pop_up_order.views.stripe.PaymentMethod.attach')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_successful_order_creation(self, mock_email, mock_fees, mock_attach, 
                                       mock_retrieve, mock_stripe_customer):
        """Test successful order creation with valid data"""
        # Setup mocks
        mock_stripe_customer.return_value = MagicMock(id='cus_test123')
        mock_retrieve.return_value = MagicMock(payment_method='pm_test123')
        mock_fees.return_value = Decimal('10.00')
        
        # Add product to cart
        self._add_product_to_cart()

        # ✅ DEBUG: Check cart contents
        cart = Cart(self.client)
        
        # Make request
        payload = self._get_valid_payload()
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('order_id', data)
        
        # Verify order was created
        order = PopUpCustomerOrder.objects.get(id=data['order_id'])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_paid, Decimal('215.00'))
        self.assertTrue(order.billing_status)
        self.assertEqual(order.shipping_address, self.shipping_address)
        self.assertEqual(order.billing_address, self.billing_address)
        
        # Verify order item was created
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.product_title, 'Air Jordan 4')
        self.assertEqual(order_item.size, '9')
        self.assertEqual(order_item.color, 'Military Blue')
        
        # Verify payment was created
        payment = PopUpPayment.objects.get(order=order)
        self.assertEqual(payment.amount, Decimal('215.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.payment_method, 'stripe')
        
        # Verify shipment was created
        shipment = PopUpShipment.objects.get(order=order)
        self.assertEqual(shipment.status, 'pending')
        self.assertEqual(shipment.carrier, 'usps')
        
        # Verify finance record was created
        finance = PopUpFinance.objects.get(order=order)
        self.assertEqual(finance.final_price, Decimal('215.00'))
        self.assertEqual(finance.fees, Decimal('10.00'))
        
        # Verify product status updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory_status, 'sold_out')
        self.assertFalse(self.product.is_active)
        
        # Verify email was sent
        mock_email.assert_called_once()

    @patch('pop_up_order.views.stripe.Customer.create')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_phone_number_extraction(self, mock_email, mock_fees, mock_stripe):
        """Test that phone number is correctly extracted from HTML span"""
        mock_stripe.return_value = MagicMock(id='cus_test123')
        mock_fees.return_value = Decimal('10.00')
        
        self._add_product_to_cart()
        
        payload = self._get_valid_payload()
        payload['phone'] = '<span class="phone-display">555-1234</span>'
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        order = PopUpCustomerOrder.objects.first()
        self.assertEqual(order.phone, '555-1234')

    @patch('pop_up_order.views.stripe.Customer.create')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_stripe_customer_creation(self, mock_email, mock_fees, mock_stripe_customer):
        """Test Stripe customer is created if user doesn't have one"""
        mock_stripe_customer.return_value = MagicMock(id='cus_new123')
        mock_fees.return_value = Decimal('10.00')
        
        # Verify user doesn't have Stripe customer ID
        self.assertIsNone(self.user_profile.stripe_customer_id)
        
        self._add_product_to_cart()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify Stripe customer was created
        mock_stripe_customer.assert_called_once()
        
        # Verify customer ID was saved
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.stripe_customer_id, 'cus_new123')

    @patch('pop_up_order.views.stripe.Customer.create')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_existing_stripe_customer_not_recreated(self, mock_email, mock_fees, mock_stripe):
        """Test existing Stripe customer is not recreated"""
        mock_fees.return_value = Decimal('10.00')
        
        # Set existing Stripe customer ID
        self.user_profile.stripe_customer_id = 'cus_existing123'
        self.user_profile.save()
        
        self._add_product_to_cart()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify Stripe customer creation was NOT called
        mock_stripe.assert_not_called()

    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_winner_reservation_marked_paid(self, mock_email, mock_fees):
        """Test that winner reservation is marked as paid after order creation"""
        mock_fees.return_value = Decimal('10.00')
        
        # Create winner reservation
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=django_timezone.now() + timedelta(hours=48),
            is_paid=False
        )
        
        self._add_product_to_cart()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify reservation is marked paid
        reservation.refresh_from_db()
        self.assertTrue(reservation.is_paid)


    def test_missing_payment_data_id(self):
        """Test error when payment_data_id is missing"""
        self._add_product_to_cart()
        
        payload = self._get_valid_payload()
        del payload['payment_data_id']
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        print('response.json()', response.json(), '\n')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


    def test_invalid_user_id(self):
        """Test error when user_id is invalid"""
        self._add_product_to_cart()
        
        payload = self._get_valid_payload()
        payload['user_id'] = str(uuid.uuid4())  # Non-existent user
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


    def test_invalid_shipping_address(self):
        """Test error when shipping address doesn't exist"""
        self._add_product_to_cart()
        
        payload = self._get_valid_payload()
        payload['shippingAddressId'] = str(uuid.uuid4())  # Non-existent address
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)


    def test_empty_cart(self):
        """Test behavior when cart is empty"""
        # Don't add anything to cart
        
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        # Should still create order but with no items
        self.assertEqual(response.status_code, 200)
        
        order = PopUpCustomerOrder.objects.first()
        self.assertEqual(order.items.count(), 0)


    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_product_not_in_reserved_status(self, mock_email, mock_fees):
        """Test that products not in 'reserved' or 'sold_out' status are skipped"""
        mock_fees.return_value = Decimal('10.00')
        
        # Change product status to something else
        self.product.inventory_status = 'in_inventory'
        self.product.save()
        
        self._add_product_to_cart()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Order created but no items
        order = PopUpCustomerOrder.objects.first()
        self.assertEqual(order.items.count(), 0)

    @patch('pop_up_order.views.get_fees_by_payment')
    def test_payment_fees_error_handling(self, mock_fees):
        """Test that payment fee errors are handled gracefully"""
        mock_fees.side_effect = Exception("Fee calculation failed")
        
        self._add_product_to_cart()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        # Should still succeed with fees = 0.00
        self.assertEqual(response.status_code, 200)
        
        finance = PopUpFinance.objects.first()
        self.assertEqual(finance.fees, Decimal('0.00'))

    @patch('pop_up_order.views.stripe.Customer.create')
    def test_stripe_error_handling(self, mock_stripe):
        """Test that Stripe errors are handled gracefully"""
       
        mock_stripe.side_effect = stripe.error.StripeError("API Error")
        
        self._add_product_to_cart()
        
        # Should still create order even if Stripe fails
        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify order was created despite Stripe error
        order = PopUpCustomerOrder.objects.first()
        self.assertIsNotNone(order)

    # @unittest.skip("Needs Further Review")
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    def test_multiple_products_in_cart(self, mock_email, mock_fees):
        """Test order creation with multiple products in cart"""
        mock_fees.return_value = Decimal('15.00')
        
        # Create second product
        product2 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            secondary_product_title='Chicago',
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            retail_price=Decimal('180.00'),
            reserve_price=Decimal('170.00'),
            inventory_status='reserved',
            is_active=True
        )
        
        # Add both products to cart
        PopUpCartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=1,
            auction_locked=False,
            buy_now=True  # Set to True since product is 'reserved'
        )

        PopUpCartItem.objects.create(
            user=self.user,
            product=product2,  # ← Second product (different!)
            quantity=1,
            auction_locked=False,
            buy_now=True
        )
        
        
        payload = self._get_valid_payload()
        payload['total_paid'] = '395.00'
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        print('response.json()', response)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify both items created
        order = PopUpCustomerOrder.objects.first()
        self.assertEqual(order.items.count(), 2)
        
        # Verify both products updated
        self.product.refresh_from_db()
        product2.refresh_from_db()
        self.assertEqual(self.product.inventory_status, 'sold_out')
        self.assertEqual(product2.inventory_status, 'sold_out')
