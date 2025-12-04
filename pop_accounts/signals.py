from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PopUpCustomerIP, PopUpCustomerProfile
from django.contrib.auth import get_user_model
from .utils.utils import get_client_ip 

User = get_user_model()

@receiver(user_logged_in)
def track_login_ip(sender, request, user, **kwargs):
    ip_address = get_client_ip(request)
    if ip_address and not PopUpCustomerIP.objects.filter(customer=user, ip_address=ip_address).exists():
        PopUpCustomerIP.objects.create(customer=user, ip_address=ip_address)


@receiver(post_save, sender=User)
def create_popup_profile(sender, instance, created, **kwargs):
    if created:
        PopUpCustomerProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_customer_profile(sender, instance, **kwargs):
    # Ensure profile always sstays in sync if needed
    if hasattr(instance, "popupcustomerprofile"):
        instance.popupcustomerprofile.save()