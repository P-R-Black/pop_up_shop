from django.urls import path
from . import views


app_name = 'pop_up_emails'
urlpatterns = [
    path('auction-winner/', views.preview_email, name='auction_winner'),

]