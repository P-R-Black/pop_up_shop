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


# def product_bid(request, product_id):
def product_bid(request, product_id=22):
    print('product_bid called!')
    return render(request, 'auction/prodcut_bid.html')
    # if request.method == "POST":
    #     # bid_amount = request.POST.get('bid_amount')
    #     bid_amount: 333
        
    #     product = "a product" #= get_object_or_404(Product, id=product_id)

    #     try:
    #         bid_amount = float(bid_amount)
    #         if bid_amount < product.minimum_bid:
    #             return JsonResponse({'success': False, 'message': 'Bid amount is too low.'})

    #         # Save the bid
    #         # Bid.objects.create(user=request.user, product=product, amount=bid_amount)
    #         return JsonResponse({'success': True, 'message': 'Your bid has been submitted.'})
    #     except ValueError:
    #         return JsonResponse({'success': False, 'message': 'Invalid bid amount.'})
    
    # return JsonResponse({'success': False, 'message': 'Invalid request'})