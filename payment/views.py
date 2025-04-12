from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
import stripe
from django.conf import settings
import json
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.views import payment_confirmation
import os

# Create your views here.
# @login_required
def cart_view(request):
    cart = Cart(request)
    total = str(cart.get_total_price())
    total = total.replace('.', '')
    total_price = int(total)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    intent = stripe.PaymentIntent.create(
        # amount=total,
        # currency='usd',
        # metadata={'userid': request.user.id}
    )

    return render(request, 'payment/payment_home.html', {'client_secret': intent.client_secret})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    event = None

    try: 
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        print(e)
        return HttpResponse(status=400)

    # Hande the event
    if event.type == 'payment_intent.succeeded':
        payment_confirmation(event.data.object.client_secret)
    else:
        print('Unhandled event type{}'.format(event.type))
    
    return HttpResponse(status=200)


def placed_order(request):
    cart = Cart(request)
    cart.clear()
    return render(request, 'payment/placed_order.html')