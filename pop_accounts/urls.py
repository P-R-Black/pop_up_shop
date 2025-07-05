from django.urls import path
from . import views
from .views import (EmailCheckView, RegisterView, Login2FAView, VerifyEmailView, 
                    UserLoginView, UserLogOutView, UserDashboardView, Verify2FACodeView,
                    UserInterestedInView, MarkProductInterestedView, MarkProductOnNoticeView,
                    UserOnNoticeView, OpenBidsView, AdminInventoryView, EnRouteView)

app_name = 'pop_accounts'
urlpatterns = [

    #Auth register / login class based views
    path('auth/check-email/', EmailCheckView.as_view(), name='check_email'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('verify/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/user-login/', Login2FAView.as_view(), name='user_login'),

    
    # Auth register / login
    path('auth/verify-code/', Verify2FACodeView.as_view(), name='verify_2fa'),
    # path('auth/verify-code/', views.verify_2fa_code, name='verify_2fa'),
    path('auth/send-reset-link/', views.send_password_reset_link, name='send_reset_link'),
    path('resend-code/', views.resend_2fa_code, name='resend_2fa_code'),
    path('password-reset/<uidb64>/<token>/', views.user_password_reset_confirm, name='password_reset_confirm'),


    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/',UserLogOutView.as_view(), name='logout'),
   
    # path('password-reset', views.user_password_reset, name='password_reset'),
    
    # path('dashboard', views.dashboard, name='dashboard'),
    path('dashboard/', UserDashboardView.as_view(), name='dashboard'),
    # path('place-bid/', DashboardPlaceBidView.as_view(), name='place_bid'),

    # User Info
    path('personal-information/', views.personal_info, name='personal_info'),
    path('get-address/<uuid:address_id>/', views.get_address, name='get_address'),
    path('delete-address/<uuid:address_id>/', views.delete_address, name='delete_address'),
    path('set-default-address/<uuid:address_id>/', views.set_default_address, name='set_default_address'),

    # path('interested-in/', views.interested_in, name='interested_in'),
    path('interested-in/', UserInterestedInView.as_view(), name='interested_in'),
    path('mark-interested/', MarkProductInterestedView.as_view(), name='mark_interested'),
    path('on-notice/', UserOnNoticeView.as_view(), name='on_notice'),
    path('mark-on-notice/', MarkProductOnNoticeView.as_view(), name='mark_on_notice'),
    # path('open-bids/', views.open_bids, name='open_bids'),
    path('open-bids/', OpenBidsView.as_view(), name="open_bids"),
    path('bids-history/', views.past_bids, name='past_bids'),
    path('purchase-history/', views.past_purchases, name='past_purchases'),

    # admin dashboard
    path('dashboard-admin/',views.dashboard_admin, name='dashboard_admin'),
    path('inventory-admin/', AdminInventoryView.as_view(), name='inventory_admin'),
    path('inventory-admin/<slug:slug>/', AdminInventoryView.as_view(), name='inventory_admin'),
    path('sales-admin/', views.sales, name='sales_admin'),
    path('most-on-notice-admin/', views.most_on_notice, name='most_on_notice'),
    path('most-interested-admin/', views.most_interested, name='most_interested'),
    path('total-open-bids-admin/', views.total_open_bids, name='total_open_bids'),
    path('total-accounts-admin/', views.total_accounts, name='total_accounts'),
    path('account-sizes-admin/', views.account_sizes, name='account_sizes'),
    path('update-shipping-admin/', views.update_shipping, name='update_shipping'),
    path('shipments-admin/', views.view_shipments, name='shipments'),
    path('dashboard-en-route/', EnRouteView.as_view(), name='enroute'),
    path('dashboard-en-route/<slug:slug>/', EnRouteView.as_view(), name='enroute')

]