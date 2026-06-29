from django.db import models
from django.contrib.auth import get_user_model
from pop_accounts.models import PopUpCustomerProfile
from django.conf import settings
import uuid

# User = get_user_model()

# Create your models here.
class PopUpCartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('pop_up_auction.PopUpProduct', on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    auction_locked = models.BooleanField(default=False)
    buy_now = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user}'s cart: {self.product.product_title} {self.product.secondary_product_title} {self.quantity}"


class ProcurementCartItem(models.Model):
    """
    Represents a $15 procurement service fee in the user's cart.
 
    Created when a user submits the procurement form and clicks
    "Proceed to Payment". Displayed alongside regular cart items
    on the checkout page. Cleared after successful payment.
    """
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='procurement_cart_items'
    )
 
    procurement_service_request = models.OneToOneField(
        'pop_up_bot.ProcurementServiceRequest',
        on_delete=models.CASCADE,
        related_name='cart_item',
        help_text="The procurement request this fee covers"
    )
 
    # Snapshot the fee at cart-add time in case the fee amount ever changes
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15.00,
        help_text="Service fee charged to user (snapshot at time of cart add)"
    )
 
    added_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = 'Procurement Cart Item'
        verbose_name_plural = 'Procurement Cart Items'
 
    def __str__(self):
        release = self.procurement_service_request.scheduled_release
        return (
            f"{self.user} → Procurement fee for "
            f"{release.product.product_title} (Size {self.procurement_service_request.size})"
        )
 
    @property
    def display_title(self):
        """Human-readable title for checkout display."""
        release = self.procurement_service_request.scheduled_release
        return f"Procurement: {release.product.product_title}"
 
    @property
    def display_subtitle(self):
        """Size and detail line for checkout display."""
        return f"Size {self.procurement_service_request.size} · Bot-secured at release"
    
 
    @property
    def price(self):
        return self.fee_amount
 
    @property
    def total_price(self):
        return self.fee_amount  # always qty 1