from django.db import models
from pop_accounts.models import PopUpCustomer
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

# Create your models here.
class PopUpCartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('pop_up_auction.PopUpProduct', on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    auction_locked = models.BooleanField(default=False)
    buy_now = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user}'s cart: {self.product.product_title} {self.product.secondary_product_title} {self.quantity}"