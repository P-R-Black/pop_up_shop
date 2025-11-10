from django.urls import path
from . import views
from .views import (EmailCheckView, RegisterView, Login2FAView, VerifyEmailView, PastPurchaseView,
                    UserLogOutView, UserDashboardView, Verify2FACodeView, AccountDeletedView,
                    UserInterestedInView, MarkProductInterestedView, MarkProductOnNoticeView, 
                    UserOnNoticeView, OpenBidsView, AdminInventoryView, EnRouteView, AddProductsView,
                    UpdateProductView, CompleteProfileView, PersonalInfoView, GetAddressView, PastBidView,
                    DeleteAddressView, SetDefaultAddressView, DeleteAccountView, UserPasswordResetConfirmView,
                    ShippingTrackingView, UserOrderPager, AdminDashboardView, SalesView, MostOnNotice, 
                    MostInterested, TotalOpenBidsView, TotalAccountsView, AccountSizesView, 
                    PendingOkayToShipView, PendingOrderShippingDetailView, UpdateShippingView, 
                    GetOrderShippingDetail, UpdateShippingPostView, ViewShipmentsView, AddProductsGetView)

app_name = 'pop_accounts'
urlpatterns = [

    # Auth register / login class based views
    path('auth/check-email/', EmailCheckView.as_view(), name='check_email'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('verify/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/user-login/', Login2FAView.as_view(), name='user_login'),

    # Social Auth / Social Login
    path('auth/complete-profile/', CompleteProfileView.as_view(), name='complete_profile'),
    path('social-login-complete/', views.social_login_complete, name='social_login_complete'),
    path('get-user-info/', views.get_user_info, name="get_user_info"),

    
    # Auth register / login
    path('auth/verify-code/', Verify2FACodeView.as_view(), name='verify_2fa'),
    path('auth/send-reset-link/', views.send_password_reset_link, name='send_reset_link'),
    path('resend-code/', views.resend_2fa_code, name='resend_2fa_code'),
    path('password-reset/<uidb64>/<token>/', UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('logout/',UserLogOutView.as_view(), name='logout'),
       
    # path('place-bid/', DashboardPlaceBidView.as_view(), name='place_bid'),

    # User Info
    path('dashboard/', UserDashboardView.as_view(), name='dashboard'),
    path('personal-information/', views.PersonalInfoView.as_view(), name='personal_info'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('account-deleted/', AccountDeletedView.as_view(), name='account_deleted'),    
    path('get-address/<uuid:address_id>/', GetAddressView.as_view(), name='get_address'),
    path('delete-address/<uuid:address_id>/', DeleteAddressView.as_view(), name='delete_address'),
    path('set-default-address/<uuid:address_id>/', SetDefaultAddressView.as_view(), name='set_default_address'),
    path('interested-in/', UserInterestedInView.as_view(), name='interested_in'),
    path('mark-interested/', MarkProductInterestedView.as_view(), name='mark_interested'),
    path('on-notice/', UserOnNoticeView.as_view(), name='on_notice'),
    path('mark-on-notice/', MarkProductOnNoticeView.as_view(), name='mark_on_notice'),
    path('open-bids/', OpenBidsView.as_view(), name="open_bids"),
    path('bids-history/', PastBidView.as_view(), name='past_bids'),
    path('purchase-history/', PastPurchaseView.as_view(), name='past_purchases'),
    path('shipping-tracking/', ShippingTrackingView.as_view(), name='shipping_tracking'),
    path('customer-order/<uuid:order_id>/', UserOrderPager.as_view(), name='customer_order'),

    # admin dashboard
    path('dashboard-admin/', AdminDashboardView.as_view(), name='dashboard_admin'),
    path('inventory-admin/', AdminInventoryView.as_view(), name='inventory_admin'),
    path('inventory-admin/<slug:slug>/', AdminInventoryView.as_view(), name='inventory_admin'),
    path('sales-admin/', SalesView.as_view(), name='sales_admin'),
    path('most-on-notice-admin/', MostOnNotice.as_view(), name='most_on_notice'),
    path('most-interested-admin/', MostInterested.as_view(), name='most_interested'),
    path('total-open-bids-admin/', TotalOpenBidsView.as_view(), name='total_open_bids'),
    path('total-accounts-admin/', TotalAccountsView.as_view(), name='total_accounts'),
    path('account-sizes-admin/', AccountSizesView.as_view(), name='account_sizes'),
    path('pending-okay-to-ship/', PendingOkayToShipView.as_view(), name='pending_okay_to_ship'),
    path('get-pending-order-shipping-detail/<uuid:order_no>/', PendingOrderShippingDetailView.as_view(), name='get_order_details'),

    path('update-shipping-admin/', UpdateShippingView.as_view(), name='update_shipping'),
    path('update-shipping-admin/<int:shipment_id>/', UpdateShippingPostView.as_view(), name='update_shipping_post'),
    path('get-shipping-detail/<int:shipment_id>/', GetOrderShippingDetail.as_view(), name='get_shipping_detail'),

    path('shipments-admin/', ViewShipmentsView.as_view(), name='shipments'),
    path('dashboard-en-route/', EnRouteView.as_view(), name='enroute'),
    path('dashboard-en-route/<slug:slug>/', EnRouteView.as_view(), name='enroute'),

    # admin dashboard | Adding products
    path('add-products-admin/', AddProductsView.as_view(), name='add_products'),
    path('add-products-admin/<int:product_type_id>/', AddProductsGetView.as_view(), name='add_products_get'),

    # admin dashboard | Updating products
    path('update-product-admin/', UpdateProductView.as_view(), name='update_product'),
    path('update-product-admin/<int:product_id>/', UpdateProductView.as_view(), name='update_product_detail'),
    # path('get-product-detail/<int:product_id>/<int:product_type_id>/', ProductDetailView.as_view(), name='get_product_detail'),
    # path('update-product-post/<int:product_id>/', UpdateProductPostView.as_view(), name='update_product_post'),



    # path('update-product-admin/<int:product_id>/', views.update_product_post, name='update_product_post'),
    # path('get-product-detail/<int:product_id>/', views.get_order_product_detail, name='get_product_detail'),

    

]