from django.db import models
from pop_accounts.models import PopUpCustomer
from orders.models import PopUpCustomerOrder, PopUpOrderItem
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta


# Create your models here.
class CryptoPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('confirming', 'Confirming'),
        ('confirmed', 'Confirmed'),
        ('finished', 'Finished'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(PopUpCustomer, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100, unique=True)
    order_id = models.CharField(max_length=100)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    pay_currency = models.CharField(max_length=10)
    pay_amount = models.DecimalField(max_digits=20, decimal_places=8)
    pay_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.payment_id} - {self.status}"


class PopUpPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('in_review', "In Review"),
        ('disputed', "Disputed"),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    order = models.OneToOneField(PopUpCustomerOrder, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    suspicious_flagged = models.BooleanField(default=False)
    notified_ready_to_ship = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',) 
        verbose_name = _("PopUp Payment")
        verbose_name_plural = _("PopUp Payments")


    def is_suspicious(self):
        order = self.order

        try:
            if order.total_paid > 500:
                return True
            if order.billing_address and order.shipping_address:
                if order.billing_address.zip != order.shipping_address.zip:
                    return True
            if not order.phone or '@' not in order.email:
                return True
        except Exception as e:
            # Log or handle missing related data gracefully
            return True  # err on the side of caution

        return False
    

    @property
    def release_at_computed(self):
        return self.calculate_shipping_release_datetime()
    

    def calculate_shipping_release_datetime(self):
        """
        Tells admin that order is ready to ship
        If payment made Mon - Wed before 4PM, then a 48 hour wait for any charge disuptes
        If payment made Mon - Wed after 4PM, then 1 60 hour wait for any charge disuptes
        If payment made Thursday before 4PM, then 72 hour hour wait for any charge disuptes
        If payment made Thurday after 4PM or Friday through Sunday, then 2 business day wait for any charge disuptes
        """
        local_time = timezone.localtime(self.created_at)
        weekday = local_time.weekday()
        hour = local_time.hour
        
        if weekday <= 2: # Mon - Wed
            if hour < 16:
                return local_time + timedelta(hours=48)
            else:
                return local_time + timedelta(hours=60)
        elif weekday == 3: # Thursday
            if hour < 16:
                return local_time + timedelta(days=4, hours=(20 - hour)) # Until Mon ~8pm
            else:
                return (local_time + timedelta(days=5)).replace(hour=8, minute=0) # Wednesday AM
        else: # Friday after 5PM or weekend
            return (local_time + timedelta(days=(7 - weekday + 2))).replace(hour=8, minute=0)

