from django.contrib import admin
from payment.models import PopUpPayment

# Register your models here.

@admin.register(PopUpPayment)
class PopUpPaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'status', 'payment_reference', 'payment_method', 'suspicious_flagged', 'notified_ready_to_ship', 'created_at', )

    def is_suspicious_flag(self, obj):
        return obj.is_suspicious()
    is_suspicious_flag.boolean = True
