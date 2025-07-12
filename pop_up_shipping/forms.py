from django import forms
from .models import PopUpShipment

# Shipping Choices

"""
order = models.OneToOneField('orders.PopUpCustomerOrder', on_delete=models.CASCADE, related_name='shipment')
carrier = models.CharField(max_length=50, choices=CARRIER_CHOICES, default='usps')
tracking_number = models.CharField(max_length=100, blank=True, null=True)
shipped_at = models.DateTimeField(blank=True, null=True)
estimated_delivery = models.DateTimeField(blank=True, null=True)
delivered_at = models.DateTimeField(blank=True, null=True)
status = models.CharField(max_length=50, default='pending')
"""

class ThePopUpShippingForm(forms.ModelForm):
    order = forms.CharField(
        label='Order No.',  min_length=2, max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': 'shipping_order_no',
            'id': '',
            'placeholder': 'Order No.',
            'name': 'order_no',
        })
    )

    carrier = forms.ChoiceField(
        label='Carrier',
        choices=[("", "Select Carrier")] + PopUpShipment.CARRIER_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': 'shipping_carrier',
            'id': 'shipping_carrier',
            'name': 'carrier'
        })
    )

    tracking_number = forms.CharField(
        label='Tracking No.', min_length=2, max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'class': 'shipping_tracking_no',
            'id': '',
            'placeholder': 'Tracking No.',
            'name': 'tracking_number'
        })
    )

    shipped_at = forms.DateTimeField(
        label='Date Shipped',  required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'date',
            'class': 'shipping_shipped_at', 
            'placeholder': 'Date Shipped',
            'id': '',
            'name': 'shipped_at'
        })
    )

    estimated_delivery = forms.DateTimeField(
        label='Estimated Delivery', required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'date',
            'class': 'shipping_estimated_deliv',
            'id': '',
            'placeholder': 'Estimated Delivery',
            'name': 'estimated_delivery',
        })
    )

    delivered_at = forms.DateTimeField(
        label='Delivered At', required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'date',
            'class': 'shipping_delivered_at',
            'id': '',
            'placeholder': 'Delivered On',
            'name': 'delivered_at'
        }
    ))

    status = forms.ChoiceField(
        label='Status',
        choices=[("pending", "Pending")] + PopUpShipment.SHIPMENT_STATUS, required=False,
        widget=forms.Select(attrs={
            'class': 'shipping_status',
            'id': 'shipping_status',
            'placeholder': 'Status',
            'name': 'status'
        }
    ))

   


    class Meta:
        model = PopUpShipment
        fields = ['order', 'carrier', 'tracking_number', 'shipped_at', 'estimated_delivery', 'delivered_at', 
                  'status',]

