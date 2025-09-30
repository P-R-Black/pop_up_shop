from django.test import TestCase, Client, override_settings
from django.urls import reverse
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress, PopUpBid
from pop_up_payment.utils.tax_utils import get_state_tax_rate
from pop_up_auction.models import PopUpProduct,PopUpBrand, PopUpCategory, PopUpProductType
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


def create_test_user(email, password, first_name, last_name, shoe_size, size_gender,**kwargs):
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
                        auction_end_date, inventory_status, bid_count, reserve_price, is_active
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