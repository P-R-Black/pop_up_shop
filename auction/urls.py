from django.urls import path
from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.all_auction_view, name="auction"),
    path('open', views.product_auction_view, name='product_auction'), # map to product id
    path('product-buy', views.product_buy_view, name='product_buy'), # map to product id
    path('products', views.products, name='products'),
    path('coming-soon', views.coming_soon, name='coming_soon'),
    path('future-releases', views.future_releases, name='future_releases'),
    path('product-details', views.product_details, name='product_details'),
    # footer_links
    path('about', views.about_us, name='about'),
    path('how-it-works', views.how_it_works, name='how-it-works'),
    path('verification', views.verification, name='verification'),
    path('contact', views.contact_us, name='contact'),
    path('help-center', views.help_center, name='help-center'),
    path('terms', views.terms_and_conditions, name='terms'),
    path('privacy', views.privacy_policy, name='privacy'),
    # help center pages
    path('buying-help', views.buying_help, name='buying-help'),
    path('selling-help', views.selling_help, name='selling-help'),
    path('account-help', views.account_help, name='account-help'),
    path('shipping-help', views.shipping_help, name='shipping-help'),
    path('payment-help', views.payment_help, name='payment-help'),
    path('fees-help', views.fees_help, name='fees-help'),


]