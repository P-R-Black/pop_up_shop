from django.urls import path
from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.all_auction_view, name="auction"),
    path('/open', views.product_auction_view, name='product_auction'), # map to product id

    

]