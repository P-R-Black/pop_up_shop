from django.test import TestCase, RequestFactory
from unittest.mock import patch
from pop_accounts.utils.pop_accounts_utils import handle_password_reset_request
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import JsonResponse
from pop_accounts.models import PopUpCustomerProfile
import json
import uuid

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

class TestHandlePasswordResetRequest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()

        # Create a test user
        # self.email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
        self.user, self.user_profile = create_test_user(
            "testuser@example.com", "testpass!23", "Test", "User1", "9", "male")
        


    @patch('pop_accounts.utils.pop_accounts_utils.send_mail', side_effect=Exception('SMTP error'))
    def test_email_failure_returns_500(self, mock_send_mail):
        """If sending email fails, the helper should return 500"""

        print('self.user', self.user)
        request = self.factory.post('/fake-url/', {'email': 'testuser@example.com'})

        response = handle_password_reset_request(request, 'testuser@example.com')

        # Assert that we get JsonResponse with status 500
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 500)

        # Decode the JSON content
        data = json.loads(response.content)

        self.assertFalse(data['success'])
        self.assertIn('Unable to send email at this time. Please try again later.', data['error'])

        # Assert send_mail was called once
        mock_send_mail.assert_called_once()