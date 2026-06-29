from django.shortcuts import render
from pop_up_cart.cart import Cart
from django.shortcuts import get_object_or_404
from pop_up_auction.models import PopUpProduct
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from pop_up_cart.models import ProcurementCartItem
from decimal import Decimal



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




class ProcurementCartDeleteView(LoginRequiredMixin, View):

    def post(self, request):
        item_id = request.POST.get('procurement_item_id')

        if not item_id:
            return JsonResponse({'success': False, 'error': 'No item ID provided.'}, status=400)

        try:
            item = ProcurementCartItem.objects.get(id=item_id, user=request.user)
        except ProcurementCartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found.'}, status=404)

        # Also mark the ProcurementServiceRequest as abandoned
        # so the bot won't run for a cancelled/unpaid request
        psr = item.procurement_service_request
        if psr.status == 'pending':
            psr.status = 'abandoned'
            psr.save(update_fields=['status'])

        item.delete()

        # Recalculate procurement subtotal for this user
        remaining = ProcurementCartItem.objects.filter(user=request.user)
        procurement_subtotal = sum(i.fee_amount for i in remaining)

        # Return updated totals so JS can refresh the UI without a page reload.
        # Grand total recalculation is simplified here — the full calculation
        # lives in ProductBuyView; JS can use this to patch the displayed value.
        return JsonResponse({
            'success': True,
            'procurement_subtotal': float(procurement_subtotal),
            # grand_total is omitted here intentionally — a full reload gives
            # the accurate number including tax/shipping. JS snippet above handles it.
        })