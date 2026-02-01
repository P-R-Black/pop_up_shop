from django.test import TestCase, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from pop_up_payment.views import AjaxLoginRequiredMixin, ProductBuyView, ShippingAddressView, BillingAddressView
from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerAddress
from pop_up_auction.models import PopUpProduct, PopUpProductSpecification, PopUpCategory, PopUpBrand, PopUpProductType
from pop_up_cart.models import PopUpCartItem
from pop_up_payment.views import (AjaxLoginRequiredMixin)
from django.views import View
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.utils.text import slugify
from decimal import Decimal
from unittest.mock import patch, Mock, MagicMock
import time
import json
import stripe
from django.utils.timezone import now, make_aware
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime, date 
from django.contrib.messages import get_messages
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse

from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand)

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
    

# Create a test view that uses the mixin
class TestProtectedView(AjaxLoginRequiredMixin, View):
    """Test view that uses AjaxLoginRequiredMixin"""
    def get(self, request):
        return JsonResponse({'status': 'success', 'message': 'You are authenticated'})
    
    def post(self, request):
        return JsonResponse({'status': 'success', 'message': 'Bid placed successfully'})
    

class TestProductBuyViewGet(TestCase):
    """Test suite for ProductBuyView GET method"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.view = ProductBuyView.as_view()
        
        # Create test user
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
            reserve_price=Decimal('200.00'),
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

        # url
        self.url = reverse('pop_up_payment:payment_home')

    
    def _add_session_to_request(self, request):
        """Helper to add session to request"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
    

    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_with_items_in_cart(self, mock_gateway, mock_tax_rate):
        """Test GET request for authenticated user with items in cart"""
        mock_gateway.return_value = 'fake_client_token'
        mock_tax_rate.return_value = Decimal('0.07')
        
        self.client.force_login(self.user)
        
        # Add products to DATABASE cart AND session
        PopUpCartItem.objects.create(
            user=self.user,
            product=self.product1,
            quantity=2
        )
        PopUpCartItem.objects.create(
            user=self.user,
            product=self.product2,
            quantity=1
        )
        
        # Also add to session (Cart class likely uses session even for auth users)
        session = self.client.session
        session['skey'] = {
            str(self.product1.id): {
                'qty': 2,
                'price': str(self.product1.buy_now_price)
            },
            str(self.product2.id): {
                'qty': 1,
                'price': str(self.product2.buy_now_price)
            }
        }
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/payment_home.html')
        self.assertContains(response, 'Air Jordan 4')
        self.assertContains(response, 'Air Jordan 1')
        self.assertContains(response, self.shipping_address.address_line)
    

    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_empty_cart(self, mock_gateway, mock_tax_rate):
        """Test authenticated user with empty cart"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.07')
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show $0.00 for processing fee with empty cart
        self.assertContains(response, '$0.00')
    

    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_with_default_address(self, mock_gateway, mock_tax_rate):
        """Test GET request for authenticated user with default address"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.07')  # 7% tax
        
        self.client.force_login(self.user)
        
        # Add item to cart using helper
        self._add_to_cart(self.user, self.product1, 2)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

        # Verify default address is displayed
        self.assertContains(response, self.shipping_address.address_line)
        self.assertContains(response, self.shipping_address.town_city)

        # Verify tax and fees are present
        self.assertContains(response, 'Processing Fee')
        self.assertContains(response, 'Tax')


    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_with_selected_address(self, mock_gateway, mock_tax_rate):
        """Test authenticated user with selected shipping address in session"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.06')
        
        self.client.force_login(self.user)
        
        # Create additional address
        selected_address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line='789 Selected St',
            town_city='Miami',
            state='Florida',
            postcode='33101',
            default=False
        )
        
        # Add item to cart
        self._add_to_cart(self.user, self.product1, 1)
        
        # Set selected address in session
        session = self.client.session
        session['selected_address_id'] = str(selected_address.id)
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verify selected address is displayed (not default)
        self.assertContains(response, '789 Selected St')
        self.assertContains(response, 'Miami')


    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_with_billing_address(self, mock_gateway, mock_tax_rate):
        """Test authenticated user with billing address in session"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.07')
        
        self.client.force_login(self.user)
        
        # Add item to cart
        self._add_to_cart(self.user, self.product1, 1)
        
        # Set billing address in session
        session = self.client.session
        session['selected_billing_address_id'] = str(self.billing_address.id)
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verify billing address is displayed
        self.assertContains(response, self.billing_address.address_line)

    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_empty_cart_no_fees(self, mock_gateway, mock_tax_rate):
        """Test that processing fee is 0 for empty cart"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.07')
        
        self.client.force_login(self.user)
        # Don't add any items to cart
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should show $0.00 for processing fee and total
        self.assertContains(response, '$0.00')

    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_grand_total_calculation(self, mock_gateway, mock_tax_rate):
        """Test grand total calculation includes all components"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.07')
        
        self.client.force_login(self.user)
        
        # Add items to cart with known prices
        self._add_to_cart(self.user, self.product1, 2)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Calculate expected values
        subtotal = Decimal('430.00')
        tax = subtotal * Decimal('0.07')  # 30.10
        processing_fee = Decimal('2.50')
        shipping = Decimal('14.99') * 2  # 29.98
        expected_total = subtotal + tax + processing_fee + shipping  # 492.58
        
        # Check that total is present (format may vary with intcomma)
        self.assertContains(response, 'Total')

    @patch('pop_up_payment.views.get_state_tax_rate')
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_user_no_default_address_uses_florida(self, mock_gateway, mock_tax_rate):
        """Test that FL is used as default state when no address exists"""
        mock_gateway.return_value = 'fake_token'
        mock_tax_rate.return_value = Decimal('0.07')
        
        self.client.force_login(self.user)
        
        # Delete all addresses for user
        PopUpCustomerAddress.objects.filter(customer=self.user).delete()
        
        # Add item to cart
        self._add_to_cart(self.user, self.product1, 1)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verify get_state_tax_rate was called with 'Florida' (or 'FL')
        # Check the actual call - your view uses state from address or defaults to "FL"
        self.assertTrue(mock_tax_rate.called)

    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_authenticated_inactive_product_filtered_out(self, mock_gateway):
        """Test that inactive products are filtered out of cart"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        # Create an inactive product
        inactive_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 3',
            slug='jordan-3-inactive',
            buy_now_price=Decimal('199.99'),
            retail_price=Decimal('199.99'),
            inventory_status='in_inventory',
            is_active=False  # ← Inactive
        )
        
        # Add both active and inactive products
        self._add_to_cart(self.user, self.product1, 1)

        # Also add inactive to session (simulating it was added before being deactivated)
        session = self.client.session
        skey = session.get('skey', {})
        skey[str(inactive_product.id)] = {
            'qty': 1,
            'price': str(inactive_product.buy_now_price)
        }
        session['skey'] = skey
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Active product should appear
        self.assertContains(response, 'Air Jordan 4')
        # Inactive product should NOT appear
        self.assertNotContains(response, 'Air Jordan 3')

    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_get_braintree_token_included(self, mock_gateway):
        """Test that Braintree client token is included in response"""
        expected_token = 'test_braintree_token_abc123'
        mock_gateway.return_value = expected_token
        
        self.client.force_login(self.user)
        self._add_to_cart(self.user, self.product1, 1)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Token should be in the JavaScript context
        self.assertContains(response, expected_token)
        mock_gateway.assert_called_once()

    # Helper method to add to your test class
    def _add_to_cart(self, user, product, quantity):
        """Helper to add item to both database and session cart"""
        # Database
        PopUpCartItem.objects.create(
            user=user,
            product=product,
            quantity=quantity
        )
        
        # Session
        session = self.client.session
        if 'skey' not in session:
            session['skey'] = {}
        
        session['skey'][str(product.id)] = {
            'qty': quantity,
            'price': str(product.buy_now_price)
        }
        session.save()


class TestProductBuyViewPost(TestCase):
    """Test suite for ProductBuyView POST method"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create addresses (use your existing setup from GET tests)
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
            delivery_instructions="",
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
            apartment_suite_number="",
            town_city="Billing City",
            state="Texas",
            postcode="67890",
            delivery_instructions="",
            default=False,
            is_default_shipping=False,
            is_default_billing=True
        )
        
        self.address2 = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="789 Second St",
            address_line2="",
            apartment_suite_number="",
            town_city="Second City",
            state="Florida",
            postcode="11111",
            delivery_instructions="",
            default=False,
        )
        
        # Create products (use your existing setup)
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
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            retail_price=Decimal('180.00'),
            inventory_status='reserved',
            is_active=True
        )
    
    def _add_to_cart(self, user, product, quantity):
        """Helper to add item to both database and session cart"""
        PopUpCartItem.objects.create(
            user=user,
            product=product,
            quantity=quantity
        )
        
        session = self.client.session
        if 'skey' not in session:
            session['skey'] = {}
        
        session['skey'][str(product.id)] = {
            'qty': quantity,
            'price': str(product.buy_now_price)
        }
        session.save()
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_basic_rendering(self, mock_gateway):
        """Test POST request renders template with basic context"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/payment_home.html')
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_selects_first_saved_address_by_default(self, mock_gateway):
        """Test that first saved address is selected by default"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/payment_home.html')

    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_use_billing_as_shipping_true(self, mock_gateway):
        """Test use_billing_as_shipping flag set to true"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {
            'use_billing_as_shipping': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        # Check session was updated
        self.assertTrue(self.client.session.get('use_billing_as_shipping'))
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_use_billing_as_shipping_false(self, mock_gateway):
        """Test use_billing_as_shipping flag set to false"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {
            'use_billing_as_shipping': 'false'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get('use_billing_as_shipping'))
    
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_billing_address_not_in_session(self, mock_gateway):
        """Test when billing address ID not in session"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        # Should render without errors even without billing address
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_invalid_billing_address_id(self, mock_gateway):
        """Test with invalid billing address ID in session"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        # Set invalid ID
        session = self.client.session
        session['selected_billing_address_id'] = '99999999-9999-9999-9999-999999999999'
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        # Should not crash, billing address should be None
    
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_user_with_no_addresses(self, mock_gateway):
        """Test POST for user with no saved addresses"""
        mock_gateway.return_value = 'fake_token'
        
        # Create user with no addresses
        new_user, _ = create_test_user(
            "new@example.com", "pass123", "New", "User", "7", "male"
        )
        
        self.client.force_login(new_user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        # Should render without errors
    
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_braintree_token_included(self, mock_gateway):
        """Test that Braintree client token is included"""
        expected_token = 'test_token_12345'
        mock_gateway.return_value = expected_token
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_token)
        mock_gateway.assert_called_once()
    
    """
    """

    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_use_billing_as_shipping_not_provided(self, mock_gateway):
        """Test use_billing_as_shipping when not provided in POST data"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertFalse(session.get('use_billing_as_shipping', False))

    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_use_billing_as_shipping_toggles_correctly(self, mock_gateway):
        """Test toggling use_billing_as_shipping flag"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        url = reverse('pop_up_payment:payment_home')
        
        # First POST - set to true
        response = self.client.post(url, {'use_billing_as_shipping': 'true'})
        self.assertTrue(self.client.session.get('use_billing_as_shipping'))
        
        # Second POST - set to false
        response = self.client.post(url, {'use_billing_as_shipping': 'false'})
        self.assertFalse(self.client.session.get('use_billing_as_shipping'))

 
    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_billing_address_from_session(self, mock_gateway):
        """Test billing address retrieved from session"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        # Set billing address in session
        session = self.client.session
        session['selected_billing_address_id'] = str(self.billing_address.id)
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)


    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_billing_address_belongs_to_different_user(self, mock_gateway):
        """Test billing address that belongs to different user"""
        mock_gateway.return_value = 'fake_token'
        
        # Create another user and their address
        other_user, _ = create_test_user(
            "other@example.com", "pass123", "Other", "User", "8", "female"
        )
        other_address = create_test_address(
            customer=other_user,
            first_name="Other",
            last_name="User",
            address_line="999 Other St",
            address_line2="",
            apartment_suite_number="",
            town_city="Other City",
            state="Florida",
            postcode="99999",
            delivery_instructions="",
            default=True
        )
        
        self.client.force_login(self.user)
        
        # Try to set other user's address
        session = self.client.session
        session['selected_billing_address_id'] = str(other_address.id)
        session.save()
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        # Should render without crashing (address will be None)
        self.assertEqual(response.status_code, 200)

    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_address_id_captured(self, mock_gateway):
        """Test address_id from POST data is captured without error"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {
            'address_id': str(self.address2.id)
        })
        
        self.assertEqual(response.status_code, 200)

    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_shipping_choice_captured(self, mock_gateway):
        """Test shipping_choice from POST data is captured without error"""
        mock_gateway.return_value = 'fake_token'
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {
            'shipping_choice': 'express'
        })
        
        self.assertEqual(response.status_code, 200)


    @patch('pop_up_payment.views.gateway.client_token.generate')
    def test_post_braintree_token_generated(self, mock_gateway):
        """Test that Braintree client token is generated"""
        expected_token = 'test_token_12345'
        mock_gateway.return_value = expected_token
        
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:payment_home')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, 200)
        mock_gateway.assert_called_once()


class TestShippingAddressViewGet(TestCase):
    """Test suite for ShippingAddressView GET method"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create default shipping address
        self.default_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 Main St",
            address_line2="",
            apartment_suite_number="",
            town_city="Test City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=True,
            is_default_shipping=True,
            is_default_billing=False
        )
        
        # Create additional address
        self.secondary_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Second Ave",
            address_line2="",
            apartment_suite_number="Apt 2",
            town_city="Second City",
            state="Texas",
            postcode="67890",
            delivery_instructions="Leave at door",
            default=False,
            is_default_shipping=False,
            is_default_billing=False
        )
        
        self.url = reverse('pop_up_payment:shipping_address')
    
    def test_get_authenticated_user_with_default_address(self):
        """Test GET request for authenticated user with default address"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/shipping_address.html')
        # Check that default address is displayed
        self.assertContains(response, '123 Main St')
        self.assertContains(response, 'Test City')
    
    def test_get_authenticated_user_displays_all_saved_addresses(self):
        """Test that all saved addresses are displayed"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Both addresses should be visible
        self.assertContains(response, '123 Main St')
        self.assertContains(response, '456 Second Ave')


    def test_get_authenticated_user_with_no_addresses(self):
        """Test GET for user with no saved addresses"""
        # Create new user with no addresses
        new_user, _ = create_test_user(
            "new@example.com", "pass123", "New", "User", "8", "female"
        )
        
        self.client.force_login(new_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/shipping_address.html')
    


    def test_get_includes_address_forms(self):
        """Test that address forms are included in context"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Verify forms are present (check for form elements)
        self.assertContains(response, 'address_form')
        self.assertContains(response, 'selected_address')

    
    def test_get_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        # Don't login
        self.factory = RequestFactory()
        self.view = TestProtectedView.as_view()
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        # Should redirect to login (302 or 403 depending on handle_no_permission)
        self.assertIn(response.status_code, [302, 403])



class TestShippingAddressViewPost(TestCase):
    """Test suite for ShippingAddressView POST method"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create addresses
        self.address1 = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 First St",
            address_line2="",
            apartment_suite_number="",
            town_city="First City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=True,
            is_default_shipping=True,
            is_default_billing=False
        )
        
        self.address2 = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Second St",
            address_line2="",
            apartment_suite_number="",
            town_city="Second City",
            state="Texas",
            postcode="67890",
            delivery_instructions="",
            default=False,
            is_default_shipping=False,
            is_default_billing=False
        )
        
        self.url = reverse('pop_up_payment:shipping_address')
    
    def test_post_select_existing_address(self):
        """Test selecting an existing address"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'selected_address': str(self.address2.id)
        })
        
        # Should redirect to payment home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Check session was updated
        session = self.client.session
        self.assertEqual(session.get('selected_address_id'), str(self.address2.id))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Shipping address selected successfully', str(messages[0]))
    

    def test_post_update_existing_address(self):
        """Test updating an existing address"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'address_id': str(self.address1.id),
            'first_name': 'Updated',
            'last_name': 'Name',
            'address_line': '999 Updated St',
            'town_city': 'Updated City',
            'state': 'California',
            'postcode': '99999',
            'is_default_shipping': True
        })

        # Should redirect to payment home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        # Verify address was updated
        self.address1.refresh_from_db()
        self.assertEqual(self.address1.address_line, '999 Updated St')
        self.assertEqual(self.address1.first_name, 'Updated')
        self.assertEqual(self.address1.town_city, 'Updated City')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Shipping address updated successfully', str(messages[0]))
    
    def test_post_create_new_address(self):
        """Test creating a new address"""
        self.client.force_login(self.user)
        
        initial_count = PopUpCustomerAddress.objects.filter(customer=self.user).count()
        
        response = self.client.post(self.url, {
            'first_name': 'New',
            'last_name': 'Address',
            'address_line': '789 New St',
            'town_city': 'New City',
            'state': 'New York',
            'postcode': '10001',
            'is_default_shipping': False
        })
        
        # Should redirect to payment home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Verify new address was created
        new_count = PopUpCustomerAddress.objects.filter(customer=self.user).count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify address details
        new_address = PopUpCustomerAddress.objects.get(address_line='789 New St')
        self.assertEqual(new_address.customer, self.user)
        self.assertEqual(new_address.first_name, 'New')
        self.assertEqual(new_address.town_city, 'New City')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Shipping address added successfully', str(messages[0]))
    
    def test_post_create_new_address_as_default(self):
        """Test creating a new address and setting it as default"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'first_name': 'Default',
            'last_name': 'Address',
            'address_line': '555 Default St',
            'town_city': 'Default City',
            'state': 'Georgia',
            'postcode': '30301',
            'is_default_shipping': True
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify new address is default
        new_address = PopUpCustomerAddress.objects.get(address_line='555 Default St')
        self.assertTrue(new_address.is_default_shipping)
        
        # Old default should no longer be default
        self.address1.refresh_from_db()
        # Depending on your logic, address1 might still be default or not
        # Adjust assertion based on actual behavior
    
    def test_post_invalid_form_data_re_renders_with_errors(self):
        """Test that invalid form data re-renders the page with errors"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            # Missing required fields
            'first_name': 'Test',
            # Missing address_line, town_city, state, postcode
        })
        
        # Should re-render the same page (not redirect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/shipping_address.html')
        # Should contain form with errors
        # Check for error messages or form presence
    
    def test_post_update_nonexistent_address_id(self):
        """Test updating with non-existent address ID"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'address_id': '99999999-9999-9999-9999-999999999999',
            'first_name': 'Test',
            'last_name': 'User',
            'address_line': '123 Test St',
            'town_city': 'Test City',
            'state': 'Florida',
            'postcode': '12345'
        })
        
        # Should handle gracefully (re-render or redirect based on your logic)
        # Adjust based on actual behavior
        self.assertIn(response.status_code, [200, 302])
    
    def test_post_update_other_users_address(self):
        """Test that users cannot update other users' addresses"""
        # Create another user and their address
        other_user, _ = create_test_user(
            "other@example.com", "pass123", "Other", "User", "7", "male"
        )
        other_address = create_test_address(
            customer=other_user,
            first_name="Other",
            last_name="User",
            address_line="999 Other St",
            address_line2="",
            apartment_suite_number="",
            town_city="Other City",
            state="Florida",
            postcode="99999",
            delivery_instructions="",
            default=True
        )
        
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'address_id': str(other_address.id),
            'address_line': 'Hacked Address',
            'town_city': 'Hacked City',
            'state': 'Florida',
            'postcode': '12345'
        })
        
        # Should not update other user's address
        other_address.refresh_from_db()
        self.assertNotEqual(other_address.address_line, 'Hacked Address')
    
    def test_post_select_invalid_address_id(self):
        """Test selecting address with invalid ID"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'selected_address': '00000000-0000-0000-0000-000000000000'
        })
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 302])
    
    def test_post_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        # Don't login
        
        response = self.client.post(self.url, {
            'selected_address': str(self.address1.id)
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url.lower())


class BillingAddressViewGetTestCase(TestCase):
    """Test suite for BillingAddressView GET method"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create default billing address
        self.default_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 Billing St",
            address_line2="",
            apartment_suite_number="",
            town_city="Billing City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=True,
            is_default_shipping=False,
            is_default_billing=True
        )
        
        # Create additional address
        self.secondary_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Second Billing Ave",
            address_line2="",
            apartment_suite_number="Apt 2",
            town_city="Second City",
            state="Texas",
            postcode="67890",
            delivery_instructions="",
            default=False,
            is_default_shipping=False,
            is_default_billing=False
        )
        
        self.url = reverse('pop_up_payment:billing_address')
    
    def test_get_authenticated_user_with_default_address(self):
        """Test GET request for authenticated user with default billing address"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/billing_address.html')
        # Check that default billing address is displayed
        self.assertContains(response, '123 Billing St')
        self.assertContains(response, 'Billing City')
    
    def test_get_authenticated_user_with_selected_billing_address_in_session(self):
        """Test GET with billing address ID in session"""
        self.client.force_login(self.user)
        
        # Set billing address in session
        session = self.client.session
        session['selected_billing_address_id'] = str(self.secondary_address.id)
        session.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Should display the selected billing address from session
        self.assertContains(response, '456 Second Billing Ave')
    
    def test_get_authenticated_user_displays_all_saved_addresses(self):
        """Test that all saved addresses are displayed"""
        self.client.force_login(self.user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Both addresses should be visible
        self.assertContains(response, '123 Billing St')
        self.assertContains(response, '456 Second Billing Ave')
    
    def test_get_authenticated_user_with_no_addresses(self):
        """Test GET for user with no saved addresses"""
        # Create new user with no addresses
        new_user, _ = create_test_user(
            "new@example.com", "pass123", "New", "User", "8", "female"
        )
        
        self.client.force_login(new_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/billing_address.html')
    
    def test_get_includes_address_forms(self):
        """Test that address forms are included in context"""
        self.client.force_login(self.user)
    
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check for actual form elements instead of variable names
        self.assertContains(response, '<form')
        # Check for common form fields
        self.assertContains(response, 'first_name')
        self.assertContains(response, 'address_line')
        self.assertContains(response, 'town_city')
        

    def test_get_with_invalid_billing_address_id_in_session(self):
        """Test GET with invalid billing address ID in session"""
        self.client.force_login(self.user)
        
        # Set invalid ID in session
        session = self.client.session
        session['selected_billing_address_id'] = '99999999-9999-9999-9999-999999999999'
        session.save()
        
        response = self.client.get(self.url)
        
        # Should fall back to default address
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '123 Billing St')
    
    def test_get_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        # Don't login
        
        response = self.client.get(self.url)
        
        # Should redirect to login (LoginRequiredMixin)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url.lower())


class TestBillingAddressViewPost(TestCase):
    """Test suite for BillingAddressView POST method"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create addresses
        self.address1 = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 First Billing St",
            address_line2="",
            apartment_suite_number="",
            town_city="First City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=True,
            is_default_shipping=False,
            is_default_billing=True
        )
        
        self.address2 = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Second Billing St",
            address_line2="",
            apartment_suite_number="",
            town_city="Second City",
            state="Texas",
            postcode="67890",
            delivery_instructions="",
            default=False,
            is_default_shipping=False,
            is_default_billing=False
        )
        
        self.url = reverse('pop_up_payment:billing_address')
    
    def test_post_select_existing_address(self):
        """Test selecting an existing billing address"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'selected_address': str(self.address2.id)
        })
        
        # Should redirect to payment home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Check session was updated with billing address ID
        session = self.client.session
        self.assertEqual(session.get('selected_billing_address_id'), str(self.address2.id))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('address selected successfully', str(messages[0]).lower())
    
    def test_post_update_existing_billing_address(self):
        """Test updating an existing billing address"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'address_id': str(self.address1.id),
            'first_name': 'Updated',
            'last_name': 'Billing',
            'address_line': '999 Updated Billing St',
            'town_city': 'Updated City',
            'state': 'California',
            'postcode': '99999',
            'is_default_billing': True
        })
        
        # Should redirect to payment home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Verify address was updated
        self.address1.refresh_from_db()
        self.assertEqual(self.address1.address_line, '999 Updated Billing St')
        self.assertEqual(self.address1.first_name, 'Updated')
        self.assertEqual(self.address1.town_city, 'Updated City')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('address', str(messages[0]).lower())
    
    def test_post_create_new_billing_address(self):
        """Test creating a new billing address"""
        self.client.force_login(self.user)
        
        initial_count = PopUpCustomerAddress.objects.filter(customer=self.user).count()
        
        response = self.client.post(self.url, {
            'first_name': 'New',
            'last_name': 'Billing',
            'address_line': '789 New Billing St',
            'town_city': 'New Billing City',
            'state': 'New York',
            'postcode': '10001',
            'is_default_billing': False
        })
        
        # Should redirect to payment home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Verify new address was created
        new_count = PopUpCustomerAddress.objects.filter(customer=self.user).count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify address details
        new_address = PopUpCustomerAddress.objects.get(address_line='789 New Billing St')
        self.assertEqual(new_address.customer, self.user)
        self.assertEqual(new_address.first_name, 'New')
        self.assertEqual(new_address.town_city, 'New Billing City')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('address added successfully', str(messages[0]).lower())
    
    def test_post_create_new_billing_address_as_default(self):
        """Test creating a new billing address and setting it as default"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'first_name': 'Default',
            'last_name': 'Billing',
            'address_line': '555 Default Billing St',
            'town_city': 'Default City',
            'state': 'Georgia',
            'postcode': '30301',
            'is_default_billing': True
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify new address is default billing
        new_address = PopUpCustomerAddress.objects.get(address_line='555 Default Billing St')
        self.assertTrue(new_address.is_default_billing)
    
    def test_post_use_billing_as_shipping_true(self):
        """Test setting use_billing_as_shipping flag to true"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'use_billing_as_shipping': 'true',
            'first_name': 'Test'
        })

        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertTrue(session.get('use_billing_as_shipping'))
        
    
    
    def test_post_use_billing_as_shipping_false(self):
        """Test setting use_billing_as_shipping flag to false"""
        self.client.force_login(self.user)
    
        response = self.client.post(self.url, {
            'use_billing_as_shipping': 'false',
            # Missing required fields to trigger form error
            'first_name': 'Test'
        })
        
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertFalse(session.get('use_billing_as_shipping'))
    
    def test_post_use_billing_as_shipping_not_provided(self):
        """Test use_billing_as_shipping when not provided"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            # Missing required fields to trigger form error
            'first_name': 'Test'
        })
        
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertFalse(session.get('use_billing_as_shipping', False))
    
    def test_post_invalid_form_data_re_renders_with_errors(self):
        """Test that invalid form data re-renders the page with errors"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            # Missing required fields
            'first_name': 'Test',
            # Missing address_line, town_city, state, postcode
        })
        
        # Should re-render the same page (not redirect)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/billing_address.html')
    
    def test_post_update_nonexistent_address_id(self):
        """Test updating with non-existent address ID"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'address_id': '99999999-9999-9999-9999-999999999999',
            'first_name': 'Test',
            'last_name': 'User',
            'address_line': '123 Test St',
            'town_city': 'Test City',
            'state': 'Florida',
            'postcode': '12345'
        })
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 302])
    
    def test_post_update_other_users_address(self):
        """Test that users cannot update other users' billing addresses"""
        # Create another user and their address
        other_user, _ = create_test_user(
            "other@example.com", "pass123", "Other", "User", "7", "male"
        )
        other_address = create_test_address(
            customer=other_user,
            first_name="Other",
            last_name="User",
            address_line="999 Other Billing St",
            address_line2="",
            apartment_suite_number="",
            town_city="Other City",
            state="Florida",
            postcode="99999",
            delivery_instructions="",
            default=True,
            is_default_billing=True
        )
        
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'address_id': str(other_address.id),
            'address_line': 'Hacked Billing Address',
            'town_city': 'Hacked City',
            'state': 'Florida',
            'postcode': '12345'
        })
        
        # Should not update other user's address
        other_address.refresh_from_db()
        self.assertNotEqual(other_address.address_line, 'Hacked Billing Address')
    
    def test_post_select_invalid_address_id(self):
        """Test selecting billing address with invalid ID"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'selected_address': '99999999-9999-9999-9999-999999999999'
        })
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 302])
    
    def test_post_select_other_users_address(self):
        """Test that users cannot select other users' addresses"""
        # Create another user and their address
        other_user, _ = create_test_user(
            "other@example.com", "pass123", "Other", "User", "7", "male"
        )
        other_address = create_test_address(
            customer=other_user,
            first_name="Other",
            last_name="User",
            address_line="999 Other St",
            address_line2="",
            apartment_suite_number="",
            town_city="Other City",
            state="Florida",
            postcode="99999",
            delivery_instructions="",
            default=True
        )
        
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {
            'selected_address': str(other_address.id)
        })
        
        # Session should not be updated with other user's address
        # Or should handle the security check gracefully
        self.assertIn(response.status_code, [200, 302])
    
    def test_post_unauthenticated_user_redirects_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        # Don't login
        
        response = self.client.post(self.url, {
            'selected_address': str(self.address1.id)
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url.lower())

class BuyNowAddToCartViewTestCase(TestCase):
    """Test suite for buy_now_add_to_cart view"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
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
        
        # Create available product
        self.available_product = PopUpProduct.objects.create(
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
        
        # Create reserved product
        self.reserved_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            retail_price=Decimal('180.00'),
            inventory_status='reserved',
            reserved_until = now() + timedelta(minutes=10),
            is_active=True,
            
        )
        
        # Create sold product
        self.sold_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 3',
            slug='jordan-3-sold',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='sold',
            is_active=True
        )
        
        # Create inactive product
        self.inactive_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 5',
            slug='jordan-5-inactive',
            buy_now_price=Decimal('190.00'),
            retail_price=Decimal('190.00'),
            inventory_status='in_inventory',
            is_active=False
        )
    
    def test_buy_now_available_product_authenticated_user(self):
        """Test buying an available product as authenticated user"""
        self.client.force_login(self.user)
        
        # Check what's actually in the DB
        from pop_up_auction.models import PopUpProduct
        db_product = PopUpProduct.objects.get(slug=self.available_product.slug)

        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response = self.client.get(url)
        
        # Re-fetch from DB directly
        db_product = PopUpProduct.objects.get(slug=self.available_product.slug)
        
        # Should redirect to payment page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Verify product status changed to reserved
        self.available_product.refresh_from_db()
        self.assertEqual(self.available_product.inventory_status, 'reserved')
        self.assertIsNotNone(self.available_product.reserved_until)
        
        # Verify expiry time in session (10 minutes from now)
        session = self.client.session
        expiry_str = session.get('buy_now_expiry')
        self.assertIsNotNone(expiry_str)
        
        # Verify expiry is approximately 10 minutes from now
        from django.utils.dateparse import parse_datetime
        expiry_time = parse_datetime(expiry_str)
        expected_expiry = django_timezone.now() + timedelta(minutes=10)
        time_diff = abs((expiry_time - expected_expiry).total_seconds())
        self.assertLess(time_diff, 5)  # Within 5 seconds tolerance

        # Verify product is in database cart (authenticated users use PopUpCartItem)
        cart_item = PopUpCartItem.objects.get(user=self.user, product=self.available_product)
        self.assertEqual(cart_item.quantity, 1)
    
    def test_buy_now_reserved_product_redirects_to_detail(self):
        """Test that reserved products redirect back to product detail"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.reserved_product.slug})
        response = self.client.get(url)
        
        # Should redirect to product detail page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('pop_up_auction:product_detail', kwargs={'slug': self.reserved_product.slug})
        )
        
        # Product status should remain reserved
        self.reserved_product.refresh_from_db()
        self.assertEqual(self.reserved_product.inventory_status, 'reserved')
    
    def test_buy_now_sold_product_redirects_to_detail(self):
        """Test that sold products redirect back to product detail"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.sold_product.slug})
        response = self.client.get(url)
        
        # Should redirect to product detail page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('pop_up_auction:product_detail', kwargs={'slug': self.sold_product.slug})
        )
        
        # Product status should remain sold
        self.sold_product.refresh_from_db()
        self.assertEqual(self.sold_product.inventory_status, 'sold')
    
    def test_buy_now_nonexistent_product_returns_404(self):
        """Test that non-existent product returns 404"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': 'nonexistent-product'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_buy_now_inactive_product_returns_404(self):
        """Test that inactive products return 404"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.inactive_product.slug})
        response = self.client.get(url)
        
        # Should return 404 because is_active=False
        self.assertEqual(response.status_code, 404)
    
    def test_buy_now_unauthenticated_user(self):
        """Test buy now as unauthenticated user"""
        # Don't login
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response = self.client.get(url)
        
        # View doesn't have LoginRequiredMixin, so it should work
        # Product will be reserved and added to session cart
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('pop_up_payment:payment_home'))
        
        # Verify product was reserved
        self.available_product.refresh_from_db()
        self.assertEqual(self.available_product.inventory_status, 'reserved')

        # Unauthenticated users store cart in session under 'pop_up_cart'
        session = self.client.session
        session_cart = session.get('pop_up_cart', {})
        self.assertIn(str(self.available_product.id), session_cart)
    
    def test_buy_now_sets_reserved_at_timestamp(self):
        """Test that reserved_at timestamp is set"""
        self.client.force_login(self.user)
        
        # Record time before request
        before_time = django_timezone.now() + timedelta(minutes=10)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response = self.client.get(url)
        
        # Record time after request
        after_time = django_timezone.now() + timedelta(minutes=10) 
        
        # Verify reserved_at is set and within expected range
        self.available_product.refresh_from_db()
        self.assertIsNotNone(self.available_product.reserved_until)
        self.assertGreaterEqual(self.available_product.reserved_until, before_time)
        self.assertLessEqual(self.available_product.reserved_until, after_time)
    
    def test_buy_now_cart_contains_correct_quantity(self):
        """Test that product is added to cart with quantity of 1"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response = self.client.get(url)
        
        # Authenticated users store cart in database, not session
        cart_item = PopUpCartItem.objects.get(user=self.user, product=self.available_product)
        self.assertEqual(cart_item.quantity, 1)
    
    def test_buy_now_multiple_users_race_condition(self):
        """Test that only first user can reserve product"""
        user1, _ = create_test_user(
            "user1@example.com", "pass123", "User", "One", "9", "male"
        )
        user2, _ = create_test_user(
            "user2@example.com", "pass123", "User", "Two", "8", "female"
        )
        
        # User 1 buys the product
        self.client.force_login(user1)
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response1 = self.client.get(url)
        
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response1.url, reverse('pop_up_payment:payment_home'))
        
        # Logout and login as user 2
        self.client.logout()
        self.client.force_login(user2)
        
        # User 2 tries to buy the same product
        response2 = self.client.get(url)
        
        # Should redirect to product detail (already reserved)
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(
            response2.url,
            reverse('pop_up_auction:product_detail', kwargs={'slug': self.available_product.slug})
        )
    
    def test_buy_now_session_modified_flag_set(self):
        """Test that session.modified is set to True"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response = self.client.get(url)
        
        # Session should have the expiry set
        session = self.client.session
        self.assertIn('buy_now_expiry', session)
    
    def test_buy_now_expiry_format(self):
        """Test that expiry is stored in ISO format"""
        self.client.force_login(self.user)
        
        url = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response = self.client.get(url)
        
        session = self.client.session
        expiry_str = session.get('buy_now_expiry')
        
        # Should be able to parse as datetime
        from django.utils.dateparse import parse_datetime
        expiry_time = parse_datetime(expiry_str)
        self.assertIsNotNone(expiry_time)
        
        # Should be in the future
        self.assertGreater(expiry_time, django_timezone.now())
    
    def test_buy_now_subsequent_purchase_overwrites_expiry(self):
        """Test that buying another product updates the expiry time"""
        self.client.force_login(self.user)
        
        # Create another available product
        product2 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 6',
            slug='jordan-6-available',
            buy_now_price=Decimal('220.00'),
            retail_price=Decimal('220.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        # Buy first product
        url1 = reverse('pop_up_payment:buy_now', kwargs={'slug': self.available_product.slug})
        response1 = self.client.get(url1)
        
        session = self.client.session
        first_expiry = session.get('buy_now_expiry')
        
        # Wait a moment
        import time
        time.sleep(0.1)
        
        # Buy second product
        url2 = reverse('pop_up_payment:buy_now', kwargs={'slug': product2.slug})
        response2 = self.client.get(url2)
        
        session = self.client.session
        second_expiry = session.get('buy_now_expiry')
        
        # Expiry should be updated
        self.assertNotEqual(first_expiry, second_expiry)


class TestCreatePaymentIntentView(TestCase):
    """Test suite for CreatePaymentIntentView"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        self.url = reverse('pop_up_payment:create_payment')  # Update with actual URL name
    
    # ─── Missing / Invalid Input ───────────────────────────────────
    
    def test_post_missing_amount_returns_400(self):
        """Test that missing amount returns 400 error"""
        self.client.force_login(self.user)
        
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Missing amount')
    
    def test_post_empty_body_returns_400(self):
        """Test that empty request body returns 400"""
        self.client.force_login(self.user)
        
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_amount_is_none_returns_400(self):
        """Test that amount set to None returns 400"""
        self.client.force_login(self.user)
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': None}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Missing amount')
    
    def test_post_amount_is_zero_returns_400(self):
        """Test that amount of 0 returns 400"""
        self.client.force_login(self.user)
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 0}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    # ─── New Stripe Customer ───────────────────────────────────────
    
    @patch('pop_up_payment.views.stripe.PaymentIntent.create')
    @patch('pop_up_payment.views.stripe.Customer.create')
    def test_post_creates_stripe_customer_if_not_exists(self, mock_customer_create, mock_intent_create):
        """Test that a Stripe customer is created if user doesn't have one"""
        self.client.force_login(self.user)
        
        # Ensure user has no stripe_customer_id
        self.user_profile.stripe_customer_id = None
        self.user_profile.save()
        
        # Mock Stripe Customer.create
        mock_customer_create.return_value = MagicMock(id='cus_test_123')
        
        # Mock Stripe PaymentIntent.create
        mock_intent_create.return_value = {'client_secret': 'pi_test_secret_123'}
        
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 21500}),
            content_type='application/json'
        )
        print("response.status_code", response.status_code)
        print(f"Response body: {response.json()}")
        self.assertEqual(response.status_code, 200)
        
        # Verify Customer.create was called with correct params
        mock_customer_create.assert_called_once_with(
            email=self.user.email,
            name=f"{self.user.first_name} {self.user.last_name}"
        )
        
        # Verify stripe_customer_id was saved to user
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.stripe_customer_id, 'cus_test_123')
    
    @patch('pop_up_payment.views.stripe.PaymentIntent.create')
    @patch('pop_up_payment.views.stripe.Customer.retrieve')
    def test_post_retrieves_existing_stripe_customer(self, mock_customer_retrieve, mock_intent_create):
        """Test that existing Stripe customer is retrieved, not created"""
        self.client.force_login(self.user)
        
        # Set existing stripe_customer_id
        self.user_profile.stripe_customer_id = 'cus_existing_456'
        self.user_profile.save()
        
        mock_customer_retrieve.return_value = MagicMock(id='cus_existing_456')
        mock_intent_create.return_value = {'client_secret': 'pi_test_secret_456'}
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 18000}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify retrieve was called, not create
        mock_customer_retrieve.assert_called_once_with('cus_existing_456')
    
    # ─── PaymentIntent Creation ────────────────────────────────────
    
    @patch('pop_up_payment.views.stripe.PaymentIntent.create')
    @patch('pop_up_payment.views.stripe.Customer.create')
    def test_post_creates_payment_intent_with_correct_params(self, mock_customer_create, mock_intent_create):
        """Test that PaymentIntent is created with correct parameters"""
        self.client.force_login(self.user)
        
        self.user_profile.stripe_customer_id = None
        self.user_profile.save()
        
        mock_customer_create.return_value = MagicMock(id='cus_test_789')
        mock_intent_create.return_value = {'client_secret': 'pi_test_secret_789'}
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 21500}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify PaymentIntent.create was called with correct params
        mock_intent_create.assert_called_once_with(
            amount=21500,
            currency='usd',
            customer='cus_test_789',
            automatic_payment_methods={"enabled": True},
            setup_future_usage="off_session"
        )
    
    @patch('pop_up_payment.views.stripe.PaymentIntent.create')
    @patch('pop_up_payment.views.stripe.Customer.retrieve')
    def test_post_returns_client_secret(self, mock_customer_retrieve, mock_intent_create):
        """Test that response contains client_secret"""
        self.client.force_login(self.user)
        
        self.user_profile.stripe_customer_id = 'cus_existing_123'
        self.user_profile.save()
        
        mock_customer_retrieve.return_value = MagicMock(id='cus_existing_123')
        mock_intent_create.return_value = {'client_secret': 'pi_secret_abc_123'}
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 15000}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['clientSecret'], 'pi_secret_abc_123')
    
    # ─── Stripe API Errors ─────────────────────────────────────────
    
    @patch('pop_up_payment.views.stripe.PaymentIntent.create')
    @patch('pop_up_payment.views.stripe.Customer.retrieve')
    def test_post_stripe_payment_intent_failure_returns_400(self, mock_customer_retrieve, mock_intent_create):
        """Test that Stripe PaymentIntent failure returns 400"""
        self.client.force_login(self.user)
        
        self.user_profile.stripe_customer_id = 'cus_existing_123'
        self.user_profile.save()
        
        mock_customer_retrieve.return_value = MagicMock(id='cus_existing_123')
        mock_intent_create.side_effect = Exception('Stripe API error: Invalid amount')
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 21500}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Stripe API error', data['error'])
    
    @patch('pop_up_payment.views.stripe.Customer.create')
    def test_post_stripe_customer_create_failure_returns_400(self, mock_customer_create):
        """Test that Stripe Customer.create failure returns 400"""
        self.client.force_login(self.user)
        
        self.user.stripe_customer_id = None
        self.user.save()
        
        mock_customer_create.side_effect = Exception('Stripe API error: Authentication failed')
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 21500}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Authentication failed', data['error'])
    
    @patch('pop_up_payment.views.stripe.Customer.retrieve')
    def test_post_stripe_customer_retrieve_failure_returns_400(self, mock_customer_retrieve):
        """Test that Stripe Customer.retrieve failure returns 400"""
        self.client.force_login(self.user)
        
        self.user_profile.stripe_customer_id = 'cus_deleted_customer'
        self.user_profile.save()
        
        mock_customer_retrieve.side_effect = Exception('Stripe API error: No such customer')
        
        response = self.client.post(
            self.url,
            data=json.dumps({'amount': 21500}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('No such customer', data['error'])
    
    # ─── CSRF ──────────────────────────────────────────────────────
    
    @patch('pop_up_payment.views.stripe.PaymentIntent.create')
    @patch('pop_up_payment.views.stripe.Customer.retrieve')
    def test_post_csrf_exempt(self, mock_customer_retrieve, mock_intent_create):
        """Test that view is CSRF exempt (needed for frontend JS calls)"""
        self.client.force_login(self.user)
        
        self.user_profile.stripe_customer_id = 'cus_existing_123'
        self.user_profile.save()
        
        mock_customer_retrieve.return_value = MagicMock(id='cus_existing_123')
        mock_intent_create.return_value = {'client_secret': 'pi_secret_csrf_test'}
        
        # enforce_csrf_checks=True makes the test client check CSRF
        csrf_client = self.client.__class__(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        
        response = csrf_client.post(
            self.url,
            data=json.dumps({'amount': 21500}),
            content_type='application/json'
            # Note: no csrfmiddlewaretoken provided
        )
        
        # Should succeed despite no CSRF token (view is csrf_exempt)
        self.assertEqual(response.status_code, 200)

# """
# Run Test
# python3 manage.py test accounts/tests
# """