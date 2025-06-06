from django.shortcuts import render
from django.http.response import JsonResponse
from cart.cart import Cart
from .models import PopUpCustomerOrder, PopUpOrderItem

# Create your views here.
def add(request):
    print('orders add called!')
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        user_id = request.user.id
        order_key = request.POST.get('order_key')
        cart_total = cart.get_total_price()

        print('cart', cart)
        for c in cart:
            print('c', c)
        print('user_iduser_id', user_id)
        print('order_key', order_key)
        print('cart_total', cart_total)

        # Check if order exists
        if PopUpCustomerOrder.objects.filter(order_key=order_key).exists():
            pass
        else:
            order = PopUpCustomerOrder.objects.create(
                user_id=user_id, full_name='name', 
                address1='add1', 
                address2='add2', 
                total_paid=cart_total, 
                order_key=order_key)
            order_id = order.pk
            for item in cart:
                PopUpOrderItem.objects.create(order_id=order_id, product=item['product'], price=item['price'], quantity=item['qty'])
            response = JsonResponse({'success': 'Return Something'})
            return response

def payment_confirmation(data):
    PopUpCustomerOrder.objects.filter(order_key=data).update(billing_status=True)


def user_orders(request):
    user_id = request.user.id
    orders = PopUpCustomerOrder.objects.filter(user_id=user_id).filter(billing_status=True)
    return orders
