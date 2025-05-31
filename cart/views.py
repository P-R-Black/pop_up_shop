from django.shortcuts import render
from .cart import Cart
from django.shortcuts import get_object_or_404
from auction.models import PopUpProduct
from django.http import JsonResponse
from django.views.decorators.http import require_POST


# Create your views here.
def cart_summary(request):
    cart = Cart(request)
    return render(request, 'auction/cart/summary.html', {'cart': cart})


@require_POST
def cart_add(request):
    cart = Cart(request)

    if request.POST.get('action') == "POST":
        product_id = int(request.POST.get('productid'))
        product_qty = int(request.POST.get('productqty'))
        product = get_object_or_404(PopUpProduct, id=product_id)
        cart.add(product=product, qty=product_qty)

        cart_qty = cart.__len__()
        response = JsonResponse({'qty': cart_qty})

        return response


@require_POST
def cart_delete(request):
    
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('productId'))
        cart.delete(product=product_id)
        cart_qty = cart.__len__()
        cart_total = cart.get_total_price()
        response = JsonResponse({'qty': cart_qty, 'subtotal': cart_total})
        return response
    
    

def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('productid'))
        product_qty = int(request.POST.get('productqty'))
        cart.update(product=product_id, qty=product_qty)

        cartqty = cart.__len__()
        carttotal = cart.get_total_price()
        response = JsonResponse({'qty': cartqty, 'subtotal': carttotal})
        return response