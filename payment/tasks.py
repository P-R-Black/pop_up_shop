from django.utils.timezone import now
from django.utils import timezone
from celery import shared_task
from .models import PopUpPayment
from pop_up_email.utils import send_okay_to_ship_email



@shared_task
def notify_admin_okay_to_ship():
    now = timezone.now()
    due_payments = PopUpPayment.objects.filter(
        status='paid', suspicious_flagged=False, notified_ready_to_ship=False
        ).select_related('order').only('created_at', 'notified_ready_to_ship', 'status')


    for payment in due_payments:
        if payment.release_at_computed <= now:
            send_okay_to_ship_email(payment.order)
            payment.notified_ready_to_ship = True
            payment.save()
