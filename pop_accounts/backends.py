from django.contrib.auth.backends import BaseBackend
from pop_accounts.models import PopUpCustomer

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None:
            email = kwargs.get('username')  # fallback to username param
        try:
            user = PopUpCustomer.objects.get(email=email)
        except PopUpCustomer.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return PopUpCustomer.objects.get(pk=user_id)
        except PopUpCustomer.DoesNotExist:
            return None
    
    # def authenticate(self, request, username=None, password=None, **kwargs):
    #     try:
    #         user = PopUpCustomer.objects.get(email=username)
    #         if user.check_password(password):
    #             return user
    #     except PopUpCustomer.DoesNotExist:
    #         return None
