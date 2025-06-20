from django.views import View
from django.shortcuts import render
from django.http.response import JsonResponse
from cart.cart import Cart
from .models import PopUpCustomerOrder, PopUpOrderItem
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress
from auction.models import PopUpProduct
from coupon.models import PopUpCoupon
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decimal import Decimal
import stripe
import json
from collections import defaultdict
import braintree
import re

# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAfterPaymentView(View):
    def post(self, request, *args, **kwargs):
        cart = Cart(request)
        ids_in_cart = [int(pid) for pid in cart.cart.keys()]

        product_qs = (
                PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
                .prefetch_related('popupproductspecificationvalue_set')
            )

        # Build diction for lookup
        product_map = {}
        for product in product_qs:
            spec_values = {spec.specification.name.lower(): spec.value for spec in product.popupproductspecificationvalue_set.all()}
            product_map[product.id] = {
                'product': product,
                'product_title': product.product_title,
                'secondary_title': product.secondary_product_title,
                'colorway': spec_values.get('colorway', ''),   # Make sure your spec names are consistent (e.g. "color", "size")
                'size': spec_values.get('size', ''),
            }

        try:
            data = json.loads(request.body)
            print('CreateOrderAfterPaymentView data', data, '\n')

            payment_data_id = data.get('payment_data_id')
            print('payment_data_id', payment_data_id)


            order_key = data.get('order_key')
            user_id = data.get('user_id')
            total_paid = Decimal(data.get('total_paid', '0.00'))
            customer = PopUpCustomer.objects.get(id=user_id)
            shipping_address = PopUpCustomerAddress.objects.get(id=data.get('shippingAddressId'))
            billing_address = PopUpCustomerAddress.objects.get(id=data.get('billingAddressId'))

            # not needed because payment_data_id = payload.nonce from Venmoe
            # nonce = data.get('payment_method_nonce') #braintree venmo
            # print('nonce', nonce)
            # if not nonce:
            #     return JsonResponse({'success': False, 'error': 'No payment method provided'})
            
            phone_number=data.get('phone')
            phone = None
            match = re.search(r'>([\d\-]+)<', phone_number)

            if match:
                phone = match.group(1)
            else:
                phone = phone_number  # fallback if already plain


            

            
            coupon = None
            if data.get('coupon_id'):
                try:
                    coupon = PopUpCoupon.objects.get(id=data.get('coupon_id'))
                except PopUpCoupon.ObjectDoesNotExist:
                    pass
            
            # create order
            order = PopUpCustomerOrder.objects.create(
                user=customer,
                full_name = customer,
                email=data.get('email'),
                address1=data.get('address1'),
                address2=data.get('address2'),
                postal_code=data.get('postal_code'),
                apartment_suite_number = data.get('apartment_suite_number'),
                city=data.get('city'),
                state=data.get('state'),
                phone=phone,
                total_paid=total_paid,
                order_key=order_key,
                billing_status=True, # payment was successful
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_data_id=payment_data_id, #this should be payment_id instead of stripe_id, since using more than one payment gate
                coupon=coupon,
                discount=data.get('discount', 0)
            )

            order_id = order.pk

            for item in cart:
                prod_data = product_map.get(item['product'].id)
                if not prod_data:
                    continue
                PopUpOrderItem.objects.create(
                    order_id=order_id, 
                    product=prod_data['product'],
                    product_title=prod_data['product_title'],
                    secondary_product_title=prod_data['secondary_title'],
                    size=prod_data['size'],
                    color=prod_data['colorway'],
                    price=item['price'], 
                    quantity=item['qty']
                )

            return JsonResponse({'success': True, 'order_id': str(order.id)})
        
        except (KeyError, ObjectDoesNotExist) as e:
            return JsonResponse({'error': f"Missing or invalid data: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def payment_confirmation(data):
    PopUpCustomerOrder.objects.filter(order_key=data).update(billing_status=True)


def user_orders(request):
    user_id = request.user.id
    orders = PopUpCustomerOrder.objects.filter(user_id=user_id).filter(billing_status=True)
    return orders
