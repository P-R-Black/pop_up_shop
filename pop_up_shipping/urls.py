from django.urls import path
from . import views


app_name ='pop_up_shipping'

urlpatterns = [
    path('generate-shipping-label/<uuid:order_id>/', views.generate_shipping_label, name='generate_shipping_label'),
    
]