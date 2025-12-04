from unittest import skip
from pop_up_auction.models import (
     PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType, PopUpProductImage, PopUpProductSpecification, 
     PopUpProductSpecificationValue, PopUpBid)
from pop_up_order.utils.utils import user_orders, user_shipments
from pop_up_payment.models import PopUpPayment
from pop_up_shipping.models import PopUpShipment
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest
from pop_up_auction.views import (AllAuctionView, AjaxLoginRequiredMixin)
from accounts.models import (PopUpCustomer, PopUpCustomerAddress, PopUpCustomerIP)
from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from datetime import timezone as dt_timezone, datetime
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.template import Context, Template
from pop_up_cart.cart import Cart
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.core.cache import cache
from django.http import JsonResponse
import json
from django.contrib.auth.models import AnonymousUser



User = get_user_model()


def create_test_user():
    return PopUpCustomer.objects.create_user(
            email="testuser@example.com",
            password="securePassword!23",
            first_name="Test",
            last_name="User",
            shoe_size="10",
            size_gender="male"
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

# create staff user
def create_test_staff_user():
    return PopUpCustomer.objects.create_user(
        email="staffuser@staff.com",
        password="staffPassword!232",
        first_name="Staff",
        last_name="User",
        shoe_size="9",
        size_gender="male",
        is_staff=True
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



def create_test_product_one(*args, **kwargs):
    # Set default values
    defaults = {
        'product_type': create_product_type('shoe', is_active=True),
        'category': create_category('Jordan 3', is_active=True),
        'product_title': "Past Bid Product 1",
        'secondary_product_title': "Past Bid 1",
        'description': "Brand new sneakers",
        'slug': "past-bid-product-1",
        'buy_now_price': "250.00",
        'current_highest_bid': "0",
        'retail_price': "150.00",
        'brand': create_brand('Jordan'),
        'auction_start_date': None,
        'auction_end_date': None,
        'inventory_status': "sold_out",  # Default value
        'bid_count': 0,
        'reserve_price': "100.00",
        'is_active': False  # Default value
    }
    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpProduct.objects.create(**defaults)


def create_test_product_two(*args, **kwargs):
    # Set default values
    defaults = {
        'product_type_id': 1, 'category': create_category('Jordan 4', is_active=True),
        'product_title': "Past Bid Product 2", 'secondary_product_title': "Past Bid 2",
        'description': "Brand new sneakers", 'slug': "past-bid-product-2", 'buy_now_price': "300.00", 
        'current_highest_bid': "0", 'retail_price': "200.00", 'brand_id': 1, 'auction_start_date': None, 
        'auction_end_date': None, 'inventory_status': "sold_out", 'bid_count': 0, 'reserve_price': "150.00",
        'is_active': False  # Default value
    }

    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpProduct.objects.create(**defaults)




def create_test_product_three(*args, **kwargs):
        # Set default values
        defaults = {
            'product_type': create_product_type('gaming system', is_active=True), 
            'category': create_category('Switch', is_active=True), 'product_title': "Switch 2", 
            'secondary_product_title': "", 'description': "New Nintendo Switch 2", 
            'slug': "switch-2", 'buy_now_price': "350.00", 'current_highest_bid': "0", 
            'retail_price': "250.00", 'brand': create_brand('Nintendo'), 'auction_start_date': None, 
            'auction_end_date': None, 'inventory_status': "in_inventory", 'bid_count': 0, 
            'reserve_price': "225.00",
            'is_active': False  # Default value
        }

        # Override defaults with any kwargs passed in
        defaults.update(kwargs)
        
        # Create and return the product
        return PopUpProduct.objects.create(**defaults)



def create_test_shipping_address_one(*args, **kwargs):
    return PopUpCustomerAddress.objects.create(
            first_name='John',
            last_name='Doe',
            address_line='123 Test St',
            town_city='Test City',
            state='Tennessee',
            postcode='12345',
            **kwargs,
        )

def create_test_order_one(*args, **kwargs):
    return PopUpCustomerOrder.objects.create(
            billing_status=True,
            address1="111 Test St",
            city="New York",
            state="NY",
            postal_code="10001",
            total_paid="100.00",
            **kwargs
        )

def create_test_order_two(*args, **kwargs):
    return PopUpCustomerOrder.objects.create(
            billing_status=True,
            address1="123 Test St",
            city="South Ozone Park",
            state="NY",
            postal_code="11434",
            total_paid="100.00",
            **kwargs
    )

def create_test_shipment_one(*args, **kwargs):
    defaults = {
        'order': None,
        'carrier': 'USPS', 'tracking_number': '1Z999AA10123456784', 
        'shipped_at': datetime(2024, 1, 15, tzinfo=dt_timezone.utc),
        'estimated_delivery': datetime(2024, 1, 20, tzinfo=dt_timezone.utc), 
        'delivered_at': None, 'status': 'pending',
    }

    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpShipment.objects.create(**defaults)


def create_test_shipment_pending(*args, **kwargs):
    defaults = {
        'order': None,
        'carrier': '',  
        'tracking_number': '',
        'shipped_at': None, 
        'estimated_delivery': None,
        'delivered_at': None, 
        'status': 'pending',  # ✅ Truly pending
    }
    defaults.update(kwargs)
    return PopUpShipment.objects.create(**defaults)


def create_test_shipment_two_pending(*args, **kwargs):
    defaults = {
        'order': None,
        'carrier': 'USPS', 'tracking_number': '1Z999AA10123456784', 
        'shipped_at': None,
        'estimated_delivery': None, 
        'delivered_at': None, 'status': 'pending'
    }

    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpShipment.objects.create(**defaults)


def create_test_payment_one(order, amount, status, payment_method, suspicious_flagged, notified_ready_to_ship):
        return PopUpPayment.objects.create(
            order=order,
            amount=Decimal(amount),
            status=status,
            payment_method=payment_method,
            suspicious_flagged=suspicious_flagged,
            notified_ready_to_ship=notified_ready_to_ship
        )




class TestAllAuctionView(TestCase):
    """Test suite for AllAuctionView"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = PopUpCustomer.objects.create(
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

        # test_brand = create_brand('Jordan')
        # test_category = create_category('Jordan 3', is_active=True)
        # test_product_type = create_product_type('shoe', is_active=True)
        
        # Create product specifications
        self.size_spec = PopUpProductSpecification.objects.create(product_type_id=1,name='size')
        self.condition_spec = PopUpProductSpecification.objects.create(product_type_id=1,name='condition')
        self.sex_spec = PopUpProductSpecification.objects.create(product_type_id=1,name='product_sex')
      
        
        # Create auction product with ongoing auction
        self.auction_product = create_test_product_one(
            product_title="Test Sneakers",
            secondary_product_title="Limited Edition",
            slug="test-sneakers",
            is_active=True,
            inventory_status="in_inventory",
            reserve_price=Decimal("100.00"),
            current_highest_bid=Decimal("150.00"),
            bid_count=5,
            auction_start_date=timezone.now() - timedelta(days=1),
            auction_end_date=timezone.now() + timedelta(days=3)
        )
        
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
        self.auction_product.auction_start_date = timezone.now() + timedelta(days=1)
        self.auction_product.auction_end_date = timezone.now() + timedelta(days=5)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        # Should be 0 because auction_status will be "Upcoming"
        self.assertEqual(len(in_auction), 0)

    def test_ended_auction_not_displayed(self):
        """Test that ended auction products are not displayed"""
        # Set auction to have ended in the past
        self.auction_product.auction_start_date = timezone.now() - timedelta(days=5)
        self.auction_product.auction_end_date = timezone.now() - timedelta(days=1)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        # Should be 0 because auction_status will be "Ended"
        self.assertEqual(len(in_auction), 0)


    def test_multiple_ongoing_auctions_displayed(self):
        """Test that multiple ongoing auctions are displayed"""
        # Create second auction product
        auction_proudct2 = create_test_product_two(
            product_title="Test Sneakers 2",
            secondary_product_title="Limited Edition",
            slug="test-sneakers-2",
            is_active=True,
            inventory_status="in_inventory",
            retail_price= Decimal("175.00"),
            reserve_price=Decimal("200.00"),
            current_highest_bid=Decimal("150.00"),
            bid_count=5,
            auction_start_date=timezone.now() - timedelta(days=1),
            auction_end_date=timezone.now() + timedelta(days=2)
        )
        
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
        self.auction_product.auction_end_date = timezone.now() - timedelta(days=1)
        self.auction_product.save()
        
        response = self.client.get(self.url)
        in_auction = response.context['in_auction']
        self.assertEqual(len(in_auction), 0)

    def test_future_auction_not_displayed(self):
        """Test that future auctions are not displayed"""
        self.auction_product.auction_start_date = timezone.now() + timedelta(days=1)
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
        self.assertContains(response, "Limited Edition")

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
        self.user = create_test_user()
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


# class TestViewResponse(TestCase):
#     def setUp(self):
#         self.c = Client()
#         self.factory = RequestFactory()

#         self.user = create_test_user()
#         self.product = create_test_product()


#     def test_url_allowed_hosts(self):
#         """
#         Test allowed hosts
#         """
#         response = self.c.get('/')
#         self.assertEqual(response.status_code, 200)
    
#     def test_product_details_url(self):
#         response = self.c.get(reverse(
#             'auction:product_detail', args=[slugify(self.product.product_title + '-' + self.product.secondary_product_title)]
#         ))
#         self.assertEqual(response.status_code, 200)
    

#     # HTML Validation test
#     def test_homepage_html(self):
#         request = HttpRequest()
#         print('request', request)
#         # response = AllAuctionView()
#         response = self.c.get(reverse(
#             'auction:auction'
#         ))
#         # print('response', response)
      
#         html = response.content.decode('utf8')
#         print('html is:', html)
#         self.assertIn('<title>\nAuction\n</title>\n', html)



# class TestBuyNowFlow(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = PopUpCustomer.objects.create_user(
#             email="testuser@example.com", password="securePassword!23", first_name="Test", last_name="User", shoe_size="10", size_gender="male")
#         self.client.login(email="testuser@example.com", password="securePassword!23")
#         self.product_type = PopUpProductType.objects.create( name="shoe", slug="shoe", is_active=True)
          
#         self.category = PopUpCategory.objects.create(name="Jordan 3",slug="jordan-3",is_active=True)
          
#         self.brand = PopUpBrand.objects.create(name="Staries", slug="staries")
          
#         auction_start =now() - timedelta(minutes=15)
#         auction_end = now() + timedelta(minutes=15)

#         buy_now_start = now() - timedelta(minutes=10)
#         buy_now_end = now() + timedelta(minutes=10)
          
#         self.product = PopUpProduct.objects.create(
#                 product_type=self.product_type,
#                 category=self.category,
#                 product_title="Test Sneaker",
#                 secondary_product_title = "Exclusive Drop",
#                 description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
#                 slug="test-sneaker-exclusive-drop", 
#                 buy_now_price="150.00", 
#                 current_highest_bid="0", 
#                 retail_price="100", 
#                 brand=self.brand, 
#                 auction_start_date=auction_start,
#                 auction_end_date=auction_end, 
#                 buy_now_start=buy_now_start,
#                 buy_now_end=buy_now_end,
#                 inventory_status="In Inventory", 
#                 bid_count="0", 
#                 reserve_price="0", 
#                 is_active=True
#             )
    
#     def test_buy_now_add_to_cart(self):
#         url = reverse("auction:buy_now_add_to_cart", kwargs={"slug": self.product.slug})
#         response = self.client.get(url)

#         #Ensure it redirects to payment 9cart added successfully)
#         self.assertRedirects(response, reverse('pop_up_payment:payment_home'))

#         # Check session has 10-minute timer
#         self.assertIn('buy_now_expiry', self.client.session)

#         # Check product inventory now 'reversed'
#         self.product.refresh_from_db()
#         self.assertEqual(self.product.inventory_status, 'reversed')

#         # verity cart has the item
#         cart = Cart(self.client)
#         self.assertEqual(len(cart), 1)
#         item = list(cart)[0]
#         self.assertEqual(item['product'], self.product)
#         self.assertEqual(item['qty'], 1)
#         self.assertTrue(item['buy_now'])
    

#     def test_buy_now_expiry_sets_auction_start(self):
#         # Simulate buy_now_end is in the past
#         self.product.buy_now_end = now() - timedelta(minutes=1)
#         self.product.save()

#         # Simulate Celery logic that should run
#         if self.product.buy_now_end < now() and self.product.inventory_status == 'in_inventory':
#             self.product.auction_start_date = now()
#             self.product.inventory_status = 'in_inventory'  # or some logic to transition to auction-ready state
#             self.product.save()

#         self.product.refresh_from_db()
#         self.assertIsNotNone(self.product.auction_start_date)
    
    
#     def test_cannot_buy_reserved_product(self):
#         self.product.inventory_status = 'reserved'
#         self.product.save()

#         url = reverse("auction:buy_now_add_to_cart", kwargs={"slug": self.product.slug})
#         response = self.client.get(url)

#         self.assertRedirects(response, reverse("auction:product_detail", kwargs={"slug": self.product.slug}))



"""
Run Test
python3 manage.py test auction/tests
"""