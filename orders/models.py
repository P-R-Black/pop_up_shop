from django.db import models
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress
from auction.models import PopUpProduct
from coupon.models import PopUpCoupon
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

"""
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_user')
    full_name = models.CharField(max_length=50)
    address1 = models.CharField(max_length=250)
    address2 = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    post_code = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    total_paid = models.DecimalField(max_digits=5, decimal_places=2)
    order_key = models.CharField(max_length=200)
    billing_status = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return str(self.created)
"""
# Create your models here.
class PopUpCustomerOrder(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(PopUpCustomer, on_delete=models.CASCADE, related_name='order_user')
    full_name = models.CharField(max_length=50)
    email = models.EmailField(_('email'))
    address1 = models.CharField(_('address'), max_length=250)
    address2 = models.CharField(_('address'), max_length=250)
    postal_code = models.CharField(_('postal code'), max_length=20)
    apartment_suite_number = models.CharField(_("Apartment/Suite"), max_length=50, blank=True)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_("State"), max_length=100)
    phone = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    order_key = models.CharField(max_length=200)
    billing_status = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(PopUpCustomerAddress, on_delete=models.SET_NULL, null=True, related_name="order_shipping")
    billing_address = models.ForeignKey(PopUpCustomerAddress, on_delete=models.SET_NULL, null=True, related_name="order_billing")
    stripe_id = models.CharField(max_length=150, blank=True)
    coupon = models.ForeignKey(PopUpCoupon, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    

    # These items below should probably go into model specifically for SHIPPING

    # item = models.ManyToManyField(PopUpProduct, related_name='ordered_products')
    # status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    # tracking_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    # carrier = models.CharField(max_length=50, blank=True, null=True)
    # estimated_delivery_date = models.DateField(blank=True, null=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
   

    # total_paid = models.DecimalField(max_digits=5, decimal_places=2)
    # order_key = models.CharField(max_length=200)

    class Meta:
        ordering = ('-created_at',)

    def mark_as_shipped(self, tracking_number, carrier, estiamted_delivery):
        """Mark the order as shipped and store tracking details."""
        self.status = 'shipped'
        self.tracking_number = tracking_number
        self.carrier = carrier
        self.estimated_delivery_date = estiamted_delivery
        self.save(updated_fields=['status', 'tracking_number', 'carrier', 'estiamted_delivery_date'])
    
    
    def __str__(self):
        return f"Order {self.id}"
    

    def get_total_cost(self):
        total_cost = sum(item.get_cost() for item in self.items.all())
        return total_cost - total_cost * (self.discount / Decimal(100))
    

class PopUpOrderItem(models.Model):
    order = models.ForeignKey(PopUpCustomerOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(PopUpProduct, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

