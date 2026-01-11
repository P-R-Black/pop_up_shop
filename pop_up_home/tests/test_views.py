from unittest import skip
from django.conf import settings
from importlib import import_module
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from pop_accounts.models import PopUpCustomerProfile
from django.http import HttpRequest
from pop_up_home.views import home_page
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

class TestPopUpHomeViewResponses(TestCase):
    def setUp(self):
        self.c = Client()
        self.user, self.user_profile = create_test_user(
            "testuser@example.com", "securePassword!23", "Test", "User", "10", "male"
        )

    def test_url_allowed_hosts(self):
        """
        Test homepage response status
        """
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
    

    def test_homepage_html(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertTrue(html.startswith('\n<!DOCTYPE html>\n'))
        self.assertIn('<title>Home</title>', html)

    def test_homepage_html_authenticated(self):
        self.c.login(email="testuser@example.com", password="securePassword!23")
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn('<title>Home</title>', html)
    
    
    def test_about_us_html(self):
        response = self.c.get('/about/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>About Us</title>', html)

        # quick test of the copy
        self.assertIn('<h2>About The Pop Up</h2>', html)


    def test_how_it_works_html(self):
        response = self.c.get('/how-it-works/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>How it Works</title>', html)

        # quick test of the copy
        self.assertIn('<h2>How it Works</h2>', html)


    def test_verification_html(self):
        response = self.c.get('/verification/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Verification</title>', html)

        # quick test of the copy
        self.assertIn('<h2>Verification</h2>', html)
    

    def test_contact_us_html(self):
        response = self.c.get('/contact/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Contact Us</title>', html)

        # quick test of the copy
        self.assertIn('<h2>Contact Us</h2>', html)
    

    def test_help_center_html(self):
        response = self.c.get('/help-center/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Help Center</title>', html)

        # quick test of the copy
        self.assertIn('<h2>Help Center</h2>', html)


    def test_terms_and_conditions_html(self):
        response = self.c.get('/terms/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Terms and Conditions</title>', html)

        # quick test of the copy
        self.assertIn('<h2>Terms and Conditions</h2>', html)
    

    def test_privacy_policy_html(self):
        response = self.c.get('/privacy/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Privacy Policy</title>', html)

        # quick test of the copy
        self.assertIn('<h2>The Pop Up Privacy Policy</h2>', html)
    

    def test_privacy_choices_html(self):
        response = self.c.get('/privacy-choices/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Privacy Choices</title>', html)

        # quick test of the copy
        self.assertIn('<h2>Your Privacy Choices</h2>', html)
    

    def test_buying_help_html(self):
        response = self.c.get('/buying-help/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Buying Help</title>', html)

        # small test of the copy
        self.assertIn('<h2>Buying</h2>', html)



    def test_selling_help_html(self):
        response = self.c.get('/selling-help/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Selling Help</title>', html)

        # small test of the copy
        self.assertIn('<h2>Selling</h2>', html)



    def test_account_help_html(self):
        response = self.c.get('/account-help/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Account Help</title>', html)

        # small test of the copy
        self.assertIn('<h2>My Account</h2>', html)
    

    def test_shipping_help_html(self):
        response = self.c.get('/shipping-help/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Shipping and Tracking Help</title>', html)

        # small test of the copy
        self.assertIn('<h2>Shipping and Tracking</h2>', html)


    def test_payment_help_html(self):
        response = self.c.get('/payment-help/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Payment Help</title>', html)

        # small test of the copy
        self.assertIn('<h2>Payment Options</h2>', html)


    def test_fees_help_html(self):
        response = self.c.get('/fees-help/')
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')
        self.assertIn('<title>Fees Help</title>', html)

        # small test of the copy
        self.assertIn('<h2>Fees</h2>', html)




    





# """
# Run Test
# python3 manage.py test pop_up_home/tests
# Run Test with Coverage
# coverage run --omit='*/venv/*' manage.py test pop_up_home/tests
# """