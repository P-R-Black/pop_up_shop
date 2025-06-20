from django.urls import path
from . import views
from .views import (ProductBuyView, ShippingAddressView, BillingAddressView, CreatePaymentIntentView,ProcessVenmoPaymentView)

app_name ='payment'

urlpatterns = [
    path('', ProductBuyView.as_view(), name='payment_home'),
    path('shipping-address/', ShippingAddressView.as_view(), name='shipping_address'),
    path('billing-address/', BillingAddressView.as_view(), name='billing_address'),
    path('placedorder/', views.placed_order, name='placed_order'),
    # path('error/', views.Error.as_view(), name='error'),
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create_payment'),
    path('braintree/get-client-token/', views.generate_client_token, name='get_client_token'),
    path('webhook/', views.stripe_webhook),
    path('process-venmo/', ProcessVenmoPaymentView.as_view(), name='process_venmo'),
    # NowPayment
    path('create-nowpayments/', views.create_nowpayments_payment, name='create_nowpayments_payment'),
    path('finalize-nowpayments/', views.finalize_nowpayments_payment, name='finalize_nowpayments_payment'),
    path('check-nowpayments-status/<str:payment_id>/', views.check_nowpayments_status, name='check_nowpayments_status'),
    path('nowpayments-webhook/', views.nowpayments_webhook, name='nowpayments_webhook'),
    path('test-nowpayments/', views.test_nowpayments_connection, name='test_nowpayments_connection'),
]