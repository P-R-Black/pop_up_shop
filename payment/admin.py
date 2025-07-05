from django.contrib import admin
from payment.models import PopUpPayment

# Register your models here.
class PopUpPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'amount', 'is_suspicious_flag',)

    def is_suspicious_flag(self, obj):
        return obj.is_suspicious()
    is_suspicious_flag.boolean = True