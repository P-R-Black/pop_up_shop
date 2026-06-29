from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from pop_accounts.models import PopUpCustomerProfile
from pop_up_auction.models import PopUpProduct, WinnerReservation
from django.db.models import Q
from pop_up_bot.models import ProcurementServiceRequest
import logging

logger = logging.getLogger(__name__)


""" 
- List of Email Utility Functions 

 1. send_2fa_code_email
 2. send_auction_winner_email
 3. send_24_hour_reminder_email
 4. send_1_hour_reminder_email
 5. send_order_confirmation_email
 6. send_okay_to_ship_email
 7. send_dispute_alert_to_customer
 8. send_customer_shipping_details
 9. send_friend_invite_email
10. get_admin_users
11. interested_in_products_update_and_notify_me_products_update
12. send_interested_in_and_coming_soon_product_update_to_users
13. send_success_notification
14. send_failure_notification
"""


def send_2fa_code_email(user, code):
    """
    Sends a 2FA verification code to the user's email.
    
    Args:
        user: User object with email and first_name
        code: 6-digit verification code string
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "Your Verification Code - The Pop Up"
    
    html_message = render_to_string('pop_up_email/two_factor.html', {
        "user": user,
        "code": code,
    })
    
    plain_text_message = f"Your Pop Up verification code is: {code}. This code expires in 5 minutes. Never share this code with anyone."
    
    try:
        send_mail(
            subject=subject,
            message=plain_text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send 2FA email to {user.email}: {str(e)}")
        return False
    

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

    # Get the reservation to pass expires_at to template
    reservation = WinnerReservation.objects.get(user=user, product=product)


    html_message = render_to_string('pop_up_email/twenty_four_hour_reminder.html', {
        "user": user,
        "product": product,
        'reservation': reservation
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

    # Get the reservation to pass expires_at to template
    reservation = WinnerReservation.objects.get(user=user, product=product)

    html_message = render_to_string('pop_up_email/one_hour_reminder.html', {
        "user": user,
        "product": product,
        "reservation": reservation
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
    subject = f"Order #{order.id} - Approved for Shipment"    
    html_message = render_to_string('pop_up_email/okay_to_ship_admin_alert.html', {
        "order": order.id
    })
    
    plain_text_message = f"Order #{order.id} has been approved for shipment. Payment verification period has passed without disputes."    
    recipients = [a.email for a in get_admin_users()]
    
    try:
        send_mail(
            subject=subject,
            message=plain_text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send okay_to_ship email for order {order.id}: {str(e)}")


    # subject = f"✅ OK to Ship Order #{order.id}"
    # message = render_to_string('pop_up_email/okay_to_ship_admin_alert.html', {"order": order})
    # recipients = [a.email for a in get_admin_users()]
    # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)


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
    print('email triggered for interested')
    users = PopUpCustomerProfile.objects.filter(
        Q(prods_interested_in=product) | Q(prods_on_notice_for=product)
        ).select_related('user').distinct()
    
    print('users interested', users)
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


REFUNDABLE_ERRORS = {
    'bot_crash', 'rate_limited', 'site_structure_changed',
    'exception', 'unknown_error',
}
 
 
def send_success_notification(service_request: ProcurementServiceRequest, execution):
    """Send HTML email when bot successfully secures item."""
    user = service_request.user
    product = service_request.scheduled_release.product
 
    subject = f"The Pop Up | ✅ We secured {product.product_title}!"
    html_message = render_to_string('pop_up_email/procurement_success_email.html', {
        'user': user,
        'product': product,
        'service_request': service_request,
        'execution': execution,
        'site_url': settings.SITE_URL,
    })
 
    try:
        send_mail(
            subject=subject,
            message='',          # plain text fallback — empty is fine
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Success notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send success email to {user.email}: {str(e)}")
 
 
def send_failure_notification(
    service_request: ProcurementServiceRequest,
    error: str,
    error_type: str = None,
):
    """
    Send HTML email when bot fails to secure item.
 
    The email content adapts based on whether the error is refundable:
    - Refundable (bot crash, rate limited): yellow banner, confirms refund
    - Non-refundable (sold out, lost to bots): red banner, explains policy
    """
    user = service_request.user
    product = service_request.scheduled_release.product
    is_refundable = error_type in REFUNDABLE_ERRORS if error_type else False
 
    # Human-readable reason for the failure
    reason = _failure_reason(error_type, error)
 
    subject = f"The Pop Up | Procurement Update — {product.product_title}"
 
    html_message = render_to_string('pop_up_email/procurement_failure_email.html', {
        'user': user,
        'product': product,
        'service_request': service_request,
        'reason': reason,
        'is_refundable': is_refundable,
        'site_url': settings.SITE_URL,
    })
 
    try:
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Failure notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send failure email to {user.email}: {str(e)}")
 
 
def _failure_reason(error_type: str, raw_error: str = None) -> str:
    """
    Convert an error_type into a user-friendly explanation.
    Avoids exposing technical stack traces to users.
    """
    reason_map = {
        'out_of_stock':           (
            'The item sold out before our bot could complete the purchase. '
            'High-demand releases often sell out in seconds.'
        ),
        'lost_to_bots':           (
            'The item was available but other bots were faster this time. '
            'We competed but were unable to complete the purchase in time.'
        ),
        'item_not_found':         (
            'Our bot could not locate the item on the retailer\'s site at release time. '
            'This may mean the product URL or SKU has changed.'
        ),
        'sold_out':               (
            'The item was listed as sold out when our bot attempted to purchase it.'
        ),
        'coming_soon':            (
            'The item was marked as "Coming Soon" and was not available for purchase '
            'during the procurement window.'
        ),
        'rate_limited':           (
            'The retailer\'s site temporarily blocked our bot due to high traffic. '
            'This is a technical issue on our end and your fee has been refunded.'
        ),
        'bot_crash':              (
            'Our bot encountered an unexpected technical error during the procurement attempt. '
            'This is a technical issue on our end and your fee has been refunded.'
        ),
        'site_structure_changed': (
            'The retailer updated their website layout, which prevented our bot from '
            'completing the purchase. Your fee has been refunded while we update our system.'
        ),
        'exception':              (
            'An unexpected error occurred during the procurement attempt. '
            'Your fee has been refunded.'
        ),
        'unknown_error':          (
            'An unexpected error occurred. Your fee has been refunded.'
        ),
    }
    return reason_map.get(error_type or '', raw_error or 'The procurement attempt was unsuccessful.')