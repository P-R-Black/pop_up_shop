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
    path('terms', views.terms_and_conditions, name='terms'),

]