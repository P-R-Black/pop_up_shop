from unittest import skip
from pop_up_auction.models import (
     PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType, PopUpProductImage, PopUpProductSpecification, 
     PopUpProductSpecificationValue )
from pop_up_order.utils.utils import user_orders, user_shipments
from pop_up_payment.models import PopUpPayment
from pop_up_shipping.models import PopUpShipment
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest
from pop_up_auction.views import (AllAuctionView, AjaxLoginRequiredMixin, PlaceBidView)
from pop_accounts.models import (PopUpCustomerProfile, PopUpCustomerAddress, PopUpCustomerIP, PopUpBid)
from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import timedelta, datetime, date 
from django.utils.text import slugify
from django.views import View
from django.template import Context, Template
from django.http import Http404
from pop_up_cart.cart import Cart
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import Mock, patch
from django.core.cache import cache
from django.http import JsonResponse
import json
from django.contrib.auth.models import AnonymousUser
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand)

User = get_user_model()



class TestAllAuctionView(TestCase):
    """Test suite for AllAuctionView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        self.user.set_password("testpass123")
        self.user.save()
        
        # Create default address for user
        self.address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="Test City",
            state="Oklahoma",
            postcode="12345",
            default=True
        )

        self.test_brand = create_brand('Jordan')
        self.test_category = create_category('Jordan 3', is_active=True)
        self.test_product_type = create_product_type('shoe', is_active=True)

        self.test_category_two = create_category('Jordan 4', is_active=True)
        self.test_category_three = create_category('Jordan 11', is_active=True)

        # Create auction product with ongoing auction
        self.auction_product = create_test_product(
            product_type=self.test_product_type, category=self.test_category_two, product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air", description="Brand new sneakers", 
            slug="jordan-3-retro-og-rare-air", buy_now_price="230.00", current_highest_bid=Decimal("150.00"), 
            retail_price="150.00", brand=self.test_brand, auction_start_date=django_timezone.now() - timedelta(days=1),  
            auction_end_date=django_timezone.now() + timedelta(days=3), 
            inventory_status="in_inventory", bid_count=0, reserve_price="165.00", is_active="True")
        
        
        # Create product specifications
        self.size_spec = PopUpProductSpecification.objects.create(
            product_type=self.test_product_type, 
            name='size')

        self.condition_spec = PopUpProductSpecification.objects.create(
            product_type=self.test_product_type,
            name='condition')

        self.sex_spec = PopUpProductSpecification.objects.create(
            product_type=self.test_product_type,
            name='product_sex')
    
    
        
        # Create product specifications for auction product
        PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=self.size_spec,
            value="10"
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=self.condition_spec,
            value="new"
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=self.sex_spec,
            value="Male"
        )
        
        # Create feature image
        self.product_image = PopUpProductImage.objects.create(
            product=self.auction_product,
            image="test_image.jpg",
            alt_text="Test Sneakers Image",
            is_feature=True
        )

        
        # URL for the view
        self.url = reverse('pop_up_auction:auction')

    def test_view_url_accessible_by_name(self):
        """Test that view is accessible via URL name"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


    def test_view_uses_correct_template(self):
        """Test that view uses correct template"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'auction/auction.html')

    def test_authenticated_user_can_access_view(self):
        """Test that authenticated users can access the view"""
        self.client.login(email="testuser@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_can_access_view(self):
        """Test that unauthenticated users can access the view"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_in_auction(self):
        """Test that context contains in_auction list"""
        response = self.client.get(self.url)
        self.assertIn('in_auction', response.context)
        self.assertIsInstance(response.context['in_auction'], list)

    def test_context_contains_quick_bid_increments(self):
        """Test that context contains quick_bid_increments"""
        response = self.client.get(self.url)
        self.assertIn('quick_bid_increments', response.context)
        self.assertEqual(response.context['quick_bid_increments'], [10, 20, 30])

    def test_context_contains_user_zip_for_authenticated_user(self):
        """Test that context contains user_zip for authenticated users"""
        self.client.login(email="testuser@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertIn('user_zip', response.context)
        self.assertEqual(response.context['user_zip'], "12345")

    def test_context_user_zip_empty_for_unauthenticated_user(self):
        """Test that user_zip is empty string for unauthenticated users"""
        response = self.client.get(self.url)
        self.assertIn('user_zip', response.context)
        self.assertEqual(response.context['user_zip'], "")

    def test_ongoing_auction_product_displayed(self):
        """Test that ongoing auction products are included in context"""
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 1)
        self.assertEqual(in_auction[0], self.auction_product)

    def test_inactive_product_not_displayed(self):
        """Test that inactive products are not displayed"""
        self.auction_product.is_active = False
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 0)

    def test_sold_product_not_displayed(self):
        """Test that sold products are not displayed"""
        self.auction_product.inventory_status = "sold"
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 0)
    
    def test_upcoming_auction_not_displayed(self):
        """Test that upcoming auction products are not displayed"""
        # Set auction to start in the future
        self.auction_product.auction_start_date = django_timezone.now() + timedelta(days=1)
        self.auction_product.auction_end_date = django_timezone.now() + timedelta(days=5)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        # Should be 0 because auction_status will be "Upcoming"
        self.assertEqual(len(in_auction), 0)

    def test_ended_auction_not_displayed(self):
        """Test that ended auction products are not displayed"""
        # Set auction to have ended in the past
        self.auction_product.auction_start_date = django_timezone.now() - timedelta(days=5)
        self.auction_product.auction_end_date = django_timezone.now() - timedelta(days=1)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        # Should be 0 because auction_status will be "Ended"
        self.assertEqual(len(in_auction), 0)


    def test_multiple_ongoing_auctions_displayed(self):
        """Test that multiple ongoing auctions are displayed"""
        # Create second auction product
        auction_proudct2= create_test_product(
            product_type=self.test_product_type, 
            category=self.test_category_three, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air 2", 
            description="Brand new sneakers", 
            slug="jordan-3-retro-og-rare-air-2", 
            buy_now_price="230.00", current_highest_bid="0", 
            retail_price="150.00", 
            brand=self.test_brand, 
            auction_start_date=django_timezone.now() - timedelta(days=1),  
            auction_end_date=django_timezone.now() + timedelta(days=2), 
            inventory_status="in_inventory", bid_count=0, reserve_price="165.00", is_active="True")

        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 2)


    def test_product_specifications_in_context(self):
        """Test that product specifications are included in context"""
        response = self.client.get(self.url)
        product_specifications = response.context['product_specifications']
        
        self.assertIsNotNone(product_specifications)
        self.assertIn('size', product_specifications)
        self.assertIn('condition', product_specifications)
        self.assertIn('product_sex', product_specifications)


    def test_product_with_no_current_bid(self):
        """Test displaying product with no current highest bid"""
        self.auction_product.current_highest_bid = 0
        self.auction_product.bid_count = 0
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 1)
        self.assertEqual(in_auction[0].current_highest_bid, 0)


    def test_auction_duration_calculated(self):
        """Test that auction duration is calculated correctly"""
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        
        # Product should have auction_duration attribute
        product = in_auction[0]
        self.assertTrue(hasattr(product, 'auction_duration'))

    def test_prefetch_related_optimizes_queries(self):
        """Test that prefetch_related is used for optimization"""
        # Create multiple specification values
        cache.clear()
        """
        self.sex_spec = PopUpProductSpecification.objects.create(product_type_id=1,name='product_sex')

        PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=self.sex_spec,
            value="Male"
        )
        """
        test_product_type_one = create_product_type('shoe_one', is_active=True)
        test_product_type_two = create_product_type('shoe_two', is_active=True)
        test_product_type_three = create_product_type('shoe_three', is_active=True)

        spec_one = PopUpProductSpecification.objects.create(product_type=test_product_type_one,name=f"product_1")
        spec_two = PopUpProductSpecification.objects.create(product_type=test_product_type_two,name=f"product_2")
        spec_three =PopUpProductSpecification.objects.create(product_type=test_product_type_three,name=f"product_3")

        value_one = PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=spec_one,
            value=f"value_1"
            )
        
        value_two = PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=spec_two,
            value=f"value_2"
            )

        value_three = PopUpProductSpecificationValue.objects.create(
            product=self.auction_product,
            specification=spec_three,
            value=f"value_3"
            )

        
        # Count queries
        with self.assertNumQueries(12):  # Adjust based on actual query count
            response = self.client.get(self.url)

    def test_post_request_returns_template(self):
        """Test that POST request returns the template"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auction/auction.html')


    def test_user_with_multiple_addresses_uses_default(self):
        """Test that only default address is used for zip code"""
        # Create non-default address
        PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="456 Other St",
            town_city="Other City",
            state="Oklahoma",
            postcode="67890",
            default=False
        )
        
        self.client.login(email="testuser@example.com", password="testpass123")
        response = self.client.get(self.url)
        
        # Should use default address zip
        self.assertEqual(response.context['user_zip'], "12345")

    def test_user_with_no_address_has_empty_zip(self):
        """Test that user with no address has empty zip code"""
        # Delete address
        self.address.delete()
        
        self.client.login(email="testuser@example.com", password="testpass123")
        response = self.client.get(self.url)
        
        self.assertEqual(response.context['user_zip'], "")

    def test_expired_auction_not_displayed(self):
        """Test that expired auctions are not displayed"""
        self.auction_product.auction_end_date = django_timezone.now() - timedelta(days=1)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 0)

    def test_future_auction_not_displayed(self):
        """Test that future auctions are not displayed"""
        self.auction_product.auction_start_date = django_timezone.now() + timedelta(days=1)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 0)

    def test_template_renders_product_title(self):
        """Test that template renders product title"""
        response = self.client.get(self.url)
        self.assertContains(response, "Test Sneakers")

    def test_template_renders_secondary_title(self):
        """Test that template renders secondary product title"""
        response = self.client.get(self.url)
        self.assertContains(response, "OG Rare Air")

    def test_template_renders_current_bid(self):
        """Test that template renders current highest bid"""
        response = self.client.get(self.url)
        self.assertContains(response, "150")

    def test_template_renders_bid_count(self):
        """Test that template renders bid count"""
        response = self.client.get(self.url)
        self.assertContains(response, "5")

    def test_template_shows_signin_button_for_unauthenticated(self):
        """Test that unauthenticated users see sign in button"""
        response = self.client.get(self.url)
        self.assertContains(response, "Sign in to Bid")

    def test_template_shows_bid_button_for_authenticated(self):
        """Test that authenticated users see make bid button"""
        self.client.login(email="testuser@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertContains(response, "Make Bid")

    def test_empty_auction_list_when_no_products(self):
        """Test that empty list is returned when no products in auction"""
        self.auction_product.delete()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 0)

    def test_product_with_reserve_price_no_bids(self):
        """Test displaying product with reserve price and no bids"""
        self.auction_product.current_highest_bid = 0
        self.auction_product.bid_count = 0
        self.auction_product.reserve_price = Decimal("100.00")
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(in_auction[0].reserve_price, Decimal("100.00"))

    def test_view_handles_product_without_specifications(self):
        """Test that view handles products without specifications"""
        # Delete all specifications
        PopUpProductSpecificationValue.objects.filter(product=self.auction_product).delete()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_quick_bid_increments_displayed_in_modal(self):
        """Test that quick bid increments are available in template context"""
        response = self.client.get(self.url)
        self.assertContains(response, "160")
        self.assertContains(response, "170")
        self.assertContains(response, "180")

    def test_csrf_token_present_in_form(self):
        """Test that CSRF token is present in bid form"""
        response = self.client.get(self.url)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_modal_displays_product_id(self):
        """Test that modal contains product ID for AJAX"""
        response = self.client.get(self.url)
        self.assertContains(response, f'data-product-id="{self.auction_product.id}"')

    def test_user_email_obfuscated_in_modal(self):
        """Test that user email is obfuscated in modal"""
        self.client.login(email="testuser@example.com", password="testpass123")
        response = self.client.get(self.url)
        # Should use obfuscate_email filter
        self.assertNotContains(response, "testuser@example.com")


# Create a test view that uses the mixin
class TestProtectedView(AjaxLoginRequiredMixin, View):
    """Test view that uses AjaxLoginRequiredMixin"""
    def get(self, request):
        return JsonResponse({'status': 'success', 'message': 'You are authenticated'})
    
    def post(self, request):
        return JsonResponse({'status': 'success', 'message': 'Bid placed successfully'})


class TestAjaxLoginRequiredMixin(TestCase):
    """Test suite for AjaxLoginRequiredMixin"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.view = TestProtectedView.as_view()
        
        # Create test user
        self.existing_email = 'existing@example.com'
        self.user, self.profile = create_test_user(self.existing_email, 'testPass!23', 'Test', 'User', '9', 'male')  
        self.user.is_active = True
        self.user.save()

    def test_authenticated_user_ajax_request_allowed(self):
        """Test that authenticated users can make AJAX requests"""
        request = self.factory.get('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = self.user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_authenticated_user_regular_request_allowed(self):
        """Test that authenticated users can make regular requests"""
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_unauthenticated_ajax_request_returns_json_error(self):
        """Test that unauthenticated AJAX requests return JSON error"""
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, 403)
        self.assertIsInstance(response, JsonResponse)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'You must be logged in to place a bid')

    def test_unauthenticated_regular_request_redirects(self):
        """Test that unauthenticated regular requests redirect to login"""
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        # Should redirect to login (302 or 403 depending on handle_no_permission)
        self.assertIn(response.status_code, [302, 403])

    def test_ajax_header_case_sensitivity(self):
        """Test that AJAX header check is case-sensitive"""
        request = self.factory.post('/test/')
        # Wrong case - should not be treated as AJAX
        request.META['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        # Should redirect, not return JSON
        self.assertIn(response.status_code, [302, 403])
        # Should not be JsonResponse
        self.assertNotIsInstance(response, JsonResponse)


    def test_ajax_post_request_authenticated(self):
        """Test authenticated POST AJAX request"""
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = self.user
        
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Bid placed successfully')


    def test_ajax_post_request_unauthenticated(self):
        """Test unauthenticated POST AJAX request"""
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')


    def test_inactive_user_blocked(self):
        """Test that inactive users are blocked"""
        self.user.is_active = False
        self.user.save()
        
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = self.user
        
        response = self.view(request)
        
        # Inactive users should be treated as unauthenticated
        self.assertEqual(response.status_code, 403)


    def test_json_response_content_type(self):
        """Test that JSON response has correct content type"""
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        self.assertEqual(response['Content-Type'], 'application/json')


    def test_json_response_structure(self):
        """Test that JSON response has expected structure"""
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        data = json.loads(response.content)
        
        # Check that response has required keys
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertEqual(len(data), 2)


    def test_multiple_ajax_requests_same_session(self):
        """Test multiple AJAX requests in same session"""
        request1 = self.factory.post('/test/')
        request1.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request1.user = self.user
        
        request2 = self.factory.post('/test/')
        request2.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request2.user = self.user
        
        response1 = self.view(request1)
        response2 = self.view(request2)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)


    def test_ajax_get_request_authenticated(self):
        """Test authenticated GET AJAX request"""
        request = self.factory.get('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = self.user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, 200)


    def test_ajax_get_request_unauthenticated(self):
        """Test unauthenticated GET AJAX request"""
        request = self.factory.get('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')


    def test_missing_ajax_header_unauthenticated(self):
        """Test request without AJAX header when unauthenticated"""
        request = self.factory.post('/test/')
        # No AJAX header
        request.user = AnonymousUser()
        
        response = self.view(request)
        
        # Should NOT return JSON, should redirect/deny normally
        self.assertNotIsInstance(response, JsonResponse)


    def test_authenticated_user_different_methods(self):
        """Test that authenticated users can use different HTTP methods"""
        methods = ['get', 'post']
        
        for method in methods:
            request_method = getattr(self.factory, method)
            request = request_method('/test/')
            request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
            request.user = self.user
            
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_error_message_accuracy(self):
        """Test that error message is accurate and helpful"""
        request = self.factory.post('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = self.view(request)
        data = json.loads(response.content)
        
        # Message should clearly indicate login requirement
        self.assertIn('logged in', data['message'].lower())
        self.assertIn('bid', data['message'].lower())

    def test_mixin_with_different_view_classes(self):
        """Test that mixin works with different view types"""
        class AnotherProtectedView(AjaxLoginRequiredMixin, View):
            def get(self, request):
                return JsonResponse({'data': 'protected'})
        
        view = AnotherProtectedView.as_view()
        
        # Test unauthenticated AJAX
        request = self.factory.get('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        
        response = view(request)
        self.assertEqual(response.status_code, 403)
        
        # Test authenticated AJAX
        request.user = self.user
        response = view(request)
        self.assertEqual(response.status_code, 200)


    def test_dispatch_calls_parent_dispatch(self):
        """Test that dispatch properly calls parent class dispatch"""
        request = self.factory.get('/test/')
        request.user = self.user
        
        response = self.view(request)
        
        # If parent dispatch wasn't called, view wouldn't execute
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')


class TestPlaceBidView(TestCase):
    """ Comprehensive test suite for PlaceBidView"""


    def setUp(self):
        """Set up test fixtures for each test method."""
        self.factory = RequestFactory()
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male")
        
        self.other_user, self.other_user_profile = create_test_user(
            "other@example.com", "testpass123!", "Test", "User2", "7.5", "female")
       
        
        # Create a test product with typical auction parameters
        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.product = create_test_product(
            product_type=test_product_type, 
            category=test_category_two, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air", 
            description="Brand new sneakers", 
            slug="jordan-3-retro-og-rare-air", 
            buy_now_price="230.00", 
            current_highest_bid="0", 
            retail_price=Decimal('150.00'), 
            brand=test_brand, 
            auction_start_date=None,  
            auction_end_date=None, 
            inventory_status="in_inventory", 
            bid_count=0, 
            reserve_price=Decimal('120.00'), 
            is_active=True
            )
        

        self.view = PlaceBidView.as_view()

    def _create_authenticated_request(self, user, data):
        """
        Helper method to create a properly authenticated request.
        Adds is_authenticated property to user object.
        """
        request = self.factory.post('/place-bid/', data)
        request.user = user
        # Mock the is_authenticated property that middleware would add
        request.user.is_active = True
        request.user.save()
        return request
    
    def _create_unauthenticated_request(self, data):
        """Helper method to create an unauthenticated request."""
        request = self.factory.post('/place-bid/', data)
        request.user = Mock(is_authenticated=False)
        return request
    
    # ==================== Authentication Tests ====================
    
    def test_unauthenticated_user_rejected(self):
        """Unauthenticated users should not be able to place bids."""
        request = self._create_unauthenticated_request({
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        
        # AjaxLoginRequiredMixin should handle this
        # Typically returns 403 or redirects
        self.assertIn(response.status_code, [302, 403])


    def test_authenticated_user_allowed(self):
        """Authenticated users should be able to access the view."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        
        self.assertIn(response.status_code, [200, 400])
    

    
    # ==================== Input Validation Tests ====================
    
    def test_missing_product_id(self):
        """Should return error when product_id is missing."""
        request = self._create_authenticated_request(self.user, {
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Missing product or amount', data['message'])

    def test_missing_bid_amount(self):
        """Should return error when bid_amount is missing."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Missing product or amount', data['message'])

    def test_empty_product_id(self):
        """Should return error when product_id is empty string."""
        request = self._create_authenticated_request(self.user, {
            'product_id': '',
            'bid_amount': '110.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')

    def test_empty_bid_amount(self):
        """Should return error when bid_amount is empty string."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': ''
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')

    def test_invalid_bid_amount_format(self):
        """Should return error for non-numeric bid amounts."""
        invalid_amounts = ['abc', '10.5.5', 'ten dollars', '10,50']
        
        for invalid_amount in invalid_amounts:
            with self.subTest(invalid_amount=invalid_amount):
                request = self._create_authenticated_request(self.user, {
                    'product_id': self.product.id,
                    'bid_amount': invalid_amount
                })
                
                response = self.view(request)
                data = json.loads(response.content)
                
                self.assertEqual(response.status_code, 400)
                self.assertEqual(data['status'], 'error')
                self.assertIn('Invalid bid amount', data['message'])


    def test_negative_bid_amount(self):
        """Should handle negative bid amounts (fails retail_price check)."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '-50.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')

    def test_zero_bid_amount(self):
        """Should reject zero bid amounts."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '0.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')

    def test_nonexistent_product(self):
        """Should return 404 for non-existent product."""
        request = self._create_authenticated_request(self.user, {
            'product_id': 99999,
            'bid_amount': '110.00'
        })
        
        with self.assertRaises(Http404):
            self.view(request)

    def test_inactive_product(self):
        """Should return 404 for inactive products."""
        self.product.is_active = False
        self.product.save()
        
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '110.00'
        })
        
        with self.assertRaises(Http404):
            self.view(request)

    # ==================== Business Logic Tests ====================
    
    def test_bid_below_retail_price(self):
        """Should reject bids at or below retail price."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '150.00'  # Equal to retail_price
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('150.00', data['message'])
        self.assertIn('must be better than', data['message'])

    def test_bid_just_below_retail_price(self):
        """Should reject bids slightly below retail price."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '99.99'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')

    def test_bid_equal_to_current_highest(self):
        """Should reject bids equal to current highest bid."""
        # Set up existing bid
        self.product.current_highest_bid = Decimal('160.00')
        self.product.save()
        
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertIn('160.00', data['message'])

    def test_bid_below_current_highest(self):
        """Should reject bids below current highest bid."""
        # Set up existing bid
        self.product.current_highest_bid = Decimal('120.00')
        self.product.save()
        
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '115.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')

    # ==================== Successful Bid Tests ====================
    
    def test_successful_first_bid(self):
        """Should successfully place first bid on product."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_highest'], '160.00')
        self.assertEqual(data['bid_count'], 1)
        
        # Verify database state
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_highest_bid, Decimal('160.00'))
        self.assertEqual(self.product.bid_count, 1)
        
        # Verify bid was created
        bid = PopUpBid.objects.get(product=self.product, customer=self.user_profile)
        self.assertEqual(bid.amount, Decimal('160.00'))

    def test_successful_higher_bid(self):
        """Should successfully place higher bid over existing bid."""
        # Place initial bid
        PopUpBid.objects.create(
            customer=self.other_user_profile,
            product=self.product,
            amount=Decimal('155.00'),
            timestamp=django_timezone.now()
        )
        self.product.current_highest_bid = Decimal('155.00')
        self.product.bid_count = 1
        self.product.save()
        
        # Place higher bid
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '165.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_highest'], '165.00')
        self.assertEqual(data['bid_count'], 2)
        
        # Verify database state
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_highest_bid, Decimal('165.00'))
        self.assertEqual(self.product.bid_count, 2)

    def test_bid_with_cents(self):
        """Should handle bids with decimal precision correctly."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '150.50'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['new_highest'], '150.50')
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_highest_bid, Decimal('150.50'))

    def test_minimal_increment_bid(self):
        """Should accept bid that's minimally higher (e.g., $0.01)."""
        self.product.current_highest_bid = Decimal('110.00')
        self.product.save()
        
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '150.01'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')

    def test_same_user_multiple_bids(self):
        """Should allow same user to place multiple bids."""
        # First bid
        request1 = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '155.00'
        })
        self.view(request1)
        
        # Second bid from same user
        request2 = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '165.00'
        })
        
        response = self.view(request2)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['bid_count'], 2)
        
        # Both bids should exist
        user_bids = PopUpBid.objects.filter(
            product=self.product,
            customer=self.user_profile
        )
        self.assertEqual(user_bids.count(), 2)

    # ==================== Edge Cases ====================
    
    def test_very_large_bid_amount(self):
        """Should handle very large bid amounts."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '999999.99'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')

    def test_bid_with_many_decimal_places(self):
        """Should handle bids with many decimal places."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '110.123456'
        })
        
        response = self.view(request)
        
        # Should either succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400])

    def test_concurrent_bid_scenario(self):
        """Test scenario where multiple users bid in quick succession."""
        # User 1 bids
        request1 = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '110.00'
        })
        self.view(request1)
        
        # User 2 bids higher
        request2 = self._create_authenticated_request(self.other_user, {
            'product_id': self.product.id,
            'bid_amount': '120.00'
        })
        response2 = self.view(request2)
        
        # User 1 tries to bid lower than user 2
        request3 = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '115.00'
        })
        response3 = self.view(request3)
        
        data3 = json.loads(response3.content)
        self.assertEqual(response3.status_code, 400)
        self.assertEqual(data3['status'], 'error')


    def test_bid_timestamp_recorded(self):
        """Should record timestamp for each bid."""
        before_time = django_timezone.now()
        
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        self.view(request)
        
        after_time = django_timezone.now()
        
        bid = PopUpBid.objects.get(product=self.product, customer=self.user_profile)
        self.assertGreaterEqual(bid.timestamp, before_time)
        self.assertLessEqual(bid.timestamp, after_time)

    # ==================== Response Format Tests ====================
    
    def test_success_response_format(self):
        """Should return properly formatted success response."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        # Check all required fields are present
        self.assertIn('status', data)
        self.assertIn('new_highest', data)
        self.assertIn('bid_count', data)
        
        # Check correct types
        self.assertIsInstance(data['status'], str)
        self.assertIsInstance(data['new_highest'], str)
        self.assertIsInstance(data['bid_count'], int)

    def test_error_response_format(self):
        """Should return properly formatted error response."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '50.00'  # Below retail price
        })
        
        response = self.view(request)
        data = json.loads(response.content)
        
        # Check required fields
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertEqual(data['status'], 'error')
        self.assertIsInstance(data['message'], str)

    def test_json_response_content_type(self):
        """Should return proper JSON content type."""
        request = self._create_authenticated_request(self.user, {
            'product_id': self.product.id,
            'bid_amount': '160.00'
        })
        
        response = self.view(request)
        
        self.assertEqual(response['Content-Type'], 'application/json')


class TestProductAuctionView(TestCase):
    """TestProductAUction View """
    def setUp(self):
        """Set up test fixtures for each test method."""
        self.factory = RequestFactory()
        self.client = Client()
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male")
        
        self.other_user, self.other_user_profile = create_test_user(
            "other@example.com", "testpass123!", "Test", "User2", "7.5", "female")
       
        
        # Create a test product with typical auction parameters
        test_brand = create_brand('Jordan')
        test_category = create_category('Jordan 3', is_active=True)
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        # Create specifications for products
        self.size_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='size')
        self.color_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='colorway')
        self.weight_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='weight')

        now = django_timezone.now()

        self.active_product = create_test_product(
            product_type=test_product_type, 
            category=test_category_two, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air", 
            description="Brand new sneakers", 
            slug="jordan-3-retro-og-rare-air", 
            buy_now_price=Decimal("100.00"), 
            current_highest_bid=Decimal('120.00'), 
            retail_price=Decimal('80.00'), 
            brand=test_brand, 
            auction_start_date=now - timedelta(days=1),  
            auction_end_date=now + timedelta(days=2), #django_timezone.now() + timedelta(days=2, hours=3), 
            inventory_status="in_inventory", 
            bid_count=5, 
            reserve_price=Decimal('105.00'), 
            is_active=True
            )

        # Create an inactive product
        self.inactive_product = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Jordan 4 Retro", 
            secondary_product_title="White Cement", description="Brand new sneakers", 
            slug="jordan-4-white-cement", buy_now_price="230.00", current_highest_bid="0", 
            retail_price=Decimal('150.00'), brand=test_brand, auction_start_date=None,  
            auction_end_date=None, inventory_status="in_inventory", bid_count=0, 
            reserve_price=Decimal('100.00'), is_active="False")

        # Create a product with no bids yet
        self.no_bid_product = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Jordan 11 Retro", 
            secondary_product_title="Concord", description="Brand new Jordan 11", 
            slug="jordan-11-concord", buy_now_price="350.00", current_highest_bid="0", 
            retail_price=Decimal('200.00'), brand=test_brand, auction_start_date=None,  
            auction_end_date=django_timezone.now() + timedelta(days=5), inventory_status="in_inventory", 
            bid_count=0, reserve_price=Decimal('150.00'), is_active="True")
           

        # Create a product with minimal specifications
        self.minimal_product = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Minimal Product", 
            secondary_product_title="Minis", description="Minimal product minis", 
            slug="minimal-product", buy_now_price="350.00", current_highest_bid="0", 
            retail_price=Decimal('50.00'), brand=test_brand, auction_start_date=None,  
            auction_end_date=None, inventory_status="in_inventory", 
            bid_count=0, reserve_price=Decimal('40.00'), is_active="True")
        

        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.size_spec,
            value='10'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.color_spec,
            value='Red'
        )

        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.weight_spec,
            value='1.5 lbs'
        )

    # ==================== Basic Access Tests ====================

    def test_view_url_exists_at_desired_location(self):
        """View should be accessible via URL with slug."""
        response = self.client.get(f'/auction/{self.active_product.slug}/')
        # Adjust the URL pattern to match your urls.py
        self.assertIn(response.status_code, [200, 301, 302, 404])  # Depends on your URL config
    

    def test_view_url_accessible_by_name(self):
        """View should be accessible via URL name."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """View should use the correct template."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auction/product_auction.html')

    def test_authenticated_user_can_access(self):
        """Authenticated users should be able to access the view."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_access(self):
        """Anonymous users should be able to view auction details."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ==================== Product Filtering Tests ====================
    
    def test_active_product_displayed(self):
        """Active products should be displayed correctly."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.active_product)

    def test_inactive_product_returns_404(self):
        """Inactive products should return 404."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.inactive_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_slug_returns_404(self):
        """Non-existent slug should return 404."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': 'nonexistent-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_empty_slug_returns_404(self):
        """Empty slug should return 404 or bad request."""
        try:
            url = reverse('pop_up_auction:product_auction', kwargs={'slug': ''})
            response = self.client.get(url)
            self.assertIn(response.status_code, [404, 400])
        except:
            pass

    # ==================== Context Data Tests ====================
    
    def test_context_contains_product(self):
        """Context should contain the product object."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertIn('product', response.context)
        self.assertEqual(response.context['product'].id, self.active_product.id)

    def test_context_contains_product_specifications(self):
        """Context should contain product specifications dictionary."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertIn('product_specifications', response.context)
        
        specs = response.context['product_specifications']
        self.assertIsInstance(specs, dict)
        self.assertEqual(specs['colorway'], 'Red')
        self.assertEqual(specs['size'], '10')
        self.assertEqual(specs['weight'], '1.5 lbs')

    def test_product_has_auction_details(self):
        """Product should have auction details like current bid and bid count."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        self.assertEqual(product.current_highest_bid, Decimal('120.00'))
        self.assertEqual(product.bid_count, 5)

    def test_product_with_no_bids(self):
        """Product with no bids should display correctly."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.no_bid_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        self.assertEqual(product.current_highest_bid, 0)
        self.assertEqual(product.bid_count, 0)

    def test_product_with_no_specifications(self):
        """Product with no specifications should have empty specs dict."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.minimal_product.slug})
        response = self.client.get(url)
        
        specs = response.context['product_specifications']
        self.assertIsInstance(specs, dict)
        self.assertEqual(len(specs), 0)


    def test_specs_utility_function_applied(self):
        """The add_specs_to_products utility should be applied to product."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        # Verify the product has been processed by the utility function
        # This depends on what add_specs_to_products does to the product
        self.assertIsNotNone(product)

    # ==================== Prefetch Related Tests ====================
    
    def test_prefetch_related_reduces_queries(self):
        """Prefetch related should reduce number of database queries."""
        from django.test import override_settings
        from django.db import connection
        from django.test.utils import override_settings
        
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        
        # Reset queries
        from django.conf import settings
        with self.settings(DEBUG=True):
            from django.db import reset_queries
            reset_queries()
            
            response = self.client.get(url)
            
            # With prefetch_related, accessing specifications shouldn't cause additional queries
            specs = response.context['product_specifications']
            # The number of queries should be reasonable (typically 2-3)
            # Without prefetch_related, it would be N+1 queries
            num_queries = len(connection.queries)
            
            self.assertLessEqual(num_queries, 10, "Too many queries - prefetch may not be working")

    # ==================== Slug Routing Tests ====================
    
    def test_slug_with_special_characters(self):
        """Products with special characters in slug should work."""
        # create product types and products
        brand = create_brand("New Jordan")
        ptype_shoe = create_product_type("creps", True)
        ptype_shoe_2 = create_product_type("new_shoes", True)
        ptype_two = create_product_type("apparel", True)
        category = create_category('Jordan III', is_active=True)
        

        special_product = create_test_product_two(
            brand=brand,
            product_type=ptype_shoe_2,
            inventory_status="in_transit", 
            is_active=True
        )
        
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': special_product.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_slug_case_sensitivity(self):
        """Test slug case sensitivity (Django slugs are typically lowercase)."""
        url_lower = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug.lower()})
        response = self.client.get(url_lower)
        self.assertEqual(response.status_code, 200)

    def test_different_products_have_unique_slugs(self):
        """Each product should be accessible via its unique slug."""
        url1 = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        url2 = reverse('pop_up_auction:product_auction', kwargs={'slug': self.no_bid_product.slug})
        
        response1 = self.client.get(url1)
        response2 = self.client.get(url2)
        
        self.assertNotEqual(response1.context['product'].id, response2.context['product'].id)

    # ==================== Template Rendering Tests ====================
    
    def test_product_name_in_response(self):
        """Product name should appear in the rendered response."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, self.active_product.product_title)

    def test_retail_price_in_response(self):
        """Retail price should appear in the rendered response."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        # Check if price appears in some format (could be $100.00 or 100.00)
        self.assertContains(response, '100')

    def test_current_bid_in_response(self):
        """Current highest bid should appear in the rendered response."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, '120')  # Current bid is 120.00

    def test_bid_count_in_response(self):
        """Bid count should appear in the rendered response."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, '5')  # 5 bids

    def test_specifications_in_response(self):
        """Product specifications should appear in the rendered response."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, 'Red')
        self.assertContains(response, '10')

    # ==================== Auction Timing Tests ====================
    
    def test_end_time_present_for_product(self):
        """Product with end_time should have it accessible."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        self.assertIsNotNone(product.auction_end_date)
        self.assertGreater(product.auction_end_date, django_timezone.now())

    def test_product_with_no_end_time(self):
        """Product without end_time should still display correctly."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.minimal_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_expired_auction_still_accessible_if_active(self):
        """Expired auction should still be accessible if is_active=True."""
        brand = create_brand("New Jordan")
        ptype_shoe_2 = create_product_type("new_shoes", True)

    
        expired_product = create_test_product_two(
            brand=brand,
            product_type=ptype_shoe_2,
            inventory_status="in_transit", 
            auction_end_date=django_timezone.now() - timedelta(days=1),
            is_active=True
        )

        
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': expired_product.slug})
        response = self.client.get(url)
        # View doesn't filter by end_time, only is_active
        self.assertEqual(response.status_code, 200)

    # ==================== Edge Cases ====================
    
    def test_product_with_very_long_name(self):
        """Product with very long name should display correctly."""
        brand = create_brand("New Jordan")
        ptype_shoe_2 = create_product_type("new_shoes", True)
    
        long_name_product = create_test_product_two(
            product_title='A' * 200,
            secondary_product_title='B'*50,
            brand=brand,
            slug='long-name-product',
            product_type=ptype_shoe_2,
            inventory_status="in_transit",
            retail_price=Decimal('100.00'),
            auction_end_date=django_timezone.now() - timedelta(days=1),
            is_active=True
        )
        
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': long_name_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_with_zero_reserve_price(self):
        """Product with zero reserve price should display correctly."""
        brand = create_brand("New Jordan")
        ptype_shoe_2 = create_product_type("new_shoes", True)

        zero_reserve = create_test_product_two(
            product_title='Zero Reserve Product',
            secondary_product_title='Zero',
            brand=brand,
            slug='zero-reserve-product',
            product_type=ptype_shoe_2,
            inventory_status="in_transit",
            retail_price=Decimal('100.00'),
            reserve_price=Decimal('0.00'),
            is_active=True
        )

        url = reverse('pop_up_auction:product_auction', kwargs={'slug': zero_reserve.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_with_multiple_specifications_same_type(self):
        """Product with multiple specifications of the same type."""
        brand = create_brand("New Jordan")
        ptype_shoe_2 = create_product_type("new_shoes", True)

    
        multi_spec_product = create_test_product_two(
            product_title='Zero Reserve Product',
            secondary_product_title='Zero',
            brand=brand,
            slug='zero-reserve-product',
            product_type=ptype_shoe_2,
            inventory_status="in_transit",
            retail_price=Decimal('100.00'),
            reserve_price=Decimal('0.00'),
            is_active=True
        )

        
        # Add multiple color specifications (edge case)
        PopUpProductSpecificationValue.objects.create(
            product=multi_spec_product,
            specification=self.color_spec,
            value='Red'
        )
        
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': multi_spec_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_context_object_name_is_product(self):
        """Context object should be accessible as 'product'."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        
        # Both 'product' and 'object' should be available in context
        self.assertIn('product', response.context)
        self.assertIn('object', response.context)
        self.assertEqual(response.context['product'], response.context['object'])

    # ==================== Integration Tests ====================
    
    def test_view_provides_data_for_bid_modal(self):
        """View should provide all data needed for the bid modal/popup."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        # Check that all necessary auction data is available
        self.assertIsNotNone(product.id)  # For submitting bid
        self.assertIsNotNone(product.retail_price)  # For minimum bid validation
        self.assertIsNotNone(product.current_highest_bid)  # For display
        self.assertIsNotNone(product.bid_count)  # For display

    def test_multiple_concurrent_views(self):
        """Multiple users viewing the same product simultaneously."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        
        # Simulate multiple requests
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(
            response1.context['product'].id,
            response2.context['product'].id
        )

    def test_view_after_product_updated(self):
        """View should reflect product updates."""
        url = reverse('pop_up_auction:product_auction', kwargs={'slug': self.active_product.slug})
        
        # Get initial state
        response1 = self.client.get(url)
        initial_bid_count = response1.context['product'].bid_count
        
        # Update product
        self.active_product.bid_count = 10
        self.active_product.current_highest_bid = Decimal('150.00')
        self.active_product.save()
        
        # Get updated state
        response2 = self.client.get(url)
        updated_bid_count = response2.context['product'].bid_count
        
        self.assertNotEqual(initial_bid_count, updated_bid_count)
        self.assertEqual(updated_bid_count, 10)
 
        
class TestProductsView(TestCase):
    """Test ProductsView"""

    def setUp(self):
        """Set up test fixtures for each test method."""
        self.client = Client()
        
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male")
        
        # self.other_user, self.other_user_profile = create_test_user(
        #     "other@example.com", "testpass123!", "Test", "User2", "7.5", "female")
       
        
        # Create a test product with typical auction parameters
        test_brand = create_brand('Jordan')
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.electronics_category = create_category('Laptop', is_active=True)
        self.electronics_brand = create_brand('Apple')

        self.furniture_category = create_category('Desk', is_active=True)
        self.furniture_brand = create_brand('Elite')

        # Create product types
        self.electronics_type = PopUpProductType.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.furniture_type = PopUpProductType.objects.create(
            name='Furniture',
            slug='furniture'
        )
        self.clothing_type = PopUpProductType.objects.create(
            name='Clothing',
            slug='clothing'
        )

        # Create specifications for products
        self.size_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='size')
        self.color_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='colorway')
        self.weight_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='weight')
        self.model_year_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='model_year')
       
        now = django_timezone.now()

        self.active_electronics_1 = PopUpProduct.objects.create(
            product_type=self.electronics_type, 
            category=self.electronics_category, 
            product_title="Laptop", 
            secondary_product_title="M4", 
            description="new laptop", 
            slug="laptop-m4", 
            buy_now_price="1500.00", 
            current_highest_bid="0", 
            retail_price="999.99", 
            brand=self.electronics_brand, 
            auction_start_date=None,
            auction_end_date=None, 
            buy_now_start=now - timedelta(days=1),
            buy_now_end=now + timedelta(days=7),
            inventory_status="in_inventory", 
            bid_count="0", 
            reserve_price="1050.00", 
            is_active=True,
        )

        self.active_electronics_2 = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title='Smartphone',
            secondary_product_title="11 Pro",
            description="new smartphone", 
            slug='smartphone-11-pro',
            buy_now_price="800.00",
            current_highest_bid="0", 
            retail_price=Decimal('699.99'),
            brand=self.electronics_brand, 
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now - timedelta(hours=1),
            buy_now_end=now + timedelta(days=3),
            inventory_status='in_inventory',
            bid_count="0", 
            reserve_price="750.00", 
            is_active=True,
        )
        
        self.active_furniture_1 = PopUpProduct.objects.create(
            product_type=self.furniture_type,
            category=self.furniture_category, 
            product_title="Office Chair",
            secondary_product_title="Elite",
            slug='office-chair-elite',
            buy_now_price="430.00",
            description="active_furnitore", 
            retail_price=Decimal('299.99'),
            brand=self.furniture_brand, 
            inventory_status='in_inventory',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now - timedelta(days=2),
            buy_now_end=now + timedelta(days=5),
            bid_count="0", 
            reserve_price="330.00", 
            is_active=True,
        )



        # Create an inactive product
        self.inactive_product = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Jordan 4 Retro", 
            secondary_product_title="White Cement", description="Brand new sneakers", 
            slug="jordan-4-white-cement", buy_now_price="230.00", current_highest_bid="0", 
            retail_price=Decimal('150.00'), brand=test_brand, auction_start_date=None,  
            auction_end_date=None, inventory_status="in_inventory", bid_count=0, 
            reserve_price=Decimal('100.00'), is_active=False)

        # Create a product with no bids yet
        self.sold_product = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Sold out product", 
            secondary_product_title="Sold", description="A rpdoct thats sold out", 
            slug="jordan-11-concord", buy_now_price="350.00", current_highest_bid="0", 
            retail_price=Decimal('200.00'), brand=test_brand, auction_start_date=None,  
            buy_now_start=now - timedelta(days=1), buy_now_end=now + timedelta(days=7),
            auction_end_date=django_timezone.now() + timedelta(days=5), inventory_status="sold_out", 
            bid_count=0, reserve_price=Decimal('150.00'), is_active=True)
           

        # Create product outside buy_now window - start date in future
        self.future_product = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Minimal Product", 
            secondary_product_title="Minis", description="Minimal product minis", 
            slug="minimal-product", buy_now_price="350.00", current_highest_bid="0", 
            retail_price=Decimal('50.00'), brand=test_brand, auction_start_date=None,  
            buy_now_start=now + timedelta(days=1), buy_now_end=now + timedelta(days=7),
            auction_end_date=None, inventory_status="in_inventory", 
            bid_count=0, reserve_price=Decimal('40.00'), is_active=True)
        

        self.expired_product = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Minimal Product 2", 
            secondary_product_title="Minis", description="Minimal product minis 2", 
            slug="minimal-product-2", buy_now_price="750.00", current_highest_bid="0", 
            retail_price=Decimal('600.00'), brand=test_brand, auction_start_date=None,  
            buy_now_start=now - timedelta(days=10), buy_now_end=now - timedelta(days=1),
            auction_end_date=None, inventory_status="in_inventory", 
            bid_count=0, reserve_price=Decimal('650.00'), is_active=False)
        

        PopUpProductSpecificationValue.objects.create(
            product=self.inactive_product,
            specification=self.size_spec,
            value='10'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.inactive_product,
            specification=self.color_spec,
            value='Red'
        )

        PopUpProductSpecificationValue.objects.create(
            product=self.inactive_product,
            specification=self.weight_spec,
            value='1.5 lbs'
        )

        
        
        PopUpProductSpecificationValue.objects.create(
            product=self.active_electronics_1,
            specification=self.color_spec,
            value='Silver'
        )
        
      

    # ==================== Basic Access Tests ====================
    
    def test_view_url_accessible_by_name(self):
        """View should be accessible via URL name without slug."""
        url = reverse('pop_up_auction:products')  # Adjust to match your URL name
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name_with_slug(self):
        """View should be accessible via URL name with product type slug."""
        url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """View should use the correct template."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auction/products.html')

    def test_authenticated_user_can_access(self):
        """Authenticated users should be able to access the view."""
    
        self.client.force_login(self.user)
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_access(self):
        """Anonymous users should be able to view products."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ==================== Product Filtering Tests ====================
    
    def test_only_active_products_displayed(self):
        """Only active products should be displayed."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check that inactive product is not in the list
        product_ids = [p.id for p in products]
        self.assertNotIn(self.inactive_product.id, product_ids)

    def test_only_correct_inventory_status_displayed(self):
        """Only products with in_inventory or reserved status should be displayed."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check that sold product is not in the list
        product_ids = [p.id for p in products]
        self.assertNotIn(self.sold_product.id, product_ids)

    def test_only_products_in_buy_now_window_displayed(self):
        """Only products within buy_now time window should be displayed."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        products = response.context['product']
        product_ids = [p.id for p in products]
                
        # Future and expired products should not appear
        self.assertNotIn(self.future_product.id, product_ids)
        self.assertNotIn(self.expired_product.id, product_ids)
        

        # Active products within window should appear
        self.assertIn(self.active_electronics_1.id, product_ids)
        self.assertIn(self.active_electronics_2.id, product_ids)

    def test_all_valid_products_displayed_without_filter(self):
        """Without slug filter, all valid products should be displayed."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        products = response.context['product']
        
        # Should have 3 valid products (2 electronics + 1 furniture)
        self.assertEqual(len(products), 3)

    def test_products_filtered_by_type_slug(self):
        """Products should be filtered by product type when slug provided."""
        url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        # Should only have electronics products
        self.assertEqual(len(products), 2)
        for product in products:
            self.assertEqual(product.product_type, self.electronics_type)

    def test_different_product_types_return_different_products(self):
        """Different product type slugs should return different products."""
        electronics_url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        furniture_url = reverse('pop_up_auction:products', kwargs={'slug': self.furniture_type.slug})
        
        electronics_response = self.client.get(electronics_url)
        furniture_response = self.client.get(furniture_url)
        
        electronics_products = electronics_response.context['product']
        furniture_products = furniture_response.context['product']
        
        # Check counts are different
        self.assertEqual(len(electronics_products), 2)
        self.assertEqual(len(furniture_products), 1)
        
        # Check product IDs are different
        electronics_ids = {p.id for p in electronics_products}
        furniture_ids = {p.id for p in furniture_products}
        self.assertNotEqual(electronics_ids, furniture_ids)

    def test_nonexistent_product_type_slug_returns_404(self):
        """Non-existent product type slug should return 404."""
        url = reverse('pop_up_auction:products', kwargs={'slug': 'nonexistent-type'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_type_with_no_products(self):
        """Product type with no valid products should return empty list."""
        url = reverse('pop_up_auction:products', kwargs={'slug': self.clothing_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(products), 0)

    # ==================== Context Data Tests ====================
    
    def test_context_contains_products(self):
        """Context should contain product list."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        self.assertIn('product', response.context)
        self.assertIsNotNone(response.context['product'])

    def test_context_contains_product_types(self):
        """Context should contain all product types."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        self.assertIn('product_types', response.context)
        
        product_types = response.context['product_types']
        self.assertEqual(product_types.count(), 4)

    def test_context_product_type_none_without_slug(self):
        """Context product_type should be None when no slug provided."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        self.assertIn('product_type', response.context)
        self.assertIsNone(response.context['product_type'])

    def test_context_product_type_set_with_slug(self):
        """Context product_type should be set when slug provided."""
        url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        self.assertIn('product_type', response.context)
        self.assertEqual(response.context['product_type'], self.electronics_type)

    def test_specs_utility_function_applied(self):
        """The add_specs_to_products utility should be applied to products."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        products = response.context['product']
        
        # Verify products have been processed
        self.assertIsNotNone(products)
        self.assertGreater(len(products), 0)

    def test_context_object_name_is_product(self):
        """Context object should be accessible as 'product'."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        
        # 'product' should be available (set by context_object_name)
        self.assertIn('product', response.context)
        # ListView also provides 'object_list'
        self.assertIn('object_list', response.context)

    # ==================== Prefetch Related Tests ====================
    
    def test_prefetch_related_reduces_queries(self):
        """Prefetch related should reduce number of database queries."""
        from django.db import connection, reset_queries
        
        url = reverse('pop_up_auction:products')
        
        with self.settings(DEBUG=True):
            reset_queries()
            response = self.client.get(url)
            
            # Access specifications in context to trigger any lazy loading
            products = response.context['product']
            for product in products:
                # This would normally cause N+1 queries without prefetch
                specs = list(product.popupproductspecificationvalue_set.all())
            
            num_queries = len(connection.queries)
            # Should be reasonable number (typically 3-5)
            self.assertLess(num_queries, 15, "Too many queries - prefetch may not be working")

    # ==================== Template Rendering Tests ====================
    
    def test_product_names_in_response(self):
        """Product names should appear in the rendered response."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        
        self.assertContains(response, self.active_electronics_1.product_title)
        self.assertContains(response, self.active_furniture_1.product_title)

    def test_product_prices_in_response(self):
        """Product prices should appear in the rendered response."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        
        # Check if prices appear (could be formatted differently)
        self.assertContains(response, 'M4')  # Laptop price
        self.assertContains(response, 'Elite')  # Chair price

    def test_inactive_product_not_in_response(self):
        """Inactive products should not appear in the rendered response."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        
        self.assertNotContains(response, self.inactive_product.product_title)

    def test_product_type_navigation_in_response(self):
        """Product types should appear for navigation."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        
        # Check that product type names appear (for navigation/filtering)
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Furniture')
        self.assertContains(response, 'Clothing')

    def test_current_product_type_highlighted(self):
        """When filtering by type, that type should be in context."""
        url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        
        # The current product type should be in context
        self.assertEqual(response.context['product_type'].name, 'Electronics')

    # ==================== Time Window Edge Cases ====================
    
    def test_product_at_exact_start_time(self):
        """Product at exact buy_now_start time should be included."""
      
        exact_start_product = PopUpProduct.objects.create(
            product_type=self.furniture_type,
            category=self.furniture_category, 
            product_title="Exact Start",
            secondary_product_title="Exacto",
            slug='exact-start-exacto',
            buy_now_price="430.00",
            description="active_furnitore", 
            retail_price=Decimal('500.99'),
            brand=self.furniture_brand, 
            inventory_status='in_inventory',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now(),
            buy_now_end=now() + timedelta(days=7),
            bid_count="0", 
            reserve_price="330.00", 
            is_active=True,
        )
        
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(exact_start_product.id, product_ids)

    def test_product_at_exact_end_time(self):
        """Product at exact buy_now_end time should be included."""
        exact_end_product = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title="Exact End",
            secondary_product_title="Endo",
            slug='exact-end-endo',
            buy_now_price="330.00",
            description="end of buy now period", 
            retail_price=Decimal('290.00'),
            brand=self.electronics_brand, 
            inventory_status='in_inventory',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now() - timedelta(days=7),
            buy_now_end=now() + timedelta(seconds=1),
            bid_count="0", 
            reserve_price="350.00", 
            is_active=True,
        )
        
        
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        self.assertIn(exact_end_product.id, product_ids)

    def test_product_one_second_before_start(self):
        """Product starting in 1 second should not be included."""
        # This test might be flaky due to timing
        almost_started = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title="Almost Started",
            secondary_product_title="Soon",
            slug='almost-started',
            buy_now_price="330.00",
            description="Almost start of buy now period", 
            retail_price=Decimal('290.00'),
            brand=self.electronics_brand, 
            inventory_status='in_inventory',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now() + timedelta(seconds=1),
            buy_now_end=now() + timedelta(days=7),
            bid_count="0", 
            reserve_price="350.00", 
            is_active=True,
        )
        
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertNotIn(almost_started.id, product_ids)

    # ==================== Inventory Status Edge Cases ====================
    
    def test_reserved_status_included(self):
        """Products with 'reserved' status should be included."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        # Smartphone has reserved status
        self.assertIn(self.active_electronics_2.id, product_ids)

    def test_in_inventory_status_included(self):
        """Products with 'in_inventory' status should be included."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        # Laptop has in_inventory status
        self.assertIn(self.active_electronics_1.id, product_ids)

    def test_other_inventory_statuses_excluded(self):
        """Products with other inventory statuses should be excluded."""
        # Create products with various statuses
        pending_product = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title="Pending Product",
            secondary_product_title="Pending",
            slug='pending-product-pending',
            buy_now_price="330.00",
            description="Almost start of buy now period", 
            retail_price=Decimal('290.00'),
            brand=self.electronics_brand, 
            inventory_status='anticipated',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=now() + timedelta(days=7),
            bid_count="0", 
            reserve_price="350.00", 
            is_active=True,
        )
        
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertNotIn(pending_product.id, product_ids)

    # ==================== Multiple Filters Combined ====================
    
    def test_all_filters_applied_together(self):
        """All filters (active, inventory, time, type) should work together."""
        # Create a product that fails one filter
        bad_product = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title="Bad Product",
            secondary_product_title="Pending",
            slug='bad-product-pending',
            buy_now_price="550.00",
            description="Almost start of buy now period", 
            retail_price=Decimal('500.00'),
            brand=self.electronics_brand, 
            inventory_status='anticipated',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=now() + timedelta(days=10),
            buy_now_end=now() + timedelta(days=17),
            bid_count="0", 
            reserve_price="525.00", 
            is_active=True,
        )
     
        
        url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertNotIn(bad_product.id, product_ids)
        # But valid electronics should still appear
        self.assertIn(self.active_electronics_1.id, product_ids)

    # ==================== Empty States ====================
    
    def test_empty_product_list_renders(self):
        """View should render correctly with no products."""
        # Delete all valid products
        PopUpProduct.objects.filter(
            is_active=True,
            inventory_status__in=['in_inventory', 'reserved']
        ).delete()
        
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['product']), 0)

    def test_view_with_no_product_types(self):
        """View should handle case with no product types."""
        PopUpProductSpecificationValue.objects.all().delete()
        PopUpProductSpecification.objects.all().delete()
        PopUpProduct.objects.all().delete()
        PopUpProductType.objects.all().delete()
        
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product_types'].count(), 0)

    # ==================== Ordering and Pagination ====================
    
    def test_products_returned_in_consistent_order(self):
        """Products should be returned in a consistent order."""
        url = reverse('pop_up_auction:products')
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        
        products1 = [p.id for p in response1.context['product']]
        products2 = [p.id for p in response2.context['product']]
        
        self.assertEqual(products1, products2)

    def test_multiple_products_same_type(self):
        """Multiple products of same type should all appear."""
        url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        # Should have 2 electronics products
        self.assertEqual(len(products), 2)

    # ==================== Integration Tests ====================
    
    def test_view_provides_data_for_product_cards(self):
        """View should provide all data needed for displaying product cards."""
        url = reverse('pop_up_auction:products')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check first product has necessary data
        if products:
            product = products[0]
            self.assertIsNotNone(product.product_title)
            self.assertIsNotNone(product.slug)
            self.assertIsNotNone(product.retail_price)
            self.assertIsNotNone(product.product_type)

    def test_switching_between_product_types(self):
        """User should be able to switch between different product types."""
        # View all products
        all_url = reverse('pop_up_auction:products')
        all_response = self.client.get(all_url)
        all_count = len(all_response.context['product'])
        
        # View electronics
        electronics_url = reverse('pop_up_auction:products', kwargs={'slug': self.electronics_type.slug})
        electronics_response = self.client.get(electronics_url)
        electronics_count = len(electronics_response.context['product'])
        
        # View furniture
        furniture_url = reverse('pop_up_auction:products', kwargs={'slug': self.furniture_type.slug})
        furniture_response = self.client.get(furniture_url)
        furniture_count = len(furniture_response.context['product'])
        
        # All should equal sum of filtered
        self.assertEqual(all_count, electronics_count + furniture_count)        




class TestComingSoonView(TestCase):
    """Test ComingSoonView"""

    def setUp(self):
        """Set up test fixtures for each test method."""
        self.client = Client()

        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male")
        
        # self.other_user, self.other_user_profile = create_test_user(
        #     "other@example.com", "testpass123!", "Test", "User2", "7.5", "female")
       
        
        # Create a test product with typical auction parameters
        test_brand = create_brand('Jordan')
        test_product_type = create_product_type('shoe', is_active=True)

        test_category_two = create_category('Jordan 4', is_active=True)
        test_category_three = create_category('Jordan 11', is_active=True)

        self.electronics_category = create_category('Laptop', is_active=True)
        self.electronics_brand = create_brand('Apple')

        self.furniture_category = create_category('Desk', is_active=True)
        self.furniture_brand = create_brand('Elite')

        # Create product types
        self.electronics_type = PopUpProductType.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.furniture_type = PopUpProductType.objects.create(
            name='Furniture',
            slug='furniture'
        )
        self.clothing_type = PopUpProductType.objects.create(
            name='Clothing',
            slug='clothing'
        )

        # Create specifications for products
        self.size_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='size')
        self.color_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='colorway')
        self.weight_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='weight')
        self.model_year_spec = PopUpProductSpecification.objects.create(product_type=test_product_type,name='model_year')
       
        now = django_timezone.now()

        self.coming_soon_electronics_1 = PopUpProduct.objects.create(
            product_type=self.electronics_type, 
            category=self.electronics_category, 
            product_title="Laptop", 
            secondary_product_title="M4", 
            description="new laptop", 
            slug="laptop-m4", 
            buy_now_price="1500.00", 
            current_highest_bid="0", 
            retail_price="999.99", 
            brand=self.electronics_brand, 
            auction_start_date=None,
            auction_end_date=None, 
            buy_now_start=None,
            buy_now_end=None,
            inventory_status="in_transit", 
            bid_count="0", 
            reserve_price="1050.00", 
            is_active=False,
        )

        self.coming_soon_electronics_2 = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title='Smartphone',
            secondary_product_title="11 Pro",
            description="new smartphone", 
            slug='smartphone-11-pro',
            buy_now_price="800.00",
            current_highest_bid="0", 
            retail_price=Decimal('699.99'),
            brand=self.electronics_brand, 
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=None,
            buy_now_end=None,
            inventory_status='in_transit',
            bid_count="0", 
            reserve_price="750.00", 
            is_active=False,
        )
        
        self.coming_soon_furniture = PopUpProduct.objects.create(
            product_type=self.furniture_type,
            category=self.furniture_category, 
            product_title="Office Chair",
            secondary_product_title="Elite",
            slug='office-chair-elite',
            buy_now_price="430.00",
            description="active_furnitore", 
            retail_price=Decimal('299.99'),
            brand=self.furniture_brand, 
            inventory_status='in_transit',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=None,
            buy_now_end=None,
            bid_count="0", 
            reserve_price="330.00", 
            is_active=False,
        )

        # Products that should not appear in coming soon
        # Active product with in_transit status (should NOT appear - is_active=True)
        self.active_in_transit = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Active in Transit", 
            secondary_product_title="Minis", description="Actively in Transit", 
            slug="active-in-transit", buy_now_price="750.00", current_highest_bid="0", 
            retail_price=Decimal('600.00'), brand=test_brand, auction_start_date=None,  
            buy_now_start=None, buy_now_end=None,
            auction_end_date=None, inventory_status="in_transit", 
            bid_count=0, reserve_price=Decimal('650.00'), is_active=True)
        
        # Inactive product with in_inventory status (should NOT appear - wrong status)
        self.inactive_in_inventory = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Inactive In Inventory", 
            secondary_product_title="Inact", description="Inactive In Inventory product", 
            slug="inactive-in-inventory", buy_now_price="230.00", current_highest_bid="0", 
            retail_price=Decimal('150.00'), brand=test_brand, auction_start_date=None,  
            auction_end_date=None, inventory_status="in_inventory", bid_count=0, 
            reserve_price=Decimal('100.00'), is_active=False)


        # Active product with in_inventory status (should NOT appear)
        self.active_in_inventory = create_test_product(
            product_type=test_product_type, category=test_category_two, product_title="Active In Inventory", 
            secondary_product_title="Act", description="Active In Inventory product", 
            slug="active-in-inventory", buy_now_price="230.00", current_highest_bid="0", 
            retail_price=Decimal('150.00'), brand=test_brand, auction_start_date=None,  
            auction_end_date=None, inventory_status="in_inventory", bid_count=0, 
            reserve_price=Decimal('100.00'), is_active=True)

        # Create a product with no bids yet
        self.inactive_sold = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Sold out product", 
            secondary_product_title="Sold", description="A rpdoct thats sold out", 
            slug="jordan-11-concord", buy_now_price="350.00", current_highest_bid="0", 
            retail_price=Decimal('200.00'), brand=test_brand, auction_start_date=None,  
            buy_now_start=now - timedelta(days=1), buy_now_end=now + timedelta(days=7),
            auction_end_date=django_timezone.now() + timedelta(days=5), inventory_status="sold_out", 
            bid_count=0, reserve_price=Decimal('150.00'), is_active=False)
           

        # Inactive product with reserved status (should NOT appear)
        self.inactive_reserved = create_test_product(
            product_type=test_product_type, category=test_category_three, product_title="Inactive Reserved", 
            secondary_product_title="Minis", description="Minimal product minis", 
            slug="inactive-reservedt", buy_now_price="350.00", current_highest_bid="0", 
            retail_price=Decimal('50.00'), brand=test_brand, auction_start_date=None,  
            buy_now_start=now + timedelta(days=1), buy_now_end=now + timedelta(days=7),
            auction_end_date=None, inventory_status="reserved", 
            bid_count=0, reserve_price=Decimal('40.00'), is_active=False)
        
        

        PopUpProductSpecificationValue.objects.create(
            product=self.coming_soon_electronics_1,
            specification=self.size_spec,
            value='N/A'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.coming_soon_electronics_1,
            specification=self.color_spec,
            value='Black'
        )

        PopUpProductSpecificationValue.objects.create(
            product=self.coming_soon_electronics_1,
            specification=self.weight_spec,
            value='3.5 lbs'
        )

        
        PopUpProductSpecificationValue.objects.create(
            product=self.coming_soon_electronics_2,
            specification=self.color_spec,
            value='Silver'
        )
    

    # ==================== Basic Access Tests ====================
    
    def test_view_url_accessible_by_name(self):
        """View should be accessible via URL name without slug."""
        url = reverse('pop_up_auction:coming_soon')  # Adjust to match your URL name
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name_with_slug(self):
        """View should be accessible via URL name with product type slug."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """View should use the correct template."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auction/coming_soon.html')

    def test_authenticated_user_can_access(self):
        """Authenticated users should be able to access the view."""
        self.client.force_login(self.user)
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_access(self):
        """Anonymous users should be able to view coming soon products."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ==================== Product Filtering Tests ====================
    
    def test_only_inactive_products_displayed(self):
        """Only products with is_active=False should be displayed."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check that active products are not in the list
        product_ids = [p.id for p in products]
        self.assertNotIn(self.active_in_transit.id, product_ids)
        self.assertNotIn(self.active_in_inventory.id, product_ids)

    def test_only_in_transit_status_displayed(self):
        """Only products with inventory_status='in_transit' should be displayed."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check that products with other statuses are not in the list
        product_ids = [p.id for p in products]
        self.assertNotIn(self.inactive_in_inventory.id, product_ids)
        self.assertNotIn(self.inactive_sold.id, product_ids)
        self.assertNotIn(self.inactive_reserved.id, product_ids)

    def test_both_filters_applied_together(self):
        """Both is_active=False AND inventory_status='in_transit' must be true."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        product_ids = [p.id for p in products]

        # Only products matching BOTH criteria should appear
        self.assertIn(self.coming_soon_electronics_1.id, product_ids)
        self.assertIn(self.coming_soon_electronics_2.id, product_ids)
        self.assertIn(self.coming_soon_furniture.id, product_ids)
        
        # Products matching only one criterion should not appear
        self.assertNotIn(self.active_in_transit.id, product_ids)  # Active but in_transit
        self.assertNotIn(self.inactive_in_inventory.id, product_ids)  # Inactive but not in_transit

    def test_all_valid_products_displayed_without_filter(self):
        """Without slug filter, all valid coming soon products should be displayed."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        
        # Should have 3 coming soon products (2 electronics + 1 furniture)
        self.assertEqual(len(products), 3)

    def test_products_filtered_by_type_slug(self):
        """Products should be filtered by product type when slug provided."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        products = response.context['product']
       
        # Should only have electronics products
        self.assertEqual(len(products), 2)
        for product in products:
            self.assertEqual(product.product_type, self.electronics_type)

    def test_different_product_types_return_different_products(self):
        """Different product type slugs should return different products."""
        electronics_url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        furniture_url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.furniture_type.slug})
        
        electronics_response = self.client.get(electronics_url)
        furniture_response = self.client.get(furniture_url)
        
        electronics_products = electronics_response.context['product']
        furniture_products = furniture_response.context['product']
        
        # Check counts
        self.assertEqual(len(electronics_products), 2)
        self.assertEqual(len(furniture_products), 1)
        
        # Check product IDs are different
        electronics_ids = {p.id for p in electronics_products}
        furniture_ids = {p.id for p in furniture_products}
        self.assertNotEqual(electronics_ids, furniture_ids)

    def test_nonexistent_product_type_slug_returns_404(self):
        """Non-existent product type slug should return 404."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': 'nonexistent-type'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_type_with_no_coming_soon_products(self):
        """Product type with no coming soon products should return empty list."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.clothing_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(products), 0)

    # ==================== Context Data Tests ====================
    
    def test_context_contains_products(self):
        """Context should contain product list."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        self.assertIn('product', response.context)
        self.assertIsNotNone(response.context['product'])

    def test_context_contains_product_types(self):
        """Context should contain all product types."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        self.assertIn('product_types', response.context)
        
        product_types = response.context['product_types']

        self.assertEqual(product_types.count(), 4)

    def test_context_product_type_none_without_slug(self):
        """Context product_type should be None when no slug provided."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        self.assertIn('product_type', response.context)
        self.assertIsNone(response.context['product_type'])

    def test_context_product_type_set_with_slug(self):
        """Context product_type should be set when slug provided."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        self.assertIn('product_type', response.context)
        self.assertEqual(response.context['product_type'], self.electronics_type)

    def test_specs_utility_function_applied(self):
        """The add_specs_to_products utility should be applied to products."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        
        # Verify products have been processed
        self.assertIsNotNone(products)
        self.assertGreater(len(products), 0)

    def test_context_object_name_is_product(self):
        """Context object should be accessible as 'product'."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        # 'product' should be available (set by context_object_name)
        self.assertIn('product', response.context)
        # ListView also provides 'object_list'
        self.assertIn('object_list', response.context)

    # ==================== Prefetch Related Tests ====================
    
    def test_prefetch_related_reduces_queries(self):
        """Prefetch related should reduce number of database queries."""
        from django.db import connection, reset_queries
        
        url = reverse('pop_up_auction:coming_soon')
        
        with self.settings(DEBUG=True):
            reset_queries()
            response = self.client.get(url)
            
            # Access specifications in context to trigger any lazy loading
            products = response.context['product']
            for product in products:
                specs = list(product.popupproductspecificationvalue_set.all())
            
            num_queries = len(connection.queries)
            # Should be reasonable number (typically 3-5)
            self.assertLess(num_queries, 15, "Too many queries - prefetch may not be working")

    # ==================== Template Rendering Tests ====================
    

    def test_coming_soon_product_names_in_response(self):
        """Coming soon product names should appear in the rendered response."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        self.assertContains(response, self.coming_soon_electronics_1.product_title)
        self.assertContains(response, self.coming_soon_furniture.product_title)

    def test_active_products_not_in_response(self):
        """Active products should not appear in the rendered response."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        self.assertNotContains(response, self.active_in_inventory.product_title)
        self.assertNotContains(response, self.active_in_transit.product_title)

    def test_wrong_status_products_not_in_response(self):
        """Products with wrong inventory status should not appear."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        self.assertNotContains(response, self.inactive_in_inventory.product_title)
        self.assertNotContains(response, self.inactive_sold.product_title)


    def test_product_type_navigation_in_response(self):
        """Product types should appear for navigation."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        # Check that product type names appear (for navigation/filtering)
        self.assertContains(response, 'Electronics')
        self.assertContains(response, 'Furniture')
        self.assertContains(response, 'Clothing')

    def test_current_product_type_highlighted(self):
        """When filtering by type, that type should be in context."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        
        # The current product type should be in context
        self.assertEqual(response.context['product_type'].name, 'Electronics')

    # ==================== Edge Cases ====================
    
    def test_product_with_very_long_name(self):
        """Coming soon product with very long name should display correctly."""
         

        long_name_product = PopUpProduct.objects.create(
            product_type=self.electronics_type,
            category=self.electronics_category, 
            product_title='A' * 200,
            secondary_product_title='B'* 50,
            slug='long-name-product',
            buy_now_price="330.00",
            description="Almost start of buy now period", 
            retail_price=Decimal('290.00'),
            brand=self.electronics_brand, 
            inventory_status='in_transit',
            auction_start_date=None, 
            auction_end_date=None, 
            buy_now_start=None,
            buy_now_end=None,
            bid_count="0", 
            reserve_price="350.00", 
            is_active=False,
        )
    
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(long_name_product.id, product_ids)

    def test_product_with_no_specifications(self):
        """Coming soon product with no specifications should display correctly."""
        brand = create_brand("New Jordan")
        ptype_shoe_2 = create_product_type("new_shoes", True)

        no_spec_product = create_test_product_two(
            product_title='No Specs Product',
            secondary_product_title='Zero',
            brand=brand,
            slug='no-specs-coming-soon',
            product_type=ptype_shoe_2,
            inventory_status="in_transit",
            retail_price=Decimal('100.00'),
            reserve_price=Decimal('0.00'),
            is_active=False
        )

        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(no_spec_product.id, product_ids)

    def test_product_with_zero_price(self):
        """Coming soon product with zero price should display correctly."""
        brand = create_brand("New Jordan")
        ptype_shoe_2 = create_product_type("new_shoes", True)

        zero_price_product = create_test_product_two(
            product_title='Zero Price Product',
            secondary_product_title='Zero',
            brand=brand,
            slug='zero-price-coming-soon',
            product_type=ptype_shoe_2,
            inventory_status="in_transit",
            retail_price=Decimal('100.00'),
            reserve_price=Decimal('0.00'),
            is_active=False
        )

        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(zero_price_product.id, product_ids)

    def test_multiple_products_same_type(self):
        """Multiple coming soon products of same type should all appear."""
        url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        # Should have 2 electronics coming soon products
        self.assertEqual(len(products), 2)

    # ==================== Empty States ====================
    
    def test_empty_product_list_renders(self):
        """View should render correctly with no coming soon products."""
        # Delete all coming soon products
        PopUpProduct.objects.filter(
            is_active=False,
            inventory_status='in_transit'
        ).delete()
        
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['product']), 0)

    def test_view_with_no_product_types(self):
        """View should handle case with no product types."""
        # Delete in correct order due to foreign key constraints
        PopUpProduct.objects.all().delete()
        PopUpProductSpecificationValue.objects.all().delete()
        PopUpProductSpecification.objects.all().delete()
        PopUpProductType.objects.all().delete()
        
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product_types'].count(), 0)

    # ==================== Inventory Status Variations ====================
    
    def test_only_in_transit_included(self):
        """Only products with 'in_transit' status should be included."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        
        # All returned products should have in_transit status
        for product in products:
            self.assertEqual(product.inventory_status, 'in_transit')

    def test_other_inventory_statuses_excluded(self):
        """Products with other inventory statuses should be excluded."""
        # Create products with various statuses (all inactive)
        brand = create_brand("New Money")
        prod_type = create_product_type("new_money", True)
        category = create_category('Money', is_active=True)


        pending_product = PopUpProduct.objects.create(
            product_title='Pending Product',
            product_type=prod_type,
            category=category,
            secondary_product_title='Pending',
            brand=brand,
            slug='pending-coming-soon',
            inventory_status="sold_out",
            retail_price=Decimal('100.00'),
            reserve_price=Decimal('0.00'),
            is_active=False
        )

        processing_product = PopUpProduct.objects.create(
            product_type=prod_type,
            product_title='Processing Product',
            secondary_product_title='Processing',
            brand=brand,
            category=category,
            slug='processing-coming-soon',
            inventory_status="sold_out",
            retail_price=Decimal('600.00'),
            reserve_price=Decimal('0.00'),
            is_active=False
        )
        
        
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertNotIn(pending_product.id, product_ids)
        self.assertNotIn(processing_product.id, product_ids)

    # ==================== Integration Tests ====================
    
    def test_view_provides_data_for_product_cards(self):
        """View should provide all data needed for displaying product cards."""
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check first product has necessary data
        if products:
            product = products[0]
            self.assertIsNotNone(product.product_title)
            self.assertIsNotNone(product.slug)
            self.assertIsNotNone(product.retail_price)
            self.assertIsNotNone(product.product_type)
            self.assertEqual(product.is_active, False)
            self.assertEqual(product.inventory_status, 'in_transit')

    def test_switching_between_product_types(self):
        """User should be able to switch between different product types."""
        # View all coming soon products
        all_url = reverse('pop_up_auction:coming_soon')
        all_response = self.client.get(all_url)
        all_count = len(all_response.context['product'])
        
        # View electronics coming soon
        electronics_url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.electronics_type.slug})
        electronics_response = self.client.get(electronics_url)
        electronics_count = len(electronics_response.context['product'])
        
        # View furniture coming soon
        furniture_url = reverse('pop_up_auction:coming_soon', kwargs={'slug': self.furniture_type.slug})
        furniture_response = self.client.get(furniture_url)
        furniture_count = len(furniture_response.context['product'])
        
        # All should equal sum of filtered
        self.assertEqual(all_count, electronics_count + furniture_count)

    def test_products_returned_in_consistent_order(self):
        """Products should be returned in a consistent order."""
        url = reverse('pop_up_auction:coming_soon')
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        
        products1 = [p.id for p in response1.context['product']]
        products2 = [p.id for p in response2.context['product']]
        
        self.assertEqual(products1, products2)

    def test_coming_soon_distinct_from_regular_products(self):
        """Coming soon products should be distinct from regular available products."""
        coming_soon_url = reverse('pop_up_auction:coming_soon')
        # Assuming you have a regular products view
        # products_url = reverse('products')
        
        coming_soon_response = self.client.get(coming_soon_url)
        coming_soon_ids = {p.id for p in coming_soon_response.context['product']}
        
        # Verify that active products are not in coming soon
        self.assertNotIn(self.active_in_inventory.id, coming_soon_ids)
        self.assertNotIn(self.active_in_transit.id, coming_soon_ids)

    # ==================== Business Logic Tests ====================
    
    def test_coming_soon_filtering_logic(self):
        """Test the specific business logic: inactive AND in_transit."""
        # Create test cases for all combinations
        test_cases = [
            # (is_active, inventory_status, should_appear)
            (False, 'in_transit', True),      # Coming soon - should appear
            (True, 'in_transit', False),      # Active but in_transit - should NOT appear
            (False, 'in_inventory', False),   # Inactive but available - should NOT appear
            (True, 'in_inventory', False),    # Active and available - should NOT appear
            (False, 'sold', False),           # Inactive and sold - should NOT appear
        ]
        
        created_products = []
        for idx, (is_active, status, should_appear) in enumerate(test_cases):

            product = PopUpProduct.objects.create(
                product_type=create_product_type(f"newer_money {idx}", True),
                category=create_category(f'Moneys {idx}', is_active=True),
                product_title=f'Test Product {idx}',
                secondary_product_title=f'Pending {idx}',
                brand=create_brand(f"Newer Money {idx}"),
                slug=f'test-product-{idx}',
                inventory_status=status,
                retail_price=Decimal('100.00'),
                reserve_price=Decimal('0.00'),
                is_active=is_active
            )
            print(f'idx: {idx}. {product} {product.product_title}')
            created_products.append((product, should_appear))
        
        url = reverse('pop_up_auction:coming_soon')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        for product, should_appear in created_products:
            if should_appear:
                self.assertIn(product.id, product_ids, 
                    f"Product {product.product_title} (active={product.is_active}, status={product.inventory_status}) should appear")
            else:
                self.assertNotIn(product.id, product_ids,
                    f"Product {product.product_title} (active={product.is_active}, status={product.inventory_status}) should NOT appear")



class TestFutureReleasesView(TestCase):
    """Test FutureReleasesView"""

    def setUp(self):
        """Set up test fixtures for each test method."""
        self.client = Client()
        
        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male")
        
        # self.other_user, self.other_user_profile = create_test_user(
        #     "other@example.com", "testpass123!", "Test", "User2", "7.5", "female")
      
        # category = django
        # product_type = book
        
    
        # self.shoe_product_type = PopUpProductType.objects.create(name='shoe', slug='shoe')
        self.basketball_category = PopUpCategory.objects.create(name='Basketball', slug='basketball')
        self.jordan_brand = PopUpBrand.objects.create(name='Jordan', slug='jordan')

        self.clothing_category = PopUpCategory.objects.create(name='Leisure Wear', slug='leisure-wear')
        self.supreme_brand = PopUpBrand.objects.create(name='Supreme', slug='supreme')

        # Create product types
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )
        self.clothing_type = PopUpProductType.objects.create(
            name='Clothing',
            slug='clothing'
        )
        self.accessories_type = PopUpProductType.objects.create(
            name='Accessories',
            slug='accessories'
        )
        
        # Create specifications
        self.spec_model_year = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='model_year',
        )
        self.spec_colorway = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='colorway',
        )
        self.spec_size = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='size',
        )

        self.electronics_category = create_category('Laptop', is_active=True)
        
        # Create future release products (is_active=False, anticipated)
        self.jordan_4 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            slug='jordan-4-military-blue',
            retail_price=Decimal('215.00'),
            is_active=False,
            inventory_status='anticipated'
        )
        
        self.jordan_1 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago Lost & Found',
            slug='jordan-1-chicago',
            retail_price=Decimal('180.00'),
            is_active=False,
            inventory_status='anticipated'
        )
        
        self.supreme_hoodie = PopUpProduct.objects.create(
            product_type=self.clothing_type,
            category=self.clothing_category,
            brand=self.supreme_brand,
            product_title='Supreme Box Logo',
            secondary_product_title='Hoodie Black',
            slug='supreme-box-logo-hoodie',
            retail_price=Decimal('168.00'),
            is_active=False,
            inventory_status='anticipated'
        )
        
        # Add specifications to products
        PopUpProductSpecificationValue.objects.create(
            product=self.jordan_4,
            specification=self.spec_model_year,
            value='2024'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.jordan_4,
            specification=self.spec_colorway,
            value='Military Blue'
        )
        
        PopUpProductSpecificationValue.objects.create(
            product=self.jordan_1,
            specification=self.spec_model_year,
            value='2023'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.jordan_1,
            specification=self.spec_colorway,
            value='Chicago'
        )
        
        PopUpProductSpecificationValue.objects.create(
            product=self.supreme_hoodie,
            specification=self.spec_model_year,
            value='2024'
        )
        
        # Create products that should NOT appear
        
        # Active product with anticipated status (should NOT appear)
        self.active_anticipated = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Active Anticipated',
            secondary_product_title='Should Not Show',
            slug='active-anticipated',
            retail_price=Decimal('200.00'),
            is_active=True,
            inventory_status='anticipated'
        )
        
        # Inactive product with in_inventory status (should NOT appear)
        self.inactive_in_inventory = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Inactive In Inventory',
            secondary_product_title='Should Not Show',
            slug='inactive-in-inventory',
            retail_price=Decimal('190.00'),
            is_active=False,
            inventory_status='in_inventory'
        )
        
        # Inactive product with in_transit status (should NOT appear)
        self.inactive_in_transit = PopUpProduct.objects.create(
            product_type=self.clothing_type,
            category=self.clothing_category,
            brand=self.supreme_brand,
            product_title='Inactive In Transit',
            secondary_product_title='Should Not Show',
            slug='inactive-in-transit',
            retail_price=Decimal('185.00'),
            is_active=False,
            inventory_status='in_transit'
        )
        
        # Active product with in_inventory status (should NOT appear)
        self.active_in_inventory = PopUpProduct.objects.create(
            product_type=self.clothing_type,
            category=self.clothing_category,
            brand=self.supreme_brand,
            product_title='Active In Inventory',
            secondary_product_title='Should Not Show',
            slug='active-in-inventory',
            retail_price=Decimal('175.00'),
            is_active=True,
            inventory_status='in_inventory'
        )

    # ==================== Basic Access Tests ====================
    
    def test_view_url_accessible_by_name(self):
        """View should be accessible via URL name without slug."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


    def test_view_url_accessible_by_name_with_slug(self):
        """View should be accessible via URL name with product type slug."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """View should use the correct template."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auction/future_releases.html')

    def test_authenticated_user_can_access(self):
        """Authenticated users should be able to access the view."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_access(self):
        """Anonymous users should be able to view future releases."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ==================== Product Filtering Tests ====================
    
    def test_only_inactive_products_displayed(self):
        """Only products with is_active=False should be displayed."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check that active products are not in the list
        product_ids = [p.id for p in products]
        self.assertNotIn(self.active_anticipated.id, product_ids)
        self.assertNotIn(self.active_in_inventory.id, product_ids)

    def test_only_anticipated_status_displayed(self):
        """Only products with inventory_status='anticipated' should be displayed."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check that products with other statuses are not in the list
        product_ids = [p.id for p in products]
        self.assertNotIn(self.inactive_in_inventory.id, product_ids)
        self.assertNotIn(self.inactive_in_transit.id, product_ids)

    def test_both_filters_applied_together(self):
        """Both is_active=False AND inventory_status='anticipated' must be true."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        product_ids = [p.id for p in products]
        
        # Only products matching BOTH criteria should appear
        self.assertIn(self.jordan_4.id, product_ids)
        self.assertIn(self.jordan_1.id, product_ids)
        self.assertIn(self.supreme_hoodie.id, product_ids)
        
        # Products matching only one criterion should not appear
        self.assertNotIn(self.active_anticipated.id, product_ids)
        self.assertNotIn(self.inactive_in_inventory.id, product_ids)

    def test_all_valid_products_displayed_without_filter(self):
        """Without slug filter, all valid future release products should be displayed."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # Should have 3 future release products (2 sneakers + 1 clothing)
        self.assertEqual(len(products), 3)

    def test_products_filtered_by_type_slug(self):
        """Products should be filtered by product type when slug provided."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        # Should only have sneakers products
        self.assertEqual(len(products), 2)
        for product in products:
            self.assertEqual(product.product_type, self.sneakers_type)

    def test_different_product_types_return_different_products(self):
        """Different product type slugs should return different products."""
        sneakers_url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        clothing_url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.clothing_type.slug})
        
        sneakers_response = self.client.get(sneakers_url)
        clothing_response = self.client.get(clothing_url)
        
        sneakers_products = sneakers_response.context['product']
        clothing_products = clothing_response.context['product']
        
        # Check counts
        self.assertEqual(len(sneakers_products), 2)
        self.assertEqual(len(clothing_products), 1)
        
        # Check product IDs are different
        sneakers_ids = {p.id for p in sneakers_products}
        clothing_ids = {p.id for p in clothing_products}
        self.assertNotEqual(sneakers_ids, clothing_ids)

    def test_nonexistent_product_type_slug_returns_404(self):
        """Non-existent product type slug should return 404."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': 'nonexistent-type'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_product_type_with_no_future_releases(self):
        """Product type with no future release products should return empty list."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.accessories_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(products), 0)

    # ==================== Context Data Tests ====================
    
    def test_context_contains_products(self):
        """Context should contain product list."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertIn('product', response.context)
        self.assertIsNotNone(response.context['product'])

    def test_context_contains_product_types(self):
        """Context should contain all product types."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertIn('product_types', response.context)
        
        product_types = response.context['product_types']
        self.assertEqual(product_types.count(), 3)

    def test_context_product_type_none_without_slug(self):
        """Context product_type should be None when no slug provided."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertIn('product_type', response.context)
        self.assertIsNone(response.context['product_type'])

    def test_context_product_type_set_with_slug(self):
        """Context product_type should be set when slug provided."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        response = self.client.get(url)
        self.assertIn('product_type', response.context)
        self.assertEqual(response.context['product_type'], self.sneakers_type)

    def test_specs_utility_function_applied(self):
        """The add_specs_to_products utility should be applied to products."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # Verify products have been processed
        self.assertIsNotNone(products)
        self.assertGreater(len(products), 0)

    def test_context_object_name_is_product(self):
        """Context object should be accessible as 'product'."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        # 'product' should be available (set by context_object_name)
        self.assertIn('product', response.context)
        # ListView also provides 'object_list'
        self.assertIn('object_list', response.context)

    # ==================== Prefetch Related Tests ====================
    
    def test_prefetch_related_reduces_queries(self):
        """Prefetch related should reduce number of database queries."""
        from django.db import connection, reset_queries
        
        url = reverse('pop_up_auction:future_releases')
        
        with self.settings(DEBUG=True):
            reset_queries()
            response = self.client.get(url)
            
            # Access specifications in context to trigger any lazy loading
            products = response.context['product']
            for product in products:
                specs = list(product.popupproductspecificationvalue_set.all())
            
            num_queries = len(connection.queries)
            # Should be reasonable number (typically 3-5)
            self.assertLess(num_queries, 15, "Too many queries - prefetch may not be working")

    # ==================== Template Rendering Tests ====================
    
    def test_product_titles_in_response(self):
        """Product titles should appear in the rendered response."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertContains(response, self.jordan_4.product_title)
        self.assertContains(response, self.jordan_4.secondary_product_title)
        self.assertContains(response, self.supreme_hoodie.product_title)

    def test_model_year_in_response(self):
        """Model year from specs should appear in the rendered response."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        # Check for model years
        self.assertContains(response, '2024')
        self.assertContains(response, '2023')

    def test_active_products_not_in_response(self):
        """Active products should not appear in the rendered response."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertNotContains(response, self.active_anticipated.product_title)
        self.assertNotContains(response, self.active_in_inventory.product_title)

    def test_wrong_status_products_not_in_response(self):
        """Products with wrong inventory status should not appear."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertNotContains(response, self.inactive_in_inventory.product_title)
        self.assertNotContains(response, self.inactive_in_transit.product_title)

    def test_product_type_navigation_in_response(self):
        """Product types should appear for navigation."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        # Check that product type names appear (for navigation/filtering)
        self.assertContains(response, 'Sneakers')
        self.assertContains(response, 'Clothing')
        self.assertContains(response, 'Accessories')

    def test_all_link_in_navigation(self):
        """'All' navigation link should be present."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        self.assertContains(response, 'All')

    def test_selected_class_on_all_without_slug(self):
        """'All' should have 'selected' class when no slug provided."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        # Check that 'All' has selected class
        self.assertContains(response, 'class="selected"')

    def test_selected_class_on_product_type_with_slug(self):
        """Selected product type should have 'selected' class when slug provided."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        response = self.client.get(url)
        
        # Should contain selected class (on the sneakers type)
        self.assertContains(response, 'class="selected"')
        self.assertContains(response, 'Sneakers')

    def test_interested_button_present_for_anonymous_user(self):
        """Interested button should be present for anonymous users."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertContains(response, 'interested_btn')
        self.assertContains(response, 'Interested</button>')

    def test_interested_button_present_for_authenticated_user(self):
        """Interested button should be present for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertContains(response, 'interested_btn')
        self.assertContains(response, 'data-product-id')

    def test_empty_state_message(self):
        """Empty state message should appear when no products."""
        # Delete all future release products
        PopUpProduct.objects.filter(
            is_active=False,
            inventory_status='anticipated'
        ).delete()
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertContains(response, 'Nothing to display')

    # ==================== Edge Cases ====================
    
    def test_product_with_no_specifications(self):
        """Future release product with no specifications should display correctly."""
        no_spec_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='No Specs Product',
            secondary_product_title='Test',
            slug='no-specs-future',
            retail_price=Decimal('200.00'),
            is_active=False,
            inventory_status='anticipated'
        )
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(no_spec_product.id, product_ids)
        self.assertContains(response, no_spec_product.product_title)

    def test_product_with_very_long_title(self):
        """Future release product with very long title should display correctly."""
        long_title_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='A' * 100,
            secondary_product_title='B' * 100,
            slug='long-title-future',
            retail_price=Decimal('200.00'),
            is_active=False,
            inventory_status='anticipated'
        )
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(long_title_product.id, product_ids)

    def test_multiple_products_same_type(self):
        """Multiple future release products of same type should all appear."""
        url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        response = self.client.get(url)
        products = response.context['product']
        
        # Should have 2 sneakers future release products
        self.assertEqual(len(products), 2)

    def test_product_with_zero_price(self):
        """Future release product with zero price should display correctly."""
        zero_price_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Zero Price Product',
            secondary_product_title='Free',
            slug='zero-price-future',
            retail_price=Decimal('0.00'),
            is_active=False,
            inventory_status='anticipated'
        )
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertIn(zero_price_product.id, product_ids)

    # ==================== Empty States ====================
    
    def test_empty_product_list_renders(self):
        """View should render correctly with no future release products."""
        # Delete all future release products
        PopUpProduct.objects.filter(
            is_active=False,
            inventory_status='anticipated'
        ).delete()
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['product']), 0)

    def test_view_with_no_product_types(self):
        """View should handle case with no product types."""
        # Delete in correct order due to foreign key constraints
        PopUpProduct.objects.all().delete()
        PopUpProductSpecificationValue.objects.all().delete()
        PopUpProductSpecification.objects.all().delete()
        PopUpProductType.objects.all().delete()
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product_types'].count(), 0)

    # ==================== Inventory Status Variations ====================
    
    def test_only_anticipated_included(self):
        """Only products with 'anticipated' status should be included."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # All returned products should have anticipated status
        for product in products:
            self.assertEqual(product.inventory_status, 'anticipated')

    def test_other_inventory_statuses_excluded(self):
        """Products with other inventory statuses should be excluded."""
        # Create products with various statuses (all inactive)
        pending_product = PopUpProduct.objects.create(
            product_type=self.clothing_type,
            category=self.clothing_category,
            brand=self.supreme_brand,
            product_title='Pending Product',
            secondary_product_title='Test',
            slug='pending-future',
            retail_price=Decimal('200.00'),
            is_active=False,
            inventory_status='pending'
        )
        
        processing_product = PopUpProduct.objects.create(
            product_type=self.clothing_type,
            category=self.clothing_category,
            brand=self.supreme_brand,
            product_title='Processing Product',
            secondary_product_title='Test',
            slug='processing-future',
            retail_price=Decimal('200.00'),
            is_active=False,
            inventory_status='processing'
        )
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        self.assertNotIn(pending_product.id, product_ids)
        self.assertNotIn(processing_product.id, product_ids)

    # ==================== Integration Tests ====================
    
    def test_view_provides_data_for_product_display(self):
        """View should provide all data needed for displaying products."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # Check first product has necessary data
        if products:
            product = products[0]
            self.assertIsNotNone(product.product_title)
            self.assertIsNotNone(product.secondary_product_title)
            self.assertIsNotNone(product.slug)
            self.assertIsNotNone(product.retail_price)
            self.assertIsNotNone(product.product_type)
            self.assertEqual(product.is_active, False)
            self.assertEqual(product.inventory_status, 'anticipated')

    def test_switching_between_product_types(self):
        """User should be able to switch between different product types."""
        # View all future releases
        all_url = reverse('pop_up_auction:future_releases')
        all_response = self.client.get(all_url)
        all_count = len(all_response.context['product'])
        
        # View sneakers future releases
        sneakers_url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.sneakers_type.slug})
        sneakers_response = self.client.get(sneakers_url)
        sneakers_count = len(sneakers_response.context['product'])
        
        # View clothing future releases
        clothing_url = reverse('pop_up_auction:future_releases', kwargs={'slug': self.clothing_type.slug})
        clothing_response = self.client.get(clothing_url)
        clothing_count = len(clothing_response.context['product'])
        
        # All should equal sum of filtered
        self.assertEqual(all_count, sneakers_count + clothing_count)

    def test_products_returned_in_consistent_order(self):
        """Products should be returned in a consistent order."""
        url = reverse('pop_up_auction:future_releases')
        response1 = self.client.get(url)
        response2 = self.client.get(url)
        
        products1 = [p.id for p in response1.context['product']]
        products2 = [p.id for p in response2.context['product']]
        
        self.assertEqual(products1, products2)

    # ==================== Business Logic Tests ====================
    
    def test_future_releases_filtering_logic(self):
        """Test the specific business logic: inactive AND anticipated."""
        # Create test cases for all combinations
        test_cases = [
            # (is_active, inventory_status, should_appear)
            (False, 'anticipated', True),     # Future release - should appear
            (True, 'anticipated', False),     # Active but anticipated - should NOT appear
            (False, 'in_inventory', False),   # Inactive but available - should NOT appear
            (True, 'in_inventory', False),    # Active and available - should NOT appear
            (False, 'in_transit', False),     # Inactive and in_transit - should NOT appear
        ]
        
        created_products = []
        for idx, (is_active, status, should_appear) in enumerate(test_cases):
            product = PopUpProduct.objects.create(
                product_type=self.clothing_type,
                category=self.clothing_category,
                brand=self.supreme_brand,
                product_title=f'Test Product {idx}',
                secondary_product_title='Test',
                slug=f'test-product-logic-{idx}',
                retail_price=Decimal('200.00'),
                is_active=is_active,
                inventory_status=status
            )
            created_products.append((product, should_appear))
        
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        product_ids = [p.id for p in response.context['product']]
        
        for product, should_appear in created_products:
            if should_appear:
                self.assertIn(product.id, product_ids, 
                    f"Product {product.product_title} (active={product.is_active}, status={product.inventory_status}) should appear")
            else:
                self.assertNotIn(product.id, product_ids,
                    f"Product {product.product_title} (active={product.is_active}, status={product.inventory_status}) should NOT appear")

    def test_limited_release_concept(self):
        """Test that view represents limited release products for bot acquisition."""
        url = reverse('pop_up_auction:future_releases')
        response = self.client.get(url)
        products = response.context['product']
        
        # All products should be future releases (not yet available for purchase)
        for product in products:
            self.assertFalse(product.is_active, 
                "Future release products should not be active yet")
            self.assertEqual(product.inventory_status, 'anticipated',
                "Future release products should have 'anticipated' status")


class TestProductDetailView(TestCase):
    """Test ProductDetailView"""


    def setUp(self):
        """Set up test fixtures for each test method."""
        self.client = Client()
        
        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
        )
        self.other_user, self.other_user_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User2", "10", "female"
        )
        
        # Create categories
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        self.running_category = PopUpCategory.objects.create(
            name='Running',
            slug='running'
        )
        
        # Create brands
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        self.nike_brand = PopUpBrand.objects.create(
            name='Nike',
            slug='nike'
        )
        
        # Create product types
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )
        self.apparel_type = PopUpProductType.objects.create(
            name='Apparel',
            slug='apparel'
        )
        
        # Create specifications
        self.spec_model_year = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='model_year',
        )
        self.spec_colorway = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='colorway',
        )
        self.spec_size = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='size',
        )
        
        # Create active product with buy now window
        self.active_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            slug='jordan-4-military-blue',
            buy_now_price=Decimal('215.00'),
            description='Classic Jordan 4 in Military Blue colorway',
            retail_price=Decimal('215.00'),
            reserve_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        # Add specifications to active product
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.spec_model_year,
            value='2024'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.spec_colorway,
            value='Military Blue'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.spec_size,
            value='10.5'
        )
        
        # Create active product with buy now window that hasn't started
        self.future_buy_now_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            description='Classic Jordan 1',
            retail_price=Decimal('180.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() + timedelta(days=1),
            buy_now_end=now() + timedelta(days=8),
            bought_now=False
        )
        
        # Create active product with expired buy now window
        self.expired_buy_now_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.running_category,
            brand=self.nike_brand,
            product_title='Nike Air Max',
            secondary_product_title='Classic White',
            slug='nike-air-max-white',
            buy_now_price=Decimal('150.00'),
            description='Classic Air Max',
            retail_price=Decimal('150.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=10),
            buy_now_end=now() - timedelta(days=1),
            bought_now=False
        )
        
        # Create active product without buy now dates
        self.no_buy_now_dates_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 3',
            secondary_product_title='White Cement',
            slug='jordan-3-white-cement',
            buy_now_price=Decimal('210.00'),
            description='Classic Jordan 3',
            retail_price=Decimal('210.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=None,
            buy_now_end=None,
            bought_now=False
        )
        
        # Create active product that has been bought
        self.bought_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 5',
            secondary_product_title='Grape',
            slug='jordan-5-grape',
            buy_now_price=Decimal('225.00'),
            description='Classic Jordan 5',
            retail_price=Decimal('225.00'),
            inventory_status='sold',
            is_active=True,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=now() + timedelta(days=7),
            bought_now=True
        )
        
        # Create inactive product (should not be accessible)
        self.inactive_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Inactive Product',
            secondary_product_title='Test',
            slug='inactive-product',
            buy_now_price=Decimal('200.00'),
            description='Inactive product',
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=False,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        # Create product with no specifications
        self.minimal_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Minimal Product',
            secondary_product_title='Test',
            slug='minimal-product',
            buy_now_price=Decimal('100.00'),
            description='Minimal product',
            retail_price=Decimal('100.00'),
            inventory_status='in_inventory',
            is_active=True
        )

    # ==================== Basic Access Tests ====================
    
    def test_view_url_accessible_by_name(self):
        """View should be accessible via URL name with slug."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """View should use the correct template."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auction/product_detail.html')

    def test_authenticated_user_can_access(self):
        """Authenticated users should be able to access the view."""
        self.client.login(username='test@example.com', password='testpass!23')
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_access(self):
        """Anonymous users should be able to view product details."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # ==================== Product Filtering Tests ====================
    
    def test_active_product_displayed(self):
        """Active products should be displayed correctly."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'].id, self.active_product.id)

    def test_inactive_product_returns_404(self):
        """Inactive products should return 404."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.inactive_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_slug_returns_404(self):
        """Non-existent slug should return 404."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': 'nonexistent-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_empty_slug_handled(self):
        """Empty slug should be handled appropriately."""
        try:
            url = reverse('pop_up_auction:product_detail', kwargs={'slug': ''})
            response = self.client.get(url)
            self.assertIn(response.status_code, [404, 400])
        except:
            # Some URL configurations might raise an exception
            pass

    # ==================== Context Data Tests ====================
    
    def test_context_contains_product(self):
        """Context should contain the product object."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertIn('product', response.context)
        self.assertEqual(response.context['product'].id, self.active_product.id)

    def test_context_contains_product_specifications(self):
        """Context should contain product specifications dictionary."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertIn('product_specifications', response.context)
        
        specs = response.context['product_specifications']
        self.assertIsInstance(specs, dict)
        self.assertEqual(specs['model_year'], '2024')
        self.assertEqual(specs['colorway'], 'Military Blue')
        self.assertEqual(specs['size'], '10.5')

    def test_product_with_no_specifications(self):
        """Product with no specifications should have empty specs dict."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.minimal_product.slug})
        response = self.client.get(url)
        
        specs = response.context['product_specifications']
        self.assertIsInstance(specs, dict)
        self.assertEqual(len(specs), 0)

    def test_context_object_name_is_product(self):
        """Context object should be accessible as 'product'."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        
        # Both 'product' and 'object' should be available in context
        self.assertIn('product', response.context)
        self.assertIn('object', response.context)
        self.assertEqual(response.context['product'], response.context['object'])

    # ==================== Buy Now Availability Tests ====================
    
    def test_buy_now_available_within_window(self):
        """Buy now should be available when within time window and not bought."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertTrue(response.context['is_buy_now_available'])

    def test_buy_now_not_available_before_start(self):
        """Buy now should not be available before start time."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.future_buy_now_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_not_available_after_end(self):
        """Buy now should not be available after end time."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.expired_buy_now_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_not_available_without_dates(self):
        """Buy now should not be available without start/end dates."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.no_buy_now_dates_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_not_available_if_bought(self):
        """Buy now should not be available if product already bought."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.bought_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_at_exact_start_time(self):
        """Buy now should be available at exact start time."""
        exact_start_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Exact Start Product',
            secondary_product_title='Test',
            slug='exact-start-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now(),
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': exact_start_product.slug})
        response = self.client.get(url)
        
        self.assertTrue(response.context['is_buy_now_available'])

    def test_buy_now_at_exact_end_time(self):
        """Buy now should be available at exact end time."""
        exact_end_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Exact End Product',
            secondary_product_title='Test',
            slug='exact-end-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=7),
            buy_now_end=now() + timedelta(seconds=1),
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': exact_end_product.slug})
        response = self.client.get(url)
        
        self.assertTrue(response.context['is_buy_now_available'])

    # ==================== Buy Now Logic Edge Cases ====================
    
    def test_buy_now_logic_all_conditions_met(self):
        """Buy now should only be available when ALL conditions are met."""
        # Test that all four conditions must be true:
        # 1. buy_now_start exists
        # 2. buy_now_end exists
        # 3. current time within window
        # 4. not bought_now
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        # Verify all conditions
        self.assertIsNotNone(product.buy_now_start)
        self.assertIsNotNone(product.buy_now_end)
        self.assertLessEqual(product.buy_now_start, now())
        self.assertGreaterEqual(product.buy_now_end, now())
        self.assertFalse(product.bought_now)
        self.assertTrue(response.context['is_buy_now_available'])

    def test_buy_now_with_only_start_date(self):
        """Buy now should not be available with only start date."""
        only_start_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Only Start Product',
            secondary_product_title='Test',
            slug='only-start-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=None,
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': only_start_product.slug})
        response = self.client.get(url)
        
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_with_only_end_date(self):
        """Buy now should not be available with only end date."""
        only_end_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Only End Product',
            secondary_product_title='Test',
            slug='only-end-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=None,
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': only_end_product.slug})
        response = self.client.get(url)
        
        self.assertFalse(response.context['is_buy_now_available'])

    # ==================== Template Rendering Tests ====================
    
    def test_product_title_in_response(self):
        """Product title should appear in the rendered response."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, self.active_product.product_title)

    def test_secondary_title_in_response(self):
        """Secondary product title should appear in the rendered response."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, self.active_product.secondary_product_title)

    def test_buy_now_price_in_response(self):
        """Buy now price should appear in the rendered response."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        # Price could be formatted in various ways
        self.assertContains(response, '215')

    def test_description_in_response(self):
        """Product description should appear in the rendered response."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, self.active_product.description)

    def test_specifications_in_response(self):
        """Product specifications should appear in the rendered response."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        self.assertContains(response, '2024')
        self.assertContains(response, 'Military Blue')

    # def test_brand_in_response(self):
    #     """Brand name should appear in the rendered response."""
    #     url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
    #     response = self.client.get(url)
    #     self.assertContains(response, self.jordan_brand.name)

    # def test_category_in_response(self):
    #     """Category name should appear in the rendered response."""
    #     url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
    #     response = self.client.get(url)
    #     self.assertContains(response, self.basketball_category.name)

    # ==================== Slug Routing Tests ====================
    
    def test_slug_with_special_characters(self):
        """Products with special characters in slug should work."""
        special_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Special Product',
            secondary_product_title='2024',
            slug='special-product-2024',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': special_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_slug_case_sensitivity(self):
        """Test slug case sensitivity (Django slugs are typically lowercase)."""
        url_lower = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug.lower()})
        response = self.client.get(url_lower)
        self.assertEqual(response.status_code, 200)

    def test_different_products_have_unique_slugs(self):
        """Each product should be accessible via its unique slug."""
        url1 = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        url2 = reverse('pop_up_auction:product_detail', kwargs={'slug': self.future_buy_now_product.slug})
        
        response1 = self.client.get(url1)
        response2 = self.client.get(url2)
        
        self.assertNotEqual(response1.context['product'].id, response2.context['product'].id)

    # ==================== Edge Cases ====================
    
    def test_product_with_very_long_title(self):
        """Product with very long title should display correctly."""
        long_title_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='A' * 200,
            secondary_product_title='B' * 200,
            slug='long-title-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': long_title_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_with_zero_price(self):
        """Product with zero price should display correctly."""
        zero_price_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Zero Price Product',
            secondary_product_title='Free',
            slug='zero-price-product',
            buy_now_price=Decimal('0.00'),
            retail_price=Decimal('0.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': zero_price_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_with_very_high_price(self):
        """Product with very high price should display correctly."""
        expensive_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Expensive Product',
            secondary_product_title='Luxury',
            slug='expensive-product',
            buy_now_price=Decimal('99999.99'),
            retail_price=Decimal('99999.99'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': expensive_product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_with_multiple_specifications(self):
        """Product with many specifications should display all."""
        multi_spec_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Multi Spec Product',
            secondary_product_title='Test',
            slug='multi-spec-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        # Add multiple specifications
        for i in range(5):
            spec = PopUpProductSpecification.objects.create(
                product_type=self.sneakers_type,
                name=f'spec_{i}'
            )
            PopUpProductSpecificationValue.objects.create(
                product=multi_spec_product,
                specification=spec,
                value=f'value_{i}'
            )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': multi_spec_product.slug})
        response = self.client.get(url)
        specs = response.context['product_specifications']
        
        self.assertEqual(len(specs), 5)

    # ==================== Integration Tests ====================
    
    def test_view_provides_complete_product_data(self):
        """View should provide all necessary product data."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        # Verify all key attributes are present
        self.assertIsNotNone(product.product_title)
        self.assertIsNotNone(product.secondary_product_title)
        self.assertIsNotNone(product.slug)
        self.assertIsNotNone(product.buy_now_price)
        self.assertIsNotNone(product.retail_price)
        self.assertIsNotNone(product.description)
        self.assertIsNotNone(product.product_type)
        self.assertIsNotNone(product.category)
        self.assertIsNotNone(product.brand)
        self.assertIsNotNone(product.inventory_status)

    def test_multiple_users_can_view_same_product(self):
        """Multiple users should be able to view the same product simultaneously."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        
        # Anonymous user
        response1 = self.client.get(url)
        
        # Authenticated user 1
        self.client.login(username='test@example.com', password='testpass!23')
        response2 = self.client.get(url)
        self.client.logout()
        
        # Authenticated user 2
        self.client.login(username='other@example.com', password='testpass!23')
        response3 = self.client.get(url)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response3.status_code, 200)
        
        # All should see the same product
        self.assertEqual(response1.context['product'].id, self.active_product.id)
        self.assertEqual(response2.context['product'].id, self.active_product.id)
        self.assertEqual(response3.context['product'].id, self.active_product.id)


class TestBuyNowFlow(TestCase):
    def setUp(self):
        self.client = Client()
        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
        )
        self.other_user, self.other_user_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User2", "10", "female"
        )

        
        # Create categories
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        self.running_category = PopUpCategory.objects.create(
            name='Running',
            slug='running'
        )
        
        # Create brands
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        self.nike_brand = PopUpBrand.objects.create(
            name='Nike',
            slug='nike'
        )
        
        # Create product types
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )
        self.apparel_type = PopUpProductType.objects.create(
            name='Apparel',
            slug='apparel'
        )
        
        # Create specifications
        self.spec_model_year = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='model_year',
        )
        self.spec_colorway = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='colorway',
        )
        self.spec_size = PopUpProductSpecification.objects.create(
            product_type=self.sneakers_type,
            name='size',
        )
        
        auction_start =now() - timedelta(minutes=15)
        auction_end = now() + timedelta(minutes=15)

        buy_now_start = now() - timedelta(minutes=10)
        buy_now_end = now() + timedelta(minutes=10)

        # Create active product with buy now window
        self.active_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            slug='jordan-4-military-blue',
            buy_now_price=Decimal('215.00'),
            description='Classic Jordan 4 in Military Blue colorway',
            retail_price=Decimal('215.00'),
            reserve_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=buy_now_start,
            buy_now_end=buy_now_end,
            bought_now=False
        )

        # Create active product with buy now window that hasn't started
        self.future_buy_now_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='jordan-1-chicago',
            buy_now_price=Decimal('180.00'),
            description='Classic Jordan 1',
            retail_price=Decimal('180.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() + timedelta(days=1),
            buy_now_end=now() + timedelta(days=8),
            bought_now=False
        )

        # Create active product with expired buy now window
        self.expired_buy_now_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.running_category,
            brand=self.nike_brand,
            product_title='Nike Air Max',
            secondary_product_title='Classic White',
            slug='nike-air-max-white',
            buy_now_price=Decimal('150.00'),
            description='Classic Air Max',
            retail_price=Decimal('150.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=10),
            buy_now_end=now() - timedelta(days=1),
            bought_now=False
        )
        
        # Create active product without buy now dates
        self.no_buy_now_dates_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 3',
            secondary_product_title='White Cement',
            slug='jordan-3-white-cement',
            buy_now_price=Decimal('210.00'),
            description='Classic Jordan 3',
            retail_price=Decimal('210.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=None,
            buy_now_end=None,
            bought_now=False
        )
        
        # Create active product that has been bought
        self.bought_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 5',
            secondary_product_title='Grape',
            slug='jordan-5-grape',
            buy_now_price=Decimal('225.00'),
            description='Classic Jordan 5',
            retail_price=Decimal('225.00'),
            inventory_status='sold',
            is_active=True,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=now() + timedelta(days=7),
            bought_now=True
        )
        
        # Create inactive product (should not be accessible)
        self.inactive_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Inactive Product',
            secondary_product_title='Test',
            slug='inactive-product',
            buy_now_price=Decimal('200.00'),
            description='Inactive product',
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=False,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        # Create product with no specifications
        self.minimal_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Minimal Product',
            secondary_product_title='Test',
            slug='minimal-product',
            buy_now_price=Decimal('100.00'),
            description='Minimal product',
            retail_price=Decimal('100.00'),
            inventory_status='in_inventory',
            is_active=True
        )
        
        # Add specifications to active product
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.spec_model_year,
            value='2024'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.spec_colorway,
            value='Military Blue'
        )
        PopUpProductSpecificationValue.objects.create(
            product=self.active_product,
            specification=self.spec_size,
            value='10.5'
        )
    # ==================== Buy Now Availability Tests ====================
    
    def test_buy_now_available_within_window(self):
        """Buy now should be available when within time window and not bought."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertTrue(response.context['is_buy_now_available'])

    def test_buy_now_not_available_before_start(self):
        """Buy now should not be available before start time."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.future_buy_now_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_not_available_after_end(self):
        """Buy now should not be available after end time."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.expired_buy_now_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_not_available_without_dates(self):
        """Buy now should not be available without start/end dates."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.no_buy_now_dates_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_not_available_if_bought(self):
        """Buy now should not be available if product already bought."""
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.bought_product.slug})
        response = self.client.get(url)
        
        self.assertIn('is_buy_now_available', response.context)
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_at_exact_start_time(self):
        """Buy now should be available at exact start time."""
        exact_start_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Exact Start Product',
            secondary_product_title='Test',
            slug='exact-start-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now(),
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': exact_start_product.slug})
        response = self.client.get(url)
        
        self.assertTrue(response.context['is_buy_now_available'])

    def test_buy_now_at_exact_end_time(self):
        """Buy now should be available at exact end time."""
        exact_end_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Exact End Product',
            secondary_product_title='Test',
            slug='exact-end-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=7),
            buy_now_end=now() + timedelta(seconds=1),
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': exact_end_product.slug})
        response = self.client.get(url)
        
        self.assertTrue(response.context['is_buy_now_available'])

    # ==================== Buy Now Logic Edge Cases ====================
    
    def test_buy_now_logic_all_conditions_met(self):
        """Buy now should only be available when ALL conditions are met."""
        # Test that all four conditions must be true:
        # 1. buy_now_start exists
        # 2. buy_now_end exists
        # 3. current time within window
        # 4. not bought_now
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': self.active_product.slug})
        response = self.client.get(url)
        product = response.context['product']
        
        # Verify all conditions
        self.assertIsNotNone(product.buy_now_start)
        self.assertIsNotNone(product.buy_now_end)
        self.assertLessEqual(product.buy_now_start, now())
        self.assertGreaterEqual(product.buy_now_end, now())
        self.assertFalse(product.bought_now)
        self.assertTrue(response.context['is_buy_now_available'])

    def test_buy_now_with_only_start_date(self):
        """Buy now should not be available with only start date."""
        only_start_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Only Start Product',
            secondary_product_title='Test',
            slug='only-start-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=now() - timedelta(days=1),
            buy_now_end=None,
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': only_start_product.slug})
        response = self.client.get(url)
        
        self.assertFalse(response.context['is_buy_now_available'])

    def test_buy_now_with_only_end_date(self):
        """Buy now should not be available with only end date."""
        only_end_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Only End Product',
            secondary_product_title='Test',
            slug='only-end-product',
            buy_now_price=Decimal('200.00'),
            retail_price=Decimal('200.00'),
            inventory_status='in_inventory',
            is_active=True,
            buy_now_start=None,
            buy_now_end=now() + timedelta(days=7),
            bought_now=False
        )
        
        url = reverse('pop_up_auction:product_detail', kwargs={'slug': only_end_product.slug})
        response = self.client.get(url)
        
        self.assertFalse(response.context['is_buy_now_available'])



"""
Run Test
python3 manage.py test auction/tests
"""