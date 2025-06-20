from django.contrib import admin
from .models import PopUpCustomerOrder, PopUpOrderItem


# Register your models here.
admin.site.register(PopUpCustomerOrder)


admin.site.register(PopUpOrderItem)
class PopUpOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'product_title', 'secondary_product_title', 'quantity']

    




