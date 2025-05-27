from unittest import skip

from auction.models import PopUpProduct, PopUpCategory
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest
from auction.views import products

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

class TestViewResponse(TestCase):
    def setUp(self):
        self.c = Client()
        self.factory = RequestFactory()

        User.objects.create(username='admin')
        PopUpCategory.objects.create(name="shoe", slug="shoe")
        PopUpProduct.objects.create(
            category_id=1, 
            model_year="2025", 
            brand="Jordan",
            name="Air Jordan 4 Retro OJ SP Nigel Sylvestor Brick by Brick",
            slug="air-jordan-4-retro-oj-sp-nigel-sylvestor-brick-by-brick",
            release_date="03/10/2025",
            auction_start_date="03/25/2025",
            auction_end_date="04/02/2025",
            starting_price="$250",
            product_sex="Male",
            product_description="It's a cool shoe",
            style_number="HF4340-800",
            colorway="Firewood Orange/Sail-Cinnabar",
            retail_price="225",
            inventory_status="In Inventory",
            is_active="True",
            )

    def test_url_allowed_hosts(self):
        """
        Test allowed hosts
        """
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
    
#     def test_product_details_url(self):
#         response = self.c.get(reverse(
#             'auction:product_details', args=['nike_air_force_one']
#         ))
#         self.assertEqual(response.status_code, 200)
    

#     # HTML Validation test
#     def test_homepage_html(self):
#         request = HttpRequest()
#         response = products(request)
#         html = response.content.decode('utf8')
#         print('html is:', html)
#         self.assertIn('<title>Home</title>', html)
#         self.assertTrue(html.startswith('\n<DOCTYPE html>\n'))


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

