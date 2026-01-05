from django.shortcuts import render
from pop_up_cart.cart import Cart
from django.shortcuts import get_object_or_404
from pop_up_auction.models import PopUpProduct
from django.http import JsonResponse
from django.views.decorators.http import require_POST


# Create your views here.
def cart_summary(request):
    cart = Cart(request)
    return render(request, 'cart/summary.html', {'cart': cart})


@require_POST
def cart_add(request):
    cart = Cart(request)

    if request.POST.get('action') == "POST":
        product_id = int(request.POST.get('productid'))

        product_qty = int(request.POST.get('productqty'))

        product = get_object_or_404(PopUpProduct, id=product_id)
        cart.add(product=product, qty=product_qty, auction_locked=False, buy_now=True)

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
    
    
@require_POST
def cart_update(request):
    cart = Cart(request)
    print('cart_updated called')

    if request.POST.get('action') == 'post':


        product_id = int(request.POST.get('productid'))
        print('product_id', product_id)

        product_qty = int(request.POST.get('productqty'))
        print('product_qty', product_qty)

         # Validate quantity
        if product_qty < 0:
            return JsonResponse({'error': 'Quantity cannot be negative'}, status=400)
        
        if product_qty == 0:
            # Optionally delete item if quantity is 0
            cart.delete(product_id)
        else:
            cart.update(product=product_id, qty=product_qty)

       #  cart.update(product=product_id, qty=product_qty)

        cart_qty = cart.__len__()
        print('cart_qty', cart_qty)

        cart_total = cart.get_total_price()
        print('cart_total', cart_total)

        return JsonResponse({'qty': cart_qty, 'subtotal': cart_total})
    
    return JsonResponse({'error': 'Invalid Action'}, status=400)