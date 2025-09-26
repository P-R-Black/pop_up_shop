from django.urls import path
from . import views
from django.contrib import sitemaps
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap, ProductSitemap

app_name = 'pop_up_home'

sitemaps_dict = {
    "static": StaticViewSitemap,
    "products": ProductSitemap
}
urlpatterns = [
    path('', views.home_page, name='home'),
     # footer_links
    path('about/', views.about_us, name='about'),
    path('how-it-works/', views.how_it_works, name='how-it-works'),
    path('verification/', views.verification, name='verification'),
    path('contact/', views.contact_us, name='contact'),
    path('help-center/', views.help_center, name='help-center'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('privacy-choices/', views.privacy_choice, name='privacy_choices'),
    path('site-map/', views.site_map, name='site-map'),
    path('sitemap.xml/', sitemap, {'sitemaps': sitemaps_dict}, name="django.contrib.site.views.sitemap"),
    # help center pages
    path('buying-help/', views.buying_help, name='buying-help'),
    path('selling-help/', views.selling_help, name='selling-help'),
    path('account-help/', views.account_help, name='account-help'),
    path('shipping-help/', views.shipping_help, name='shipping-help'),
    path('payment-help/', views.payment_help, name='payment-help'),
    path('fees-help/', views.fees_help, name='fees-help'),
    path('friend-invite-success/', views.friend_invite_success, name='invite_success'),
    path('friend-invite-fail/', views.friend_invite_failure, name='invite_failed')

]


