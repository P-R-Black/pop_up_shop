from django import forms
from pop_up_order.models import PopUpCustomerOrder


class CreatePopUpOrderForms(forms.ModelForm):
    class Meta:
        model = PopUpCustomerOrder
        fields = ['full_name', 'address1', 'address2', 'city', 'state', 'postal_code', 'phone']