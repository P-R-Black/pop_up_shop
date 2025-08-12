from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.
class PopUpShipment(models.Model):
    CARRIER_CHOICES = [
        ('n/a', 'N/A'),
        ('usps', 'USPS'),
        ('ups', 'UPS'),
        ('FedEx', 'FedEx')
    ]

    SHIPMENT_STATUS = [
        ('cancelled', 'Cancelled'),
        ('in_dispute', 'In Dispute'),
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('returned', 'Returned'),
        ('delivered', 'Delivered')
     
    ]
    
    order = models.OneToOneField('pop_up_order.PopUpCustomerOrder', on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=50, choices=CARRIER_CHOICES, default='n/a')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    estimated_delivery = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=SHIPMENT_STATUS, default='pending')

    class Meta:
        verbose_name = _("PopUp Shipment")
        verbose_name_plural = _("PopUp Shipments")

    def __str__(self):
        return f"{self.order_id}"
    