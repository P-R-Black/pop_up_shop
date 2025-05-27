from django import forms
from orders.models import PopUpCustomerOrder

"""
id
user
full_name
email
address1
address2
apartment_suite_number
city
state
postal_code
phone
created_at
updated_at
total_paid
order_key
billing_status
stripe_id
coupon
discount
"""
class CreatePopUpOrderForms(forms.ModelForm):
    class Meta:
        model = PopUpCustomerOrder
        fields = ['full_name', 'address1', 'address2', 'city', 'state', 'postal_code', 'phone']