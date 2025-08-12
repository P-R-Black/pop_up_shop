from django.db import models
import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class PopUpCoupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    active = models.BooleanField()

    def __str__(self):
        return self.code

# This is a temporary model. This is to track referral from inviting 
# friends $10 to invitee and inviter if invitee signs up.
# This doesnt meet MVP requiremment, so it's being pushed down the road
def generate_referral_code():
    return uuid.uuid4().hex[:12].upper()

class PopUpReferral(models.Model):
    code = models.CharField(max_length=12, unique=True, default=generate_referral_code)
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_referrals')
    invitee = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='referral_from')
    created_at = models.DateTimeField(auto_now_add=True)
    is_reward = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.inviter.email} invited {self.invitee.email if self.invitee else 'Pending'}"