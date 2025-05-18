from django import forms
from django.contrib import admin
from django.utils.html import format_html_join
from .models import (PopUpCustomer, PopUpCustomerAddress,PopUpPasswordResetRequestLog, PopUpBid, PopUpPurchase)


# Register your models here.
@admin.register(PopUpCustomerAddress)
class PopUpCustomerAddressAdmin(admin.ModelAdmin):
    list_display = ['address_line', 'address_line2', 'apartment_suite_number', 'town_city', 
                    'state', 'delivery_instructions', 'postcode',]


@admin.register(PopUpPasswordResetRequestLog)
class PopUpPasswordResetRequestLogAdmin(admin.ModelAdmin):
    list_display = ['customer', 'ip_address', 'requested_at',]


@admin.register(PopUpBid)
class PopUpBidAdmin(admin.ModelAdmin):
    list_display =['id', 'customer', 'product_id', 'amount', 'timestamp', 'is_active', 'is_winning_bid',
                    'max_auto_bid', 'bid_increment', 'expires_at',]


class PurchaseInLine(admin.TabularInline):
    model = PopUpPurchase
    fk_name = "customer"
    extra = 0
    can_delete = False
    verbose_name_plural = "Past Purchases"
    fields = ("product", "price", "purchased_at")
    readonly_fields = fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("-purchased_at")

class ActiveBidInline(admin.TabularInline):
    model = PopUpBid
    fk_name = "customer"          # FK on PopUpBid → PopUpCustomer
    extra = 0
    can_delete = False
    verbose_name_plural = "Open bids"
    fields = ("product", "amount", "timestamp", "is_winning_bid")
    readonly_fields = fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)


class PastBidInline(admin.TabularInline):
    model = PopUpBid
    fk_name = "customer"
    extra = 0
    can_delete = False
    verbose_name_plural = "Past bids"
    fields = ("product", "amount", "timestamp", "is_winning_bid")
    readonly_fields = fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=False)


@admin.register(PopUpCustomer)
class PopUpCustomerAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "middle_name", "last_name", "is_active")
    readonly_fields = ("email",) 

    inlines = [ActiveBidInline, PastBidInline, PurchaseInLine]

    
    