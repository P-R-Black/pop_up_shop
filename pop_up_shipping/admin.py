from django.contrib import admin
from pop_up_shipping.models import PopUpShipment

# Register your models here.

@admin.register(PopUpShipment)
class PopUpShipmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'carrier', 'tracking_number', 'shipped_at', 'estimated_delivery', 'delivered_at', 'status', )

