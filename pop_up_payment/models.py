from django.db import models
from pop_accounts.models import PopUpCustomerProfile
from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from decimal import Decimal
from pop_up_bot.models import ProcurementServiceRequest



# Create your models here.
class ServicePayment(models.Model):
    """
    Track payments for procurement service requests.
    
    Different from PopUpPayment which is for item purchases.
    This is specifically for the $15 procurement service fee.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('venmo', 'Venmo'),
    ]
    
    # Link to procurement service request
    service_request = models.OneToOneField(
        'pop_up_bot.ProcurementServiceRequest',
        on_delete=models.CASCADE,
        related_name='service_payment'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('15.00')  # Standard service fee
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    
    # References for payment processors
    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe PaymentIntent ID, PayPal transaction ID, or Braintree transaction ID"
    )
    
    refund_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Refund transaction ID from payment processor"
    )
    
    # Metadata
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if payment failed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _("Service Payment")
        verbose_name_plural = _("Service Payments")
    
    def __str__(self):
        return f"ServicePayment {self.id} - {self.service_request.user.email} - ${self.amount} ({self.status})"
    
    def mark_paid(self, payment_reference: str):
        """Mark payment as paid"""
        self.status = 'paid'
        self.payment_reference = payment_reference
        self.paid_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message: str):
        """Mark payment as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def mark_refunded(self, refund_reference: str):
        """Mark payment as refunded"""
        self.status = 'refunded'
        self.refund_reference = refund_reference
        self.refunded_at = timezone.now()
        self.save()
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def is_refunded(self):
        return self.status == 'refunded'
    


class CryptoPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('confirming', 'Confirming'),
        ('confirmed', 'Confirmed'),
        ('finished', 'Finished'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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

    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('venmo', 'Venmo'),
        ('apple_pay', 'Apple Pay'),
        ('google_pay', 'Google Pay'),
    ]
    
    order = models.OneToOneField(PopUpCustomerOrder, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
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
            if not order.billing_address or not order.shipping_address:
                return True
            if order.billing_address.postcode != order.shipping_address.postcode:
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
        If payment made Mon - Wed after 4PM, then a 60 hour wait for any charge disuptes
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
