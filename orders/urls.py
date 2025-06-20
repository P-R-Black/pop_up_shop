from django.urls import path
from . import views
from .views import (CreateOrderAfterPaymentView)

app_name ='orders'

urlpatterns = [
    path('create-after-payment/', CreateOrderAfterPaymentView.as_view(), name='create_after_payment'),
    
]