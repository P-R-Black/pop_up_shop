from django.shortcuts import render
from pop_up_cart.cart import Cart
from django.shortcuts import get_object_or_404
from pop_up_auction.models import PopUpProduct
from django.http import JsonResponse
from django.views.decorators.http import require_POST


# Create your views here.
def cart_summary(request):
    cart = Cart(request)
    print('cart is in cart_summary', cart)
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
        product = get_object_or_404(PopUpProduct, id=product_id)

        # Check for 'buy_now' status before deleting
        item_data = None
        for pid, item in cart.get_items():
            if int(pid) == product_id:
                item_data = item
                break

        is_buy_now = item_data.get('buy_now', False) if item_data else False

        # Delete from cart
        cart.delete(product_id)

        # If not a buy_now item, reset product availability
        if not is_buy_now:
            product.inventory_status = 'in_inventory'
            product.reserved_until = None
            product.save()

        response = JsonResponse({
            'qty': len(cart),
            'subtotal': float(cart.get_total_price())
        })
        return response
    
    

def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('productid'))
        product_qty = int(request.POST.get('productqty'))
        cart.update(product=product_id, qty=product_qty)

        cart_qty = cart.__len__()
        cart_total = cart.get_total_price()
        response = JsonResponse({'qty': cart_qty, 'subtotal': cart_total})
        return response