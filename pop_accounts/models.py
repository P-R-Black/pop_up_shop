from ast import arg
from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin, BaseUserManager)
# from django_countries.fields import CountryField
import uuid
from pop_up_auction.models import PopUpProduct
from django.contrib.auth.models import UserManager
# from .managers import CustomPopUpAccountManager  # Assuming you have a custom user manager


# Create your models here.
class ActiveUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class AllUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    
class CustomPopUpAccountManager(ActiveUserManager, BaseUserManager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def get_by_natural_key(self, email):
        return self.get(email=email)
    
    def create_superuser(self, email, first_name, last_name, password, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must be assinged to is staff=True.'))

        if other_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must be assigned to is_superuser=True.'))


        return self.create_user(email, first_name, last_name, password, **other_fields)

    def create_user(self, email, first_name=None, last_name=None, password=None, **other_fields):
        if not email:
            raise ValueError(_('An email address is required.'))

        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **other_fields)
        user.set_password(password)
        user.save(using=self._db)
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
    first_name = models.CharField(max_length=50, blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    mobile_phone = models.CharField(max_length=20, blank=True, null=True)
    mobile_notification = models.BooleanField(default=True)
    stripe_customer_id = models.CharField(max_length=40, blank=True, null=True)
    shoe_size = models.CharField(max_length=10, null=True)
    size_gender = models.CharField(choices=SIZE_BY_GENDER, default='male', max_length=200, null=True)
    favorite_brand = models.CharField(max_length=100, choices=BRAND_CHOICES, default='nike')
    deleted_at = models.DateTimeField(null=True, blank=True)  

    # Relationships
    prods_interested_in = models.ManyToManyField(PopUpProduct, related_name="interested_users", blank=True)
    prods_on_notice_for = models.ManyToManyField(PopUpProduct, related_name="notified_users", blank=True)


    # User Status
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    last_password_reset = models.DateTimeField(null=True, blank=True)

    objects = CustomPopUpAccountManager() # only active users (soft-delete-aware)
    all_objects = AllUserManager() # includes deleted

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    class Meta:
        verbose_name = 'PopUpCustomer'
        verbose_name_plural = 'PopUpCustomers'
    
    @property
    def open_bids(self):
        return self.bids.filter(is_active=True)

    @property
    def past_bids(self):
        return self.bids.filter(is_active=False)
    

    def soft_delete(self):
        """ 
        Mark the user account as inactive instead of deleting it.
        """
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
        super().delete()
    



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
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Ms.', 'Ms.'),
        ('Miss', 'Miss'),
        ('Dr', 'Dr.'),
        ('Prof', 'Prof.'),
    ]

    SUFFIX_CHOICES = [
        ('Jr.', 'Jr.'),
        ('Sr.', 'Sr.'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
        ('CPA', 'CPA'),
        ('M.D.', 'M.D.'),
        ('PhD', 'PhD'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(PopUpCustomer, verbose_name=_("Customer"), on_delete=models.CASCADE, related_name='address')
    
    # New data, this allows for a name and phone# to be assigned to address
    prefix = models.CharField(max_length=10, choices=PREFIX_CHOICES, default="", blank=True, null=True)
    suffix = models.CharField(max_length=10, choices=SUFFIX_CHOICES, default="", blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    # Don't actually Need Phone Number in this model, text updates about delivery would be sent
    # to primary user in PopUpCustomer
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    postcode = models.CharField(_("Postcode"), max_length=50)
    address_line = models.CharField(_("Address Line 1"), max_length=255)
    address_line2 = models.CharField(_("Address Line 2"), max_length=255, blank=True)
    apartment_suite_number = models.CharField(_("Apartment/Suite"), max_length=50, blank=True)
    town_city = models.CharField(_("Town/City"), max_length=150)
    state = models.CharField(_("State"), max_length=100)
    delivery_instructions = models.TextField(_("Deliver Instructions"), blank=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    default = models.BooleanField(_("Default"), default=False)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)
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
    product = models.ForeignKey('pop_up_auction.PopUpProduct', on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_winning_bid = models.BooleanField(default=False)

    # Auto-bidding fields
    max_auto_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum bid limit for automatic bidding.")
    bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Minimum amount by which the next bid must increase.")

    # Expiration Field
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Bid expiration time.")

    class Meta:
        verbose_name = 'PopUpBid'
        verbose_name_plural = 'PopUpBids'
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.customer} - {self.product} - ${self.amount}"

    def save(self, *args, **kwargs):
        """
        Ensure bid amount is valid before saving
        """
        # latest_bid = PopUpBid.objects.filter(product=self.product, is_active=True).order_by('-amount').first()
        latest_bid = PopUpBid.objects.filter(product=self.product, is_active=True).exclude(pk=self.pk).order_by('-amount').first()

        if latest_bid:
            print('latest_bid', latest_bid)
            if self.amount <= latest_bid.amount:
                print(f'self.amount: {self.amount} | latest_bid.amount: {latest_bid.amount}')
                raise ValueError('Bid amount must be higher than the current highest bid.')
        if self.expires_at and self.expires_at < timezone.now():
            self.is_active = False

        super().save(*args, **kwargs)


        highest = PopUpBid.get_highest_bid(self.product)
        product = self.product
        product.current_highest_bid = highest.amount if highest else None
        product.bid_count += 1
        product.save(update_fields=['current_highest_bid', 'bid_count'])

        # Reset all other bids to is_winning_bid=False
        PopUpBid.objects.filter(product=self.product).update(is_winning_bid=False)

        # ✅ Set current highest bid to is_winning_bid=True
        if highest:
            PopUpBid.objects.filter(pk=highest.pk).update(is_winning_bid=True)

        # Handle aut-bidding after saving
        self.process_auto_bid()
    

    def process_auto_bid(self, round=0, max_rounds=5):
        """
        Handles auto-bidding with protection against infinite loops.
        """
        if round >= max_rounds:
            print(f"[Auto-bid] Max rounds ({max_rounds}) reached. Stopping auto-bids.")
            return

        current_highest = PopUpBid.objects.filter(product=self.product, is_active=True).order_by('-amount', '-timestamp').first()
        print(f'current_highest: {current_highest}' )

        # Check if auto-bidding applies
        if not current_highest or not current_highest.max_auto_bid:
            return
        
        # Check if there's another user's auto-bid that needs to be triggered
        competing_bids = PopUpBid.objects.filter(
            product=self.product,
            is_active=True,
            max_auto_bid__isnull=False
        ).exclude(customer=self.customer) #.order_by('-amount','-timestamp')

        print(f'competing_bids: {competing_bids}')

        for competitor in competing_bids:
            proposed_amount = current_highest.amount + competitor.bid_increment    
            if proposed_amount <= competitor.max_auto_bid:
                try:
                    new_bid = PopUpBid.objects.create(
                        customer=competitor.customer,
                        product=competitor.product,
                        amount=proposed_amount,
                        is_active=True,
                        max_auto_bid=competitor.max_auto_bid,
                        bid_increment=competitor.bid_increment
                    )
                    new_bid.save()
                    print(f"[Auto-bid] New auto-bid placed: {new_bid}")

                    # Recursively check for another auto-bid with incremented round
                    new_bid.process_auto_bid(round=round + 1, max_rounds=max_rounds)
                except ValueError as e:
                    print(f"[Auto-bid] skipped at: {proposed_amount}")
            
                break # Stop after first successful auto-bid to prevent mass bid pileups

    
    @classmethod
    def get_highest_bid(cls, product):
        """
        Get the highest bid for a given a product
        """
        return cls.objects.filter(product=product).order_by('-amount').first()
    

class PopUpPurchase(models.Model):
    """
    Model for tracking purchases
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(PopUpCustomer, on_delete=models.PROTECT, related_name="purchases")
    product = models.ForeignKey(PopUpProduct, on_delete=models.PROTECT, related_name="purchases")
    bid = models.ForeignKey(PopUpBid, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    purchased_at = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(PopUpCustomerAddress, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_api = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-purchased_at"]
        verbose_name = _("PopUp Customer Purchase")
        verbose_name_plural = _("PopUp Customer PopUp Purchases")
    
    def __str__(self):
        return f"{self.customer} - {self.product} - ${self.price}"

    
    
class PopUpCustomerIP(models.Model):
    """
    Model for tracking customer IP Address
    """
    customer = models.ForeignKey(PopUpCustomer, on_delete=models.CASCADE, related_name="ip_addresses")
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "PopUp Customer IP Address"
        verbose_name_plural = "PopUp Customer IP Addresses"
    
    def __str__(self):
        return f"{self.customer.email} - {self.ip_address} ({self.created_at})"


class PopUpCustomerPayment(models.Model):
    """
    Model for tracking customer payment preference
    """
    customer = models.OneToOneField(PopUpCustomer, on_delete=models.CASCADE, related_name="payment_info")
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_billing_agreement_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


# To track every password reset link sent
class PopUpPasswordResetRequestLog(models.Model):
    customer = models.ForeignKey(PopUpCustomer, on_delete=models.CASCADE, related_name='password_reset_logs')
    ip_address = models.GenericIPAddressField()
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'PopUp Password Reset Request Log'
        verbose_name_plural = 'PopUp Password Reset Request Logs'

    def __str__(self):
        return f"{self.customer.email} - {self.ip_address} @ {self.requested_at}"
    

"""
rm -rf quotes_api/migrations/  # Remove migration files
python3 manage.py flush         # Clears all data from the database
python3 manage.py makemigrations quotes_api
python3 manage.py migrate

"""
