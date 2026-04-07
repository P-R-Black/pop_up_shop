from django.urls import path
from . import views
from .views import (InviteFriendView)

app_name = 'pop_up_emails'
urlpatterns = [
    path('invite/',InviteFriendView.as_view(), name='invite'),
    path('auction-winner/', views.preview_email, name='auction_winner'),
    path('email-confirmation/', views.preview_email_confirmation, name='email_confirms'),
    path('two-factor-auth/', views.preview_two_factor_auth, name='two_factor_auth'),
    path('preview-order-confirmation/', views.preview_order_confirmation, name='preview_order_confirmation'),
    path('preview-shipping-details/', views.preview_send_customer_shipping_details, name='preview_shipping_details'),
    path('preview-invite-friend/', views.preview_invite_friend_email, name='invite_friend'),
    path('preview-interested-in-update/', views.preview_send_interested_in_and_coming_soon_product_update_to_users_email, name='interested_in_update'),
    path('preview-twenty-four-hour-notice/', views.preview_twenty_four_hour_reminder_email, name='preview-twenty-four-hour-notice'),
    path('preview-one-hour-notice/', views.preview_one_hour_reminder_email, name='preview-one-hour-notice'),
    path('preview-two-factor-auth-email/', views.preview_two_factor_auth_email, name='preview_two_factor_auth_email'),
    path('preview_okay_to_ship_admin_alert/', views.preview_okay_to_ship_admin_alert, name='preview_okay_to_ship_admin_alert')

]