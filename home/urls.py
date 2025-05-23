from django.urls import path
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.home_page, name='home'),
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