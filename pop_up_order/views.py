from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import JsonResponse
from pop_up_cart.cart import Cart
from .models import PopUpCustomerOrder, PopUpOrderItem
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress
from pop_up_auction.models import PopUpProduct, WinnerReservation
from pop_up_shipping.models import PopUpShipment
from pop_accounts.utils.utils import add_specs_to_products
from pop_up_coupon.models import PopUpCoupon
from pop_up_payment.models import PopUpPayment
from pop_up_shipping.models import PopUpShipment
from pop_up_finance.models import PopUpFinance
from pop_up_order.models import PopUpOrderItem
from pop_up_payment.utils.payment_fee_handler import get_fees_by_payment
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.decorators import staff_member_required
from pop_up_email.utils import send_order_confirmation_email
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decimal import Decimal
import stripe
import json
from collections import defaultdict
import braintree
import re
from django.db.models import Q
from django.http import HttpResponse
from django.db.models import Prefetch
import logging

logger = logging.getLogger(__name__)



# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAfterPaymentView(View):
    def post(self, request, *args, **kwargs):
        cart = Cart(request)
        ids_in_cart = cart.get_product_ids()
        product_qs = PopUpProduct.objects.filter(Q(id__in=ids_in_cart), Q(is_active=True), Q(inventory_status__in=["reserved", "sold_out"]))
        

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
                'product_sex': spec_values.get('product_sex', '')
            }

        try:
            data = json.loads(request.body)
            print('CreateOrderAfterPaymentView data', data, '\n')

            payment_data_id = data.get('payment_data_id')
            print('payment_data_id', payment_data_id)

            payment_method = data.get('payment_method')
            print('payment_method', payment_method)


            order_key = data.get('order_key')
            user_id = data.get('user_id')
            total_paid = Decimal(data.get('total_paid', '0.00'))

            customer = PopUpCustomer.objects.get(id=user_id)
            shipping_address = PopUpCustomerAddress.objects.get(id=data.get('shippingAddressId'))
            billing_address = PopUpCustomerAddress.objects.get(id=data.get('billingAddressId'))

            
            # Need to work on the get_fees_by_payment function
            try:
                payment_fees = get_fees_by_payment(payment_method, payment_data_id)
            except Exception as e:
                logger.error('Failed to retrieve payment fees: {e}')
                payment_fees = Decimal('0.00')
           

            # not needed because payment_data_id = payload.nonce from Venmo
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

            # 2. Create payment object with "pending" status (will be updated by webhook)
            try:
                PopUpPayment.objects.create(
                    order=order,
                    amount=total_paid,
                    payment_reference=payment_data_id,
                    payment_method=payment_method,
                    status='pending',
                    suspicious_flagged=False,
                    notified_ready_to_ship=False,
                )
            except Exception as e:
                print('e for PopUpPayment', e)

            order_id = order.pk
            order_items = []

            for item in cart:
                product_id = item['product'].id
                prod_data = product_map.get(product_id)
                print('prod_data', prod_data)
                if not prod_data:
                    continue
                order_item = PopUpOrderItem.objects.create(
                    order_id=order_id, 
                    product=prod_data['product'],
                    product_title=prod_data['product_title'],
                    secondary_product_title=prod_data['secondary_title'],
                    size=prod_data['size'],
                    color=prod_data['colorway'],
                    price=item['price'], 
                    quantity=item['qty']
                )

                order_items.append(order_item)
            
            # Create shipping instance here with order_no, set status to pending
            try: 
                PopUpShipment.objects.create(
                    order=order,
                    carrier='usps',
                    tracking_number=None,
                    shipped_at=None,
                    estimated_delivery=None,
                    delivered_at=None,
                    status="pending",
                )

            except Exception as e:
                print('create_shipping e', e)
        

            send_order_confirmation_email(request.user, order_id, order_items, total_paid, payment_status="pending")
          
            for id in ids_in_cart:
                product = PopUpProduct.objects.get(id=id)
                product.inventory_status = 'sold_out'
                product.is_active = False
                product.save()
            
                reservation = WinnerReservation.objects.filter(user=customer, product=product, is_paid=False).first()

                try:
                    PopUpFinance.objects.create(
                        order=order,
                        product=product,
                        reserve_price=product.reserve_price,
                        final_price=total_paid,
                        fees=payment_fees,
                        refunded_amount=0.00,
                        profit=Decimal(total_paid) - Decimal(product.reserve_price),
                        payment_method=payment_method,
                        is_disputed=False,
                        is_refunded=False
                    )
                except Exception as e:
                    print('PopUpFinance Error', e)
                
                if reservation:
                    reservation.is_paid = True
                    reservation.save()
                
           
            return JsonResponse({'success': True, 'order_id': str(order.id)})
        
        except (KeyError, ObjectDoesNotExist) as e:
            return JsonResponse({'error': f"Missing or invalid data: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


def payment_confirmation(data):
    PopUpCustomerOrder.objects.filter(order_key=data).update(billing_status=True)


def user_orders(request):
    user_id = request.user.id
    orders = (
        PopUpCustomerOrder.objects
        .filter(user=user_id, billing_status=True)
        .prefetch_related('items')  # load PopUpOrderItems efficiently
        .only('id', 'created_at', 'city', 'state', 'postal_code')  # minimize selected fields
    )
    return orders


def user_shipments(request):
    user_id = request.user.id
    """Get shipped products for a specific user with specs, shipment info, and shipping address"""
    
    orders = PopUpCustomerOrder.objects.select_related(
        'shipment',
        'shipping_address'
    ).prefetch_related(
        Prefetch(
            'items__product',  # Changed from 'order_items' to 'items'
            queryset=PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set__specification')
        )
    ).filter(
        user=user_id,
        shipment__isnull=False
    )
    
    result = []
    
    for order in orders:
        # Get products with specs
        products_in_order = [item.product for item in order.items.all()]  # Changed to 'items'
        products_with_specs = add_specs_to_products(products_in_order)
        
        for order_item in order.items.all():
            product = order_item.product
            # Find the corresponding product with specs
            product_with_specs = next(p for p in products_with_specs if p.id == product.id)
            
            result.append(
                {
                'order_id': order.id,
                'order_item_id': order_item.id,
                'product_id': product_with_specs.id,
                'product_title': product_with_specs.product_title,
                'secondary_product_title': product_with_specs.secondary_product_title,
                'model_year': product_with_specs.specs.get('model_year'),
                'all_specs': product_with_specs.specs,
                'order_item': {
                    'quantity': order_item.quantity,
                    'price': order_item.price,
                    'size': order_item.size,
                    'color': order_item.color,
                },
                'shipment': {
                    'carrier': order.shipment.carrier,
                    'tracking_number': order.shipment.tracking_number,
                    'shipped_at': order.shipment.shipped_at,
                    'estimated_delivery': order.shipment.estimated_delivery,
                    'delivered_at': order.shipment.delivered_at,
                    'status': order.shipment.status,
                },
                'billing_address': {
                    'full_name': order.full_name,
                    'address1': order.address1,
                    'address2': order.address2,
                    'city': order.city,
                    'state': order.state,
                    'postal_code': order.postal_code,
                    'apartment_suite_number': order.apartment_suite_number,
                },
                'shipping_address': {
                    'prefix': order.shipping_address.prefix if order.shipping_address else None,
                    'first_name': order.shipping_address.first_name if order.shipping_address else None,
                    'middle_name': order.shipping_address.middle_name if order.shipping_address else None,
                    'last_name': order.shipping_address.last_name if order.shipping_address else None,
                    'suffix': order.shipping_address.suffix if order.shipping_address else None,
                    'address_line': order.shipping_address.address_line if order.shipping_address else None,
                    'address_line2': order.shipping_address.address_line2 if order.shipping_address else None,
                    'town_city': order.shipping_address.town_city if order.shipping_address else None,
                    'state': order.shipping_address.state if order.shipping_address else None,
                    'postcode': order.shipping_address.postcode if order.shipping_address else None,
                    'apartment_suite_number': order.shipping_address.apartment_suite_number if order.shipping_address else None,
                    'delivery_instructions': order.shipping_address.delivery_instructions if order.shipping_address else None,
                } if order.shipping_address else None
            })
    
    return result



@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(PopUpCustomerOrder, id=order_id)
    return render(request, 'orders/admin/details.html', {'order': order})


