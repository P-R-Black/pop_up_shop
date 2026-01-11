from django.db import models
from pop_accounts.models import PopUpCustomerAddress, PopUpCustomerProfile
from pop_up_auction.models import PopUpProduct
from pop_up_coupon.models import PopUpCoupon
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Create your models here.
class PopUpCustomerOrder(models.Model):
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_user')
    full_name = models.CharField(max_length=50)
    email = models.EmailField(_('email'))
    address1 = models.CharField(_('address'), max_length=250)
    address2 = models.CharField(_('address'), max_length=250, blank=True, null=True)
    postal_code = models.CharField(_('postal code'), max_length=20)
    apartment_suite_number = models.CharField(_("Apartment/Suite"), max_length=50, blank=True)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_("State"), max_length=100)
    phone = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    order_key = models.CharField(max_length=200)
    billing_status = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(PopUpCustomerAddress, on_delete=models.SET_NULL, null=True, related_name="order_shipping")
    billing_address = models.ForeignKey(PopUpCustomerAddress, on_delete=models.SET_NULL, null=True, related_name="order_billing")
    payment_data_id = models.CharField(max_length=150, blank=True)
    coupon = models.ForeignKey(PopUpCoupon, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    


    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Pop Up Customer Order")
        verbose_name_plural = _("Pop Up Customer Orders")

    

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

    # Denormalize fields to preserve snapshot at time of purchase
    product_title = models.CharField(max_length=100)
    secondary_product_title = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=10, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)


    class Meta:
        ordering = ('-order',)
        verbose_name = _("PopUp Order Item")
        verbose_name_plural = _("PopUp Order Items")


    def __str__(self):
        return f"{self.product_title} {self.secondary_product_title}: Product id: {self.id}"

    def get_cost(self):
        return self.price * self.quantity



