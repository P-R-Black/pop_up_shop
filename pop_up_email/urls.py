from django.urls import path
from . import views


app_name = 'pop_up_emails'
urlpatterns = [
    path('auction-winner/', views.preview_email, name='auction_winner'),
    path('email-confirmation/', views.preview_email_confirmation, name='email_confirms'),
    path('two-factor-auth/', views.preview_two_factor_auth, name='two_factor_auth'),
    path('preview-order-confirmation/', views.preview_order_confirmation, name='preview_order_confirmation'),
    path('preview-shipping-details/', views.preview_send_customer_shipping_details, name='preview_shipping_details'),
    path('preview-invite-friend/', views.preview_invite_friend_email, name='invite_friend')

]