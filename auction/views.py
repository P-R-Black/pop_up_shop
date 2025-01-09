from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
# from .models import Product, Bid


# Create your views here.
def all_auction_view(request):
    # need items currently in auction
    # need items picture, name, highest bid, product id
    return render(request, 'auction/auction.html')


def product_auction_view(request):
    # need image of product in auction
    # need name of product:
    # need product size
    # need product condition
    # need product buy now price
    # need days left in auction
    return render(request, 'auction/product_auction.html')

def product_buy_view(request):
    print('page requested')
    # need payment option attached to account  | # shopping cart length
    # shopping cart amount  |  # state tax info  | # ship to info  |  # product pic 
    # product title  |  # product size  |  # product buy now price  |  # quantity
    # estimated delivery info  |  # delivery address
    return render(request, 'auction/product_buy.html')


def products(request):
    return render(request, ('auction/products.html'))


def coming_soon(request):
    return render(request, ('auction/coming_soon.html'))

def future_releases(request):
    return render(request, ('auction/future_releases.html'))

def product_details(request):
    return render(request, ('auction/product_details.html'))