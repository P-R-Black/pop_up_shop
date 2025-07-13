from django.urls import path
from . import views
from .views import (PlaceBidView, AllAuctionView, ProductAuctionView, ProductsView, 
                    ComingSoonView, FutureReleases, ProductDetailView)

app_name = 'auction'
urlpatterns = [
    path('', AllAuctionView.as_view(), name="auction"),
    path('place-bid/', PlaceBidView.as_view(), name='place_bid'),
    path('open/', ProductAuctionView.as_view(), name='product_auction'),
    path('open/<slug:slug>/', ProductAuctionView.as_view(), name='product_auction'),
    # path('product-buy/', ProductBuyView.as_view(), name='product_buy'),
    path('products/', ProductsView.as_view(), name='products'),
    path('products/<slug:slug>/', ProductsView.as_view(), name='products'),
    path('coming-soon/', ComingSoonView.as_view(), name='coming_soon'),
    path('coming-soon/<slug:slug>/', ComingSoonView.as_view(), name='coming_soon'),
    path('future-releases/', FutureReleases.as_view(), name='future_releases'),
    path('future-releases/<slug:slug>/', FutureReleases.as_view(), name='future_releases'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('past-product-details/<int:item_id>/', views.past_product_detail, name='past_product_details'),
    path('past-bids-product-detail/<int:product_id>/', views.past_bid_product_detail_by_product, name='past_bids_product_detail')
   
]