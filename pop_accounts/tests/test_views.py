from django.test import TestCase, Client, override_settings
from django.urls import reverse
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress, PopUpBid
from pop_up_payment.utils.tax_utils import get_state_tax_rate
from pop_up_auction.models import PopUpProduct,PopUpBrand, PopUpCategory, PopUpProductType
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
from django.core import mail
from pop_accounts.utils.utils import validate_password_strength
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from pop_up_cart.cart import Cart
from decimal import Decimal, ROUND_HALF_UP
from django.http import HttpRequest
from django.utils.text import slugify

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
            buy_now_price="150.00", 
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
        self.assertEqual(response.json()["status"], "added")
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
            buy_now_price="150.00", 
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
        self.assertEqual(response.json()["status"], "added")
        self.assertIn(self.product, self.user.prods_on_notice_for.all())
    

class ProductBuyViewGETTests(TestCase):
        
    # test correct user displayed
    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male")
        
        auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
        self.brand = create_brand("Jordan")
        self.category = create_category("Jordan 3", True)
        self.product_type = create_product_type("shoe", True)

   
        
        self.product = create_test_product(
            product_type=self.product_type, 
            category=self.category, 
            product_title="Air Jordan 1 Retro", 
            secondary_product_title="Carolina Blue", 
            description="The most uncomfortable basketball shoe their is", 
            slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
            buy_now_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=self.brand, 
            auction_start_date=auction_start, 
            auction_end_date=auction_end, 
            inventory_status="in_inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True)
        
        self.client.login(email="testuser@example.com", password="securePassword!23")
        
        request = self.client.get('/dummy/')
        request = request.wsgi_request

        cart = Cart(request)

        cart.add(product=self.product, qty=1)

        # Save the cart back to the test client's session
        session = self.client.session
        session.update(request.session)
        session.save()
    

        # Create Address for user
        self.address = PopUpCustomerAddress.objects.create(
            customer = self.user,
            address_line = "123 Main St",
            apartment_suite_number = "1A",
            town_city = "New York",
            state = "NY",
            postcode="10001",
            delivery_instructions="Leave with doorman",
            default=True
        )

        self.tax_rate = get_state_tax_rate("NY")
        self.standard_shipping = Decimal('14.99')
        self.processing_fee = Decimal('2.50')


    def test_user_is_correct_in_view(self):
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
    

    def test_product_buy_view_get_correct_tax_rate_applied(self):
        self.assertEqual(get_state_tax_rate("NY"), 0.08375)
        self.assertEqual(get_state_tax_rate("FL"), 0.0)
        self.assertEqual(get_state_tax_rate("CA"), 0.095)
        self.assertEqual(get_state_tax_rate("GA"), 0.07)
        self.assertEqual(get_state_tax_rate("TX"), 0.0625)
        self.assertEqual(get_state_tax_rate("IL"), 0.0886)
        

    def test_product_buy_view_get_basic_cart_data(self):
        response = self.client.get(reverse('pop_up_auction:product_buy'))
        self.assertEqual(response.status_code, 200)

        context = response.context
        cart_items = context['cart_items']

        self.assertEqual(len(cart_items), 1)

        self.assertEqual(cart_items[0]['qty'], 1)
        self.assertEqual(cart_items[0]['product'], self.product)
        self.assertIn('cart_total', context)
        self.assertIn('sales_tax', context)

        
        # Test tax rate and tax calculation
        expected_subtotal = Decimal(self.product.buy_now_price)
        expected_tax = expected_subtotal * Decimal(self.tax_rate)
        self.assertEqual(Decimal(context['sales_tax']), expected_tax.quantize(Decimal('0.01')))

        # Test grand total calcuation
        expected_grand_total = expected_subtotal + expected_tax + (self.standard_shipping  * len(cart_items)) + self.processing_fee
        self.assertEqual(Decimal(context['grand_total']), expected_grand_total.quantize(Decimal('0.01')))
    


    def test_selected_address_used_if_exists(self):
        # Simulate address selected in session
        session = self.client.session
        session['selected_address_id'] = str(self.address.id)
        session.save()

        response = self.client.get(reverse('pop_up_auction:product_buy'))
        self.assertEqual(response.context['selected_address'], self.address)
        self.assertEqual(response.context['address_form'].instance, self.address)
    
    

    def _login_and_seed_cart(self, qty: int = 1):
        """Log the test client in and drop one product in to the Cart session"""
        self.client.login(email=self.user.email, password=self.user.password)

        # make a cart entry directly into the session
        session = self.client.session
        session['cart'] = {str(self.product.id): {'qty': qty, 'price': str(self.product.buy_now_price)}}
        session.save()
    
    def test_product_buy_view_get_selected_address_displayed(self):
        """
        If we stuff selected_address_id into session, the view shoudl surface that exact PopUpCustomerAddress
        instance via context['selected_address']
        """
        self._login_and_seed_cart()

        # store chosen address ID in session
        session = self.client.session
        session['selected_address_id'] = str(self.address.id)
        session.save()

        response = self.client.get(reverse('pop_up_auction:product_buy'))
        self.assertEqual(response.status_code, 200)

        # the view should echo back exactly *that* address as selected
        self.assertIn('selected_address', response.context)
        self.assertEqual(response.context['selected_address'], self.address)


    def test_product_buy_view_get_cart_totals_correct(self):
        """
        Verify subtotal, sales-tax, shipping and grand-total calculations
        for 1 item at $150 (NY tax ≈ 8.375 %), $14.99 std shipping & $2.50 fee.
        """
        self._login_and_seed_cart()          # qty = 1
        # store chosen address ID in session
        session = self.client.session
        session['selected_address_id'] = str(self.address.id)
        session.save()

        response = self.client.get(reverse('pop_up_auction:product_buy'))
        self.assertEqual(response.status_code, 200)

        # the view should echo back exactly *that* address as selected
        self.assertIn('selected_address', response.context)
        self.assertEqual(response.context['selected_address'], self.address)

    
    def test_product_buy_view_get_cart_totals_correct(self):
        """
        Verify subtotal, sales-tax, shipping and grand-total calculations
        for 1 item at $150 (NY tax ≈ 8.375 %), $14.99 std shipping & $2.50 fee.
        """
        self._login_and_seed_cart()          # qty = 1

        response = self.client.get(reverse('pop_up_auction:product_buy'))
        ctx      = response.context

        # --- compute what we EXPECT -----------------
        subtotal        = Decimal('150.00')
        tax_rate        = Decimal(str(get_state_tax_rate('New York')))
        expected_tax    = (subtotal * tax_rate).quantize(Decimal('0.01'), ROUND_HALF_UP)

        shipping        = Decimal('14.99')   # 1499/100 * qty(1)
        processing_fee  = Decimal('2.50')

        expected_total  = (subtotal + expected_tax + shipping + processing_fee).quantize(
                              Decimal('0.01'), ROUND_HALF_UP)

        # --- pull what the view produced -------------
        view_subtotal   = ctx['cart_subtotal']
        view_tax        = Decimal(ctx['sales_tax'])
        view_total      = Decimal(ctx['grand_total'])

        # --- assertions ------------------------------
        self.assertEqual(view_subtotal, subtotal)
        self.assertEqual(view_tax,      expected_tax)
        self.assertEqual(view_total,    expected_total)
    

    def test_invalid_selected_address_id_fails_gracefully(self):
        self._login_and_seed_cart()
        session = self.client.session
        session["selected_address_id"] = "99999999-0000-0000-0000-000000000000"  # invalid UUID
        session.save()

        response = self.client.get(reverse("auction:product_buy"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "\n<h3>Shipping to</h3>\n")  # whatever text implies success


class ProductBuyViewPOSTTests(TestCase):
     # test correct user displayed
    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male")
        
        auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
        self.brand = create_brand("Jordan")
        self.category = create_category("Jordan 3", True)
        self.product_type = create_product_type("shoe", True)


        self.product = create_test_product(
            product_type=self.product_type, 
            category=self.category, 
            product_title="Air Jordan 1 Retro", 
            secondary_product_title="Carolina Blue", 
            description="The most uncomfortable basketball shoe their is", 
            slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
            buy_now_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=self.brand, 
            auction_start_date=auction_start, 
            auction_end_date=auction_end, 
            inventory_status="in_inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True)
        
        self.client.login(email="testuser@example.com", password="securePassword!23")
        
        request = self.client.get('/dummy/')
        request = request.wsgi_request

        cart = Cart(request)

        cart.add(product=self.product, qty=1)

        # Save the cart back to the test client's session
        session = self.client.session
        session.update(request.session)
        session.save()
    

        # Create Address for user
        self.address = PopUpCustomerAddress.objects.create(
            customer = self.user,
            address_line = "123 Main St",
            apartment_suite_number = "1A",
            town_city = "New York",
            state = "NY",
            postcode="10001",
            delivery_instructions="Leave with doorman",
            default=True
        )

        self.tax_rate = get_state_tax_rate("NY")
        self.standard_shipping = Decimal('14.99')
        self.processing_fee = Decimal('2.50')
    

    def _login_and_seed_cart(self, qty: int = 1):
        """Log the test client in and drop one product in to the Cart session"""
        self.client.login(email=self.user.email, password=self.user.password)

        # make a cart entry directly into the session
        session = self.client.session
        session['cart'] = {str(self.product.id): {'qty': qty, 'price': str(self.product.buy_now_price)}}
        session.save()

    def test_post_select_existing_address_sets_session(self):
        self._login_and_seed_cart()
        post_data = {"selected_address": str(self.address.id),}
        response = self.client.post(reverse('pop_up_auction:product_buy'), post_data, follow=True)
        session = self.client.session

        self.assertEqual(response.status_code, 200)
        self.assertIn('selected_address_id', session)
        self.assertEqual(session['selected_address_id'], str(self.address.id))


    def test_post_update_existing_address_success(self):
        self._login_and_seed_cart()

        updated_data = {
            'address_id': self.address.id,
            'prefix': 'Mr.',
            'first_name': 'Updated',
            'last_name': 'Name',
            'address_line': '456 New Ave',
            'apartment_suite_number': '2B',
            'town_city': 'Brooklyn',
            'state': 'New York',
            'postcode': '11201',
            'delivery_instructions': 'New instructions',
        }

        response = self.client.post(reverse('pop_up_auction:product_buy'), updated_data, follow=True)
        self.address.refresh_from_db()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.address.first_name, 'Updated')
        self.assertContains(response, 'Address updated successfully.')
        self.assertEqual(self.client.session['selected_address_id'], str(self.address.id))


    def test_post_add_new_address_success(self):
        self._login_and_seed_cart()

        new_data = {
            'prefix': 'Ms.',
            'first_name': 'New',
            'last_name': 'User',
            'address_line': '789 Fresh St',
            'apartment_suite_number': '3C',
            'town_city': 'Queens',
            'state': 'New York',
            'postcode': '11375',
            'delivery_instructions': 'Ring bell',
        }

        response = self.client.post(reverse('pop_up_auction:product_buy'), new_data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(PopUpCustomerAddress.objects.filter(first_name='New', customer=self.user).exists())

        new_address = PopUpCustomerAddress.objects.get(first_name='New')
        self.assertEqual(self.client.session['selected_address_id'], str(new_address.id))
        self.assertContains(response, "Address added successfully")


    def test_post_add_new_address_invalid_form(self):
        self._login_and_seed_cart()

        invalid_data = {
            'first_name': '',  # Missing required fields
            'last_name': '',
            'postcode': '',
        }

        response = self.client.post(reverse('pop_up_auction:product_buy'), invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please correct the errors below.")


    def test_product_not_in_inventory_skipped_in_cart(self):
        self._login_and_seed_cart()

        # Mark product as not in inventory
        self.product.inventory_status = 'sold'
        self.product.save()

        response = self.client.get(reverse('pop_up_auction:product_buy'))
        cart_items = response.context['cart_items']

        self.assertEqual(len(cart_items), 0)


    def test_cart_is_empty_grand_total_zero(self):
        self.client.login(email='test@test.com', password='123Strong!')
        session = self.client.session
        session['cart'] = {}  # Empty cart
        session.save()

        response = self.client.get(reverse('pop_up_auction:product_buy'))

        self.assertEqual(response.context['cart_total'], 0)
        self.assertEqual(response.context['grand_total'], "0.00")


class ProductBuyGuestTest(TestCase):

    
    
    def setUp(self):
        self.client = Client()

        auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
        self.brand = create_brand("Jordan")
        self.category = create_category("Jordan 3", True)
        self.product_type = create_product_type("shoe", True)

        # seed one product in session cart
        self.product = create_test_product(
            product_type=self.product_type, 
            category=self.category, 
            product_title="Air Jordan 1 Retro", 
            secondary_product_title="Carolina Blue", 
            description="The most uncomfortable basketball shoe their is", 
            slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
            buy_now_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=self.brand, 
            auction_start_date=auction_start, 
            auction_end_date=auction_end, 
            inventory_status="in_inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True
        )

        session = self.client.session
        session['cart'] = {str(self.product.id) : {"qty": 1, "price": str(self.product.buy_now_price)}}
        session.save()
    
    def test_guest_sees_cart_summary_only(self):
        resp = self.client.get(reverse('pop_up_auction:product_buy'))
        self.assertEqual(resp.status_code, 200)

        # Cart bits should be present
        self.assertContains(resp, self.product.product_title)
        self.assertContains(resp, "Subtotal")

        self.assertNotContains(resp, "Shipping Address")
        self.assertNotContains(resp, '<button>Sign in or create account to complete order.</button>')


class ProductBuyAuthTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user(email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male")
        
        auction_start = make_aware(datetime(2025, 6, 22, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 6, 29, 12, 0, 0))
        self.brand = create_brand("Jordan")
        self.category = create_category("Jordan 3", True)
        self.product_type = create_product_type("shoe", True)


        self.product = create_test_product(
            product_type=self.product_type, 
            category=self.category, 
            product_title="Air Jordan 1 Retro", 
            secondary_product_title="Carolina Blue", 
            description="The most uncomfortable basketball shoe their is", 
            slug=slugify("Air Jordan 1 Retro Carolina Blue"), 
            buy_now_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=self.brand, 
            auction_start_date=auction_start, 
            auction_end_date=auction_end, 
            inventory_status="in_inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True)
        
        # Create Address for user
        self.address = PopUpCustomerAddress.objects.create(
            customer = self.user,
            address_line = "123 Main St",
            apartment_suite_number = "1A",
            town_city = "New York",
            state = "NY",
            postcode="10001",
            delivery_instructions="Leave with doorman",
            default=True
        )

        self.client.login(email="testuser@example.com", password="securePassword!23")

        # seed cart
        session = self.client.session
        session['cart'] = {str(self.product.id) : {"qty": 1, "price": str(self.product.buy_now_price)}}
        session.save()
    
    
    def test_authenticated_sees_checkout_controls(self):
        resp = self.client.get(reverse("auction:product_buy"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Shipping Choice")
        self.assertContains(resp, self.address.address_line)
        # self.assertContains(resp, "<button>\n<i class=\'bx bxl-apple\'></i>Pay\n</button>\n")
    

    def test_empty_cart_totals_zero_for_guest(self):
        resp = self.client.get(reverse("auction:product_buy"))
        self.assertContains(resp, "$0.00")
    

    def test_no_default_address_guest_graceful(self):
        # user with no addresses (or guest) should not 500:
        resp = self.client.get(reverse("auction:product_buy"))
        self.assertEqual(resp.status_code, 200)





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
    # """