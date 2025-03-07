from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin, BaseUserManager)
# from django_countries.fields import CountryField
import uuid
from auction.models import PopUpProducts

# from .managers import CustomPopUpAccountManager  # Assuming you have a custom user manager


# Create your models here.
class CustomPopUpAccountManager(BaseUserManager):
    def create_superuser(self, email, first_name, last_name, password=None, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assinged to is staff=True.')

        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True.')

        if not email:
            raise ValueError('An email address is required.')

        # if not user_name:
        #     raise ValueError('An user name is required.')

        # if not password:
        #     raise ValueError('A user password is required.')

        # user = self.create_superuser(email, user_name, first_name, password, **other_fields)
        # user.is_superuser = True
        # user.is_staff = True
        # user.save()

        return self.create_user(email, first_name, last_name, password, **other_fields)

    def create_user(self, email, first_name, last_name, password, **other_fields):
        if not email:
            raise ValueError(_('An email address is required.'))

        email = self.normalize_email(email)
        user = self.model(email=email, last_name=last_name, first_name=first_name, **other_fields)
        user.set_password(password)
        user.save()
        return user


"""THE POP UP SHOP"""

class SoftDeleteUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)



class PopUpCustomer(AbstractBaseUser, PermissionsMixin):
    BRAND_CHOICES = (
        ('adidas', 'Adidas'),
        {'asics', 'Asics'},
        ('balenciaga', 'Balenciaga'),
        ('brooks', 'Brooks'),
        ('fear_of_god ', 'Fear of God'),
        ('gucci', 'Gucci'),
        ('jordan', 'Jordan'),
        ('new_balance', 'New Balance'),
        ('nike', 'Nike'),
        ('prada', 'Prada'),
        ('puma', 'Puma'),
        ('reebok', 'Reebok'),
        ('saucony', 'Saucony'),
        ('yeezy', 'Yeezy')
    )

    SIZE_BY_GENDER = (
        ('male', 'Male'),
        ('female', 'Female')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    first_name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    mobile_phone = models.CharField(max_length=20, blank=True)
    mobile_notification = models.BooleanField(default=False)
    shoe_size = models.CharField(max_length=6)
    size_gender = models.CharField(choices=SIZE_BY_GENDER, default='male', max_length=200)
    favorite_brand = models.CharField(max_length=100, choices=BRAND_CHOICES, default='nike')
    deleted_at = models.DateTimeField(null=True, blank=True)  

    # Relationships
    prods_interested_in = models.ManyToManyField(PopUpProducts, related_name="interested_users", blank=True)
    prods_on_notice_for = models.ManyToManyField(PopUpProducts, related_name="notified_users", blank=True)

    # Bidding Information
    open_bids = models.ManyToManyField("PopUpBid", related_name="active_bids", blank=True)
    past_bids = models.ManyToManyField("PopUpBid", related_name="past_bids", blank=True)
    past_purchases = models.ManyToManyField("PopUpPurchase", related_name="user_purchases", blank=True)

    # User Status
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SoftDeleteUserManager()
    all_objects = models.Manager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'PopUpCustomers'
        verbose_name_plural = 'PopUpCustomers'
    
    def soft_delete(self):
        """Mark the user account as inactive instead of deleting it."""
        self.is_active = False  # Prevents login
        self.deleted_at = now()
        self.save(update_fields=["is_active", "deleted_at"])

    def restore(self):
        """Restore a previously deactivated account."""
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=["is_active", "deleted_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def delete(self, *args, **kwargs):
        """Override delete method to soft delete the user instead."""
        self.soft_delete()

    def hard_delete(self):
        """Permanently delete the account (only for admin use)."""
        super().delete(*args, **kwargs)


    def email_user(self, subject, message):
        send_mail(
            subject,
            message,
            'l@1.com',
            [self.email],
            fail_silently=False,
        )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class PopUpCustomerAddress(models.Model):
    """
    Shipping Address for Users
    """
    PREFIX_CHOICES = [
        ('mr', 'Mr.'),
        ('mrs', 'Mrs.'),
        ('ms', 'Ms.'),
        ('dr', 'Dr.'),
        ('prof', 'Prof.'),
        ('none', 'None'),
    ]

    SUFFIX_CHOICES = [
        ('jr', 'Jr.'),
        ('sr', 'Sr.'),
        ('ii', 'II'),
        ('iii', 'III'),
        ('iv', 'IV'),
        ('none', 'None'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(PopUpCustomer, verbose_name=_("Customer"), on_delete=models.CASCADE)
    prefix = models.CharField(max_length=10, choices=PREFIX_CHOICES, default="none")
    suffix = models.CharField(max_length=10, choices=SUFFIX_CHOICES, default="none")
    postcode = models.CharField(_("Postcode"), max_length=50)
    address_line = models.CharField(_("Address Line 1"), max_length=255)
    address_line2 = models.CharField(_("Address Line 2"), max_length=255, blank=True)
    apartment_suite_number = models.CharField(_("Apartment/Suite"), max_length=50)
    town_city = models.CharField(_("Town/City"), max_length=150)
    state = models.CharField(_("State"), max_length=100)
    delivery_instructions = models.TextField(_("Deliver Instructions"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    default = models.BooleanField(_("Default"), default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'PopUpCustomerAddress'
        verbose_name_plural = 'PopUpCustomerAddresses'

    def __str__(self):
        return f"{self.customer.first_name} {self.customer.last_name} - {self.address_line}, {self.town_city}"


    def save(self, *args, **kwargs):
        if self.default:
            PopUpCustomerAddress.objects.filter(customer=self.customer, default=True).update(default=False)
        super().save(*args, **kwargs)
    

    def soft_delete(self):
        """Mark the address as deleted instead of removing it."""
        self.__class__.all_objects.filter(id=self.id).update(deleted_at=now())
    

    def restore(self):
        """Restore a soft-deleted address."""
        self.__class__.all_objects.filter(id=self.id).update(deleted_at=None)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def delete(self, *args, **kwargs):
        self.soft_delete()


class PopUpBid(models.Model):
    """
    Model for tracking Bids
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(PopUpCustomer, on_delete=models.CASCADE, related_name="bids")
    product = models.ForeignKey(PopUpProducts, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.customer} - {self.product} - ${self.amount}"


class PopUpPurchase(models.Model):
    """
    Model for tracking purchases
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(PopUpCustomer, on_delete=models.CASCADE, related_name="purchases")
    product = models.ForeignKey(PopUpProducts, on_delete=models.CASCADE, related_name="purchases")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(PopUpCustomerAddress, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-purchased_at"]
    
    def __str__(self):
        return f"{self.customer} - {self.product} - ${self.price}"