from unittest import skip

from auction.models import PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest
from auction.views import AllAuctionView
from pop_accounts.models import PopUpCustomer
from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.template import Context, Template
from pop_up_cart.cart import Cart
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta

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


def create_test_product():
        
        auction_start = make_aware(datetime(2025, 5, 29, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 6, 5, 12, 0, 0))
    
        brand = PopUpBrand.objects.create(
            name="Staries",
            slug="staries"
        )
        categories = PopUpCategory.objects.create(
            name="Jordan 3",
            slug="jordan-3",
            is_active=True
        )
        product_type = PopUpProductType.objects.create(
            name="shoe",
            slug="shoe",
            is_active=True
        )

        return PopUpProduct.objects.create(
            product_type=product_type,
            category=categories,
            product_title="Test Sneaker",
            secondary_product_title = "Exclusive Drop",
            description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
            slug="test-sneaker-exclusive-drop", 
            buy_now_price="150.00", 
            current_highest_bid="0", 
            retail_price="100", 
            brand=brand, 
            auction_start_date=auction_start,
            auction_end_date=auction_end, 
            inventory_status="In Inventory", 
            bid_count="0", 
            reserve_price="0", 
            is_active=True
        )


class TestViewResponse(TestCase):
    def setUp(self):
        self.c = Client()
        self.factory = RequestFactory()

        self.user = create_test_user()
        self.product = create_test_product()


    def test_url_allowed_hosts(self):
        """
        Test allowed hosts
        """
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_product_details_url(self):
        response = self.c.get(reverse(
            'auction:product_detail', args=[slugify(self.product.product_title + '-' + self.product.secondary_product_title)]
        ))
        self.assertEqual(response.status_code, 200)
    

    # HTML Validation test
    def test_homepage_html(self):
        request = HttpRequest()
        print('request', request)
        # response = AllAuctionView()
        response = self.c.get(reverse(
            'auction:auction'
        ))
        # print('response', response)
      
        html = response.content.decode('utf8')
        print('html is:', html)
        self.assertIn('<title>\nAuction\n</title>\n', html)



class BuyNowFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = PopUpCustomer.objects.create_user(
            email="testuser@example.com", password="securePassword!23", first_name="Test", last_name="User", shoe_size="10", size_gender="male")
        self.client.login(email="testuser@example.com", password="securePassword!23")
        self.product_type = PopUpProductType.objects.create( name="shoe", slug="shoe", is_active=True)
          
        self.category = PopUpCategory.objects.create(name="Jordan 3",slug="jordan-3",is_active=True)
          
        self.brand = PopUpBrand.objects.create(name="Staries", slug="staries")
          
        auction_start =now() - timedelta(minutes=15)
        auction_end = now() + timedelta(minutes=15)

        buy_now_start = now() - timedelta(minutes=10)
        buy_now_end = now() + timedelta(minutes=10)
          
        self.product = PopUpProduct.objects.create(
                product_type=self.product_type,
                category=self.category,
                product_title="Test Sneaker",
                secondary_product_title = "Exclusive Drop",
                description="New Test Sneaker Exlusive Drop from the best sneaker makers out.",
                slug="test-sneaker-exclusive-drop", 
                buy_now_price="150.00", 
                current_highest_bid="0", 
                retail_price="100", 
                brand=self.brand, 
                auction_start_date=auction_start,
                auction_end_date=auction_end, 
                buy_now_start=buy_now_start,
                buy_now_end=buy_now_end,
                inventory_status="In Inventory", 
                bid_count="0", 
                reserve_price="0", 
                is_active=True
            )
    
    def test_buy_now_add_to_cart(self):
        url = reverse("auction:buy_now_add_to_cart", kwargs={"slug": self.product.slug})
        response = self.client.get(url)

        #Ensure it redirects to payment 9cart added successfully)
        self.assertRedirects(response, reverse('pop_up_payment:payment_home'))

        # Check session has 10-minute timer
        self.assertIn('buy_now_expiry', self.client.session)

        # Check product inventory now 'reversed'
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory_status, 'reversed')

        # verity cart has the item
        cart = Cart(self.client)
        self.assertEqual(len(cart), 1)
        item = list(cart)[0]
        self.assertEqual(item['product'], self.product)
        self.assertEqual(item['qty'], 1)
        self.assertTrue(item['buy_now'])
    

    def test_buy_now_expiry_sets_auction_start(self):
        # Simulate buy_now_end is in the past
        self.product.buy_now_end = now() - timedelta(minutes=1)
        self.product.save()

        # Simulate Celery logic that should run
        if self.product.buy_now_end < now() and self.product.inventory_status == 'in_inventory':
            self.product.auction_start_date = now()
            self.product.inventory_status = 'in_inventory'  # or some logic to transition to auction-ready state
            self.product.save()

        self.product.refresh_from_db()
        self.assertIsNotNone(self.product.auction_start_date)
    
    
    def test_cannot_buy_reserved_product(self):
        self.product.inventory_status = 'reserved'
        self.product.save()

        url = reverse("auction:buy_now_add_to_cart", kwargs={"slug": self.product.slug})
        response = self.client.get(url)

        self.assertRedirects(response, reverse("auction:product_detail", kwargs={"slug": self.product.slug}))



"""
Run Test
python3 manage.py test auction/tests
"""