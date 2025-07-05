from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model

def send_auction_winner_email(user, product):
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
    subject = f"✅ OK to Ship Order #{order.id}"
    message = render_to_string('emails/okay_to_ship_admin_alert.html', {"order": order})
    recipients = [a.email for a in get_admin_users()]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)


def send_dispute_alert_to_customer(order):
    return f"Payment failed for order #{order}"


def get_admin_users():
    User = get_user_model()
    return User.objects.filter(is_staff=True, is_active=True)