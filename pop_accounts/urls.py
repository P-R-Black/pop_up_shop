from django.urls import path
from . import views

app_name = 'pop_accounts'
urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('personal-information', views.personal_info, name='personal_info'),
    path('interested-in', views.interested_in, name='interested_in'),
    path('on-notice', views.on_notice, name='on_notice'),
    path('open-bids', views.open_bids, name='open_bids'),
    path('bids-history', views.past_bids, name='past_bids'),
    path('purchase-history', views.past_purchases, name='past_purchases'),
    # admin dashboard
    path('dashboard-admin',views.dashboard_admin, name='dashboard_admin'),
    path('inventory-admin',views.inventory, name='inventory_admin'),
    path('sales-admin', views.sales, name='sales_admin'),

]