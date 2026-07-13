from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http.response import JsonResponse
from pop_up_cart.cart import Cart
from pop_up_cart.models import ProcurementCartItem
from .models import PopUpCustomerOrder, PopUpOrderItem
from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerAddress
from pop_up_auction.models import PopUpProduct, WinnerReservation
from pop_up_shipping.models import PopUpShipment
from pop_accounts.utils.pop_accounts_utils import add_specs_to_products
from pop_up_coupon.models import PopUpCoupon
from pop_up_payment.models import PopUpPayment, ServicePayment
from pop_up_shipping.models import PopUpShipment
from pop_up_finance.models import PopUpFinance
from pop_up_order.models import PopUpOrderItem
from pop_up_bot.utils import get_procurement_service_product
from pop_up_payment.utils.payment_fee_handler import get_fees_by_payment
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.decorators import staff_member_required
from pop_up_email.utils import send_order_confirmation_email
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
import stripe
import json
import braintree
import re
from django.db.models import Q
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
import logging


User = get_user_model()

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderAfterPaymentView(View):
     def post(self, request, *args, **kwargs):
        cart = Cart(request)
        ids_in_cart = cart.get_product_ids()
        product_qs = PopUpProduct.objects.filter(
            Q(id__in=ids_in_cart),
            Q(is_active=True),
            Q(inventory_status__in=["reserved", "sold_out"])
        )
        procurement_product = get_procurement_service_product()
 
        # Build product map for physical cart items
        product_map = {}
        for product in product_qs:
            spec_values = {
                spec.specification.name.lower(): spec.value
                for spec in product.popupproductspecificationvalue_set.all()
            }
            product_map[product.id] = {
                'product': product,
                'product_title': product.product_title,
                'secondary_title': product.secondary_product_title,
                'colorway': spec_values.get('colorway', ''),
                'size': spec_values.get('size', ''),
                'product_sex': spec_values.get('product_sex', '')
            }
 
        try:
            data = json.loads(request.body)
 
            required_fields = [
                'payment_data_id', 'payment_method', 'order_key', 'user_id',
                'total_paid', 'email', 'address1', 'postal_code', 'city',
                'state', 'shippingAddressId', 'billingAddressId'
            ]
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)
 
            payment_data_id = data.get('payment_data_id')
            payment_method = data.get('payment_method')
            order_key = data.get('order_key')
            user_id = data.get('user_id')
            total_paid = Decimal(data.get('total_paid', '0.00'))
 
            customer = PopUpCustomerProfile.objects.get(user_id=user_id)
            user = customer.user
 
            shipping_address = PopUpCustomerAddress.objects.get(id=data.get('shippingAddressId'))
            billing_address = PopUpCustomerAddress.objects.get(id=data.get('billingAddressId'))
 
            # --- Stripe customer creation ---
            if not customer.stripe_customer_id:
                try:
                    stripe_customer = stripe.Customer.create(
                        email=data.get('email'),
                        name=f"{user.first_name} {user.last_name}",
                        address={
                            "line1": data.get('address1'),
                            "line2": data.get('address2'),
                            "postal_code": data.get('postal_code'),
                            "city": data.get('city'),
                            "state": data.get('state'),
                        },
                    )
                    customer.stripe_customer_id = stripe_customer.id
                    customer.save(update_fields=["stripe_customer_id"])
                    try:
                        payment_intent = stripe.PaymentIntent.retrieve(payment_data_id)
                        if payment_intent.payment_method:
                            stripe.PaymentMethod.attach(
                                payment_intent.payment_method,
                                customer=stripe_customer.id,
                            )
                    except stripe.error.StripeError as e:
                        print(f"Error attaching PaymentMethod to customer: {e}")
                except stripe.error.StripeError as e:
                    print(f"Stripe error creating customer: {e}")
 
            # --- Payment fees ---
            try:
                payment_fees = get_fees_by_payment(payment_method, payment_data_id)
            except Exception as e:
                logger.error(f'Failed to retrieve payment fees: {e}')
                payment_fees = Decimal('0.00')
 
            # --- Phone ---
            phone_number = data.get('phone')
            phone = None
            match = re.search(r'>([\d\-]+)<', phone_number)
            phone = match.group(1) if match else phone_number
 
            # --- Coupon ---
            coupon = None
            if data.get('coupon_id'):
                try:
                    coupon = PopUpCoupon.objects.get(id=data.get('coupon_id'))
                except PopUpCoupon.DoesNotExist:
                    pass
 
            # --- 1. Create order ---
            order = PopUpCustomerOrder.objects.create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                email=data.get('email'),
                address1=data.get('address1'),
                address2=data.get('address2'),
                postal_code=data.get('postal_code'),
                apartment_suite_number=data.get('apartment_suite_number'),
                city=data.get('city'),
                state=data.get('state'),
                phone=phone,
                total_paid=total_paid,
                order_key=order_key,
                billing_status=True,
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment_data_id=payment_data_id,
                coupon=coupon,
                discount=data.get('discount', 0)
            )
 
            # FIX: define order_id immediately after order creation
            # so all subsequent blocks can use it safely
            order_id = order.pk
 
            # --- 2. Payment record ---
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
                print(f'PopUpPayment error: {e}')
 
            # --- 3. Physical cart items ---
            order_items = []
            for item in cart:
                product_id = item['product'].id
                prod_data = product_map.get(product_id)
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
 
            # --- 4. Procurement cart items ---
            try:
                procurement_items = ProcurementCartItem.objects.filter(
                    user=user
                ).select_related(
                    'procurement_service_request__scheduled_release__product'
                )
                
                for item in procurement_items:
                    psr = item.procurement_service_request
                    try:
                        PopUpOrderItem.objects.create(
                            order_id=order_id,
                            product=procurement_product,
                            product_title='Procurement Service Fee',
                            secondary_product_title=psr.scheduled_release.product.product_title,
                            size=psr.size,
                            color='',
                            price=item.fee_amount,
                            quantity=1
                        )
                    except Exception as e:
                        print(f'PopOrderItem Error: {e}')
                    
                    try:
                        PopUpFinance.objects.create(
                            order=order,
                            product=procurement_product,
                            reserve_price=Decimal('0.00'),
                            final_price=item.fee_amount,
                            fees=payment_fees,
                            refunded_amount=Decimal('0.00'),
                            profit=item.fee_amount,
                            payment_method=payment_method,
                            is_disputed=False,
                            is_refunded=False
                        )
                    except Exception as e:
                        print(f'PopUpFinance Error: {e}')

                    
                    # ← NEW: Create ServicePayment so refunds can be processed if bot fails
                    ServicePayment.objects.get_or_create(
                        service_request=psr,
                        defaults={
                            'amount': item.fee_amount,
                            'status': 'paid',
                            'payment_method': payment_method,   # 'stripe', 'venmo', etc.
                            'payment_reference': payment_data_id,  # Stripe PaymentIntent ID
                        }
                    )
 
                    psr.status = 'pending'
                    psr.fee_paid_at = timezone.now()
                    psr.save(update_fields=['status', 'fee_paid_at'])
                    item.delete()
 
            except Exception as e:
                logger.error(
                    f'Failed to update procurement requests for user {user.id} '
                    f'on order {order.id}: {e}'
                )
 
            # --- 5. Shipment (physical items only) ---
            if order_items:
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
                    print(f'create_shipping error: {e}')
 
            # --- 6. Mark physical products sold + finance records ---
            for pid in ids_in_cart:
                try:
                    product = PopUpProduct.objects.get(id=pid)
                    product.inventory_status = 'sold_out'
                    product.is_active = False
                    product.save()
 
                    PopUpFinance.objects.create(
                        order=order,
                        product=product,
                        reserve_price=product.reserve_price,
                        final_price=total_paid,
                        fees=payment_fees,
                        refunded_amount=Decimal('0.00'),
                        profit=Decimal(total_paid) - Decimal(product.reserve_price),
                        payment_method=payment_method,
                        is_disputed=False,
                        is_refunded=False
                    )

                    reservation = WinnerReservation.objects.filter(
                        user=user, product=product, is_paid=False
                    ).first()

                    if reservation:
                        reservation.is_paid = True
                        reservation.save()
 
                except Exception as e:
                    print(f'Physical product processing error for id {pid}: {e}')
 
            # --- 7. Order confirmation email ---
            send_order_confirmation_email(
                request.user, order_id, order_items, total_paid, payment_status="pending"
            )
 
            return JsonResponse({'success': True, 'order_id': str(order.id)})
 
        except (KeyError, ObjectDoesNotExist) as e:
            return JsonResponse({'error': f"Missing or invalid data: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
 
    # def post(self, request, *args, **kwargs):
    #     cart = Cart(request)
    #     ids_in_cart = cart.get_product_ids()
    #     product_qs = PopUpProduct.objects.filter(Q(id__in=ids_in_cart), Q(is_active=True), Q(inventory_status__in=["reserved", "sold_out"]))
    #     procurement_product = get_procurement_service_product()

    #     # Build diction for lookup
    #     product_map = {}
    #     for product in product_qs:
    #         spec_values = {spec.specification.name.lower(): spec.value for spec in product.popupproductspecificationvalue_set.all()}
    #         product_map[product.id] = {
    #             'product': product,
    #             'product_title': product.product_title,
    #             'secondary_title': product.secondary_product_title,
    #             'colorway': spec_values.get('colorway', ''),   # Make sure your spec names are consistent (e.g. "color", "size")
    #             'size': spec_values.get('size', ''),
    #             'product_sex': spec_values.get('product_sex', '')
    #         }

    #     try:
    #         data = json.loads(request.body)
    #         # print('CreateOrderAfterPaymentView data', data, '\n')

    #         # Add Validation- Before doing anything else
    #         required_fields = [
    #             'payment_data_id',
    #             'payment_method',
    #             'order_key',
    #             'user_id',
    #             'total_paid',
    #             'email',
    #             'address1',
    #             'postal_code',
    #             'city',
    #             'state',
    #             'shippingAddressId',
    #             'billingAddressId'
    #         ]
            
    #         missing_fields = [field for field in required_fields if not data.get(field)]
    #         if missing_fields:
    #             return JsonResponse({
    #                 'success': False,
    #                 'error': f'Missing required fields: {", ".join(missing_fields)}'
    #             }, status=400)

    #         payment_data_id = data.get('payment_data_id')

    #         payment_method = data.get('payment_method')
    #         # print('payment_method', payment_method)


    #         order_key = data.get('order_key')
    #         user_id = data.get('user_id')
    #         total_paid = Decimal(data.get('total_paid', '0.00'))

    #         customer = PopUpCustomerProfile.objects.get(user_id=user_id)
    #         user = customer.user
            
    #         shipping_address = PopUpCustomerAddress.objects.get(id=data.get('shippingAddressId'))
    #         billing_address = PopUpCustomerAddress.objects.get(id=data.get('billingAddressId'))
            
    #         if not customer.stripe_customer_id:
    #             try:
    #                 stripe_customer = stripe.Customer.create(
    #                     email=data.get('email'),
    #                     name=f"{user.first_name} {user.last_name}",
    #                     address={
    #                         "line1": data.get('address1'),
    #                         "line2": data.get('address2'),
    #                         "postal_code": data.get('postal_code'),
    #                         "city": data.get('city'),
    #                         "state": data.get('state'),
    #                     },
    #                 )
    #                 customer.stripe_customer_id = stripe_customer.id
    #                 customer.save(update_fields=["stripe_customer_id"])
    #                 # NEW: Attach the PaymentMethod to this customer
    #                 try:
    #                     # Retrieve the PaymentIntent to get the PaymentMethod
    #                     payment_intent = stripe.PaymentIntent.retrieve(payment_data_id)
                        
    #                     if payment_intent.payment_method:
    #                         # Attach the PaymentMethod to the newly created customer
    #                         stripe.PaymentMethod.attach(
    #                             payment_intent.payment_method,
    #                             customer=stripe_customer.id,
    #                         )
                            
    #                 except stripe.error.StripeError as e:
    #                     print(f"Error attaching PaymentMethod to customer: {e}")
                        
                        
    #             except stripe.error.StripeError as e:
    #                 print(f"Stripe error creating customer: {e}")
    #             # except stripe.error.StripeError as e:
    #             #     print(f"Stripe error creating customer: {e}")

            
    #         # Need to work on the get_fees_by_payment function
    #         try:
    #             payment_fees = get_fees_by_payment(payment_method, payment_data_id)
    #         except Exception as e:
    #             logger.error('Failed to retrieve payment fees: {e}')
    #             payment_fees = Decimal('0.00')
           

    #         # not needed because payment_data_id = payload.nonce from Venmo
    #         # nonce = data.get('payment_method_nonce') #braintree venmo
    #         # print('nonce', nonce)
    #         # if not nonce:
    #         #     return JsonResponse({'success': False, 'error': 'No payment method provided'})
            
    #         phone_number=data.get('phone')
    #         phone = None
    #         match = re.search(r'>([\d\-]+)<', phone_number)

    #         if match:
    #             phone = match.group(1)
    #         else:
    #             phone = phone_number  # fallback if already plain

            
    #         coupon = None
    #         if data.get('coupon_id'):
    #             try:
    #                 coupon = PopUpCoupon.objects.get(id=data.get('coupon_id'))
    #             except PopUpCoupon.ObjectDoesNotExist:
    #                 pass
            
    #         # create order
    #         order = PopUpCustomerOrder.objects.create(
    #             user=user,
    #             full_name = f"{user.first_name} {user.last_name}",
    #             email=data.get('email'),
    #             address1=data.get('address1'),
    #             address2=data.get('address2'),
    #             postal_code=data.get('postal_code'),
    #             apartment_suite_number = data.get('apartment_suite_number'),
    #             city=data.get('city'),
    #             state=data.get('state'),
    #             phone=phone,
    #             total_paid=total_paid,
    #             order_key=order_key,
    #             billing_status=True, # payment was successful
    #             shipping_address=shipping_address,
    #             billing_address=billing_address,
    #             payment_data_id=payment_data_id, #this should be payment_id instead of stripe_id, since using more than one payment gate
    #             coupon=coupon,
    #             discount=data.get('discount', 0)
    #         )

    #         # 2. Confirm any procurement requests that were in the cart
    #         try:
    #             procurement_items = ProcurementCartItem.objects.filter(
    #             user=user
    #             ).select_related('procurement_service_request')

    #             for item in procurement_items:
    #                 psr = item.procurement_service_request
    #                 # Counts as an order item for bookkeeping
    #                 PopUpOrderItem.objects.create(
    #                     order_id=order_id,
    #                     product=procurement_product,
    #                     product_title='Procurement Service Fee',
    #                     secondary_product_title=psr.scheduled_release.product.product_title,
    #                     size=psr.size,
    #                     color='',
    #                     price=item.fee_amount,
    #                     quantity=1
    #                 )

    #                 # Finance record
    #                 PopUpFinance.objects.create(
    #                     order=order,
    #                     product=procurement_product,
    #                     reserve_price=Decimal('0.00'),
    #                     final_price=item.fee_amount,
    #                     fees=payment_fees,
    #                     refunded_amount=Decimal('0.00'),
    #                     profit=item.fee_amount,  # pure profit, no acquisition cost
    #                     payment_method=payment_method,
    #                     is_disputed=False,
    #                     is_refunded=False
    #                 )
    #                 psr.status = 'pending'
    #                 psr.fee_paid_at = timezone.now()
    #                 psr.save(update_fields=['status', 'fee_paid_at'])
    #                 item.delete()  # remove from cart now that payment is confirmed
    #         except Exception as e:
    #             logger.error(f"Failed to update procurement reuqests for user {user.id} on order {order.id}: {e}")
            

    #         # 3. Create payment object with "pending" status (Payment status will be updated by webhook)
    #         try:
    #             PopUpPayment.objects.create(
    #                 order=order,
    #                 amount=total_paid,
    #                 payment_reference=payment_data_id,
    #                 payment_method=payment_method,
    #                 status='pending',
    #                 suspicious_flagged=False,
    #                 notified_ready_to_ship=False,
    #             )
    #         except Exception as e:
    #             print('e for PopUpPayment', e)

            
    #         order_id = order.pk
    #         order_items = []

    #         for item in cart:
    #             product_id = item['product'].id
    #             prod_data = product_map.get(product_id)
    #             if not prod_data:
    #                 continue
    #             order_item = PopUpOrderItem.objects.create(
    #                 order_id=order_id, 
    #                 product=prod_data['product'],
    #                 product_title=prod_data['product_title'],
    #                 secondary_product_title=prod_data['secondary_title'],
    #                 size=prod_data['size'],
    #                 color=prod_data['colorway'],
    #                 price=item['price'], 
    #                 quantity=item['qty']
    #             )
    #             order_items.append(order_item)
            
    #         # Create shipping instance here with order_no, set status to pending
    #         try: 
    #             PopUpShipment.objects.create(
    #                 order=order,
    #                 carrier='usps',
    #                 tracking_number=None,
    #                 shipped_at=None,
    #                 estimated_delivery=None,
    #                 delivered_at=None,
    #                 status="pending",
    #             )
    #         except Exception as e:
    #             print('create_shipping e', e)
        
    #         send_order_confirmation_email(request.user, order_id, order_items, total_paid, payment_status="pending")

    #         for id in ids_in_cart:
                
    #             product = PopUpProduct.objects.get(id=id)
    #             product.inventory_status = 'sold_out'
    #             product.is_active = False
    #             product.save()

    #             try:
    #                 PopUpFinance.objects.create(
    #                     order=order,
    #                     product=product,
    #                     reserve_price=product.reserve_price,
    #                     final_price=total_paid,
    #                     fees=payment_fees,
    #                     refunded_amount=0.00,
    #                     profit=Decimal(total_paid) - Decimal(product.reserve_price),
    #                     payment_method=payment_method,
    #                     is_disputed=False,
    #                     is_refunded=False
    #                 )
    #             except Exception as e:
    #                 print('PopUpFinance Error', e)
            
    #             reservation = WinnerReservation.objects.filter(user=user, product=product, is_paid=False).first()
                
    #             if reservation:
    #                 reservation.is_paid = True
    #                 reservation.save()
                
           
    #         return JsonResponse({'success': True, 'order_id': str(order.id)})
        
    #     except (KeyError, ObjectDoesNotExist) as e:
    #         return JsonResponse({'error': f"Missing or invalid data: {str(e)}"}, status=400)
    #     except Exception as e:
    #         return JsonResponse({'error': str(e)}, status=500)


def payment_confirmation(data):
    PopUpCustomerOrder.objects.filter(order_key=data).update(billing_status=True)




@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(PopUpCustomerOrder, id=order_id)
    return render(request, 'orders/admin/detail.html', {'order': order})


