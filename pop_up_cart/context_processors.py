from pop_up_cart.cart import Cart

def cart(request):
    return {'cart': Cart(request)}

def procurement_cart(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        from pop_up_cart.models import ProcurementCartItem
        procurement_cart_length = ProcurementCartItem.objects.filter(user=user).count()
    else:
        procurement_cart_length = 0

    return {'procurement_cart_length': procurement_cart_length}