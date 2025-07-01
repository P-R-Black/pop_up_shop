from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.
class Shipment(models.Model):
    CARRIER_CHOICES = (
        ('usps', 'USPS'),
        ('ups', 'UPS'),
        ('FedEx', 'FedEx')
    )
    order = models.OneToOneField('orders.PopUpCustomerOrder', on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=50, choices=CARRIER_CHOICES, default='usps')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    label_url = models.URLField(blank=True, null=True) # link to PDF if stored on S3 or Cloudinary
    shipped_at = models.DateTimeField(blank=True, null=True)
    estimated_delivery = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')

    class Meta:
        verbose_name = _("PopUp Shipment")
        verbose_name_plural = _("PopUp Shipments")

    def __str__(self):
        return f"Shipment for Order {self.order_id}"
    