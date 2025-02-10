from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin, BaseUserManager)
# from django_countries.fields import CountryField
import uuid


# Create your models here.
class CustomPopUpAccountManager(BaseUserManager):
    def create_superuser(self, email, user_name, first_name, password=None, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assinged to is staff=True.')

        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True.')

        if not email:
            raise ValueError('An email address is required.')

        if not user_name:
            raise ValueError('An user name is required.')

        if not password:
            raise ValueError('A user password is required.')

        # user = self.create_superuser(email, user_name, first_name, password, **other_fields)
        # user.is_superuser = True
        # user.is_staff = True
        # user.save()

        return self.create_user(email, user_name, first_name, password, **other_fields)

    def create_user(self, email, user_name, first_name, password, **other_fields):
        if not email:
            raise ValueError(_('An email address is required.'))

        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, first_name=first_name, **other_fields)
        user.set_password(password)
        user.save()
        return user


"""THE POP UP SHOP"""

# class PopUpCustomer(AbstractBaseUser, PermissionsMixin):
#     BRAND_CHOICES = (
#         ('adidas', 'Adidas'),
#         ('balenciaga', 'Balenciaga'),
#         ('brooks', 'Brooks'),
#         ('fear_of_god ', 'Fear of God'),
#         ('gucci', 'Gucci'),
#         ('jordan', 'Jordan'),
#         ('new_balance', 'New Balance'),
#         ('nike', 'Nike'),
#         ('prada', 'Prada'),
#         ('puma', 'Puma'),
#         ('reebok', 'Reebok'),
#         ('saucony', 'Saucony'),
#         ('yeezy', 'Yeezy')
#     )

#     SIZE_BY_GENDER = (
#         ('male', 'Male'),
#         ('female', 'Female')
#     )


#     email = models.EmailField(_('email address'), unique=True)
#     name = models.CharField(max_length=150)
#     name_prefix = models.CharField(max_length=6)
#     first_name = models.CharField(max_length=50, blank=True)
#     middle_name = models.CharField(max_length=50, blank=True)
#     last_name = models.CharField(max_length=50, blank=True)
#     name_suffix = models.CharField(max_length=10)
#     mobile_phone = models.CharField(max_length=20, blank=True)
#     mobilie_notification = models.BooleanField(default=False)
#     size = models.CharField(max_length=6)
#     size_gender = models.CharField(choices=SIZE_BY_GENDER, default='male')
#     favorite_brand = models.CharField(max_length=100, choices=BRAND_CHOICES, default='nike')

#     # User Status
#     is_active = models.BooleanField(default=False)
#     is_staff = models.BooleanField(default=False)
#     created = models.DateTimeField(auto_now_add=True)
#     updated = models.DateTimeField(auto_now_add=True)

#     objects = CustomPopUpAccountManager()

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['name', 'email']

#     class Meta:
#         verbose_name = 'Accounts'
#         verbose_name_plural = 'Accounts'

#     def email_user(self, subject, message):
#         send_mail(
#             subject,
#             message,
#             'l@1.com',
#             [self.email],
#             fail_silently=False,
#         )

    # def __str__(self):
    #     return self.name


# class PopUpCustomerAddress(models.Model):
#     """
#     Addresses
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     customer = models.ForeignKey(PopUpCustomer, verbose_name=_("Customer"), on_delete=models.CASCADE)
#     full_name = models.CharField(_("Full Name"), max_length=150)
#     phone = models.CharField(_("Phone Number"), max_length=50)
#     postcode = models.CharField(_("Postcode"), max_length=50)
#     address_line = models.CharField(_("Address Line 1"), max_length=255)
#     address_line2 = models.CharField(_("Address Line 2"), max_length=255, blank=True)
#     apartment_suite_number = models.CharField(_("Apartment/Suite"), max_length=50)
#     town_city = models.CharField(_("Town/City/State"), max_length=150)
#     delivery_instructions = models.CharField(_("Deliver Instructions"), max_length=255)
#     created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
#     updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
#     default = models.BooleanField(_("Default"), default=False)

#     class Meta:
#         verbose_name = 'Address'
#         verbose_name_plural = 'Addresses'

#     def __str__(self):
#         return "Address"