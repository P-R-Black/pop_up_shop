from django.contrib import admin
from .models import PopUpCustomerOrder, PopUpOrderItem


# Register your models here.
admin.site.register(PopUpCustomerOrder)
class PopUpCustomerOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'email', 'total_paid', 'billing_status']

admin.site.register(PopUpOrderItem)
class PopUpOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'product_title', 'secondary_product_title', 'quantity']