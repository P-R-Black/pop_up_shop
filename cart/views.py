from django.shortcuts import render
from .cart import Cart
from django.shortcuts import get_object_or_404
from auction.models import PopUpProduct
from django.http import JsonResponse


# Create your views here.
def cart_summary(request):
    return render(request, 'auction/cart/summary.html')

def cart_add(request):
    cart = Cart(request)
    if request.POST.get('action') == "post":
        print('post hit')
        product_id = int(request.POST.get('productid'))
        product_qty = int(request.POST.get('prodcutqty'))
        product = get_object_or_404(PopUpProduct, id=product_id)
        cart.add(product=product, qty=product_qty)
        response = JsonResponse({'test': 'data'})
        return response
