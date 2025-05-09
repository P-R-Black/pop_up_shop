from django.test import TestCase
from pop_accounts.models import (PopUpCustomer, CustomPopUpAccountManager, SoftDeleteManager, PopUpCustomerAddress)

from django.utils.timezone import now
from datetime import datetime, timedelta
from django.utils.timezone import make_aware


class TestPopUpCustomerModel(TestCase):
    def setUp(self):
        self.customer = PopUpCustomer.objects.create(
            email="testMail@gmail.com",
            first_name="Palo",
            last_name="Negro",
            middle_name="Olop",
            mobile_phone="555-555-5555",
            mobile_notification=True,
            shoe_size="9.5",
            size_gender="Male",
            favorite_brand="Jordan"
        )

    def test_pop_customer_model_entry(self):
        """
        Test PopUpCustomer Data Insertion/Types Field Attributes
        """

        self.assertEqual(str(self.customer.email), 'testMail@gmail.com')
        self.assertEqual(str(self.customer.first_name), 'Palo')
        self.assertEqual(str(self.customer.last_name), 'Negro')
        self.assertEqual(str(self.customer.middle_name), 'Olop')
        self.assertEqual(str(self.customer.mobile_phone), '555-555-5555')
        self.assertEqual(str(self.customer.mobile_notification), "True")
        self.assertEqual(str(self.customer.shoe_size), "9.5")
        self.assertEqual(str(self.customer.size_gender), "Male")
        self.assertEqual(str(self.customer.favorite_brand), "Jordan")


class TestSoftDeleteManager(TestCase):
    pass

class TestPopUpCustomerAddress(TestCase):
    pass


"""
Run Test
python3 manage.py test pop_accounts/tests
"""

"""
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
    mobile_notification = models.BooleanField(default=True)
    shoe_size = models.CharField(max_length=10)
    size_gender = models.CharField(choices=SIZE_BY_GENDER, default='male', max_length=200)
    favorite_brand = models.CharField(max_length=100, choices=BRAND_CHOICES, default='nike')
    deleted_at = models.DateTimeField(null=True, blank=True)  

    # Relationships
    prods_interested_in = models.ManyToManyField(PopUpProduct, related_name="interested_users", blank=True)
    prods_on_notice_for = models.ManyToManyField(PopUpProduct, related_name="notified_users", blank=True)

    # Bidding Information
    open_bids = models.ManyToManyField("PopUpBid", related_name="active_bids", blank=True)
    past_bids = models.ManyToManyField("PopUpBid", related_name="past_bids", blank=True)
    past_purchases = models.ManyToManyField("PopUpPurchase", related_name="user_purchases", blank=True)

    # User Status
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    last_password_reset = models.DateTimeField(null=True, blank=True)

    objects = CustomPopUpAccountManager()
    # objects = SoftDeleteUserManager()
    # all_objects = models.Manager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']


    class Meta:
        verbose_name = 'PopUpCustomer'
        verbose_name_plural = 'PopUpCustomers'
    
"""