from celery import shared_task
from django.utils.timezone import now
from .models import PopUpProduct
from datetime import timedelta
from pop_up_cart.cart import Cart
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.timezone import now
from pop_up_auction.models import WinnerReservation
from pop_up_cart.models import PopUpCartItem
from django.core.mail import mail_admins
from pop_up_email.utils import (
    send_auction_winner_email, send_24_hour_reminder_email, send_1_hour_reminder_email,
    send_interested_in_and_coming_soon_product_update_to_users
    )
import logging
logger = logging.getLogger(__name__)

# auction.tasks.check_auctions_and_finalize
@shared_task
def check_auctions_and_finalize():
    """
    Checks for end of auctions, 
    1. Adds product to cart of user with highest bid, 
    2. Locks item from other users from purchasing by updating inventory_status
    3. Creates WinnerReservation entry, which sets 48 hour clock on user to complete purchase
    4. Sends email to user notifying them that they've won
    """
    logger.info("check_auctions_and_finalize started")
    ended_auctions = PopUpProduct.objects.filter(
        auction_end_date__lte=now(),
        auction_finalized=False,
        is_active=True
    )

    print('ended_auctions', ended_auctions)

    for product in ended_auctions:
        highest_bid = product.bids.order_by('-amount', '-timestamp').first()
        print('check_auctions_and_finalize highest_bid:', highest_bid)

        if highest_bid:
            
            print('Hey!')
            print('product', product)        
  
            winner = highest_bid.customer
            
            product.winner = winner
            product.current_highest_bid = highest_bid.amount
            product.auction_finalized = True
            product.inventory_status = "sold_out"
            product.save()

            # Lock product in winner's cart
            try:
                PopUpCartItem.objects.update_or_create(
                    user=winner, 
                    product=product, 
                    defaults={'quantity': 1, 'auction_locked': True, 'buy_now': False}
                    )
                
                print('added to cart', winner, product)
            except Exception as e:
                print('e', e)

            # Add WinnerReservation
            try:
                reservation = WinnerReservation.objects.create(
                    user=winner,
                    product=product,
                    expires_at=now() + timedelta(hours=48),
                    is_paid=False,
                    is_expired=False,
                    notification_sent=True,
                    reminder_24hr_sent=False,
                    reminder_1hr_sent=False
                )
            except Exception as e:
                print('e', e)

            # Notify winner
            send_auction_winner_email(winner, product)
        else:
            product.auction_finalized = True
            product.save()


@shared_task
def mark_expired_reservations():
    """
    Marks all WinnerReservations as expired if their deadline has passed and they are not paid.
    """
    now_time = now()
    expired = WinnerReservation.objects.filter(
        expires_at__lte=now_time,
        is_paid=False,
        is_expired=False
    )

    for reservation in expired:
        reservation.is_expired = True
        reservation.save()

        # Re-list product
        product = reservation.product
        product.inventory_status = "in_inventory"
        product.winner = None
        product.save()

        # Remove from winner's cart
        Cart.objects.filter(
            user=reservation.user,
            product=product,
            auction_locked=True
        ).delete()
        
        mail_admins(subject=f"Auction Reservation Expired: {reservation.product.product_title}",
                message=(
                    f"The reservation for '{reservation.product.product_title}' by user "
                    f"{reservation.user.email} has expired and was not paid.\n\n"
                    f"Reservation expired at: {reservation.expires_at}"
                        )
                    )

   

    updated_count = expired.updated(is_expired=True)
    return f"{updated_count} reservations marked as expired"


@shared_task
def transition_expired_buy_now_to_auction():
    current_time = now()
    products = PopUpProduct.objects.filter(
        buy_now_end__lt=current_time,
        bought_now=False,
        auction_start_date__isnull=False,
        auction_end_date__isnull=False,
        is_active=True
    )


    for product in products:
        # if buy now expired and it wasn't purchased, it's ready for auction
        product.buy_now_start = None
        product.buy_now_end = None
        product.save()

        # notifiy users who checked "notify me" or "interested in" on product
        send_interested_in_and_coming_soon_product_update_to_users(
            product,
            auction_start_date = product.auction_start_date
        )


@shared_task
def send_reservation_reminders():
    now_time = now()
    reservations = WinnerReservation.objects.filter(is_paid=False, is_expired=False)

    for res in reservations:
        time_left = res.exipres_at - now_time

        if timedelta(hours=23, minutes=30) <= time_left <= timedelta(hours=24, minutes=30) and not res.reminder_24hr_sent:
            # send 24 hour reminder
            send_24_hour_reminder_email(res.user, res.product)
            res.reminder_24hr_sent = True
            res.save()

        elif timedelta(minutes=30) <= time_left <= timedelta(hours=1, minutes=30) and not res.reminder_1hr_sent:
            # send 1 hour reminder
            send_1_hour_reminder_email(res.user, res.product)
            res.reminder_1hr_sent = True
            res.save()