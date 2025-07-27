from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import PopUpCustomerIP
from .utils.utils import get_client_ip 

# @receiver(user_logged_in)
# def track_login_ip(sender, request, user, **kwargs):
#     ip_address = get_client_ip(request)
#     if not PopUpCustomerIP.objects.filter(customer=user, ip_address=ip_address).exists():
#         PopUpCustomerIP.objects.create(customer=user, ip_address=ip_address)

@receiver(user_logged_in)
def track_login_ip(sender, request, user, **kwargs):
    ip_address = get_client_ip(request)
    if ip_address and not PopUpCustomerIP.objects.filter(customer=user, ip_address=ip_address).exists():
        PopUpCustomerIP.objects.create(customer=user, ip_address=ip_address)
