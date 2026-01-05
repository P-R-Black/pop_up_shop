from django.utils import timezone
from pop_up_auction.models import PopUpProduct
from celery import shared_task


@shared_task
def release_expired_reservations():
    now = timezone.now()
    expired = PopUpProduct.objects.filter(inventory_status='reserved', reserved_until__lt=now)
    expired.update(inventory_status='in_inventory', reserved_until=None)
