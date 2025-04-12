from django.urls import path
from . import views

app_name ='payment'

urlpatterns = [
    path('', views.cart_view, name='cart'),
    path('placedorder/', views.placed_order, name='placed_order'),
    # path('error/', views.Error.as_view(), name='error'),
    path('webhook/', views.stripe_webhook)
    
]