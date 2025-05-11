from django import forms
from django.contrib import admin

from .models import (PopUpCustomer, PopUpCustomerAddress,PopUpPasswordResetRequestLog)


# Register your models here.

@admin.register(PopUpCustomer)
class PopUpCustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'favorite_brand',]


@admin.register(PopUpCustomerAddress)
class PopUpCustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['address_line', 'address_line2', 'apartment_suite_number', 'town_city', 
                    'state', 'delivery_instructions', 'postcode',]


@admin.register(PopUpPasswordResetRequestLog)
class PopUpPasswordResetRequestLogAdmin(admin.ModelAdmin):
    list_display = ['customer', 'ip_address', 'requested_at',]