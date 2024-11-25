from django.shortcuts import render

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
