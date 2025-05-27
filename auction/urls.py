from django.urls import path
from . import views
from .views import PlaceBidView, ProductBuyView

app_name = 'auction'
urlpatterns = [
    path('', views.all_auction_view, name="auction"),
    path('place-bid/', PlaceBidView.as_view(), name='place_bid'),
    path('open/', views.product_auction_view, name='product_auction'), # map to product id
    path('open/<slug:slug>/', views.product_auction_view, name='product_auction'), # map to product id
    # path('product-buy/', views.product_buy_view, name='product_buy'), # map to product id
    path('product-buy/', ProductBuyView.as_view(), name='product_buy'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.products, name='products'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('coming-soon/<slug:slug>/', views.coming_soon, name='coming_soon'),
    path('future-releases/', views.future_releases, name='future_releases'),
    path('future-releases/<slug:slug>/', views.future_releases, name='future_releases'),
    path('<slug:slug>', views.product_detail, name='product_detail'),
   
]