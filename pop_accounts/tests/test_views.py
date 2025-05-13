from django.test import TestCase, Client
from django.urls import reverse
from pop_accounts.models import PopUpCustomer
from auction.models import PopUpProduct,PopUpBrand, PopUpCategory, PopUpProductType
from unittest.mock import patch
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from uuid import uuid4
from django.middleware.csrf import CsrfViewMiddleware
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_protect
from django.test import RequestFactory
from django.http import JsonResponse
from django.core import mail
from pop_accounts.utils import validate_password_strength
from django.core.exceptions import ValidationError

class EmailCheckViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('pop_accounts:check_email')

        # create an existing user
        self.existing_email = 'existing@example.com'
        self.user = PopUpCustomer.objects.create_user(
            email = self.existing_email,
            password = 'testPass!23',
            first_name = 'Test',
            last_name = 'User'
        )
    
    def test_existing_email(self):
        response = self.client.post(self.url, {'email': self.existing_email})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': False})
        self.assertEqual(self.client.session['auth_email'], self.existing_email)
    
    def test_new_mail(self):
        new_mail = 'newuser@example.com'
        response = self.client.post(self.url, {'email': new_mail})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': True})
        self.assertNotIn('auth_email', self.client.session)
    
    def test_invalid_email(self):
        response = self.client.post(self.url, {'email': 'noteanemail'})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': False, 'error': 'Invalid or missing email'})
    
    def test_missing_email(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': False, 'error': 'Invalid or missing email'})



class Login2FAViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('pop_accounts:user_login')
        self.email = 'testuser@example.com'
        self.password = 'strongPassword!'
        self.user = PopUpCustomer.objects.create_user(
            email = self.email,
            password = self.password,
            first_name = 'Test',
            last_name = 'User'
        )
        self.client.session['auth_email'] = self.email
        self.client.session.save()
    
    @patch('pop_accounts.views.send_mail')
    def test_successful_login_sends_2fa_code(self, mock_send_mail):
        session = self.client.session
     
        session['auth_email'] = self.email
        session.save()

        response = self.client.post(self.url, {'password': self.password})

        code = self.client.session['2fa_code']

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'authenticated': True, '2fa_required': True})

        self.assertIn('2fa_code', self.client.session)
        self.assertEqual(self.client.session['pending_login_user_id'], str(self.user.id))
        self.assertTrue(code.isdigit() and len(code) == 6)
        self.assertTrue(mock_send_mail.called)

    
    def test_failed_login_increments_attempts(self):
        for i in range(1, 3):
            response = self.client.post(self.url, {'password': 'wrongpass'})
            self.assertEqual(response.status_code, 401)
            self.assertIn(f'Attempt {i}/5', response.json()['error'])
        
    def test_lockout_after_max_attempts(self):
        for _ in range(5):
            self.client.post(self.url, {'password': 'wrongpass'})
        
        response = self.client.post(self.url, {'password': 'wrongpass'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.json()['locked_out'])
    
    def test_locked_out_if_within_lockout_period(self):
        session = self.client.session
        session['locked_until'] = (now() + timedelta(minutes=10)).isoformat()
        session.save()
        response = self.client.post(self.url, {'password': 'wrongpass'})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()['error'], 'Locked out')


    def test_lockout_resets_after_time_passes(self):
        session = self.client.session
        session['login_attempts'] = 5
        session['first_attempt_times'] = (now() - timedelta(minutes=16)).isoformat()
        session.save()
        response = self.client.post(self.url, {'password': 'wrongpass'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('Attempt 1/5', response.json()['error'])



class Verify2FACodeViewTests(TestCase):
    def setUp(self):
        self.user = PopUpCustomer.objects.create_user(
            email='test@example.com',
            password='securepassword!23',
            first_name='Test',
            last_name='User'
        )

        self.url = reverse('pop_accounts:verify_2fa')
        self.code = '123456'
        self.session = self.client.session
        self.session['2fa_code'] = self.code
        self.session['2fa_code_created_at'] = timezone.now().isoformat()
        self.session['pending_login_user_id'] = str(self.user.id)
        self.session.save()
    
    def test_successful_verification(self):
        response = self.client.post(self.url, {'code': self.code})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'verified': True, 'user_name': self.user.first_name})
    

    def test_invalid_code(self):
        response = self.client.post(self.url, {'code': '000000'})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'verified': False, 'error': 'Invalid Code'})
    
    def test_expired_code(self):
        self.session['2fa_code_created_at'] = (timezone.now() - timedelta(minutes=6)).isoformat()
        self.session.save()
        response = self.client.post(self.url, {'code': self.code})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'verified': False, 'error': 'Verification code has expired'})
    

    def test_missing_session_data(self):
        self.client.session.flush() # clears session
        response = self.client.post(self.url, {'code': self.code})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'verified': False, 'error': 'Session expired or invalid'})
    
    def test_invalid_timestamp(self):
        self.session['2fa_code_created_at'] = 'not-a-valid-timestamp'
        self.session.save()
        response = self.client.post(self.url, {'code': self.code})
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'verified': False, 'error': 'Invalid timestamp format'})
    

    def test_user_not_found(self):
        self.session['pending_login_user_id'] = str(uuid4())
        self.session.save()
        response = self.client.post(self.url, {'code': self.code})
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content, {'verified': False, 'error': 'User not found'})
    

    def test_csrf_rejected_when_token_missing(self):
        factory = RequestFactory()
        request = factory.post(self.url, {'code': self.code})

        # Attach user and session manually if needed
        request.user = self.user
        request.session = self.client.session

        # Create CSRF middleware with dummy get_response
        middleware = CsrfViewMiddleware(lambda req: None)

        # Define a dummy view that requires CSRF
        @csrf_protect
        def dummy_view(req):
            return JsonResponse({'ok': True})

        # Run the middleware manually
        response = middleware.process_view(request, dummy_view, (), {})

        if response is None:
            response = dummy_view(request)

        self.assertEqual(response.status_code, 403)
    
    def test_missing_ajax_header(self):
        response = self.client.post(self.url, {'code': self.code}, HTTP_X_REQUESTED_WITH='')
        self.assertEqual(response.status_code, 200)



class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('pop_accounts:register')
    
    def test_valid_registration_sends_verification_email(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'first_name': 'John',
            'password': 'securePassword!23',
            'password2': 'securePassword!23',

        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'registered': True,
            'message': 'Check your email to confirm your account'
        })

        user = PopUpCustomer.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify Your Email', mail.outbox[0].subject)
    
    def test_registration_with_mismatched_passwords(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'first_name': 'Jane',
            'password': 'password!23',
            'password2': 'differentPassword!'
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())
        self.assertFalse(PopUpCustomer.objects.filter(email='test@example.com').exists())
    

    def test_registration_bad_password_strength(self):
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'first_name': 'Jane',
            'password': 'password123',
            'password2': 'password123!'
        })

        self.assertEqual(response.status_code, 400)
    

    def test_missing_required_fields(self):
        response = self.client.post(self.url, {
            'email': '',
            'first_name': '',
            'password': '',
            'password2': ''
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())
    

    def test_registration_fails_without_password2(self):
        response = self.client.post(self.url, {
            'email': 'missing@example.com',
            'first_name': 'Sam',
            'password': 'somePassword'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.json())


class PasswordStrengthValidationTests(TestCase):

    def test_valid_password(self):
        try:
            validate_password_strength('StrongPass1!')
        except ValidationError:
            self.fail('validate_password_strength() raised ValidationError unexpectedly!')

    def test_password_too_short(self):
        with self.assertRaisesMessage(ValidationError, "Password must be at least 8 characters long."):
            validate_password_strength('S1!a')

    def test_missing_uppercase(self):
        with self.assertRaisesMessage(ValidationError, "Password must contain at least one uppercase letter."):
            validate_password_strength('weakpass1!')

    def test_missing_lowercase(self):
        with self.assertRaisesMessage(ValidationError, "Password must contain at least one lower case letter"):
            validate_password_strength('WEAKPASS1!')

    def test_missing_digit(self):
        with self.assertRaisesMessage(ValidationError, "Password must contain at lease one number."):
            validate_password_strength('Weakpass!')

    def test_missing_special_char(self):
        with self.assertRaisesMessage(
            ValidationError,
            'Password must contain at least one special character (!@#$%^&*(),.?":|<>)'
        ):
            validate_password_strength('Weakpass1')


class MarkProductInterestedViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = PopUpCustomer.objects.create_user(
            email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male"
        )

        self.brand = PopUpBrand.objects.create(
            name="Staries",
            slug="staries"
        )
        self.categories = PopUpCategory.objects.create(
            name="Jordan 3",
            slug="jordan-3",
            is_active=True
        )
        self.product_type = PopUpProductType.objects.create(
            name="shoe",
            slug="shoe",
            is_active=True
        )

        now = timezone.now()
        self.product = PopUpProduct.objects.create(
            # id=uuid.uuid4(),
            product_type=self.product_type,
            category=self.categories,
            product_title="Test Sneaker",
            secondary_product_title = "Exclusive Drop",
            description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
            slug="test-sneaker-exclusive-drop", 
            starting_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=self.brand, 
            auction_start_date=now + timedelta(days=5), 
            auction_end_date=now + timedelta(days=10), 
            inventory_status="In Inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True
        )
        self.url = reverse('pop_accounts:mark_interested')

    
    def test_authenticated_user_can_mark_product_interested(self):
        self.client.login(email="testuser@example.com", password="securePassword!23")
        response = self.client.post(
            self.url,
            data={"product_id": str(self.product.id)},
            content_type = "application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertIn(self.product, self.user.prods_interested_in.all())
    

    def test_unathenticated_user_redirected(self):
        response = self.client.post(
            self.url, data={'product_id': str(self.product.id)}, content_type='application/json'
        )

        # Should redirect to home page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/'))
    
    
    def test_product_does_not_exist(self):
        self.client.login(email='testuser@example.com', password='securePassword!23')
        invalid_id = 999999
        response = self.client.post(
            self.url, data={'product_id': str(invalid_id)},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['status'], 'error')



class MarkProductOnNoticeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = PopUpCustomer.objects.create_user(
            email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male"
        )

        self.brand = PopUpBrand.objects.create(
            name="Staries",
            slug="staries"
        )
        self.categories = PopUpCategory.objects.create(
            name="Jordan 3",
            slug="jordan-3",
            is_active=True
        )
        self.product_type = PopUpProductType.objects.create(
            name="shoe",
            slug="shoe",
            is_active=True
        )

        now = timezone.now()
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.categories,
            product_title="Test Sneaker",
            secondary_product_title = "Exclusive Drop",
            description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
            slug="test-sneaker-exclusive-drop", 
            starting_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=self.brand, 
            auction_start_date=now + timedelta(days=5), 
            auction_end_date=now + timedelta(days=10), 
            inventory_status="In Inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True
        )
        self.url = reverse('pop_accounts:mark_on_notice')

    
    def test_authenticated_user_can_mark_product_on_notice(self):
        self.client.login(email="testuser@example.com", password="securePassword!23")
        response = self.client.post(
            self.url,
            data={"product_id": str(self.product.id)},
            content_type = "application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertIn(self.product, self.user.prods_on_notice_for.all())
    
