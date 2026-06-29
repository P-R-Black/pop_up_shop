from django.urls import path
from . import views
from .views import (ProcurementCartDeleteView)

app_name = 'pop_up_cart'

urlpatterns = [
    path('', views.cart_summary, name='cart_summary'),
    path('add/', views.cart_add, name='cart_add'),
    path('delete/', views.cart_delete, name='cart_delete'),
    path('update/', views.cart_update, name='cart_update'),
    path('procurement/delete/', ProcurementCartDeleteView.as_view(), name='procurement_cart_delete'),
]
