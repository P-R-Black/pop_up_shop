from django.db import models
import uuid


# from .managers import CustomPopUpAccountManager  # Assuming you have a custom user manager

# Create your models here.

class PopUpProducts(models.Model):

    PRODUCT_TYPE_CHOICES = (
        ('shoe', 'Shoe'),
        ('clothing', 'Clothing'),
        ('miscellaneous', 'Miscellaneous'),
        ('memorabilia', 'Memorabilia'),
        
    )

    INVENTORY_STATUS_CHOICES = (
        ('anticipated', 'Anticipated'),
        ('in_transit', 'In Transit'),
        ('in_inventory', 'In Inventory')
    )

    PRODUCT_SEX_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex')
    )
       
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_year = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    auction_start_date = models.DateTimeField(null=True, blank=True)
    auction_end_date = models.DateTimeField(null=True, blank=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    product_sex = models.CharField(max_length=100, choices=PRODUCT_SEX_CHOICES, default='male')
    product_type = models.CharField(max_length=100, choices=PRODUCT_TYPE_CHOICES, default='shoe')
    product_description = models.TextField(null=True, blank=True)
    style_number = models.CharField(max_length=100, null=True, blank=True)
    colorway = models.CharField(max_length=100, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory_status = models.CharField(max_length=30, choices=INVENTORY_STATUS_CHOICES, default="anticipated")
  

    class Meta:
        ordering = ['release_date']
    
    def __str__(self):
        return f"{self.brand} - {self.name}"

class PopUpProductSize(models.Model):
    SIZE_CATEGORY_CHOICES = (
        ('shoe', 'Shoe Size'),
        ('clothing', 'Clothing Size')
    )

    product = models.ForeignKey(PopUpProducts, on_delete=models.CASCADE, related_name="sizes")
    size_category = models.CharField(max_length=20, choices=SIZE_CATEGORY_CHOICES)
    size_value = models.CharField(max_length=10) # e.g., '9', '7.5' for shoes, 'M', 'L' for clothing

    def __str__(self):
        return f"{self.product.name} - {self.size_value} - {self.product.product_sex}"




