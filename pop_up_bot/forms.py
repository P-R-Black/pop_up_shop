from django import forms
from pop_up_bot.models import ProcurementServiceRequest

from django.contrib.auth import get_user_model

User = get_user_model()

"""
Forms By Name
 1. ServicePaymentForm
"""


class ServicePaymentForm(forms.ModelForm):
    class Meta:
        model = ProcurementServiceRequest
        fields = ['user', 'scheduled_release', 'size', 'color', 'max_price', 'strategy', 'service_fee', 'fee_paid_at', 'status']



