from django.core.management.base import BaseCommand
from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerAddress
from pop_accounts.dummy_user_data import test_account_data
from django.contrib.auth import get_user_model

User = get_user_model()


"""
 email = models.EmailField(_('email address'), unique=True, db_index=True)
first_name = models.CharField(max_length=50, blank=True)
middle_name = models.CharField(max_length=50, blank=True)
last_name = models.CharField(max_length=50, blank=True)
mobile_phone = models.CharField(max_length=20, blank=True)
mobile_notification = models.BooleanField(default=True)
# stripe_customer_id = models.CharField(max_length=40, blank=True, null=True)
shoe_size = models.CharField(max_length=10)
size_gender = models.CharField(choices=SIZE_BY_GENDER, default='male', max_length=200)
favorite_brand = models.CharField(max_length=100, choices=BRAND_CHOICES, default='nike')
"""

"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(PopUpCustomer, verbose_name=_("Customer"), on_delete=models.CASCADE, related_name='address')
    prefix = models.CharField(max_length=10, choices=PREFIX_CHOICES, default="none")
    suffix = models.CharField(max_length=10, choices=SUFFIX_CHOICES, default="none")

    # New data, this allows for a name and phone# to be assigned to address
    # first_name = models.CharField(max_length=100, blank=True, null=True)
    # middle_name = models.CharField(max_length=100, blank=True, null=True)
    # last_name = models.CharField(max_length=100, blank=True, null=True)
    # phone_number = models.CharField(max_length=20, blank=True, null=True)

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
    deleted_at = models.DateTimeField(null=True, blank=True)
"""
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print('Running dummy user populate...')

        for tad in test_account_data:
            # print('tad', tad, '\n')
            if User.objects.filter(email=tad['email']).exists():
                self.stdout.write(self.style.WARNING(f"User with email {tad['email']} already exists, skipping name..."))
                continue

            # create the user
            new_user = User(
                email = tad['email'],
                first_name = tad['first_name'],
                middle_name = tad['middle_name'],
                last_name = tad['last_name'],
                mobile_phone = tad['mobile_phone'],
                mobile_notification = True,
            )
            new_user.set_password(tad['password'])
            new_user.save()

            # Update the auto-created PopUpCustomerProfile because it is already created by the signal
            profile = new_user.popupcustomerprofile
            profile.shoe_size = tad['shoe_size']
            profile.size_gender = tad['size_gender']
            profile.favorite_brand = tad['favorite_brand']
            profile.save()

            user_address = PopUpCustomerAddress(
                customer=new_user,
                postcode = tad["postcode"],
                address_line = tad["address_line"],
                address_line2 = tad["address_line2"],
                apartment_suite_number = tad["apartment_suite_number"],
                town_city = tad["town_city"],
                state = tad["state"],
                delivery_instructions = tad["delivery_instructions"],
                default=True,
                # first_name=user.first_name,
                # middle_name=user.middle_name,
                # last_name=user.last_name,
                # phone_number=user.mobile_phone,
            )

            user_address.save()

            self.stdout.write(self.style.SUCCESS(f"Created account for {tad['email']} with address"))
