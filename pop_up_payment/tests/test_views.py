from pop_up_payment.views import ShippingAddressView, BillingAddressView
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from accounts.models import PopUpCustomer, PopUpCustomerAddress


def create_test_user(email, password, first_name, last_name, shoe_size, size_gender):
    return PopUpCustomer.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            shoe_size=shoe_size,
            size_gender=size_gender
        )

def create_test_user_two():
    return PopUpCustomer.objects.create_user(
            email="testuse2r@example.com",
            password="securePassword!232",
            first_name="Test2",
            last_name="User2",
            shoe_size="11",
            size_gender="male"
        )


class AddressViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male")
        self.shipping_url = reverse("payment:shipping_address")
        self.billing_url = reverse("payment:billing_address")
        self.client.login(email="testuser@example.com", password="securePassword!23")
        self.client.get('/', REMOTE_ADDR='127.0.0.1') # Trigger login with IP

        self.existing_address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line='123 Test St',
            town_city='Testville',
            state='FL',
            postcode='12345',
            default=True
        )


    def test_shipping_get_view_renders(self):
        response = self.client.get(self.shipping_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/shipping_address.html')
        self.assertIn('saved_addresses', response.context)

    
    def test_billing_get_view_renders(self):
        response = self.client.get(self.billing_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/billing_address.html')
        self.assertIn('saved_addresses', response.context)
    
    @patch('payment.views.handle_selected_address')
    def test_shipping_selects_existing_address(self, mock_select):
        response = self.client.post(self.shipping_url, {'selected_address': self.existing_address.id})
        mock_select.assert_called_once()
        self.assertRedirects(response, reverse('payment:payment_home'))
    
    @patch('payment.views.handle_selected_address')
    def test_billing_selects_existing_address(self, mock_select):
        response = self.client.post(self.billing_url, {'selected_address': self.existing_address.id})
        mock_select.assert_called_once()
        self.assertRedirects(response, reverse('payment:payment_home'))
    
    @patch('payment.views.handle_update_address')
    def test_shipping_updates_address(self, mock_update):
        mock_update.return_value = (self.existing_address, None)
        response = self.client.post(self.shipping_url, {'address_id': self.existing_address.id})
        self.assertRedirects(response, reverse('payment:payment_home'))
        mock_update.assert_called_once()
    
    @patch('payment.views.handle_update_address')
    def test_billing_updates_addres(self, mock_update):
        mock_update.return_value = (self.existing_address, None)
        response = self.client.post(self.billing_url, {'address_id': self.existing_address.id})
        self.assertRedirects(response, reverse('payment:payment_home'))
        mock_update.assert_called_once()

    @patch('payment.views.handle_new_address')
    def test_shipping_adds_new_address(self, mock_new):
        mock_new.return_value = (self.existing_address, None)
        response = self.client.post(self.shipping_url, {})
        self.assertRedirects(response, reverse('payment:payment_home'))
        mock_new.assert_called_once()
    
    @patch('payment.views.handle_new_address')
    def test_billing_adds_new_address(self, mock_new):
        mock_new.return_value = (self.existing_address, None)
        response = self.client.post(self.billing_url, {})
        self.assertRedirects(response, reverse('payment:payment_home'))
        mock_new.assert_called_once()
    
    @patch('payment.views.handle_new_address')
    def test_billing_sets_use_billing_as_shipping_flag(self, mock_new):
        mock_new.return_value = (None, None)
        response = self.client.post(self.billing_url, {'use_billing_as_shipping': 'true'})
        self.assertEqual(self.client.session['use_billing_as_shipping'], True)
        self.assertEqual(response.status_code, 200)





# """
# Run Test
# python3 manage.py test accounts/tests
# """