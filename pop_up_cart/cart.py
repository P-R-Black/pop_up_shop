from pop_up_auction.models import PopUpProduct
from pop_up_cart.models import PopUpCartItem
from django.contrib.auth.models import AnonymousUser
from decimal import Decimal
from django.conf import settings
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta


class Cart:
    """
    A base cart class
    """

    def __init__(self, request):

        self.request = request
        self._user = getattr(request, 'user', None) or AnonymousUser()
        self.session = request.session
        self.session_cart = self.session.get('cart', {})
       

        # self.user = request.user # <= negativly impacting sign in 
        # self.is_authenticated = request.user.is_authenticated


        # self.session_cart = self.session.get(settings.CART_SESSION_ID, {})

        # if self.is_authenticated:
        #     self.user_cart = PopUpCartItem.objects.filter(user=self.user)
        # else:
        #     self.session_cart = self.session.get(settings.CART_SESSION_ID, {})

        
        # if settings.CART_SESSION_ID not in self.session:
        #     self.session[settings.CART_SESSION_ID] = {}

        if self._user and self._user.is_authenticated:
            self.user_cart = PopUpCartItem.objects.filter(user=self._user)
        else:
            self.user_cart = []
        
    
    @property
    def user(self):
        return getattr(self.request.user, 'user', None)

    @property
    def is_authenticated(self):
        return self.user and self.user.is_authenticated

    def add(self, product, qty, auction_locked=False, buy_now=False):
        """
        Add or update the user's cart with a product.
        Includes optional buy_now flag for exclusive purchase logic.
        """
        if buy_now:
            product.inventory_status = 'reserved'
            product.reserved_util = timezone.now() + timedelta(minutes=10)
            product.save()


        if self._user.is_authenticated:
            # persistent cart
            cart_item, created = PopUpCartItem.objects.get_or_create(
                user=self._user,
                product=product,
                defaults={'quantity': qty, 'auction_locked': auction_locked, 'buy_now': buy_now}
            )
            if not created:
                cart_item.quantity += qty
                cart_item.save()
        else:
            # session cart
            product_id = str(product.id)
            item_data = {
                'price': float(product.display_price()),
                'qty': int(qty),
                'auction_locked': auction_locked,
                'buy_now': buy_now
            }
            if product_id in self.session:
                self.session_cart[product_id].update(item_data)
            else:
                self.session_cart[product_id] = item_data
            self.save()
        
    
    def get_product_ids(self):
        """
        Return product IDs in the cart, whether session-based or DB-based.
        """
        if self._user and self._user.is_authenticated:
            return list(
                PopUpCartItem.objects.filter(user=self._user).values_list('product_id', flat=True)
            )
        else:
            return [int(pid) for pid in self.session.get(settings.CART_SESSION_ID, {}).keys()]
            
            
    def get_items(self):
        """
        Return cart items (product_id, data dict) depending on user auth status.
        """
        if self._user and self._user.is_authenticated:
            cart_items = PopUpCartItem.objects.filter(user=self._user).select_related('product')
            for item in cart_items:
                yield str(item.product.id), {
                    "qty": item.quantity,
                    "price": float(item.product.display_price()),  # or item.price if stored
                }
        else:
            return self.session.get(settings.CART_SESSION_ID, {}).items()
    

    def __iter__(self):
        """
        Collect the product_id in the session data
        """
        if self._user.is_authenticated:
            cart_items = PopUpCartItem.objects.filter(user=self._user).select_related('product')
            for item in cart_items:
                product = item.product
                price = product.display_price()
                yield {
                    'product': product,
                    'qty': item.quantity,
                    'price': price,
                    'total_price': item.quantity * price
                }
        else:
            product_ids = self.session_cart.keys()
            products = PopUpProduct.objects.filter(id__in=product_ids)
            for product in products:
                item = self.session_cart[str(product.id)]
                yield {
                    'product': product,
                    'qty': item['qty'],
                    'price': item['price'],
                    'total_price': item['price'] * item['qty']
                }

    def __len__(self):
        """
        Get cart dta and count the quantity of the items in the basket
        """
        if self._user.is_authenticated:
            return sum(item.quantity for item in PopUpCartItem.objects.filter(user=self._user))
        return sum(item['qty'] for item in self.session_cart.values())
        # return sum(item['qty'] for item in self.cart.values())


    def get_subtotal_price(self):
        print('get_subtotal_price user_cart', self.session_cart)
        if self._user.is_authenticated:
            return sum(
                Decimal(item.product.display_price() or 0) * item.quantity
                for item in self.user_cart
            )
        else:
            return sum(
                Decimal(item['price']) * item['qty']
                for item in self.session_cart.values()
            )
        


    def get_total_price(self):
        if self._user and self._user.is_authenticated:
            subtotal = sum(
            Decimal(item.product.display_price() or 0) * item.quantity
            for item in self.user_cart
            )
        else:
            subtotal = sum(
            Decimal(item['price']) * item['qty']
            for item in self.session_cart.values()
            )

        shipping = Decimal(0.00)
        return subtotal + shipping


    def delete(self, product):
        """
        Delete item from session data
        """
        print('delete called!')
        product_id = str(product)
        print('product_id', product_id)

        if self._user and self._user.is_authenticated:
            PopUpCartItem.objects.filter(user=self._user, product_id=product_id).delete()
        else:
            session_cart = self.session.get(settings.CART_SESSION_ID, {})
            if product_id in session_cart:
                del session_cart[product_id]
                self.session[settings.CART_SESSION_ID] = session_cart
                self.save()

        # product_id = str(product)
        # if product_id in self.cart:
        #     del self.cart[product_id]
        #     self.save()
        
    
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
        self.session[settings.CART_SESSION_ID] = self.session_cart
        self.session.modified = True
    
    def clear(self):
        """
        Remove cart from session
        """
        if self._user.is_authenticated:
            PopUpCartItem.objects.filter(user=self._user).delete()
        else:
            self.session_cart = {}
            self.save()
        # del self.session[settings.CART_SESSION_ID]
        # self.save()