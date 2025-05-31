from unittest import skip

from auction.models import PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest
from auction.views import products, AllAuctionView
from pop_accounts.models import PopUpCustomer
from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.template import Context, Template

"""
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(PoPUpCategory, related_name='product', on_delete=models.CASCADE)
    model_year = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    brand = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    auction_start_date = models.DateTimeField(null=True, blank=True)
    auction_end_date = models.DateTimeField(null=True, blank=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    product_sex = models.CharField(max_length=100, choices=PRODUCT_SEX_CHOICES, default='male')
    # product_type = models.CharField(max_length=100, choices=PRODUCT_TYPE_CHOICES, default='shoe')
    product_description = models.TextField(null=True, blank=True)
    style_number = models.CharField(max_length=100, null=True, blank=True)
    colorway = models.CharField(max_length=100, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory_status = models.CharField(max_length=30, choices=INVENTORY_STATUS_CHOICES, default="anticipated")
    is_active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class PoPUpCategory(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255)

    class Meta:
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name
"""
"2025"
"Air Air Jordan 4 Retro OG SP"
"Nigel Sylvester Brick by Brick"



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
            starting_price="150.00", 
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


#     # using Request factory
#     def test_view_function(self):
#         request = self.factory_get('/item/django-beginners')
#         response = products(request)
#         html = response.content.decode('utf8')
#         print('html is:', html)
#         self.assertIn('<title>Home</title>', html)
#         self.assertTrue(html.startswith('\n<DOCTYPE html>\n'))

    
#     def test_url_allowed_hosts(self):
#         """
#         Test Allowed Hosts
#         """
#         response = self.c.get('/', HTTP_HOST='noaddress.com')
#         self.assertEqual(response.status_code, 400)
#         response = self.c.get('/', HTTP_HOST='localhost:8080')
#         self.assertEqual(response.status_code, 200)




# how to skip a test
# @skip("demonstrate skipping")
# class TestSkip(TestCase):
#     def test_skip_example(self):
#         pass

