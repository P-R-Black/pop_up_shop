from django.db import models
from pop_accounts.models import PopUpCustomer

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
