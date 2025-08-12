from django.urls import path
from . import views

app_name = 'pop_up_coupon'
urlpatterns = [
    path('apply/', views.coupon_apply, name='apply')
]