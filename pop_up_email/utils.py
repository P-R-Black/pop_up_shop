from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model


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
    message = render_to_string('emails/okay_to_ship_admin_alert.html', {"order": order})
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
            "USPS": "https://tools.usps.com/go/TrackConfirmAction_input?_gl=1*ctcvbi*_ga*MjA2NDExMTY3Ni4xNzUxNTA0NzI3*_ga_QM3XHZ2B95*czE3NTI3MDA0MzkkbzExJGcxJHQxNzUyNzAwNTM0JGo2MCRsMCRoMA..",
            "UPS": "https://www.ups.com/us/en/home",
            "FedEx": "https://www.fedex.com/en-us/tracking.html"

    }



    subject = f"Your order has shipped Order #{order.id}."
    html_message = render_to_string('emails/send_customer_shipping_details.html', {
        'order': order, 'carrier': carrier,
        'tracking_no': tracking_no, 'shipped_at': shipped_at,
        'estimated_deliv': estimated_deliv, 'status': status, 'tracke_link': links_to_track_shipment[carrier]})
    
    send_mail(
        subject = subject,
        message = "",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )
    



def get_admin_users():
    User = get_user_model()
    return User.objects.filter(is_staff=True, is_active=True)