from django import forms
from django.contrib import admin

from .models import (PopUpCustomer)


# Register your models here.

@admin.register(PopUpCustomer)
class PopUpCustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'favorite_brand',]
