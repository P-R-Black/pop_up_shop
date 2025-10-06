from django.test import TestCase, Client, override_settings
from django.urls import reverse
from pop_up_order.utils.utils import user_orders
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress, PopUpBid
from pop_up_payment.utils.tax_utils import get_state_tax_rate
from pop_up_auction.models import (PopUpProduct,PopUpBrand, PopUpCategory, PopUpProductType, PopUpProductSpecification,
                                   PopUpProductSpecificationValue)
from pop_accounts.views import PersonalInfoView
from unittest.mock import patch
from django.utils import timezone
from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from uuid import uuid4
from django.middleware.csrf import CsrfViewMiddleware
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_protect
from django.test import RequestFactory
from django.http import JsonResponse
import json
from django.core import mail
from pop_accounts.utils.utils import validate_password_strength
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from pop_up_cart.cart import Cart
from decimal import Decimal, ROUND_HALF_UP
from django.http import HttpRequest
from django.utils.text import slugify
from .conftest import create_seed_data
from django.contrib.messages import get_messages
from unittest.mock import patch, MagicMock
from pop_up_auction.utils.utils import get_customer_bid_history_context  # Adjust import path
from pop_accounts.pop_accounts_copy.user_copy.user_copy import USER_PAST_BIDS_COPY  # Adjust import p


def create_test_user(email, password, first_name, last_name, shoe_size, size_gender, **kwargs):
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
            size_gender="male",
        )

def create_test_address(customer, first_name, last_name, address_line, address_line2, apartment_suite_number, 
                        town_city, state, postcode, delivery_instructions, default=True, is_default_shipping=False,
                        is_default_billing=False):
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

def create_brand(name):
    return PopUpBrand.objects.create(
        name=name,
        slug=slugify(name)
    )

def create_category(name, is_active):
    return PopUpCategory.objects.create(
            name=name,
            slug=slugify(name),
            is_active=is_active
        )


def create_product_type(name, is_active):
    return PopUpProductType.objects.create(
            name=name,
            slug=slugify(name),
            is_active=is_active
        )

def create_test_product(product_type, category, product_title, secondary_product_title, description, slug, 
                        buy_now_price, current_highest_bid, retail_price, brand, auction_start_date, 
                        auction_end_date, inventory_status, bid_count, reserve_price, is_active, *args, **kwargs
                        ):
        
        return PopUpProduct.objects.create(
            product_type=product_type,
            category=category,
            product_title=product_title,
            secondary_product_title= secondary_product_title,
            description=description,
            slug=slug, 
            buy_now_price=buy_now_price, 
            current_highest_bid=current_highest_bid, 
            retail_price=retail_price, 
            brand=brand, 
            auction_start_date=auction_start_date, 
            auction_end_date=auction_end_date, 
            inventory_status=inventory_status, 
            bid_count=bid_count, 
            reserve_price=reserve_price, 
            is_active=is_active
        )


def create_test_order(user, full_name, email, address1, postal_code, city, state, phone, total_paid, order_key):
    return PopUpCustomerOrder.objects.create(
        user=user, full_name=full_name, email=email, address1=address1, 
        postal_code=postal_code, city=city, state=state, phone=phone, 
        total_paid=total_paid, order_key=order_key
    )

class TestPopUpUserDashboardView(TestCase):
    def setUp(self):
        # create an existing user
        self.existing_email = 'existing@example.com'
        self.user = PopUpCustomer.objects.create_user(
            email = self.existing_email,
            password = 'testPass!23',
            first_name = 'Test',
            last_name = 'User'
        )

        self.url = reverse('pop_accounts:dashboard')


    def test_dashboard_view_authenicated_user(self):
        # Log the user in
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pop_accounts/user_accounts/dashboard_pages/dashboard.html")

        html = response.content.decode('utf-8')
        self.assertIn('<title>Dashboard</title>', html)

        self.assertIn('<h2>Dashboard</h2>', html)


    def test_dashboard_redirects_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)



class TestUserInterestedInView(TestCase):
    def setUp(self):
        # create an existing user
        self.existing_email = 'existing@example.com'

        # create an existing user
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')

        self.url = reverse('pop_accounts:interested_in')
    
    def test_interested_in_view_authenicated_user(self):
        # Log the user in
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pop_accounts/user_accounts/dashboard_pages/interested_in.html")

        html = response.content.decode('utf-8')
        self.assertIn('<title>Interested In</title>', html)

        self.assertIn('<h2>Interested In</h2>', html)


    def test_interested_in_redirects_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class TestMarkProductInterestedView(TestCase):
    def setUp(self):
        
        # create an existing user
        self.existing_email = 'existing@example.com'

        # create an existing user
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')

        self.url = reverse('pop_accounts:mark_interested')

        self.product, _, _, self.user1, _ = create_seed_data()

    def test_add_product_to_interested(self):
       
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse('pop_accounts:mark_interested'),
            data=json.dumps({'product_id': str(self.product.id), 'action': 'add'}),
            content_type = 'application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status':'added', 'message': 'Product added to interested list.'})


    def test_remove_product_from_interested(self):
        self.client.force_login(self.user1)

        # First add product manually
        self.user1.prods_interested_in.add(self.product)

        response = self.client.post(
            reverse('pop_accounts:mark_interested'),
            data=json.dumps({'product_id': str(self.product.id), 'action': 'remove'}),
            content_type='application/json'
        )
      
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'removed', 'message': 'Product removed from interested list.'})
        self.assertNotIn(self.product, self.user.prods_interested_in.all())


    def test_missing_product_id(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('pop_accounts:mark_interested'),
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Product ID missing'})


    def test_product_does_not_exist(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('pop_accounts:mark_interested'),
            data=json.dumps({'product_id': 99999999}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Product not found'})


class TestUserOnNoticeView(TestCase):
    def setUp(self):
        # create an existing user
        self.existing_email = 'existing@example.com'

        # create an existing user
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')

        self.url = reverse('pop_accounts:on_notice')
    
    def test_on_notice_view_authenicated_user(self):
        # Log the user in
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pop_accounts/user_accounts/dashboard_pages/on_notice.html")

        html = response.content.decode('utf-8')
        self.assertIn('<title>On Notice</title>', html)

        self.assertIn('<h2>On Notice</h2>', html)


    def test_on_notice_redirects_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class TestMarkProductOnNoticeView(TestCase):
    def setUp(self):
        
        # create an existing user
        self.existing_email = 'existing@example.com'

        # create an existing user
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')

        self.url = reverse('pop_accounts:mark_on_notice')

        self.product, _, _, self.user1, _ = create_seed_data()


    def test_add_product_to_interested(self):
       
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse('pop_accounts:mark_on_notice'),
            data=json.dumps({'product_id': str(self.product.id), 'action': 'add'}),
            content_type = 'application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'added', 'message': 'Product added to notify me list.'})
    

    def test_remove_product_from_interested(self):
        self.client.force_login(self.user1)

        # First add product manually
        self.user1.prods_on_notice_for.add(self.product)

        response = self.client.post(
            reverse('pop_accounts:mark_on_notice'),
            data=json.dumps({'product_id': str(self.product.id), 'action': 'remove'}),
            content_type='application/json'
        )
      
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'removed', 'message': 'Product removed from notify me list.'})
        self.assertNotIn(self.product, self.user.prods_on_notice_for.all())


    def test_missing_product_id(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('pop_accounts:mark_on_notice'),
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Product ID missing'})


    def test_product_does_not_exist(self):
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('pop_accounts:mark_on_notice'),
            data=json.dumps({'product_id': 99999999}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Product not found'})



class TestPersonalInfoView(TestCase):
    def setUp(self):
        # create an existing user
        self.existing_email = 'existing@example.com'

        # create an existing user
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', mobile_phone="1234567890")
        # create_test_address(customer, first_name, last_name, address_line, address_line2, apartment_suite_number, 
        #                 town_city, state, postcode, delivery_instructions, default=True, is_default_shipping=False, 
        # is_default_billing=False)
        self.address = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="123 Test St", address_line2="", apartment_suite_number="", town_city="Test City", state="TS", 
                                           postcode="12345",delivery_instructions="", default=True, 
                                           is_default_shipping=True, is_default_billing=True)

        self.url = reverse('pop_accounts:personal_info')
    
    
    def test_personal_info_view_authenicated_user(self):
        # Log the user in
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        html = response.content.decode('utf-8')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pop_accounts/user_accounts/dashboard_pages/personal_info.html")

        html = response.content.decode('utf-8')
        self.assertIn('<title>Personal Info</title>', html)

        self.assertIn('<h2>Account Data</h2>', html)


    def test_personal_info_view_redirects_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    

    def test_get_request_authenticated(self):
        """Test GET request for authenticated user"""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertContains(response, 'Test')  # User's first name
        self.assertIn('form', response.context)
        self.assertIn('address_form', response.context)
        self.assertIn('addresses', response.context)
        
        # Check forms are properly initialized
        form = response.context['form']
        self.assertEqual(form.initial['first_name'], 'Test')
        self.assertEqual(form.initial['last_name'], 'User')
    

    def test_get_context_data(self):
        """Test the get_context_data method"""
        self.client.force_login(self.user)
        view = PersonalInfoView()
        view.request = self.client.request()
        view.request.user = self.user
        
        
        context = view.get_context_data()
        
        self.assertIn('form', context)
        self.assertIn('address_form', context)
        self.assertIn('addresses', context)
        self.assertIn('user', context)
        self.assertEqual(context['user'], self.user)
    
    
    def test_personal_form_submission_valid(self):
        """Test valid personal information form submission"""
        self.client.force_login(self.user)
        
        form_data = {
            'first_name': 'Test',
            'middle_name': 'M',
            'last_name': 'User',
            'shoe_size': '11',
            'size_gender': 'male',
            'favorite_brand': 'nike',
            'mobile_phone': '9876543210',
            'mobile_notification': True
        }
        
       
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, self.url)
        
        # Check user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.middle_name, 'M')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.shoe_size, '11')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your profile has been updated.")
    

    def test_personal_form_submission_invalid(self):
        """Test invalid personal information form submission"""
        self.client.force_login(self.user)
        
        form_data = {
            'first_name': '',  # Required field empty
            'last_name': 'Smith'
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())    


    def test_address_form_submission_new_address(self):
        """Test adding a new address"""
        self.client.force_login(self.user)
        
        form_data = {
            'prefix': 'Mr.',
            'first_name': 'John',
            'last_name': 'Doe',
            'street_address_1': '456 New St',
            'city_town': 'New City',
            'state': 'North Carolina',
            'postcode': '54321',
            'delivery_instructions': 'Ring doorbell'
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, self.url)
        
        # Check new address was created
        new_address = PopUpCustomerAddress.objects.filter(
            customer=self.user,
            address_line='456 New St'
        ).first()
        self.assertIsNotNone(new_address)
        self.assertEqual(new_address.town_city, 'New City')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Address has been added.")


    def test_address_form_submission_update_existing(self):
        """Test updating an existing address"""
        self.client.force_login(self.user)
        
        form_data = {
            'address_id': str(self.address.id),
            'prefix': 'Mr.',
            'first_name': 'John',
            'last_name': 'Doe',
            'street_address_1': '789 Updated St',
            'city_town': 'Updated City',
            'state': 'South Carolina',
            'postcode': '98765'
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertRedirects(response, self.url)
        
        # Check address was updated
        self.address.refresh_from_db()
        self.assertEqual(self.address.address_line, '789 Updated St')
        self.assertEqual(self.address.town_city, 'Updated City')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Address has been updated.")


    def test_address_form_submission_invalid(self):
        """Test invalid address form submission"""
        self.client.force_login(self.user)
        
        form_data = {
            'street_address_1': '456 New St',
            'city_town': '' # Missing required fields like city, state, postcode
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('address_form', response.context)
       
       # Add these missing assertions:
        address_form = response.context['address_form']
        self.assertFalse(address_form.is_valid())
        
        # Check that specific fields have validation errors
        form_errors = address_form.errors
        self.assertIn('city_town', form_errors)
        
        # You might also want to test other required fields
        # Check your ThePopUpUserAddressForm to see what's required
        if 'state' in address_form.fields and address_form.fields['state'].required:
            self.assertIn('state', form_errors)
        if 'postcode' in address_form.fields and address_form.fields['postcode'].required:
            self.assertIn('postcode', form_errors)
        
        # Verify no address was created
        new_address = PopUpCustomerAddress.objects.filter(
            customer=self.user,
            address_line='456 New St'
        ).first()
        self.assertIsNone(new_address)


    def test_address_form_submission_nonexistent_address_id(self):
        """Test updating non-existent address returns 404"""
        self.client.force_login(self.user)
        
        form_data = {
            'address_id': '00000000-0000-0000-0000-000000000000',  # Non-existent ID
            'street_address_1': '789 Updated St',
            'city_town': 'Updated City',
            'state': 'UC',
            'postcode': '98765'
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, 404)
    
    def test_address_form_submission_other_users_address(self):
        """Test updating another user's address returns 404"""

        other_user = create_test_user_two()
        print('other_user', other_user)

        other_address = PopUpCustomerAddress.objects.create(
            customer=other_user,
            first_name='Other',
            last_name='User',
            address_line='999 Other St',
            town_city='Other City',
            state='Oklahoma',
            postcode='99999'
        )
        
        self.client.force_login(self.user)
        
        form_data = {
            'address_id': str(other_address.id),
            'street_address_1': '789 Hacked St',
            'city_town': 'Hacked City',
            'state': 'North Carolina',
            'postcode': '12345'
        }
        
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, 404)
    

    def test_form_detection_methods(self):
        """Test the helper methods for form detection"""
        view = PersonalInfoView()
        
        # Test personal form detection
        view.request = MagicMock()
        view.request.POST = {'first_name': 'John', 'last_name': 'Doe'}
        self.assertTrue(view._is_personal_form_submission())
        self.assertFalse(view._is_address_form_submission())
        
        # Test address form detection
        view.request.POST = {'street_address_1': '123 Main St', 'first_name': 'John'}
        self.assertFalse(view._is_personal_form_submission())
        self.assertTrue(view._is_address_form_submission())
    

    def test_address_form_exception_handling(self):
        """Test exception handling in address form submission"""
        self.client.force_login(self.user)
        
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'street_address_1': '456 New St',
            'city_town': 'New City',
            'state': 'North Carolina',
            'postcode': '54321'
        }
        
        with patch('pop_accounts.forms.ThePopUpUserAddressForm.save', side_effect=Exception("Database error")):
            
            response = self.client.post(self.url, form_data)

            self.assertEqual(response.status_code, 200)
            # Should render the form again with error message
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any("error occurred" in str(m) for m in messages))
    



class PersonalInfoViewIntegrationTests(TestCase):
    """Integration tests for PersonalInfoView"""
    
    def setUp(self):
        """Set up integration test data"""
        self.client = Client()
        self.user = create_test_user('integration@example.com', 'integrationpass!123', 'Integration', 'User', '10', 'male', mobile_phone="1234567890")

        # self.user = User.objects.create_user(
        #     email='integration@example.com',
        #     password='integrationpass!123'
        # )
        self.url = reverse('pop_accounts:personal_info')
    
    def test_full_workflow_personal_and_address_forms(self):
        """Test complete workflow of updating both personal info and address"""
        self.client.force_login(self.user)
        
        # First, update personal information
        personal_data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'shoe_size': '9',
            'mobile_phone': '5555555555'
        }
        
        response = self.client.post(self.url, personal_data)
        
        self.assertRedirects(response, self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Integration')
        
        # Then, add an address
        address_data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'street_address_1': '123 Integration St',
            'city_town': 'Test City',
            'state': 'Tennessee',
            'postcode': '12345'
        }
        
        response = self.client.post(self.url, address_data)
        
        self.assertRedirects(response, self.url)
        
        # Verify address was created
        address = PopUpCustomerAddress.objects.filter(customer=self.user).first()
        self.assertIsNotNone(address)
        self.assertEqual(address.address_line, '123 Integration St')


class TestGetAddressView(TestCase):
    def setUp(self):
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')
        self.client.force_login(self.user)
        self.address = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="123 Test St", address_line2="Unit 4", 
                                           apartment_suite_number="128", town_city="Test City", 
                                           state="TS", postcode="12345", delivery_instructions="Leave at the door",
                                           default=True, is_default_shipping=False, is_default_billing=False)
        

    def test_get_address_requires_login(self):
        self.client.logout()
        url = reverse("pop_accounts:get_address", args=[self.address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # redirect to login
    
    def test_get_address_returns_json(self):
        url = reverse("pop_accounts:get_address", args=[self.address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify key fields
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")
        self.assertEqual(data["address_line"], "123 Test St")
        self.assertEqual(data["postcode"], "12345")
    

    def test_get_address_404_for_other_users_address(self):
        # Create another user and an address for them
        other_user = PopUpCustomer.objects.create_user(
            email="user2@example.com",
            password="testPass!45",
            first_name="Jane",
            last_name="Smith",
        )
        other_address = PopUpCustomerAddress.objects.create(
            customer=other_user,
            first_name="Jane",
            last_name="Smith",
            address_line="999 Hidden St",
            town_city="SecretTown",
            state="CA",
            postcode="54321",
        )

        url = reverse("pop_accounts:get_address", args=[other_address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # cannot access another user’s address
    

    def test_get_address_404_if_does_not_exist(self):
        url = reverse("pop_accounts:get_address", args=['00000000-0000-0000-0000-000000000000'])  # non-existent ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)



class TestDeleteAddressView(TestCase):
    def setUp(self):
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')
        self.other_user = create_test_user_two()

        self.address = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="123 Test St", address_line2="Unit 4", 
                                           apartment_suite_number="128", town_city="Test City", 
                                           state="North Carolina", postcode="12345", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)
        
        self.url = reverse("pop_accounts:delete_address", args=[self.address.id])
    

    def test_redirect_if_not_logged_in(self):
        """Should redirect unauthenticated users to login page"""
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)  # redirect
        self.assertIn("/", response.url)
    

    def test_successful_delete_by_owner(self):
        """User should be able to delete their own address"""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success"})
        self.assertFalse(PopUpCustomerAddress.objects.filter(id=self.address.id).exists())

    def test_cannot_delete_other_users_address(self):
        """User cannot delete an address they don't own"""
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)  # get_object_or_404 should trigger

    def test_get_request_not_allowed(self):
        """GET request should return error JSON"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "Invalid Request"})


class TestSetDefaultAddressView(TestCase):
    """Test Suite for SetDefaultAddressView"""
    def setUp(self):
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')
        # self.client.force_login(self.user)
        self.address = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="123 Test St", address_line2="Unit 4", 
                                           apartment_suite_number="128", town_city="Test City", 
                                           state="North Carolina", postcode="12345", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)
        
        self.address_two = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="456 Second St", address_line2="", 
                                           apartment_suite_number="", town_city="Second City", 
                                           state="New York", postcode="54321", 
                                           delivery_instructions="", default=False, is_default_shipping=False, 
                                           is_default_billing=False)
        
        self.address_three = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="789 Third St", address_line2="", 
                                           apartment_suite_number="", town_city="Third City", 
                                           state="Texas", postcode="67890", 
                                           delivery_instructions="", default=False, is_default_shipping=False, 
                                           is_default_billing=False)
        
        self.other_user = create_test_user_two()
        self.other_user_address = create_test_address(
            customer=self.other_user, first_name=self.other_user.first_name, last_name=self.other_user.last_name, 
            address_line="789 Third St", address_line2="", apartment_suite_number="", town_city="Third City", 
            state="Texas", postcode="67890", delivery_instructions="", default=True, is_default_shipping=False, 
            is_default_billing=False)
        
        self.url = reverse("pop_accounts:delete_address", args=[self.address.id])

        # Force reset defaults to ensure clean state
        # PopUpCustomerAddress.objects.filter(customer=self.user).update(default=False)
        # self.address.default = True
        # self.address.save()

    def get_url(self, address_id):
        """Helper to get the URL for setting default address"""
        return reverse('pop_accounts:set_default_address', kwargs={'address_id': address_id})

    def test_view_requires_login(self):
        """Test that the view requires authentication"""
        url = self.get_url(self.address.id)
        response = self.client.post(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)
    

    def test_get_request_rejected(self):
        """Test that GET requests are rejected"""
        self.client.force_login(self.user)
        url = self.get_url(self.address.id)
        
        response = self.client.get(url)        
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)

        self.assertFalse(data['success'])  # Now explicitly False
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid Request')



    def test_set_default_address_success(self):
        """Test successfully setting a new default address"""
        self.client.force_login(self.user)
        url = self.get_url(self.address_two.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify address2 is now default
        self.address_two.refresh_from_db()
        self.assertTrue(self.address_two.default)
        
        # Verify address1 is no longer default
        self.address.refresh_from_db()
        self.assertFalse(self.address.default)
        
        # Verify address3 remains non-default
        self.address_three.refresh_from_db()
        self.assertFalse(self.address_three.default)
    
    def test_only_one_default_address(self):
        """Test that only one address can be default at a time"""
        self.client.force_login(self.user)
        
        # Set address2 as default
        url = self.get_url(self.address_two.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        # Verify only address2 is default
        addresses = PopUpCustomerAddress.objects.filter(customer=self.user, default=True)
        self.assertEqual(addresses.count(), 1)
        self.assertEqual(addresses.first().id, self.address_two.id)
        
        # Now set address3 as default
        url = self.get_url(self.address_three.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        # Verify only address3 is default
        addresses = PopUpCustomerAddress.objects.filter(customer=self.user, default=True)
        self.assertEqual(addresses.count(), 1)
        self.assertEqual(addresses.first().id, self.address_three.id)
    
    def test_set_already_default_address(self):
        """Test setting an address that's already default"""
        self.client.force_login(self.user)
        url = self.get_url(self.address.id)
        
        # address1 is already default
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Should still be default
        self.address.refresh_from_db()
        self.assertTrue(self.address.default)
        
        # Only one default should exist
        default_count = PopUpCustomerAddress.objects.filter(
            customer=self.user, 
            default=True
        ).count()
        self.assertEqual(default_count, 1)
    
    def test_nonexistent_address_id(self):
        """Test attempting to set default for non-existent address"""
        self.client.force_login(self.user)
        url = self.get_url('00000000-0000-0000-0000-000000000000')  # Non-existent ID
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_cannot_set_other_users_address(self):
        """Test that user cannot set another user's address as default"""

        self.client.force_login(self.user)
        url = self.get_url(self.other_user_address.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        
        # Verify other user's address wasn't affected
        self.other_user_address.refresh_from_db()
        self.assertTrue(self.other_user_address.default)
        
        # Verify current user's addresses weren't affected
        self.address.refresh_from_db()

        self.assertTrue(self.address.default)
    

    def test_deleted_address_cannot_be_set_default(self):
        """Test that soft-deleted addresses cannot be set as default"""
        from django.utils import timezone
        
        # Soft delete address2
        self.address_two.deleted_at = timezone.now()
        self.address_two.save()
        
        self.client.force_login(self.user)
        url = self.get_url(self.address_two.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        
        # Verify address2 didn't become default
        self.address_two.refresh_from_db()
        self.assertFalse(self.address_two.default)
        self.assertIsNotNone(self.address_two.deleted_at)
    
    def test_json_response_format(self):
        """Test that response is valid JSON with correct structure"""
        self.client.force_login(self.user)
        url = self.get_url(self.address_two.id)
        
        response = self.client.post(url)
        
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('success', data)
        self.assertIsInstance(data['success'], bool)
    
    def test_json_error_response_format(self):
        """Test error response format"""
        self.client.force_login(self.user)
        url = self.get_url('00000000-0000-0000-0000-000000000000')
        
        response = self.client.post(url)
        
        # Note: The view returns 404 for non-existent, not 400 with JSON
        # So this test verifies the actual behavior
        self.assertEqual(response.status_code, 404)
    
    def test_multiple_users_can_have_default_addresses(self):
        """Test that different users can each have their own default address"""
        # User 1 sets their default
        self.client.force_login(self.user)
        url = self.get_url(self.address_two.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        # User 2's default should be unaffected
        self.other_user_address.refresh_from_db()
        self.assertTrue(self.other_user_address.default)
        
        # User 2 can also set their default
        self.client.force_login(self.other_user)
        url = self.get_url(self.other_user_address.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        # Both users should have their own defaults
        user1_defaults = PopUpCustomerAddress.objects.filter(
            customer=self.user, 
            default=True
        ).count()
        user2_defaults = PopUpCustomerAddress.objects.filter(
            customer=self.other_user, 
            default=True
        ).count()
        
        self.assertEqual(user1_defaults, 1)
        self.assertEqual(user2_defaults, 1)
    
    def test_ajax_request_handling(self):
        """Test that view handles AJAX requests properly"""
        self.client.force_login(self.user)
        url = self.get_url(self.address_two.id)
        
        # Simulate AJAX request
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_database_transaction_integrity(self):
        """Test that database operations are atomic"""
        self.client.force_login(self.user)
        
        # Count initial defaults
        initial_defaults = PopUpCustomerAddress.objects.filter(
            customer=self.user, 
            default=True
        ).count()
        self.assertEqual(initial_defaults, 1)
        
        # Set new default
        url = self.get_url(self.address_three.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        # Count final defaults - should still be exactly 1
        final_defaults = PopUpCustomerAddress.objects.filter(
            customer=self.user, 
            default=True
        ).count()
        self.assertEqual(final_defaults, 1)
        
        # Verify it's the correct one
        default_address = PopUpCustomerAddress.objects.get(
            customer=self.user, 
            default=True
        )
        self.assertEqual(default_address.id, self.address_three.id)


class SetDefaultAddressViewIntegrationTests(TestCase):
    """Integration tests for SetDefaultAddressView"""
    
    def setUp(self):
        """Set up integration test data"""
        self.client = Client()
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male')
    
    def test_user_workflow_changing_defaults(self):
        """Test complete workflow of user changing default addresses"""
        self.client.force_login(self.user)
        
        # Create addresses
        addr1 = create_test_address(customer=self.user, first_name="Integration", last_name="User", 
                                           address_line="111 First", address_line2="", 
                                           apartment_suite_number="", town_city="City1", 
                                           state="California", postcode="11111", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)
        
        addr2 = create_test_address(customer=self.user, first_name="Integration", last_name="User", 
                                           address_line="222 Second", address_line2="", 
                                           apartment_suite_number="", town_city="City2", 
                                           state="New York", postcode="22222", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)
        
        addr3 = create_test_address(customer=self.user, first_name="Integration", last_name="User", 
                                           address_line="333 Third", address_line2="", 
                                           apartment_suite_number="", town_city="City3", 
                                           state="Texas", postcode="33333", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)
        
        
        # Change default to addr2
        url = reverse('pop_accounts:set_default_address', kwargs={'address_id': addr2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        addr2.refresh_from_db()
        self.assertTrue(addr2.default)
        
        # Change default to addr3
        url = reverse('pop_accounts:set_default_address', kwargs={'address_id': addr3.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        addr3.refresh_from_db()
        self.assertTrue(addr3.default)
        
        # Verify only addr3 is default
        defaults = PopUpCustomerAddress.objects.filter(
            customer=self.user, 
            default=True
        )
        self.assertEqual(defaults.count(), 1)
        self.assertEqual(defaults.first().id, addr3.id)


class DeleteAccountViewTests(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.other_user = create_test_user('existingTwo@example.com', 'testPassTwo!23', 'Testi', 'Usera', '6', 'female', is_active=False)
        
        self.url = reverse('pop_accounts:delete_account')

        self.user.is_active = True
        self.user.save()
        self.other_user.is_active = True
        self.other_user.save()


    def test_view_reqiures_login(self):
        """Test that view requires authentication"""
        response = self.client.post(self.url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)
    
    def test_get_request_rejected(self):
        """Test that GET requests are rejected"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid Request')


    def test_soft_delete_account_success(self):
        """Test successful soft deletion of account"""

        self.client.force_login(self.user)

        # verify user is active before deletion
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.deleted_at)

        response = self.client.post(self.url)

        # Should redirect to account deleted page
        self.assertRedirects(response, reverse('pop_accounts:account_deleted'))

        # refresh user from database
        self.user.refresh_from_db()

        # self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)

        # Verify deleted_at is recent (within last minute)
        time_diff = now() - self.user.deleted_at
        self.assertLess(time_diff.total_seconds(), 60)
    
    
    def test_user_logged_out_after_deletion(self):
        """Test that user is logged out after account deletion"""
        self.client.force_login(self.user)

        #verify user is authenticated
        response = self.client.get(reverse('pop_accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

        # Delete Account
        self.client.post(self.url)

        # Try to access a protected page
        response = self.client.get(reverse('pop_accounts:dashboard'))

        # Should redirect to login (user is logged out)
        self.assertEqual(response.status_code,302)
        self.assertIn('/', response.url)

    def test_deleted_user_cannot_login(self):
        """Test that soft-deleted user cannot log in"""
        # Delete account
        self.client.force_login(self.user)
        self.client.post(self.url)

        # attempt to log in again
        login_successful = self.client.login(email='existing@example.com', password='testPass!23'
        )
        self.assertFalse(login_successful)



    def test_soft_delete_preserves_user_data(self):
        """Test that soft delete preserves user data in database"""
        user_id = self.user.id
        user_email = self.user.email

        self.client.force_login(self.user)
        self.client.post(self.url)

        # User should still exist in database
        deleted_user = PopUpCustomer.all_objects.get(id=user_id)
        self.assertEqual(deleted_user.email, user_email)
        self.assertFalse(deleted_user.is_active)
        self.assertIsNotNone(deleted_user.deleted_at)


    def test_soft_deleted_excludes_from_default_queryset(self):
        self.client.force_login(self.user)
        self.client.post(self.url)

        # Should not appear in default queryset
        with self.assertRaises(PopUpCustomer.DoesNotExist):
            PopUpCustomer.objects.get(email='existing@example.com')



        # Should appearn in all objects queryset
        deleted_user = PopUpCustomer.all_objects.get(email='existing@example.com')
        self.assertIsNotNone(deleted_user)


    def test_other_users_unaffected(self):
        """Test that deleted one user doesn't affect others"""

        self.client.force_login(self.user)
    
        # Verify other user is active
        self.assertTrue(self.other_user.is_active)

        # Delete current account
        self.client.post(self.url)

        # Verify other user is still active
        self.other_user.refresh_from_db()
        self.assertTrue(self.other_user.is_active) # <- this fails, other_user not longer active after refresh
        self.assertIsNone(self.other_user.deleted_at)
    


    def test_multiple_deletion_attempts_idempotent(self):
        """Test that multiple delete attempts are idempotent"""
        self.client.force_login(self.user)
        
        # First deletion
        response1 = self.client.post(self.url)
        self.user.refresh_from_db()
        first_deleted_at = self.user.deleted_at
        
        # Try to delete again (need to log in as all_objects)
        deleted_user = PopUpCustomer.all_objects.get(id=self.user.id)
        deleted_user.soft_delete()
        deleted_user.refresh_from_db()
        
        # Should maintain same is_active status
        self.assertFalse(deleted_user.is_active)

        # deleted_at might update, but that's okay
        self.assertIsNotNone(deleted_user.deleted_at)
    

    def test_account_deleted_page_accessible(self):
        """Test that account_deleted redirect target exists"""
        self.client.force_login(self.user)
        response = self.client.post(self.url, follow=True)
        
        # Should successfully reach the account_deleted page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pop_accounts/user_accounts/dashboard_pages/account_deleted.html')
    

    def test_session_cleared_after_deletion(self):
        """Test that user is logged out after deletion"""
        self.client.force_login(self.user)
        
        # Verify user is authenticated before deletion
        self.assertIn('_auth_user_id', self.client.session)
        
        # Delete account
        response = self.client.post(self.url)
        
        # After logout, try to access a protected page
        response = self.client.get(reverse('pop_accounts:dashboard'))
        
        # Should redirect to login (user is not authenticated)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)
    

    def test_is_deleted_property(self):
        """Test the is_deleted property on user model"""
        # Before deletion
        self.assertFalse(self.user.is_deleted)
        
        # After deletion
        self.user.soft_delete()
        self.assertTrue(self.user.is_deleted)
    

    def test_restore_functionality(self):
        """Test that soft-deleted accounts can be restored"""
        # Delete account
        self.user.soft_delete()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)
        
        # Restore account
        self.user.restore()
        
        # Verify restoration
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.deleted_at)
        self.assertFalse(self.user.is_deleted)
    

    def test_delete_method_calls_soft_delete(self):
        """Test that calling delete() triggers soft_delete()"""
        user_id = self.user.id
        
        # Call delete method
        self.user.delete()
        
        # User should still exist but be soft-deleted
        deleted_user = PopUpCustomer.all_objects.get(id=user_id)
        self.assertFalse(deleted_user.is_active)
        self.assertIsNotNone(deleted_user.deleted_at)

    
    def test_post_request_with_follow(self):
        """Test POST request following redirects"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, follow=True)
        
        # Should end up on account_deleted page
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response, 
            reverse('pop_accounts:account_deleted'),
            fetch_redirect_response=False
        )


class DeleteAccountViewIntegrationTests(TestCase):
    """Integration tests for DeleteAccountView"""
    
    def setUp(self):
        """Set up integration test data"""
        self.client = Client()
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.other_user = create_test_user('existingTwo@example.com', 'testPassTwo!23', 'Testi', 'Usera', '6', 'female', is_active=False)
        
        self.url = reverse('pop_accounts:delete_account')

        self.user.is_active = True
        self.user.save()
        self.other_user.is_active = True
        self.other_user.save()

        self.url = reverse('pop_accounts:delete_account')
    
    def test_full_account_deletion_workflow(self):
        """Test complete workflow from login to deletion"""
        # User logs in
        login_successful = self.client.login(
            email='existing@example.com',
            password='testPass!23'
        )
        self.assertTrue(login_successful)
        
        # User accesses dashboard
        response = self.client.get(reverse('pop_accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # User deletes account
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('pop_accounts:account_deleted'))
        
        # User is logged out
        response = self.client.get(reverse('pop_accounts:dashboard'))
        self.assertEqual(response.status_code, 302)
        
        # User cannot log back in
        login_successful = self.client.login(
            email='existing@example.com',
            password='testPass!23'
        )
        self.assertFalse(login_successful)
        
        # User still exists in database (soft delete)
        deleted_user = PopUpCustomer.all_objects.get(email='existing@example.com')
        self.assertIsNotNone(deleted_user)
        self.assertFalse(deleted_user.is_active)
    

    def test_account_restoration_workflow(self):
        """Test that admin can restore a deleted account"""
        # User deletes account
        self.client.force_login(self.user)
        self.client.post(self.url)
        
        # Admin restores account (simulated)
        deleted_user = PopUpCustomer.all_objects.get(email='existing@example.com')
        deleted_user.restore()
        
        # User can log in again
        login_successful = self.client.login(
            email='existing@example.com',
            password='testPass!23'
        )
        self.assertTrue(login_successful)
        
        # User can access protected pages
        response = self.client.get(reverse('pop_accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

class UserPasswordResetConfirmViewTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.other_user = create_test_user('existingTwo@example.com', 'testPassTwo!23', 'Testi', 'Usera', '6', 'female', is_active=False)
        self.user.is_active = True
        self.user.save()
        self.other_user.is_active = True
        self.other_user.save()
        
        # endcode UID
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

        self.url = reverse('pop_accounts:password_reset_confirm', kwargs={'uidb64': self.uidb64, 'token': self.token})


    def test_valid_get_request_renders_form(self):
        """GET with valid uid/token should render the password reset form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pop_accounts/login/password_reset_confirm.html")
        self.assertIn('validlink', response.context)
        self.assertTrue(response.context['validlink'])


    def test_invalid_get_request_renders_invalid_page(self):
        """GET with invalid uid should show invalid link page."""
        bad_uid = urlsafe_base64_encode(force_bytes('00000000-0000-0000-0000-000000000000'))  # non-existent user
        bad_url = reverse("pop_accounts:password_reset_confirm", kwargs={"uidb64": bad_uid, "token": self.token})
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("validlink", response.context)
        self.assertFalse(response.context["validlink"])


    def test_post_with_invalid_uid_returns_json_error(self):
        """POST with invalid uid should return JSON error."""
        bad_uid = urlsafe_base64_encode(force_bytes('00000000-0000-0000-0000-000000000000'))
        bad_url = reverse("pop_accounts:password_reset_confirm", kwargs={"uidb64": bad_uid, "token": self.token})
        response = self.client.post(bad_url, {"password": "NewPass123!", "password2": "NewPass123!"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Invalid reset link."})


    def test_post_with_missing_fields_returns_error(self):
        """POST with missing password fields should return error."""
        response = self.client.post(self.url, {"password": "", "password2": ""})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "All fields are required."})


    def test_post_with_mismatched_passwords_returns_error(self):
        """POST with mismatched passwords should return error."""
        response = self.client.post(self.url, {"password": "Pass1", "password2": "Pass2"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Passwords do not match."})


    def test_post_with_valid_data_resets_password(self):
        """POST with valid data should reset password successfully."""
        response = self.client.post(self.url, {"password": "NewPassword123!", "password2": "NewPassword123!"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "message": "Password reset successful."})

        # Verify user password is updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123!"))


class OpenBidsViewTests(TestCase):
    """Test suite for OpenBidsView"""
    def setUp(self):
        self.client = Client()

        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.other_user = create_test_user('existingTwo@example.com', 'testPassTwo!23', 'Testi', 'Usera', '6', 'female', is_active=False)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.other_user.is_active = True
        self.other_user.save(update_fields=['is_active'])

        self.address = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="111 First", address_line2="", 
                                           apartment_suite_number="", town_city="City1", 
                                           state="California", postcode="11111", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)
        

        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.test_prod_one = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air", description="Brand new sneakers", 
            slug="jordan-3-retro-og-rare-air", buy_now_price="230.00", current_highest_bid="0", 
            retail_price="150.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="165.00", is_active="True")


        self.test_prod_two = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Jordan 4 Retro", 
            secondary_product_title="White Cement", description="Brand new sneakers", 
            slug="jordan-4-white-cement", buy_now_price="230.00", current_highest_bid="0", 
            retail_price="150.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="165.00", is_active="True")

        self.test_prod_three = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Jordan 11 Retro", 
            secondary_product_title="Concord", description="Brand new Jordan 11", 
            slug="jordan-11-concord", buy_now_price="350.00", current_highest_bid="0", 
            retail_price="200.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="225.00", is_active="False")

        # Create specifications for products
        self.size_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='Size')
        self.color_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='colorway')
        
        
        PopUpProductSpecificationValue.objects.create(
            product=self.test_prod_one,
            specification=self.size_spec,
            value='10'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.test_prod_one,
            specification=self.color_spec,
            value='Red'
        )
        
        # Create bids
        self.bid1 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('105.00'),
            is_active=True
        )

        # Create other user's bid (should not appear in user's view)
        self.other_user_bid = PopUpBid.objects.create(
            customer=self.other_user,
            product=self.test_prod_one,
            amount=Decimal('115.00'),
            is_active=True
        )

        self.bid2 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('125.00'),
            is_active=True
        )
        
        self.bid2 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_two,
            amount=Decimal('175.00'),
            is_active=True
        )
        
        
        # Create inactive bid (should not appear)
        self.inactive_bid = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('176.00'),
            is_active=False
        )
        
        # Create bid on inactive product
        self.bid_on_inactive = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_three,
            amount=Decimal('80.00'),
            is_active=True
        )
        
       
        
        # Add products to user's interests
        self.user.prods_interested_in.add(self.test_prod_one)
        self.user.prods_on_notice_for.add(self.test_prod_two)
        
        self.url = reverse('pop_accounts:open_bids')
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)


    def test_get_request_authenticated(self):
        """Test GET request for authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pop_accounts/user_accounts/dashboard_pages/open_bids.html')
    

    def test_context_contains_required_data(self):
        """Test that context contains all required variables"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertIn('user', response.context)
        self.assertIn('addresses', response.context)
        self.assertIn('prod_interested_in', response.context)
        self.assertIn('prods_on_notice_for', response.context)
        self.assertIn('highest_bid_objects', response.context)
        self.assertIn('open_bids', response.context)
        self.assertIn('quick_bid_increments', response.context)
        
        self.assertEqual(response.context['user'], self.user)


    def test_only_highest_bids_shown(self):
        """Test that only the highest bid per product is shown"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        highest_bid_objects = response.context['highest_bid_objects']
        
        # Should have 3 bids (test_prod_one and test_prod_two, not product3 which is inactive)
        self.assertEqual(len(highest_bid_objects), 3)
        
        # Find the bid for product1
        product1_bid = None
        for bid in highest_bid_objects:
            if bid.product_id == self.test_prod_one.id:
                product1_bid = bid
                break
        
        # Should be the highest bid (110.00), not the lower one (105.00)
        self.assertIsNotNone(product1_bid)
        self.assertEqual(product1_bid.amount, Decimal('125.00'))



    def test_inactive_bids_excluded(self):
        """Test that inactive bids are not shown"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        highest_bid_objects = list(response.context['highest_bid_objects'])
        
        # Inactive bid should not appear
        bid_amounts = [bid.amount for bid in highest_bid_objects]
        self.assertNotIn(Decimal('120.00'), bid_amounts)

    def test_inactive_products_excluded(self):
        """Test that bids on inactive products are excluded"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        open_bids = response.context['open_bids']
        
        # Should not include product3 (inactive)
        product_ids = [bid_data['product'].id for bid_data in open_bids]
        self.assertNotIn(self.test_prod_three.id, product_ids)
    

    def test_only_users_bids_shown(self):
        """Test that only authenticated user's bids are shown"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        highest_bid_objects = response.context['highest_bid_objects']
        
        # All bids should belong to self.user
        for bid in highest_bid_objects:
            self.assertEqual(bid.customer_id, self.user.id)

    def test_enriched_data_structure(self):
        """Test that enriched bid data has correct structure"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        open_bids = response.context['open_bids']
        
        self.assertGreater(len(open_bids), 0)
        
        # Check structure of first bid data
        bid_data = open_bids[0]
        self.assertIn('highest_user_bid', bid_data)
        self.assertIn('product', bid_data)
        self.assertIn('specs', bid_data)
        self.assertIn('current_highest', bid_data)
        self.assertIn('bid_count', bid_data)
        self.assertIn('duration', bid_data)
        self.assertIn('retail_price', bid_data)


    def test_product_specifications_included(self):
        """Test that product specifications are included in enriched data"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        open_bids = response.context['open_bids']
        
        # Find product1 in open_bids
        product1_data = None
        for bid_data in open_bids:
            if bid_data['product'].id == self.test_prod_one.id:
                product1_data = bid_data
                break
        
        self.assertIsNotNone(product1_data)
        self.assertGreater(len(product1_data['specs']), 0)
        
        # Check that specs contain expected data
        spec_values = [spec.value for spec in product1_data['specs']]
        self.assertIn('10', spec_values)  # Size
        self.assertIn('Red', spec_values)  # Color
    

    def test_quick_bid_increments(self):
        """Test that quick bid increments are provided"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        increments = response.context['quick_bid_increments']
        
        self.assertEqual(increments, [10, 20, 30])
    
    def test_default_address_retrieved(self):
        """Test that user's default address is retrieved"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        addresses = response.context['addresses']
        
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0].id, self.address.id)
        self.assertTrue(addresses[0].default)
    

    def test_interested_products_retrieved(self):
        """Test that products user is interested in are retrieved"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        prod_interested_in = list(response.context['prod_interested_in'])
        
        self.assertEqual(len(prod_interested_in), 1)
        self.assertEqual(prod_interested_in[0].id, self.test_prod_one.id)
    

    def test_notice_products_retrieved(self):
        """Test that products user is on notice for are retrieved"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        prods_on_notice_for = list(response.context['prods_on_notice_for'])
        
        self.assertEqual(len(prods_on_notice_for), 1)
        self.assertEqual(prods_on_notice_for[0].id, self.test_prod_two.id)
    

    def test_user_with_no_bids(self):
        """Test view for user with no active bids"""
        # Create user with no bids
        no_bid_user = PopUpCustomer.objects.create_user(
            email='nobids@example.com',
            password='testpass123'
        )
        no_bid_user.is_active = True
        no_bid_user.save(update_fields=['is_active'])
        
        self.client.force_login(no_bid_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        open_bids = response.context['open_bids']
        self.assertEqual(len(open_bids), 0)
    

    def test_user_with_no_default_address(self):
        """Test view for user without default address"""
        # Create user with no default address
        no_addr_user = PopUpCustomer.objects.create_user(
            email='noaddr@example.com',
            password='testpass123'
        )
        no_addr_user.is_active = True
        no_addr_user.save(update_fields=['is_active'])
        
        self.client.force_login(no_addr_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        addresses = response.context['addresses']
        self.assertEqual(len(addresses), 0)
    

    def test_post_request(self):
        """Test POST request behavior"""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        
        # Currently just re-renders template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pop_accounts/user_accounts/dashboard_pages/open_bids.html')
    
    
    def test_multiple_bids_same_product(self):
        """Test that only highest bid shown when user has multiple bids on same product"""
        # Create additional higher bid on product1
        higher_bid = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('126.00'),
            is_active=True
        )
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        highest_bid_objects = list(response.context['highest_bid_objects'])
        
        # Find product1 bid
        product1_bids = [bid for bid in highest_bid_objects if bid.product_id == self.test_prod_one.id]
        
        # Should only have one bid for product1
        self.assertEqual(len(product1_bids), 1)
        # Should be the highest amount
        self.assertEqual(product1_bids[0].amount, Decimal('126.00'))
    
    def test_bid_count_and_current_highest(self):
        """Test that bid count and current highest bid are included"""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        open_bids = response.context['open_bids']
        
        # Each bid should have bid_count and current_highest
        for bid_data in open_bids:
            self.assertIn('bid_count', bid_data)
            self.assertIn('current_highest', bid_data)
            self.assertIsNotNone(bid_data['bid_count'])



class OpenBidsViewIntegrationTests(TestCase):
    """Integration tests for OpenBidsView"""
    
    def setUp(self):
        self.client = Client()

        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
       
        self.url = reverse('pop_accounts:open_bids')
    
    def test_complete_bidding_workflow(self):
        """Test complete workflow from placing bid to viewing in open bids"""
        # Create product
        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)
        
        product = create_test_product(
            product_type=test_product_type, category=test_category, product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air", description="Brand new sneakers", 
            slug="jordan-3-retro-og-rare-air", buy_now_price="230.00", current_highest_bid="0", 
            retail_price="150.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="165.00", is_active="True")
       
        
        # User places bid
        bid = PopUpBid.objects.create(
            customer=self.user,
            product=product,
            amount=Decimal('80.00'),
            is_active=True
        )
        
        # User views open bids
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        open_bids = response.context['open_bids']
        self.assertEqual(len(open_bids), 1)
        self.assertEqual(open_bids[0]['product'].id, product.id)
        self.assertEqual(open_bids[0]['highest_user_bid'].amount, Decimal('80.00'))


class PastBidsViewTest(TestCase):
    """Test Suite for PastBidsView"""

    def setUp(self):
        self.client = Client()
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])

        self.other_user = create_test_user('existingTwo@example.com', 'testPassTwo!23', 'Testi', 'Usera', '6', 'female', is_active=False)
        self.other_user.is_active = True
        self.other_user.save(update_fields=['is_active'])        

        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.test_prod_one = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Past Bid Product 1", 
            secondary_product_title="Past Bid 1", description="Brand new sneakers", 
            slug="past-bid-product-1", buy_now_price="250.00", current_highest_bid="0", 
            retail_price="150.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="sold_out", bid_count=0, reserve_price="100.00", is_active=False)


        self.test_prod_two = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Past Bid Product 2", 
            secondary_product_title="Past Bid 2", description="Brand new sneakers", 
            slug="past-bid-product-2", buy_now_price="300.00", current_highest_bid="0", 
            retail_price="200.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="sold_out", bid_count=0, reserve_price="150.00", is_active=False)

        self.test_prod_three = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Jordan 11 Retro", 
            secondary_product_title="Concord", description="Brand new Jordan 11", 
            slug="jordan-11-concord", buy_now_price="350.00", current_highest_bid="0", 
            retail_price="200.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="225.00", is_active="False")


        # Create past bids (inactive)
        self.bid1 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('110.00'),
            is_active=False
        )

        self.bid2 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_two,
            amount=Decimal('160.00'),
            is_active=False
        )

        
        self.url = reverse('pop_accounts:past_bids')
        

    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)
        
    
    def test_get_request_authenticated(self):
        """Test GET request for authenticated user"""
        self.client.force_login(self.user)
        
        with patch('pop_up_auction.utils.utils.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': [],
                'statistics': {}
            }
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pop_accounts/user_accounts/dashboard_pages/past_bids.html')


    def test_context_contains_required_data(self):
        """Test that context contains all required variables"""
        # Create real bid data
        bid = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('100.00'),
            is_active=False
        )
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        # Verify context structure
        self.assertIn('bid_history', response.context)
        self.assertIn('statistics', response.context)
        self.assertIn('user_past_bids_copy', response.context)
        
        # Verify data types
        self.assertIsInstance(response.context['bid_history'], list)
        self.assertIsInstance(response.context['statistics'], dict)
        
        # Verify bid history has data
        self.assertGreater(len(response.context['bid_history']), 0)
    

    def test_get_customer_bid_history_context_called_with_user_id(self):
        """Test that utility function is called with correct user ID"""
        self.client.force_login(self.user)
        
        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': [],
                'statistics': {}
            }
            
            response = self.client.get(self.url)
            
            # Verify function was called with user's ID
            mock_func.assert_called_once_with(self.user.id)
    

    def test_user_past_bids_copy_in_context(self):
        """Test that static copy is included in context"""
        self.client.force_login(self.user)
        
        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': [],
                'statistics': {}
            }
            
            response = self.client.get(self.url)
        
        self.assertIn('user_past_bids_copy', response.context)
        self.assertEqual(response.context['user_past_bids_copy'], USER_PAST_BIDS_COPY)
    

    def test_empty_bid_history(self):
        """Test view with user who has no past bids"""
        # Create user with no bids
        no_bid_user = PopUpCustomer.objects.create_user(
            email='nobids@example.com',
            password='testpass123'
        )
        no_bid_user.is_active = True
        no_bid_user.save(update_fields=['is_active'])
        
        self.client.force_login(no_bid_user)
        
        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': [],
                'statistics': {
                    'total_bids': 0,
                    'won_bids': 0,
                    'lost_bids': 0
                }
            }
            
            response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['bid_history']), 0)
        self.assertEqual(response.context['statistics']['total_bids'], 0)
    

    def test_multiple_past_bids(self):
        """Test view with user who has multiple past bids"""
        self.client.force_login(self.user)
        
        mock_bid_history = [
            {
                'id': 1,
                'product': self.test_prod_one,  # Use actual product object
                'product_name': 'Product 1',
                'product_slug': 'product-1',
                'bid_amount': Decimal('100.00'),
                'bid_time': timezone.now(),
                'is_winning': True,
                'status': 'Winning',
                'status_class': 'success',
                'has_auto_bid': False,
                'max_auto_bid': None,
                'bid_increment': Decimal('5.00'),
                'is_auction_active': False,
                'auction_status': 'closed',
                'sale_outcome': 'sold',
                'is_finalized': True,
                'current_highest_bid': Decimal('100.00'),
                'time_since_bid': timezone.timedelta(days=1),
                'specifications': {},
                'mptt_specs': {},
                'all_specs': {}
            },
            {
            'id': 2,
            'product': self.test_prod_two,  # Use actual product object
            'product_name': 'Product 1',
            'product_slug': 'product-1',
            'bid_amount': Decimal('100.00'),
            'bid_time': timezone.now(),
            'is_winning': True,
            'status': 'Winning',
            'status_class': 'success',
            'has_auto_bid': False,
            'max_auto_bid': None,
            'bid_increment': Decimal('5.00'),
            'is_auction_active': False,
            'auction_status': 'closed',
            'sale_outcome': 'sold',
            'is_finalized': True,
            'current_highest_bid': Decimal('150.00'),
            'time_since_bid': timezone.timedelta(days=1),
            'specifications': {},
            'mptt_specs': {},
            'all_specs': {}
            },
            {
            'id': 3,
            'product': self.test_prod_three,  # Use actual product object
            'product_name': 'Product 1',
            'product_slug': 'product-1',
            'bid_amount': Decimal('100.00'),
            'bid_time': timezone.now(),
            'is_winning': True,
            'status': 'Winning',
            'status_class': 'success',
            'has_auto_bid': False,
            'max_auto_bid': None,
            'bid_increment': Decimal('5.00'),
            'is_auction_active': False,
            'auction_status': 'closed',
            'sale_outcome': 'sold',
            'is_finalized': True,
            'current_highest_bid': Decimal('200.00'),
            'time_since_bid': timezone.timedelta(days=1),
            'specifications': {},
            'mptt_specs': {},
            'all_specs': {}
            },
        ]
        
        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': mock_bid_history,
                'statistics': {'total_bids': 3}
            }
            
            response = self.client.get(self.url)
        
        self.assertEqual(len(response.context['bid_history']), 3)
    

    def test_statistics_structure(self):
        """Test that statistics have expected structure"""
        self.client.force_login(self.user)
        
        expected_statistics = {
            'total_bids': 10,
            'won_bids': 3,
            'lost_bids': 7,
            'average_bid_amount': Decimal('125.50'),
            'total_spent': Decimal('450.00')
        }
        

        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': [],
                'statistics': expected_statistics
            }
            
            response = self.client.get(self.url)
        
        statistics = response.context['statistics']
        self.assertEqual(statistics['total_bids'], 10)
        self.assertEqual(statistics['won_bids'], 3)
        self.assertEqual(statistics['lost_bids'], 7)

    
    def test_user_isolation(self):
        """Test that users only see their own bid history"""
        self.client.force_login(self.user)
        
        # Mock should only be called with self.user.id
        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.return_value = {
                'bid_history': [],
                'statistics': {}
            }
            
            response = self.client.get(self.url)
            
            # Verify it was called with the correct user ID
            mock_func.assert_called_once_with(self.user.id)
            self.assertNotEqual(mock_func.call_args[0][0], self.other_user.id)

    
    def test_view_handles_exception_from_utility_function(self):
        """Test view handles exceptions from get_customer_bid_history_context"""
        self.client.force_login(self.user)
        
        with patch('pop_accounts.views.get_customer_bid_history_context') as mock_func:
            mock_func.side_effect = Exception("Database error")
            
            # View should handle the exception gracefully
            # Depending on your error handling, adjust the assertion
            with self.assertRaises(Exception):
                response = self.client.get(self.url)

    
    def test_only_post_method_not_allowed(self):
        """Test that POST requests are not handled"""
        self.client.force_login(self.user)
        
        response = self.client.post(self.url, {})
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)



class PastBidsViewIntegrationTests(TestCase):
    """Integration tests for PastBidsView with real utility function"""
    
    def setUp(self):
        self.client = Client()

        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.user.is_active = True
        self.user.save(update_fields=['is_active']) 

        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.test_prod_one = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Integration Product 1'", 
            secondary_product_title="Past Bid 1", description="Brand new sneakers", 
            slug="integration-product-1'", buy_now_price="250.00", current_highest_bid="0", 
            retail_price="100.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="sold_out", bid_count=0, reserve_price="75.00", is_active=False)


        self.test_prod_two = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Integration Product 2", 
            secondary_product_title="Past Bid 2", description="Brand new sneakers", 
            slug="integration-product-2", buy_now_price="300.00", current_highest_bid="0", 
            retail_price="150.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="sold_out", bid_count=0, reserve_price="100.00", is_active=False)

        
        self.url = reverse('pop_accounts:past_bids')
    
    def test_real_bid_history_retrieval(self):
        """Test with real get_customer_bid_history_context function"""
        # Create past bids in order (lowest to highest per product)
        bid1 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('100.00'),
            is_active=True
        )
        bid1.is_active = False
        bid1.save(update_fields=['is_active'])
        
        bid2 = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_two,
            amount=Decimal('110.00'),
            is_active=True
        )
        bid2.is_active = False
        bid2.save(update_fields=['is_active'])
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify bid history is populated
        bid_history = response.context['bid_history']
        self.assertIsNotNone(bid_history)
        
        # Verify statistics are populated
        statistics = response.context['statistics']
        self.assertIsNotNone(statistics)
    
    def test_complete_bidding_lifecycle(self):
        """Test complete lifecycle: active bid -> closed bid -> past bids view"""
        # Create active bid
        bid = PopUpBid.objects.create(
            customer=self.user,
            product=self.test_prod_one,
            amount=Decimal('85.00'),
            is_active=True
        )
        
        # Close the bid (simulate auction ending)
        bid.is_active = False
        bid.save(update_fields=['is_active'])
        
        # View past bids
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        # Bid should appear in history
        bid_history = response.context['bid_history']

        # Structure depends on your get_customer_bid_history_context implementation
        self.assertIsNotNone(bid_history)


class PastPurchaseViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])

        

        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.test_prod_one = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Integration Product 1'", 
            secondary_product_title="Past Bid 1", description="Brand new sneakers", 
            slug="integration-product-1'", buy_now_price="250.00", current_highest_bid="0", 
            retail_price="100.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="75.00", is_active=True)
        

        self.address = create_test_address(customer=self.user, first_name="Test", last_name="User", 
                                           address_line="111 First", address_line2="", 
                                           apartment_suite_number="", town_city="City1", 
                                           state="California", postcode="11111", 
                                           delivery_instructions="Leave at the door", default=True, 
                                           is_default_shipping=False, is_default_billing=False)

        # def create_test_order(user, full_name, email, address1, postal_code, city, state, phone, total_paid, order_key):

        self.order = PopUpCustomerOrder.objects.create(
            user=self.user,
            email=self.user.email,
            billing_status=True,
            address1="111 Test St",
            city="New York",
            state="NY",
            postal_code="10001",
            total_paid="100.00"
        )

       

        # Add items to the order if your model supports it
        self.order_item = PopUpOrderItem.objects.create(
            order=self.order,
            product=self.test_prod_one,
            product_title="Test Product",
            quantity=1,
            price=100.00
        )

        self.url = reverse('pop_accounts:past_purchases')


    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)


    def test_authenticated_user_can_view_past_purchases(self):
        """Authenticated users should see their past purchase page."""
        
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "pop_accounts/user_accounts/dashboard_pages/past_purchases.html"
        )
        self.assertIn("orders", response.context)
        self.assertIn("user_past_purchase_copy", response.context)
        self.assertContains(response, "Past Purchases")
    

    def test_orders_are_filtered_by_logged_in_user(self):
        """Ensure only orders belonging to the logged-in user are displayed."""

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        orders = response.context["orders"]
        self.assertEqual(orders.count(), 1)
        self.assertEqual(orders.first().user, self.user)

    
    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated users should be redirected to login page."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.url)
    

    def test_context_contains_user_past_purchase_copy(self):
        """Check that the static page copy is correctly included in context."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertIn("user_past_purchase_copy", response.context)
        self.assertIsInstance(response.context["user_past_purchase_copy"], dict)


class TestUserOrdersUtility(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user('existing@example.com', 'testPass!23', 'Test', 'User', '9', 'male', is_active=False)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])

        self.other_user = create_test_user('existingTwo@example.com', 'testPassTwo!23', 'Testi', 'Usera', '6', 'female', is_active=False)
        self.other_user.is_active = True
        self.other_user.save(update_fields=['is_active'])        

        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.test_prod_one = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Past Bid Product 1", 
            secondary_product_title="Past Bid 1", description="Brand new sneakers", 
            slug="past-bid-product-1", buy_now_price="250.00", current_highest_bid="0", 
            retail_price="150.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="sold_out", bid_count=0, reserve_price="100.00", is_active=False)


        self.test_prod_two = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Past Bid Product 2", 
            secondary_product_title="Past Bid 2", description="Brand new sneakers", 
            slug="past-bid-product-2", buy_now_price="300.00", current_highest_bid="0", 
            retail_price="200.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="sold_out", bid_count=0, reserve_price="150.00", is_active=False)

        self.test_prod_three = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Jordan 11 Retro", 
            secondary_product_title="Concord", description="Brand new Jordan 11", 
            slug="jordan-11-concord", buy_now_price="350.00", current_highest_bid="0", 
            retail_price="200.00", brand=test_brand, auction_start_date=None,  auction_end_date=None, 
            inventory_status="in_inventory", bid_count=0, reserve_price="225.00", is_active="False")

        # Orders for the main user
        self.completed_order = PopUpCustomerOrder.objects.create(
            user=self.user,
            email=self.user.email,
            billing_status=True,
            address1="111 Test St",
            city="New York",
            state="NY",
            postal_code="10001",
            total_paid="100.00"
        )


        self.incompleted_order = PopUpCustomerOrder.objects.create(
            user=self.user,
            email=self.user.email,
            billing_status=False,
            address1="111 Test St",
            city="Chicago",
            state="IL",
            postal_code="60601",
            total_paid="110.00"
        )

        self.other_user_order = PopUpCustomerOrder.objects.create(
            user=self.other_user,
            email=self.other_user.email,
            billing_status=True,
            address1="111 Test St",
            city="Chicago",
            state="IL",
            postal_code="60601",
            total_paid="110.00"
        )


        # Add items to the order if your model supports it
        self.order_item = PopUpOrderItem.objects.create(
            order=self.completed_order,
            product=self.test_prod_one,
            product_title="Test Product",
            quantity=1,
            price=100.00
        )
    
    def test_returns_only_completed_orders_for_user(self):
        """Should only return orders with billing_status=True for the user."""
        self.client.force_login(self.user)
        orders = user_orders(self.user.id)
        self.assertEqual(orders.count(), 1)
        self.assertEqual(orders.first(), self.completed_order)


    def test_does_not_return_other_users_orders(self):
        """Ensure the utility does not leak other users' data."""
        self.client.force_login(self.user)
        orders = user_orders(self.user.id)
        user_ids = [o.user_id for o in orders]
        self.assertNotIn(self.other_user.id, user_ids)
    

    def test_prefetch_related_items_are_accessible(self):
        """The returned orders should have pre-fetched items for performance."""
        self.client.force_login(self.user)
        orders = user_orders(self.user.id)
        order = orders.first()
        with self.assertNumQueries(0):  # Ensures prefetch_related works
            _ = list(order.items.all())


# class EmailCheckViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.url = reverse('pop_accounts:check_email')

        # # create an existing user
        # self.existing_email = 'existing@example.com'
        # self.user = PopUpCustomer.objects.create_user(
        #     email = self.existing_email,
        #     password = 'testPass!23',
        #     first_name = 'Test',
        #     last_name = 'User'
        # )
    
    # def test_existing_email(self):
    #     response = self.client.post(self.url, {'email': self.existing_email})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertJSONEqual(response.content, {'status': False})
    #     self.assertEqual(self.client.session['auth_email'], self.existing_email)
    
#     def test_new_mail(self):
#         new_mail = 'newuser@example.com'
#         response = self.client.post(self.url, {'email': new_mail})
#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(response.content, {'status': True})
#         self.assertNotIn('auth_email', self.client.session)
    
#     def test_invalid_email(self):
#         response = self.client.post(self.url, {'email': 'noteanemail'})
#         self.assertEqual(response.status_code, 400)
#         self.assertJSONEqual(response.content, {'status': False, 'error': 'Invalid or missing email'})
    
#     def test_missing_email(self):
#         response = self.client.post(self.url, {})
#         self.assertEqual(response.status_code, 400)
#         self.assertJSONEqual(response.content, {'status': False, 'error': 'Invalid or missing email'})



# class Login2FAViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.url = reverse('pop_accounts:user_login')
#         self.email = 'testuser@example.com'
#         self.password = 'strongPassword!'
#         self.user = PopUpCustomer.objects.create_user(
#             email = self.email,
#             password = self.password,
#             first_name = 'Test',
#             last_name = 'User'
#         )
#         self.client.session['auth_email'] = self.email
#         self.client.session.save()
    
#     @patch('pop_accounts.views.send_mail')
#     def test_successful_login_sends_2fa_code(self, mock_send_mail):
#         session = self.client.session
     
#         session['auth_email'] = self.email
#         session.save()

#         response = self.client.post(self.url, {'password': self.password})

#         code = self.client.session['2fa_code']

#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(response.content, {'authenticated': True, '2fa_required': True})

#         self.assertIn('2fa_code', self.client.session)
#         self.assertEqual(self.client.session['pending_login_user_id'], str(self.user.id))
#         self.assertTrue(code.isdigit() and len(code) == 6)
#         self.assertTrue(mock_send_mail.called)

    
#     def test_failed_login_increments_attempts(self):
#         for i in range(1, 3):
#             response = self.client.post(self.url, {'password': 'wrongpass'})
#             self.assertEqual(response.status_code, 401)
#             self.assertIn(f'Attempt {i}/5', response.json()['error'])
        
#     def test_lockout_after_max_attempts(self):
#         for _ in range(5):
#             self.client.post(self.url, {'password': 'wrongpass'})
        
#         response = self.client.post(self.url, {'password': 'wrongpass'})
#         self.assertEqual(response.status_code, 403)
#         self.assertTrue(response.json()['locked_out'])
    
#     def test_locked_out_if_within_lockout_period(self):
#         session = self.client.session
#         session['locked_until'] = (now() + timedelta(minutes=10)).isoformat()
#         session.save()
#         response = self.client.post(self.url, {'password': 'wrongpass'})
#         self.assertEqual(response.status_code, 429)
#         self.assertEqual(response.json()['error'], 'Locked out')


#     def test_lockout_resets_after_time_passes(self):
#         session = self.client.session
#         session['login_attempts'] = 5
#         session['first_attempt_times'] = (now() - timedelta(minutes=16)).isoformat()
#         session.save()
#         response = self.client.post(self.url, {'password': 'wrongpass'})
#         self.assertEqual(response.status_code, 401)
#         self.assertIn('Attempt 1/5', response.json()['error'])



# class Verify2FACodeViewTests(TestCase):
#     def setUp(self):
#         self.user = PopUpCustomer.objects.create_user(
#             email='test@example.com',
#             password='securepassword!23',
#             first_name='Test',
#             last_name='User'
#         )

#         self.url = reverse('pop_accounts:verify_2fa')
#         self.code = '123456'
#         self.session = self.client.session
#         self.session['2fa_code'] = self.code
#         self.session['2fa_code_created_at'] = timezone.now().isoformat()
#         self.session['pending_login_user_id'] = str(self.user.id)
#         self.session.save()
    
#     def test_successful_verification(self):
#         response = self.client.post(self.url, {'code': self.code})
#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(response.content, {'verified': True, 'user_name': self.user.first_name})
    

#     def test_invalid_code(self):
#         response = self.client.post(self.url, {'code': '000000'})
#         self.assertEqual(response.status_code, 400)
#         self.assertJSONEqual(response.content, {'verified': False, 'error': 'Invalid Code'})
    
#     def test_expired_code(self):
#         self.session['2fa_code_created_at'] = (timezone.now() - timedelta(minutes=6)).isoformat()
#         self.session.save()
#         response = self.client.post(self.url, {'code': self.code})
#         self.assertEqual(response.status_code, 400)
#         self.assertJSONEqual(response.content, {'verified': False, 'error': 'Verification code has expired'})
    

#     def test_missing_session_data(self):
#         self.client.session.flush() # clears session
#         response = self.client.post(self.url, {'code': self.code})
#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(response.content, {'verified': False, 'error': 'Session expired or invalid'})
    
#     def test_invalid_timestamp(self):
#         self.session['2fa_code_created_at'] = 'not-a-valid-timestamp'
#         self.session.save()
#         response = self.client.post(self.url, {'code': self.code})
#         self.assertEqual(response.status_code, 400)
#         self.assertJSONEqual(response.content, {'verified': False, 'error': 'Invalid timestamp format'})
    

#     def test_user_not_found(self):
#         self.session['pending_login_user_id'] = str(uuid4())
#         self.session.save()
#         response = self.client.post(self.url, {'code': self.code})
#         self.assertEqual(response.status_code, 404)
#         self.assertJSONEqual(response.content, {'verified': False, 'error': 'User not found'})
    

#     def test_csrf_rejected_when_token_missing(self):
#         factory = RequestFactory()
#         request = factory.post(self.url, {'code': self.code})

#         # Attach user and session manually if needed
#         request.user = self.user
#         request.session = self.client.session

#         # Create CSRF middleware with dummy get_response
#         middleware = CsrfViewMiddleware(lambda req: None)

#         # Define a dummy view that requires CSRF
#         @csrf_protect
#         def dummy_view(req):
#             return JsonResponse({'ok': True})

#         # Run the middleware manually
#         response = middleware.process_view(request, dummy_view, (), {})

#         if response is None:
#             response = dummy_view(request)

#         self.assertEqual(response.status_code, 403)
    
#     def test_missing_ajax_header(self):
#         response = self.client.post(self.url, {'code': self.code}, HTTP_X_REQUESTED_WITH='')
#         self.assertEqual(response.status_code, 200)



# class RegisterViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.url = reverse('pop_accounts:register')
    
#     def test_valid_registration_sends_verification_email(self):
#         response = self.client.post(self.url, {
#             'email': 'test@example.com',
#             'first_name': 'John',
#             'password': 'securePassword!23',
#             'password2': 'securePassword!23',

#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertJSONEqual(response.content, {
#             'registered': True,
#             'message': 'Check your email to confirm your account'
#         })

#         user = PopUpCustomer.objects.get(email='test@example.com')
#         self.assertFalse(user.is_active)
#         self.assertEqual(len(mail.outbox), 1)
#         self.assertIn('Verify Your Email', mail.outbox[0].subject)
    
#     def test_registration_with_mismatched_passwords(self):
#         response = self.client.post(self.url, {
#             'email': 'test@example.com',
#             'first_name': 'Jane',
#             'password': 'password!23',
#             'password2': 'differentPassword!'
#         })

#         self.assertEqual(response.status_code, 400)
#         self.assertIn('errors', response.json())
#         self.assertFalse(PopUpCustomer.objects.filter(email='test@example.com').exists())
    

#     def test_registration_bad_password_strength(self):
#         response = self.client.post(self.url, {
#             'email': 'test@example.com',
#             'first_name': 'Jane',
#             'password': 'password123',
#             'password2': 'password123!'
#         })

#         self.assertEqual(response.status_code, 400)
    

#     def test_missing_required_fields(self):
#         response = self.client.post(self.url, {
#             'email': '',
#             'first_name': '',
#             'password': '',
#             'password2': ''
#         })
#         self.assertEqual(response.status_code, 400)
#         self.assertIn('errors', response.json())
    

#     def test_registration_fails_without_password2(self):
#         response = self.client.post(self.url, {
#             'email': 'missing@example.com',
#             'first_name': 'Sam',
#             'password': 'somePassword'
#         })
#         self.assertEqual(response.status_code, 400)
#         self.assertIn('errors', response.json())


# class PasswordStrengthValidationTests(TestCase):

#     def test_valid_password(self):
#         try:
#             validate_password_strength('StrongPass1!')
#         except ValidationError:
#             self.fail('validate_password_strength() raised ValidationError unexpectedly!')

#     def test_password_too_short(self):
#         with self.assertRaisesMessage(ValidationError, "Password must be at least 8 characters long."):
#             validate_password_strength('S1!a')

#     def test_missing_uppercase(self):
#         with self.assertRaisesMessage(ValidationError, "Password must contain at least one uppercase letter."):
#             validate_password_strength('weakpass1!')

#     def test_missing_lowercase(self):
#         with self.assertRaisesMessage(ValidationError, "Password must contain at least one lower case letter"):
#             validate_password_strength('WEAKPASS1!')

#     def test_missing_digit(self):
#         with self.assertRaisesMessage(ValidationError, "Password must contain at lease one number."):
#             validate_password_strength('Weakpass!')

#     def test_missing_special_char(self):
#         with self.assertRaisesMessage(
#             ValidationError,
#             'Password must contain at least one special character (!@#$%^&*(),.?":|<>)'
#         ):
#             validate_password_strength('Weakpass1')


# class MarkProductInterestedViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = PopUpCustomer.objects.create_user(
#             email="testuser@example.com",
#             password="securePassword!23",
#             first_name="Test",
#             last_name="User",
#             shoe_size="10",
#             size_gender="male"
#         )

#         self.brand = PopUpBrand.objects.create(
#             name="Staries",
#             slug="staries"
#         )
#         self.categories = PopUpCategory.objects.create(
#             name="Jordan 3",
#             slug="jordan-3",
#             is_active=True
#         )
#         self.product_type = PopUpProductType.objects.create(
#             name="shoe",
#             slug="shoe",
#             is_active=True
#         )

#         now = timezone.now()
#         self.product = PopUpProduct.objects.create(
#             # id=uuid.uuid4(),
#             product_type=self.product_type,
#             category=self.categories,
#             product_title="Test Sneaker",
#             secondary_product_title = "Exclusive Drop",
#             description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
#             slug="test-sneaker-exclusive-drop", 
#             buy_now_price="150.00", 
#             current_highest_bid="0", 
#             retail_price="100", 
#             brand=self.brand, 
#             auction_start_date=now + timedelta(days=5), 
#             auction_end_date=now + timedelta(days=10), 
#             inventory_status="In Inventory", 
#             bid_count="0", 
#             reserve_price="0", 
#             is_active=True
#         )
#         self.url = reverse('pop_accounts:mark_interested')

    
#     def test_authenticated_user_can_mark_product_interested(self):
#         self.client.login(email="testuser@example.com", password="securePassword!23")
#         response = self.client.post(
#             self.url,
#             data={"product_id": str(self.product.id)},
#             content_type = "application/json"
#         )
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json()["status"], "added")
#         self.assertIn(self.product, self.user.prods_interested_in.all())
    

#     def test_unathenticated_user_redirected(self):
#         response = self.client.post(
#             self.url, data={'product_id': str(self.product.id)}, content_type='application/json'
#         )

#         # Should redirect to home page
#         self.assertEqual(response.status_code, 302)
#         self.assertTrue(response.url.startswith('/'))
    
    
#     def test_product_does_not_exist(self):
#         self.client.login(email='testuser@example.com', password='securePassword!23')
#         invalid_id = 999999
#         response = self.client.post(
#             self.url, data={'product_id': str(invalid_id)},
#             content_type='application/json'
#         )
#         self.assertEqual(response.status_code, 404)
#         self.assertEqual(response.json()['status'], 'error')



# class MarkProductOnNoticeViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = PopUpCustomer.objects.create_user(
#             email="testuser@example.com",
#             password="securePassword!23",
#             first_name="Test",
#             last_name="User",
#             shoe_size="10",
#             size_gender="male"
#         )

#         self.brand = PopUpBrand.objects.create(
#             name="Staries",
#             slug="staries"
#         )
#         self.categories = PopUpCategory.objects.create(
#             name="Jordan 3",
#             slug="jordan-3",
#             is_active=True
#         )
#         self.product_type = PopUpProductType.objects.create(
#             name="shoe",
#             slug="shoe",
#             is_active=True
#         )

#         now = timezone.now()
#         self.product = PopUpProduct.objects.create(
#             product_type=self.product_type,
#             category=self.categories,
#             product_title="Test Sneaker",
#             secondary_product_title = "Exclusive Drop",
#             description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
#             slug="test-sneaker-exclusive-drop", 
#             buy_now_price="150.00", 
#             current_highest_bid="0", 
#             retail_price="100", 
#             brand=self.brand, 
#             auction_start_date=now + timedelta(days=5), 
#             auction_end_date=now + timedelta(days=10), 
#             inventory_status="In Inventory", 
#             bid_count="0", 
#             reserve_price="0", 
#             is_active=True
#         )
#         self.url = reverse('pop_accounts:mark_on_notice')

    
#     def test_authenticated_user_can_mark_product_on_notice(self):
#         self.client.login(email="testuser@example.com", password="securePassword!23")
#         response = self.client.post(
#             self.url,
#             data={"product_id": str(self.product.id)},
#             content_type = "application/json"
#         )
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json()["status"], "added")
#         self.assertIn(self.product, self.user.prods_on_notice_for.all())
    

# class ProductBuyViewGETTests(TestCase):
        
#     # test correct user displayed
#     def setUp(self):
#         self.client = Client()
#         self.user = create_test_user(email="testuser@example.com",
#             password="securePassword!23",
#             first_name="Test",
#             last_name="User",
#             shoe_size="10",
#             size_gender="male")
        
#         auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
#         auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
#         self.brand = create_brand("Jordan")
#         self.category = create_category("Jordan 3", True)
#         self.product_type = create_product_type("shoe", True)

   
        
#         self.product = create_test_product(
#             product_type=self.product_type, 
#             category=self.category, 
#             product_title="Air Jordan 1 Retro", 
#             secondary_product_title="Carolina Blue", 
#             description="The most uncomfortable basketball shoe their is", 
#             slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
#             buy_now_price="150.00", 
#             current_highest_bid="0", 
#             retail_price="100", 
#             brand=self.brand, 
#             auction_start_date=auction_start, 
#             auction_end_date=auction_end, 
#             inventory_status="in_inventory", 
#             bid_count="0", 
#             reserve_price="0", 
#             is_active=True)
        
#         self.client.login(email="testuser@example.com", password="securePassword!23")
        
#         request = self.client.get('/dummy/')
#         request = request.wsgi_request

#         cart = Cart(request)

#         cart.add(product=self.product, qty=1)

#         # Save the cart back to the test client's session
#         session = self.client.session
#         session.update(request.session)
#         session.save()
    

#         # Create Address for user
#         self.address = PopUpCustomerAddress.objects.create(
#             customer = self.user,
#             address_line = "123 Main St",
#             apartment_suite_number = "1A",
#             town_city = "New York",
#             state = "NY",
#             postcode="10001",
#             delivery_instructions="Leave with doorman",
#             default=True
#         )

#         self.tax_rate = get_state_tax_rate("NY")
#         self.standard_shipping = Decimal('14.99')
#         self.processing_fee = Decimal('2.50')


#     def test_user_is_correct_in_view(self):
#         self.assertEqual(self.user.first_name, "Test")
#         self.assertEqual(self.user.last_name, "User")
    

#     def test_product_buy_view_get_correct_tax_rate_applied(self):
#         self.assertEqual(get_state_tax_rate("NY"), 0.08375)
#         self.assertEqual(get_state_tax_rate("FL"), 0.0)
#         self.assertEqual(get_state_tax_rate("CA"), 0.095)
#         self.assertEqual(get_state_tax_rate("GA"), 0.07)
#         self.assertEqual(get_state_tax_rate("TX"), 0.0625)
#         self.assertEqual(get_state_tax_rate("IL"), 0.0886)
        

#     def test_product_buy_view_get_basic_cart_data(self):
#         response = self.client.get(reverse('pop_up_auction:product_buy'))
#         self.assertEqual(response.status_code, 200)

#         context = response.context
#         cart_items = context['cart_items']

#         self.assertEqual(len(cart_items), 1)

#         self.assertEqual(cart_items[0]['qty'], 1)
#         self.assertEqual(cart_items[0]['product'], self.product)
#         self.assertIn('cart_total', context)
#         self.assertIn('sales_tax', context)

        
#         # Test tax rate and tax calculation
#         expected_subtotal = Decimal(self.product.buy_now_price)
#         expected_tax = expected_subtotal * Decimal(self.tax_rate)
#         self.assertEqual(Decimal(context['sales_tax']), expected_tax.quantize(Decimal('0.01')))

#         # Test grand total calcuation
#         expected_grand_total = expected_subtotal + expected_tax + (self.standard_shipping  * len(cart_items)) + self.processing_fee
#         self.assertEqual(Decimal(context['grand_total']), expected_grand_total.quantize(Decimal('0.01')))
    


#     def test_selected_address_used_if_exists(self):
#         # Simulate address selected in session
#         session = self.client.session
#         session['selected_address_id'] = str(self.address.id)
#         session.save()

#         response = self.client.get(reverse('pop_up_auction:product_buy'))
#         self.assertEqual(response.context['selected_address'], self.address)
#         self.assertEqual(response.context['address_form'].instance, self.address)
    
    

#     def _login_and_seed_cart(self, qty: int = 1):
#         """Log the test client in and drop one product in to the Cart session"""
#         self.client.login(email=self.user.email, password=self.user.password)

#         # make a cart entry directly into the session
#         session = self.client.session
#         session['cart'] = {str(self.product.id): {'qty': qty, 'price': str(self.product.buy_now_price)}}
#         session.save()
    
#     def test_product_buy_view_get_selected_address_displayed(self):
#         """
#         If we stuff selected_address_id into session, the view shoudl surface that exact PopUpCustomerAddress
#         instance via context['selected_address']
#         """
#         self._login_and_seed_cart()

#         # store chosen address ID in session
#         session = self.client.session
#         session['selected_address_id'] = str(self.address.id)
#         session.save()

#         response = self.client.get(reverse('pop_up_auction:product_buy'))
#         self.assertEqual(response.status_code, 200)

#         # the view should echo back exactly *that* address as selected
#         self.assertIn('selected_address', response.context)
#         self.assertEqual(response.context['selected_address'], self.address)


#     def test_product_buy_view_get_cart_totals_correct(self):
#         """
#         Verify subtotal, sales-tax, shipping and grand-total calculations
#         for 1 item at $150 (NY tax ≈ 8.375 %), $14.99 std shipping & $2.50 fee.
#         """
#         self._login_and_seed_cart()          # qty = 1
#         # store chosen address ID in session
#         session = self.client.session
#         session['selected_address_id'] = str(self.address.id)
#         session.save()

#         response = self.client.get(reverse('pop_up_auction:product_buy'))
#         self.assertEqual(response.status_code, 200)

#         # the view should echo back exactly *that* address as selected
#         self.assertIn('selected_address', response.context)
#         self.assertEqual(response.context['selected_address'], self.address)

    
#     def test_product_buy_view_get_cart_totals_correct(self):
#         """
#         Verify subtotal, sales-tax, shipping and grand-total calculations
#         for 1 item at $150 (NY tax ≈ 8.375 %), $14.99 std shipping & $2.50 fee.
#         """
#         self._login_and_seed_cart()          # qty = 1

#         response = self.client.get(reverse('pop_up_auction:product_buy'))
#         ctx      = response.context

#         # --- compute what we EXPECT -----------------
#         subtotal        = Decimal('150.00')
#         tax_rate        = Decimal(str(get_state_tax_rate('New York')))
#         expected_tax    = (subtotal * tax_rate).quantize(Decimal('0.01'), ROUND_HALF_UP)

#         shipping        = Decimal('14.99')   # 1499/100 * qty(1)
#         processing_fee  = Decimal('2.50')

#         expected_total  = (subtotal + expected_tax + shipping + processing_fee).quantize(
#                               Decimal('0.01'), ROUND_HALF_UP)

#         # --- pull what the view produced -------------
#         view_subtotal   = ctx['cart_subtotal']
#         view_tax        = Decimal(ctx['sales_tax'])
#         view_total      = Decimal(ctx['grand_total'])

#         # --- assertions ------------------------------
#         self.assertEqual(view_subtotal, subtotal)
#         self.assertEqual(view_tax,      expected_tax)
#         self.assertEqual(view_total,    expected_total)
    

#     def test_invalid_selected_address_id_fails_gracefully(self):
#         self._login_and_seed_cart()
#         session = self.client.session
#         session["selected_address_id"] = "99999999-0000-0000-0000-000000000000"  # invalid UUID
#         session.save()

#         response = self.client.get(reverse("auction:product_buy"))
#         self.assertEqual(response.status_code, 200)
#         self.assertNotContains(response, "\n<h3>Shipping to</h3>\n")  # whatever text implies success


# class ProductBuyViewPOSTTests(TestCase):
#      # test correct user displayed
#     def setUp(self):
#         self.client = Client()
#         self.user = create_test_user(email="testuser@example.com",
#             password="securePassword!23",
#             first_name="Test",
#             last_name="User",
#             shoe_size="10",
#             size_gender="male")
        
#         auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
#         auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
#         self.brand = create_brand("Jordan")
#         self.category = create_category("Jordan 3", True)
#         self.product_type = create_product_type("shoe", True)


#         self.product = create_test_product(
#             product_type=self.product_type, 
#             category=self.category, 
#             product_title="Air Jordan 1 Retro", 
#             secondary_product_title="Carolina Blue", 
#             description="The most uncomfortable basketball shoe their is", 
#             slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
#             buy_now_price="150.00", 
#             current_highest_bid="0", 
#             retail_price="100", 
#             brand=self.brand, 
#             auction_start_date=auction_start, 
#             auction_end_date=auction_end, 
#             inventory_status="in_inventory", 
#             bid_count="0", 
#             reserve_price="0", 
#             is_active=True)
        
#         self.client.login(email="testuser@example.com", password="securePassword!23")
        
#         request = self.client.get('/dummy/')
#         request = request.wsgi_request

#         cart = Cart(request)

#         cart.add(product=self.product, qty=1)

#         # Save the cart back to the test client's session
#         session = self.client.session
#         session.update(request.session)
#         session.save()
    

#         # Create Address for user
#         self.address = PopUpCustomerAddress.objects.create(
#             customer = self.user,
#             address_line = "123 Main St",
#             apartment_suite_number = "1A",
#             town_city = "New York",
#             state = "NY",
#             postcode="10001",
#             delivery_instructions="Leave with doorman",
#             default=True
#         )

#         self.tax_rate = get_state_tax_rate("NY")
#         self.standard_shipping = Decimal('14.99')
#         self.processing_fee = Decimal('2.50')
    

#     def _login_and_seed_cart(self, qty: int = 1):
#         """Log the test client in and drop one product in to the Cart session"""
#         self.client.login(email=self.user.email, password=self.user.password)

#         # make a cart entry directly into the session
#         session = self.client.session
#         session['cart'] = {str(self.product.id): {'qty': qty, 'price': str(self.product.buy_now_price)}}
#         session.save()

#     def test_post_select_existing_address_sets_session(self):
#         self._login_and_seed_cart()
#         post_data = {"selected_address": str(self.address.id),}
#         response = self.client.post(reverse('pop_up_auction:product_buy'), post_data, follow=True)
#         session = self.client.session

#         self.assertEqual(response.status_code, 200)
#         self.assertIn('selected_address_id', session)
#         self.assertEqual(session['selected_address_id'], str(self.address.id))


#     def test_post_update_existing_address_success(self):
#         self._login_and_seed_cart()

#         updated_data = {
#             'address_id': self.address.id,
#             'prefix': 'Mr.',
#             'first_name': 'Updated',
#             'last_name': 'Name',
#             'address_line': '456 New Ave',
#             'apartment_suite_number': '2B',
#             'town_city': 'Brooklyn',
#             'state': 'New York',
#             'postcode': '11201',
#             'delivery_instructions': 'New instructions',
#         }

#         response = self.client.post(reverse('pop_up_auction:product_buy'), updated_data, follow=True)
#         self.address.refresh_from_db()
        
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(self.address.first_name, 'Updated')
#         self.assertContains(response, 'Address updated successfully.')
#         self.assertEqual(self.client.session['selected_address_id'], str(self.address.id))


#     def test_post_add_new_address_success(self):
#         self._login_and_seed_cart()

#         new_data = {
#             'prefix': 'Ms.',
#             'first_name': 'New',
#             'last_name': 'User',
#             'address_line': '789 Fresh St',
#             'apartment_suite_number': '3C',
#             'town_city': 'Queens',
#             'state': 'New York',
#             'postcode': '11375',
#             'delivery_instructions': 'Ring bell',
#         }

#         response = self.client.post(reverse('pop_up_auction:product_buy'), new_data, follow=True)

#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(PopUpCustomerAddress.objects.filter(first_name='New', customer=self.user).exists())

#         new_address = PopUpCustomerAddress.objects.get(first_name='New')
#         self.assertEqual(self.client.session['selected_address_id'], str(new_address.id))
#         self.assertContains(response, "Address added successfully")


#     def test_post_add_new_address_invalid_form(self):
#         self._login_and_seed_cart()

#         invalid_data = {
#             'first_name': '',  # Missing required fields
#             'last_name': '',
#             'postcode': '',
#         }

#         response = self.client.post(reverse('pop_up_auction:product_buy'), invalid_data)
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "Please correct the errors below.")


#     def test_product_not_in_inventory_skipped_in_cart(self):
#         self._login_and_seed_cart()

#         # Mark product as not in inventory
#         self.product.inventory_status = 'sold'
#         self.product.save()

#         response = self.client.get(reverse('pop_up_auction:product_buy'))
#         cart_items = response.context['cart_items']

#         self.assertEqual(len(cart_items), 0)


#     def test_cart_is_empty_grand_total_zero(self):
#         self.client.login(email='test@test.com', password='123Strong!')
#         session = self.client.session
#         session['cart'] = {}  # Empty cart
#         session.save()

#         response = self.client.get(reverse('pop_up_auction:product_buy'))

#         self.assertEqual(response.context['cart_total'], 0)
#         self.assertEqual(response.context['grand_total'], "0.00")


# class ProductBuyGuestTest(TestCase):

    
    
#     def setUp(self):
#         self.client = Client()

#         auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
#         auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
#         self.brand = create_brand("Jordan")
#         self.category = create_category("Jordan 3", True)
#         self.product_type = create_product_type("shoe", True)

#         # seed one product in session cart
#         self.product = create_test_product(
#             product_type=self.product_type, 
#             category=self.category, 
#             product_title="Air Jordan 1 Retro", 
#             secondary_product_title="Carolina Blue", 
#             description="The most uncomfortable basketball shoe their is", 
#             slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
#             buy_now_price="150.00", 
#             current_highest_bid="0", 
#             retail_price="100", 
#             brand=self.brand, 
#             auction_start_date=auction_start, 
#             auction_end_date=auction_end, 
#             inventory_status="in_inventory", 
#             bid_count="0", 
#             reserve_price="0", 
#             is_active=True
#         )

#         session = self.client.session
#         session['cart'] = {str(self.product.id) : {"qty": 1, "price": str(self.product.buy_now_price)}}
#         session.save()
    
#     def test_guest_sees_cart_summary_only(self):
#         resp = self.client.get(reverse('pop_up_auction:product_buy'))
#         self.assertEqual(resp.status_code, 200)

#         # Cart bits should be present
#         self.assertContains(resp, self.product.product_title)
#         self.assertContains(resp, "Subtotal")

#         self.assertNotContains(resp, "Shipping Address")
#         self.assertNotContains(resp, '<button>Sign in or create account to complete order.</button>')


# class ProductBuyAuthTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = create_test_user(email="testuser@example.com",
#             password="securePassword!23",
#             first_name="Test",
#             last_name="User",
#             shoe_size="10",
#             size_gender="male")
        
#         auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
#         auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
#         self.brand = create_brand("Jordan")
#         self.category = create_category("Jordan 3", True)
#         self.product_type = create_product_type("shoe", True)


#         self.product = create_test_product(
#             product_type=self.product_type, 
#             category=self.category, 
#             product_title="Air Jordan 1 Retro", 
#             secondary_product_title="Carolina Blue", 
#             description="The most uncomfortable basketball shoe their is", 
#             slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
#             buy_now_price="150.00", 
#             current_highest_bid="0", 
#             retail_price="100", 
#             brand=self.brand, 
#             auction_start_date=auction_start, 
#             auction_end_date=auction_end, 
#             inventory_status="in_inventory", 
#             bid_count="0", 
#             reserve_price="0", 
#             is_active=True)
        
#         # Create Address for user
#         self.address = PopUpCustomerAddress.objects.create(
#             customer = self.user,
#             address_line = "123 Main St",
#             apartment_suite_number = "1A",
#             town_city = "New York",
#             state = "NY",
#             postcode="10001",
#             delivery_instructions="Leave with doorman",
#             default=True
#         )

#         self.client.login(email="testuser@example.com", password="securePassword!23")

#         # seed cart
#         session = self.client.session
#         session['cart'] = {str(self.product.id) : {"qty": 1, "price": str(self.product.buy_now_price)}}
#         session.save()
    
    
#     def test_authenticated_sees_checkout_controls(self):
#         resp = self.client.get(reverse("auction:product_buy"))
#         self.assertEqual(resp.status_code, 200)
#         self.assertContains(resp, "Shipping Choice")
#         self.assertContains(resp, self.address.address_line)
#         # self.assertContains(resp, "<button>\n<i class=\'bx bxl-apple\'></i>Pay\n</button>\n")
    

#     def test_empty_cart_totals_zero_for_guest(self):
#         resp = self.client.get(reverse("auction:product_buy"))
#         self.assertContains(resp, "$0.00")
    

#     def test_no_default_address_guest_graceful(self):
#         # user with no addresses (or guest) should not 500:
#         resp = self.client.get(reverse("auction:product_buy"))
#         self.assertEqual(resp.status_code, 200)





    # test cart items ✅
    # test ids_in_cart ✅
    # test number of cart items ✅
    # test shipping to address
    # test saved_address, test default_adderess, test addres_form
    # test if session seelcted_addres_id exists
    # test change to shipping address 
    # test cart total | cart.get_total_price()
    # test getting user_state
    # test correct tax_rate
    # test grand_total
    # test product filtering, is_active, and inventory_statys ="in_inventory" should be in cart
    # test enriched_cart
    # test shipping_cost
    # test Anonymous access behavior
    # test Product filtering logic
    # test Empty cart handling
    # test Handling of invalid/missing addresses
    # test Correct form rendering on failed POST
    # test Session logic behavior

    # POST stuff
    # test selected_add_id valid
    # test selected_address_id invalid
    # user updates existing address
    # test user adds new address

    # Edge Case Test
    # empty cart
    # no default or selected address
    # invalid session address Id
    # products missing ni db
    

    # """
    # Run Test
    # python3 manage.py test pop_accounts/tests
    # python3 manage.py test pop_accounts.tests.test_views.PersonalInfoViewIntegrationTests
    # Run Test with Coverage
    # coverage run --omit='*/venv/*' manage.py test pop_accounts/tests 
    # """


"""
# Debug output
# print(f"Response status: {response.status_code}")
# print(f"Form data sent: {form_data}")

# # Check if it's being detected as address form
# view = PersonalInfoView()
# view.request = response.wsgi_request
# print(f"Detected as address form: {view._is_address_form_submission()}")

# if response.status_code == 200:
#     print("Form didn't redirect - checking for validation errors")
#     if hasattr(response, 'context') and 'address_form' in response.context:
#         address_form = response.context['address_form']
#         if hasattr(address_form, 'errors'):
#             print(f"Address form errors: {address_form.errors}")

# print(f"Response content preview: {response.content.decode()[:500]}")

# Debug output
# print(f"Response status: {response.status_code}")
# print(f"Is personal form: {response.wsgi_request.POST}")
# print(f"response.content: {response.content.decode()[:500]}")

# if hasattr(response, 'context') and response.context:
#     form = response.context.get('form')
#     if form and hasattr(form, 'errors'):
#         print(f"Form errors: {form.errors}")
"""