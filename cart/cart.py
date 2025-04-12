from auction.models import PopUpProduct
from decimal import Decimal
from django.conf import settings

class Cart:
    """
    A base cart class
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if settings.CART_SESSION_ID not in request.session:
            cart = self.session[settings.CART_SESSION_ID] = {}
        
        self.cart = cart
    

    def add(self, product, qty):
        """
        Add and updating the users cart data
        """
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['qty'] = qty
        else:
            self.cart[product_id] = {'price': float(product.starting_price), 'qty': int(qty)}
        
        self.save()
    

    def __iter__(self):
        """
        Collect the product_id in the session data
        """
        product_id = self.cart.keys()
        products = PopUpProduct.objects.filter(id__in=product_id)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['qty']
            yield item
        
    def __len__(self):
        """
        Get cart dta and count the quantity of the items in the basket
        """
        return sum(item['qty'] for item in self.cart.values())

    def get_subtotal_price(self):
        return sum(Decimal(item['price']) * item['qty'] for item in self.cart.values())


    def get_total_price(self):
        subtotal = sum(Decimal(item['price']) * item['qty'] for item in self.cart.values())
        if subtotal == 0:
            shipping = Decimal(0.00)
        else:
            shipping = Decimal(11.50)
        
        total = subtotal + Decimal(shipping)
        return total

    def delete(self, product):
        """
        Delete item from session data
        """
        product_id = str(product)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def update(self, product, qty):
        """
        Update values in session data
        """
        product_id = str(product)
        qty = qty
        if product_id in self.cart:
            self.cart[product_id]['qty'] = qty
        self.save()
    
    def save(self):
        self.session.modified = True
    
    def clear(self):
        """
        Remove cart from session
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()