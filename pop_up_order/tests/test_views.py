"""
NEED TO WORK ON THE PAYMENTS APP BEFORE THE ORDERS APP
ONCE PAYMENTS IS TESTED AND SQUARED AWAY, CAN FINISH THESE TESTS
ALSO, NEED TO VERIFY THAT THE "admin_order_detail" VIEW IS NEEDED
"""

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

        service_type, _ = PopUpProductType.objects.get_or_create(
        slug='service', defaults={'name': 'Service', 'is_active': True}
        )

        service_category, _ = PopUpCategory.objects.get_or_create(
            slug='service', defaults={'name': 'Service'}
        )

        service_brand, _ = PopUpBrand.objects.get_or_create(
            slug='pop-up-shop', defaults={'name': 'Pop Up Shop'}
        )
        self.procurement_product = PopUpProduct.objects.create(
            product_type=service_type,
            category=service_category,
            brand=service_brand,
            product_title='Procurement Service Fee',
            slug='procurement-service-fee',
            retail_price=Decimal('15.00'),
            buy_now_price=Decimal('15.00'),
            inventory_status='in_inventory',
            is_active=False,
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
        
        print('test reservation:', reservation)
        print(f'r.user:', reservation.user)
        print(f'r.product:', reservation.product)
        print(f'r.expires_at:', reservation.expires_at)
        print(f'r.is_paid:', reservation.is_paid)

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

        print('response.json()', response.json())
        
        self.assertEqual(response.status_code, 200)
        
        # Verify both items created
        order = PopUpCustomerOrder.objects.first()
        self.assertEqual(order.items.count(), 2)
        
        # Verify both products updated
        self.product.refresh_from_db()
        product2.refresh_from_db()
        self.assertEqual(self.product.inventory_status, 'sold_out')
        self.assertEqual(product2.inventory_status, 'sold_out')




class TestAdminOrderDetailView(TestCase):
    """Test suite for admin_order_detail view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create regular user
        self.user, self.user_profile = create_test_user(
            "customer@example.com", "testpass!23", "John", "Customer", "9", "male"
        )
        
        # Create staff user (admin)
        # self.staff_user, self.staff_profile = create_test_user(
        #     "admin@example.com", "adminpass!23", "Admin", "User", "10", "male"
        # )
        # self.staff_user.is_staff = True
        # self.staff_user.save()
        
        self.staff_user, self.staff_profile = create_test_staff_user(
            'admin@example.com', 'adminpass!23', 'Admin',' User', '10', 'male'
        )
        
        # Create superuser
        self.superuser, self.superuser_profile = create_test_user(
            "super@example.com", "superpass!23", "Super", "Admin", "11", "male"
        )
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        
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
            inventory_status='sold_out',
            is_active=False
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
            inventory_status='sold_out',
            is_active=False
        )
        
        # Create test order
        self.order = PopUpCustomerOrder.objects.create(
            user=self.user,
            email=self.user.email,
            billing_status=True,
            address1='123 Test St',
            address2='Apt 4B',
            apartment_suite_number='4B',
            city='Test City',
            state='TN',
            postal_code="12345",
            total_paid=Decimal('395.00'),
        )
        
        # Create order items
        self.order_item1 = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product1,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            price=Decimal('215.00'),
            quantity=1
        )
        
        self.order_item2 = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.product2,
            product_title='Air Jordan 1',
            secondary_product_title='Chicago',
            price=Decimal('180.00'),
            quantity=1
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order_item1.id})
        
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)

    def test_non_staff_user_forbidden(self):
        """Test that non-staff users cannot access the view"""
        self.client.force_login(self.user)
        url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order_item1.id})
        
        response = self.client.get(url)
        
        # Should redirect to login (staff_member_required behavior)
        self.assertEqual(response.status_code, 302)

    # @unittest.skip("Come Back And Reasses I many not need this view")
    # def test_staff_user_can_access(self):
    #     """Test that staff users can access the view"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order_item1.id})
        
    #     response = self.client.get(url)
    #     print('response.context', response.context)
        
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'orders/admin/detail.html')

    # @unittest.skip("Come Back And Reasses I may not need this view")
    # def test_superuser_can_access(self):
    #     """Test that superusers can access the view"""
    #     self.client.force_login(self.superuser)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order_item1.id})
        
    #     response = self.client.get(url)
        
    #     # self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'orders/admin/detail.html')

    # def test_order_in_context(self):
    #     """Test that order is passed to template context"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order_item1.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('order', response.context)
    #     self.assertEqual(response.context['order'], self.order)

    # def test_order_details_displayed(self):
    #     """Test that order details are displayed in the response"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     # Check order details in response
    #     content = response.content.decode('utf-8')
    #     self.assertIn('John Customer', content)
    #     self.assertIn('customer@example.com', content)
    #     self.assertIn('123 Test St', content)
    #     self.assertIn('Test City', content)
    #     self.assertIn('12345', content)

    # def test_order_items_displayed(self):
    #     """Test that order items are displayed"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     content = response.content.decode('utf-8')
    #     # Check both products are shown
    #     self.assertIn('Air Jordan 4', content)
    #     self.assertIn('Air Jordan 1', content)

    # def test_order_total_displayed(self):
    #     """Test that order total is calculated and displayed"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     # Check total is correct (215 + 180 = 395)
    #     content = response.content.decode('utf-8')
    #     self.assertIn('395', content)  # Total amount

    # def test_nonexistent_order_returns_404(self):
    #     """Test that requesting a non-existent order returns 404"""
    #     self.client.force_login(self.staff_user)
        
    #     # Generate random UUID that doesn't exist
    #     fake_order_id = uuid.uuid4()
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': fake_order_id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 404)

    # def test_order_with_no_items(self):
    #     """Test display of order with no items"""
    #     # Create order with no items
    #     empty_order = PopUpCustomerOrder.objects.create(
    #         user=self.user,
    #         full_name='Empty Order',
    #         email='empty@example.com',
    #         address1='456 Empty St',
    #         postal_code='99999',
    #         city='Empty City',
    #         state='ES',
    #         total_paid=Decimal('0.00'),
    #         order_key='EMPTY-ORDER',
    #         billing_status=False
    #     )
        
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': empty_order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.context['order'].items.count(), 0)

    # def test_order_with_discount(self):
    #     """Test display of order with discount applied"""
    #     # Create order with discount
    #     discounted_order = PopUpCustomerOrder.objects.create(
    #         user=self.user,
    #         full_name='Discount Customer',
    #         email='discount@example.com',
    #         address1='789 Discount Ave',
    #         postal_code='88888',
    #         city='Discount City',
    #         state='DC',
    #         total_paid=Decimal('180.00'),
    #         order_key='DISCOUNT-ORDER',
    #         billing_status=True,
    #         discount=10  # 10% discount
    #     )
        
    #     # Add item
    #     PopUpOrderItem.objects.create(
    #         order=discounted_order,
    #         product=self.product1,
    #         product_title='Air Jordan 4',
    #         price=Decimal('200.00'),
    #         quantity=1
    #     )
        
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': discounted_order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     # Check discounted total (200 - 10% = 180)
    #     order_total = response.context['order'].get_total_cost()
    #     self.assertEqual(order_total, Decimal('180.00'))

    # def test_breadcrumbs_present(self):
    #     """Test that breadcrumb navigation is present"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     content = response.content.decode('utf-8')
    #     self.assertIn('breadcrumbs', content)
    #     self.assertIn('Home', content)
    #     self.assertIn('Orders', content)

    # def test_print_button_present(self):
    #     """Test that print button is present"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     content = response.content.decode('utf-8')
    #     self.assertIn('Print Order', content)
    #     self.assertIn('window.print()', content)

    # def test_order_status_paid_displayed(self):
    #     """Test that paid status is displayed correctly"""
    #     # Order already has billing_status=True
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     content = response.content.decode('utf-8')
    #     # Based on template: {% if order.paid %}Paid{% else %}Pending payment{% endif %}
    #     # Note: Your template uses order.paid but model has billing_status
    #     # This might need adjustment in template or test
    #     # Assuming template should check billing_status
    #     self.assertIn('Paid', content)

    # def test_order_status_pending_displayed(self):
    #     """Test that pending payment status is displayed"""
    #     # Create unpaid order
    #     unpaid_order = PopUpCustomerOrder.objects.create(
    #         user=self.user,
    #         full_name='Unpaid Customer',
    #         email='unpaid@example.com',
    #         address1='999 Unpaid Rd',
    #         postal_code='77777',
    #         city='Unpaid City',
    #         state='UP',
    #         total_paid=Decimal('100.00'),
    #         order_key='UNPAID-ORDER',
    #         billing_status=False  # Not paid
    #     )
        
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': unpaid_order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     content = response.content.decode('utf-8')
    #     self.assertIn('Pending payment', content)

    # def test_multiple_quantity_items_cost_calculation(self):
    #     """Test that item costs are calculated correctly for multiple quantities"""
    #     # Create order with multiple quantity item
    #     multi_qty_order = PopUpCustomerOrder.objects.create(
    #         user=self.user,
    #         full_name='Multi Qty Customer',
    #         email='multi@example.com',
    #         address1='111 Multi St',
    #         postal_code='66666',
    #         city='Multi City',
    #         state='MQ',
    #         total_paid=Decimal('600.00'),
    #         order_key='MULTI-QTY-ORDER',
    #         billing_status=True
    #     )
        
    #     # Add item with quantity 3
    #     multi_item = PopUpOrderItem.objects.create(
    #         order=multi_qty_order,
    #         product=self.product1,
    #         product_title='Air Jordan 4',
    #         price=Decimal('200.00'),
    #         quantity=3
    #     )
        
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': multi_qty_order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     # Verify item cost calculation (200 * 3 = 600)
    #     self.assertEqual(multi_item.get_cost(), Decimal('600.00'))

    # def test_order_id_in_page_title(self):
    #     """Test that order ID appears in page title"""
    #     self.client.force_login(self.staff_user)
    #     url = reverse('pop_up_order:admin_order_detail', kwargs={'order_id': self.order.id})
        
    #     response = self.client.get(url)
        
    #     self.assertEqual(response.status_code, 200)
        
    #     content = response.content.decode('utf-8')
    #     self.assertIn(f'Order {self.order.id}', content)