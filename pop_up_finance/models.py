from django.db import models
from pop_up_order.models import PopUpCustomerOrder
from pop_up_auction.models import PopUpProduct
from django.utils.translation import gettext_lazy as _


# Create your models here.
class PopUpFinance(models.Model):
    order = models.OneToOneField(PopUpCustomerOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(PopUpProduct, on_delete=models.CASCADE)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2) #COST product reserve price which is retail + shipping
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_method = models.CharField(max_length=50) #e.g. stripe, paypal, venmo, apple pay, google pay, crypto
    is_disputed = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)

    sold_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = _("PopUp Finance")
        verbose_name_plural = _("PopUp Finances")
    
    def calculate_revenue(self):
        """Use this to calculate revenue"""
        return self.final_price - self.refunded_amount

    def calculate_profit(self):
        """Use this to recalculate if refund or fees change"""
        revenue = self.final_price - self.refunded_amount
        return revenue - self.fees - self.reserve_price
