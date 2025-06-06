from .models import PopUpProduct
from pop_accounts.models import PopUpCustomer, PopUpPurchase
from django.core.mail import send_mail


def notify_winner(customer, product, amount, purchase):

    subject = f"You won the auction for {product.product_titile}"
    message = f"Congrats!\n\nYour winning bid: ${amount:2f}.\nPlease complete payment within 48 hours: {settings.SITE_URL}/checkout/{purchase.id}"

    
    send_mail(
        subject,
        message,
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [customer.email],
    )

    # SMS
    if customer.mobile_notification and customer.mobile_phone:
        twilio_client.messages.create(
            to = customer.mobile_phone,
            from_ = settings.TWILIO_FROM,
            body = f"You won {product.product_title}! Complete payment in your account."
        )


def close_auction(product: PopUpProduct):
    highest = product.bids.filter(is_active=True).order_by('-amount').first()
    if not highest:
        return
    
    highest.is_winning_bid = True
    highest.save(update_fields=['is_winning_bid'])
    customer = highest.customer
    amount = highest.amount

    # build / reuse Stripe customer
    if not customer.stripe_customer_id:
        stripe_customer = stripe.Customer.create(
            email = customer.email,
            phone = customer.mobile_phone or None,
            name = f"{customer.first_name} {customer.last_name}"
        )
        customer.stripe_customer_id = stripe_customer.id
        customer.save(update_fields=['stripe_customer_id'])
    
    pi = stripe.PaymentIntent.create(
        customer = customer.stripe_customer_id,
        amount = int(amount * 100), # cents
        currency = 'usd',
        capture_method = 'automatic',
        metadata = {'product_id': str(product.id), 'bid_id': str(highest.id)}
    )

    purchase = PopUpPurchase.objects.create(
        customer = customer,
        product = product,
        bid = highest,
        stripe_pi = pi.id
    )

    notify_winner(customer, product, amount, purchase)
