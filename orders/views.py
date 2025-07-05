from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import JsonResponse
from cart.cart import Cart
from .models import PopUpCustomerOrder, PopUpOrderItem
from pop_accounts.models import PopUpCustomer, PopUpCustomerAddress
from auction.models import PopUpProduct, WinnerReservation
from coupon.models import PopUpCoupon
from payment.models import PopUpPayment
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
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint

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


            order_key = data.get('order_key')
            user_id = data.get('user_id')
            total_paid = Decimal(data.get('total_paid', '0.00')) 
            # paypal total: $28308.99 should be $283.09
            print('total_paid', total_paid)
            customer = PopUpCustomer.objects.get(id=user_id)
            shipping_address = PopUpCustomerAddress.objects.get(id=data.get('shippingAddressId'))
            billing_address = PopUpCustomerAddress.objects.get(id=data.get('billingAddressId'))

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
        
            PopUpPayment.objects.create(
                order=order,
                amount=total_paid,
                payment_reference=payment_data_id,
                status='pending',
                suspicious_flagged=False,
                notified_ready_to_ship=False,
            )
          


            order_id = order.pk
            order_items = []
            for item in cart:
                print('item', item)
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
                        
            send_order_confirmation_email(request.user, order_id, order_items, total_paid, payment_status="pending")
          
            for id in ids_in_cart:
                product = PopUpProduct.objects.get(id=id)
                print('product in order', product)
                product.inventory_status = 'sold_out'
                product.save()
            
                reservation = WinnerReservation.objects.filter(user=customer, product=product, is_paid=False).first()
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
    orders = PopUpCustomerOrder.objects.filter(user_id=user_id).filter(billing_status=True)
    return orders


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(PopUpCustomerOrder, id=order_id)
    return render(request, 'orders/admin/details.html', {'order': order})


# couldn't figure out issue with weasyprint and the
# Additionally, ctypes.util.find_library() did not manage to locate a library called 'gobject-2.0-0' error

@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(PopUpCustomerOrder, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order', order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=order_{order.id}.pdf'
    weasyprint.HTML(string=html).write_pdf(response, stylesheets=[weasyprint.CSS(
        settings.STATIC_ROOT + 'css/pdf.css')
    ])
    return response