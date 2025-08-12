# cart/signals.py

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart import Cart
from .models import PopUpCartItem
from pop_up_auction.models import PopUpProduct

@receiver(user_logged_in)
def move_session_cart_to_db(sender, request, user, **kwargs):
    cart = Cart(request)
    session_cart = cart.session_cart

    for product_id, item in session_cart.items():
        product = PopUpProduct.objects.get(id=product_id)
        cart_item, created = PopUpCartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={
                'quantity': item['qty'],
                'auction_locked': item.get('auction_locked', False),
                'buy_now': item.get('buy_now', False)
            }
        )
        if not created:
            cart_item.quantity += item['qty']
            cart_item.save()

    cart.clear()
