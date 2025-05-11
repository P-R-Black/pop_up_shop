from django.test import TestCase, Client
from django.urls import reverse
from pop_accounts.models import PopUpCustomer
from unittest.mock import patch
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from uuid import uuid4



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

