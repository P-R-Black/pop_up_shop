from django.urls import path
from . import views


app_name ='orders'

urlpatterns = [
    path('generate-shipping-label/', views.generate_shipping_label, name='generate_shipping_label'),
    
]