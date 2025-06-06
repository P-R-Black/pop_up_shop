from django.urls import path
from . import views
from .views import (ProductBuyView, ShippingAddressView, BillingAddressView)

app_name ='payment'

urlpatterns = [
    path('', ProductBuyView.as_view(), name='payment_home'),
    path('shipping-address/', ShippingAddressView.as_view(), name='shipping_address'),
    path('billing-address/', BillingAddressView.as_view(), name='billing_address'),
    path('placedorder/', views.placed_order, name='placed_order'),
    # path('error/', views.Error.as_view(), name='error'),
    path('webhook/', views.stripe_webhook)
    
]