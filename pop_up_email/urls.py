from django.urls import path
from . import views


app_name = 'pop_up_emails'
urlpatterns = [
    path('auction-winner/', views.preview_email, name='auction_winner'),
    path('email-confirmation/', views.preview_email_confirmation, name='email_confirms'),
    path('two-factor-auth/', views.preview_two_factor_auth, name='two_factor_auth')

]