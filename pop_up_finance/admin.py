from django.contrib import admin
from pop_up_finance.models import PopUpFinance

# Register your models here.

@admin.register(PopUpFinance)
class PopUpFinanceAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'final_price', 'fees', 'sold_at', )



"""
order
product
reserve_price
final_price
fees
refunded_amount
profit
payment_method
is_disputed
is_refunded
sold_at
updated_at
"""