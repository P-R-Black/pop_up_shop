from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from pop_accounts.models import PopUpCustomerProfile
from pop_up_auction.models import PopUpProduct
from django.db.models import Q




def send_auction_winner_email(user, product):
    """
    Notifies highest bidder in auction that they've won the auction
    Auction winner has 48 hours to pay for item.
    """

    deadline = now() + timedelta(hours=48)
    subject = "🎉 You Won the Auction!"
    html_message = render_to_string("pop_up_email/auction_winner.html", {
        "user": user,
        "product": product,
        "deadline": deadline,
    })

    send_mail(
        subject = subject,
        message="You've won an auction!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )

    return html_message


def send_24_hour_reminder_email(user, product):
    """
    Notifies auction winner that they have 24 hours remaining to pay for item.
    """
    now_time = now()
    subject = "24 Hours Left to Purchase Your Auction Item"
    html_message = render_to_string('pop_up_email/twenty_four_hour_reminder.html', {
        "user": user,
        "product": product,
    })

    send_mail(
        subject =subject,
        message=f"Hey {user.first_name}, you have 24 hours left to purchase {product.product_title}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )

    return html_message



def send_1_hour_reminder_email(user, product):
    """
    Notifies auction winner that they have 1 hour remaining to pay for item.
    """
    now_time = now()
    subject = "1 Hours Left to Purchase Your Auction Item"

    html_message = render_to_string('pop_up_email/one_hour_reminder.html', {
        "user": user,
        "product": product,
    })

    send_mail(
        subject =subject,
        message=f"Hey {user.first_name}, you have 1 hours left to purchase {product.product_title}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )

    return html_message


def send_order_confirmation_email(user, order_id, items, total_paid, payment_status="pending"):
    """
    Sent to user after purchase, providing user order number
    """
    subject = f"The Pop Up | Order No {order_id}"
    html_message = render_to_string('pop_up_email/order_confirmation.html', {
        'user': user,
        'order_id': order_id,
        'items': items,
        'total_paid': total_paid,
        'payment_status': payment_status
    })
   

    send_mail(
        subject = subject,
        message = "",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )


def send_okay_to_ship_email(order):
    """
    Notifies admin after a waiting period that item is okay to ship.
    Item is "okay to ship" if no payment disputes within waiting period.
    """
    subject = f"✅ OK to Ship Order #{order.id}"
    message = render_to_string('pop_up_email/okay_to_ship_admin_alert.html', {"order": order})
    recipients = [a.email for a in get_admin_users()]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)


def send_dispute_alert_to_customer(order):
    """
    Notifies customer that payment wasn't approved
    """
    return f"Payment failed for order #{order}"


def send_customer_shipping_details(user, order, carrier, tracking_no, shipped_at, estimated_deliv, status):
    """
    Notifies user that item has been shipped. 
    Provides user with order no and shipping details
    """
    links_to_track_shipment = {
            "usps": "https://tools.usps.com/",
            "ups": "https://www.ups.com/us/en/home",
            "FedEx": "https://www.fedex.com/en-us/tracking.html"

    }

    subject = f"Your order has shipped Order #{order.id}."
    html_message = render_to_string('pop_up_email/send_customer_shipping_details.html', {
        'order': order.id, 'carrier': carrier,
        'tracking_no': tracking_no, 'shipped_at': shipped_at,
        'estimated_deliv': estimated_deliv, 
        'status': status, 
        'tracker_link': links_to_track_shipment[carrier] })
    
    send_mail(
        subject = subject,
        message = "",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )
    


def send_friend_invite_email(user, user_email, friend_name, friend_email):
    """
    Emails invitation from member to member's friend
    """
    subject = f"{user} invited you to join The Pop Up!"
    # invite_link = reverse('account_signup')
 
    # full_invite_url = f"{settings.SITE_DOMAIN}/?show_auth_modal=true"
    full_invite_url = f"localhost:8000/?show_auth_modal=true"
    html_message = render_to_string('pop_up_email/invite_friend.html', {
        'user': user, 
        'user_email': user_email, 
        'friend_name': friend_name, 
        'friend_email': friend_email, 
        'invite': friend_name,
        'invite_link': full_invite_url
    })

    send_mail(
        subject = subject,
        message = "",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[friend_email],
        html_message=html_message
    )



def get_admin_users():
    User = get_user_model()
    return User.objects.filter(is_staff=True, is_active=True)


def interested_in_products_update_and_notify_me_products_update(product_id):
    """
    Finds all users interested in a product and notifies them via email.
    """
    
    try:
        product = PopUpProduct.objects.get(id=product_id)
    except PopUpProduct.DoesNotExist:
        return []

    # Fetch all users who are either interested OR notified, without duplicates
    users = PopUpCustomerProfile.objects.filter(Q(prods_interested_in=product) | Q(prods_on_notice_for=product)
    ).select_related('user').distinct()

    # Return their emails
    return list(users.values_list("user__email", flat=True))



def send_interested_in_and_coming_soon_product_update_to_users(
    product, 
    buy_now_start_date=None,
    auction_start_date=None,
    ):
    """
    Emails Users who have marked a product "interested in" of udpate with product
    """
    
    users = PopUpCustomerProfile.objects.filter(
        Q(prods_interested_in=product) | Q(prods_on_notice_for=product)
        ).select_related('user').distinct()
    
    if not users.exists():
        return
    
    # Choose subject & plan text message
    subject = f"Update on {product.product_title} {product.secondary_product_title}"

    from_email = settings.DEFAULT_FROM_EMAIL

    # Send Individually for personalization
    for user in users:
        print('user.user', user.user)
        print('user', user)
        html_message = render_to_string(
            'pop_up_email/update_interested_users.html', 
            {
                'user': user,
                'product': product, 
                'buy_now_start_date': buy_now_start_date if buy_now_start_date else "", 
                'auction_start_date': auction_start_date if auction_start_date else "", 

            }
        )

        send_mail(
            subject=subject,
            message = "",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.user.email], # sent to single user for a more personalized email
            html_message=html_message,
            fail_silently=False
        )