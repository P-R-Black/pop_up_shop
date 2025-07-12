from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from cart.cart import Cart
from django.http import JsonResponse
from auction.models import PopUpProduct, PopUpProductSpecificationValue, PopUpProductType
from pop_accounts.models import PopUpBid, PopUpCustomerAddress
from cart.models import PopUpCartItem
from payment.models import PopUpPayment
from orders.models import PopUpCustomerOrder
from pop_accounts.forms import ThePopUpUserAddressForm, PopUpUpdateShippingInformationForm
import stripe
from django.conf import settings
from django.views.decorators.http import require_http_methods
import json
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator
from orders.views import payment_confirmation
from pop_up_email.utils import send_dispute_alert_to_customer
import os
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.views import View
from decimal import Decimal
from django.utils.timezone import now
from datetime import timedelta
from dateutil.parser import parse as parse_datetime
from payment.utils.tax_utils import get_state_tax_rate
from payment.utils.address_form_handler import(handle_new_address, handle_selected_address, handle_update_address)
import braintree
import logging
import requests
import hmac
import hashlib

logger = logging.getLogger(__name__)


gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        braintree.Environment.Sandbox,
        merchant_id=settings.BRAINTREE_MERCHANT_ID,
        public_key=settings.BRAINTREE_PUBLIC_KEY,
        private_key=settings.BRAINTREE_PRIVATE_KEY,
    )
)


# NowPayments API configuration
NOWPAYMENTS_API_KEY = getattr(settings, 'NOWPAYMENTS_API_KEY', settings.NOWPAYMENTS_API_KEY)
NOWPAYMENTS_IPN_SECRET = getattr(settings, 'NOWPAYMENTS_IPN_SECRET', settings.NOWPAYMENTS_IPN_SECRET)
NOWPAYMENTS_BASE_URL = 'https://api.nowpayments.io/v1'



# Create your views here.
class AjaxLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'You must be logged in to place a bid'}, status=403)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class OptionalLoginMixin(AccessMixin):
    """
    Allow both authenticated and anonymous users.
    Provides 'self.request.user.is_authenticated' for view logic.
    """
    def dispatch(self, request, *args, **kwargs):
        # Dont redirect
        return super().dispatch(request, *args, **kwargs)
    

class ProductBuyView(OptionalLoginMixin, View):
    template_name = 'payment/payment_home.html'
    
    def get(self, request):
        """Cart view for user if not signed in"""
        if not request.user.is_authenticated:
            cart = Cart(request)
            session_cart = getattr(cart, "session_cart", {})
           
            # 1. Collect product IDs in the cart
            # ids_in_cart = [int(pid) for pid in cart.session_cart.keys()]
            ids_in_cart = cart.get_product_ids()

            # 2 Fetch products ounce with needed data
            products = (
                PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
                .prefetch_related('popupproductspecificationvalue_set')
            )

            product_map = {p.id: p for p in products}

            # 3 Build "enriched" cart rows
            enriched_cart = []
            for pid, item in cart.session_cart.items():
                pid_int = int(pid)
                product = product_map.get(pid_int)
                if not product:
                    continue # shouldn't happen, but just to be safe

                enriched_cart.append({
                    "product": product,
                    "specs": list(product.popupproductspecificationvalue_set.all()),
                    "qty": item["qty"],
                    "unit_price": Decimal(item["price"]),
                    "line_total": Decimal(item["price"]) * item["qty"],
                })

            
            # 4 Item quantity in cart
            cart_length = len(cart)

            # 5. Shipping Standard
            standard_shipping = 1499
        
            # 6. Totals
            subtotal = cart.get_subtotal_price()
            
            # enriched_cart = build_enriched_cart(cart)  # helper you already have
            cart_length = len(cart)

            # braintree client_token
            client_token = gateway.client_token.generate()


            # Shared context for everyone (guest or auth'd)
            context = {
                "cart_items": enriched_cart,
                "cart_length": cart_length,
                "cart_total": cart.get_total_price(),
                "cart_subtotal": subtotal,
                "client_token":  client_token,
                'braintree_public_key': settings.BRAINTREE_PUBLIC_KEY
            }
            return render(request, self.template_name, context)
        

        """ Cart view for user who is signed in"""
        if request.user.is_authenticated:
            user = request.user
            cart = Cart(request)
            # cart = PopUpCartItem.objects.filter(user=request.user)
            saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
            default_address = saved_addresses.filter(default=True).first()
            billing_address_id = request.session.get("selected_billing_address_id")
            billing_address = PopUpCustomerAddress.objects.filter(id=billing_address_id, customer=user).first()
            
            use_billing_as_shipping = request.session.get('use_billing_as_shipping', False)
            
            selected_address = None
            selected_address_id = request.session.get('selected_address_id')


            if selected_address_id:
                try:
                    selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
                    address_form = PopUpUpdateShippingInformationForm(instance=selected_address)
                except PopUpCustomerAddress.DoesNotExist:
                    selected_address = None

            
            total = "{:.2f}".format(cart.get_total_price())
            total = total.replace('.', '')
            total = int(total)

            # user_state = selected_address.state if selected_address else default_address.state
            user_state = (selected_address or default_address).state if (selected_address or default_address) else "FL"

            tax_rate =  get_state_tax_rate(user_state)
        
            # 1. Collect product IDs in the cart
            ids_in_cart = cart.get_product_ids()

            # 2 Fetch products ounce with needed data
            products = (
                PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
                .prefetch_related('popupproductspecificationvalue_set')
            )

            product_map = {p.id: p for p in products}

            # 3 Build "enriched" cart rows
            enriched_cart = []
            for pid, item in cart.get_items():
                pid_int = int(pid)
                product = product_map.get(pid_int)
                if not product:
                    continue # shouldn't happen, but just to be safe

                enriched_cart.append({
                    "product": product,
                    "specs": list(product.popupproductspecificationvalue_set.all()),
                    "qty": item["qty"],
                    "unit_price": Decimal(item["price"]),
                    "line_total": Decimal(item["price"]) * item["qty"],
                })
            
            # 4 Item quantity in cart
            cart_length = len(cart)

            # 5. Shipping Standard
            standard_shipping = 1499
        
            # 6. Totals
            subtotal = cart.get_subtotal_price()
            
            processing_fee = Decimal(2.50) if cart_length > 0 else Decimal(0.00)
            sales_tax = subtotal * Decimal(tax_rate)
            subtotal_plus_tax = subtotal + sales_tax
            order_shipping_chart = (Decimal((standard_shipping) / 100) * cart_length)

            grand_total =  subtotal_plus_tax +  order_shipping_chart + processing_fee if cart_length > 0 else 0
            grand_total_adjust_decimal = f"{grand_total:.2f}"
            grand_total_adjusted = grand_total_adjust_decimal.replace('.','')


             # braintree client_token
            client_token = gateway.client_token.generate()

            context = {"user": user, 
                    "cart_items": enriched_cart, 
                    "cart_subtotal": subtotal, 
                    "shipping_cost": standard_shipping, 
                    "cart_total": grand_total,
                    "cart_length": cart_length,
                    "sales_tax": f'{sales_tax:.2f}',
                    "processing_fee": f'{processing_fee:.2f}',
                    "grand_total": f"{Decimal(grand_total):.2f}",
                    "address": default_address,
                    "billing":billing_address,
                    "saved_addresses": saved_addresses,
                    "selected_address": selected_address,
                    "tax_rate":tax_rate,
                    "STRIPE_PUBLISHABLE_KEY": os.environ.get('STRIPE_PUBLISHABLE_KEY'),
                    "PAYPAL_CLIENT_ID": os.environ.get('PAYPAL_CLIENT_ID'),
                    "USER": user,
                    "USER_EMAIL": user.email,
                    "client_token": client_token,
                    'braintree_public_key': settings.BRAINTREE_PUBLIC_KEY
                    }
            
            
            return render(request, self.template_name, context)
    

    def post(self, request):
        user = request.user
        address_instance = None
        address_id = request.POST.get('address_id')
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        shipping_choice = request.POST.get('shipping_choice')

        # Default to first saved address
        selected_address = saved_addresses.first()
        use_billing_as_shipping = False

        use_billing_as_shipping = request.POST.get('use_billing_as_shipping') == "true"
        request.session['use_billing_as_shipping'] = use_billing_as_shipping

        billing_address_id = request.session.get("selected_billing_address_id")
        billing_address = PopUpCustomerAddress.objects.filter(id=billing_address_id, customer=user).first()

        # expiry time for user to buy product before it becomes available to others again
        expiry_str = request.session.get('buy_now_expiry')
        if expiry_str:
            expiry_time = parse_datetime(expiry_str)
            if now() > expiry_str:
                # release product
                for pid in cart.cart.keys():
                    try:
                        product = PopUpProduct.objects.get(id=pid)
                        product.inventory_status = 'in_inventory'
                        product.save()
                    except PopUpProduct.DoesNotExist:
                        continue
                
                # Clear session + cart
                cart.clear()
                del request.session['buy_now_expiry']
                request.sesion.modified = True
                messages.error(request, "Your reservation expired. Please try again")
                return redirect('action:products')
        


        # If the form isn't valid, re-render the page with the forms filled in
        # cart = Cart(request)
        cart = PopUpCartItem.objects.filter(user=request.user)
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        address_form = PopUpUpdateShippingInformationForm(instance=address_instance)
        edit_address_form = PopUpUpdateShippingInformationForm()
        client_token = gateway.client_token.generate()

        context = {
            # "form": form,  # whichever one failed validation
            "billing_address":billing_address,
            "edit_address_form": edit_address_form,
            "address_form": address_form,
            "saved_addresses": saved_addresses,
            "selected_address": selected_address,
            "use_billing_as_shipping": use_billing_as_shipping,
            "client_token": client_token,
            "braintree_public_key": settings.BRAINTREE_PUBLIC_KEY
        }
        return render(request, self.template_name, context)
    


def buy_now_add_to_cart(request, slug):
    product = get_object_or_404(PopUpProduct, slug=slug, is_active=True)
    
    # check if already sold/reserved | CREATE A PAGE FOR THIS - > ITEM HAS BEEN PURCHASED OR IN THE PROCESS OF BEING PURCHASED
    if product.inventory_status != 'in_inventory':
        return redirect('auction:product_detail', slug=slug)
    
    # Lock the product
    product.inventory_status = 'reserved'
    product.reserved_at = now()
    product.save()

    cart = Cart(request)
    cart.add(product=product, qty=1, auction_locked=True, buy_now=True)
    # cart.add(product=product, qty=1, buy_now=True) # need to add buy_now to cart

    # Save a 10 min expirty in session
    request.session['buy_now_expiry'] = (now() + timedelta(minutes=10)).isoformat()
    request.session.modified = True

    return redirect('payment:payment_home')



class ShippingAddressView(LoginRequiredMixin, View):
    template_name = "payment/shipping_address.html"
    def post(self, request):
        user = request.user
        address_instance = None
        address_id = request.POST.get('address_id')
        selected_address_id = request.POST.get('selected_address') 
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        selected_address = saved_addresses.first()

        if selected_address_id:
            handle_selected_address(
                request, 
                user, 
                selected_address_id,
                'selected_address_id', 
                'Shipping address selected successfully.'
            )
            return redirect('payment:payment_home')

        if address_id:
            updated_address, form = handle_update_address(
                request, PopUpUpdateShippingInformationForm,
                address_id, user,
                'is_default_shipping',
                'is_default_shipping',
                'selected_address_id',
                'Shipping address updated successfully.'
            )
            if updated_address:
                return redirect('payment:payment_home')
        else:
            new_address, form = handle_new_address(
                request, PopUpUpdateShippingInformationForm, user,
                'is_default_shipping',
                'is_default_shipping',
                'selected_address_id',
                'Shipping address added successfully.'

            )
            if new_address:
                return redirect('payment:payment_home')
        
        address_form = PopUpUpdateShippingInformationForm()
        edit_address_form = PopUpUpdateShippingInformationForm(instance=updated_address if address_id else None)


        # If the form isn't valid, re-render the page with the forms filled in
        cart = Cart(request)
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)        
        address_form = PopUpUpdateShippingInformationForm(instance=address_instance)
        edit_address_form = PopUpUpdateShippingInformationForm()

        context = {
            "form": form,  # whichever one failed validation
            "edit_address_form": edit_address_form,
            "address_form": address_form,
            "saved_addresses": saved_addresses,
            "selected_address": selected_address,
        }
        return render(request, self.template_name, context)

    def get(self, request):
        user = request.user
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        default_address = saved_addresses.filter(default=True).first()
        address_form = PopUpUpdateShippingInformationForm(instance=default_address)
        edit_address_form = PopUpUpdateShippingInformationForm()

        context = {
            "saved_addresses": saved_addresses,
            "address_form": address_form,
            "edit_address_form": edit_address_form
        }

        return render(request, self.template_name, context)
    


class BillingAddressView(LoginRequiredMixin, View):
    template_name = "payment/billing_address.html"

    def post(self, request):
        user = request.user
        address_instance = None
        address_id = request.POST.get('address_id')
        selected_address_id = request.POST.get('selected_address') 
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        selected_address = saved_addresses.first()

        if selected_address_id:
            handle_selected_address(
                request, 
                user, 
                selected_address_id,
                'selected_billing_address_id', 
                'Shipping address selected successfully.'
            )
            return redirect('payment:payment_home')

        if address_id:
            updated_address, form = handle_update_address(
                request, PopUpUpdateShippingInformationForm,
                address_id, user,
                'is_default_billing',
                'is_default_billing',
                'selected_billing_address_id',
                'Shipping address updated successfully.'
            )
            if updated_address:
                return redirect('payment:payment_home')
        else:
            new_address, form = handle_new_address(
                request, PopUpUpdateShippingInformationForm, user,
                'is_default_billing',
                'is_default_billing',
                'selected_billing_address_id',
                'Shipping address added successfully.'

            )
            if new_address:
                return redirect('payment:payment_home')
        
        address_form = PopUpUpdateShippingInformationForm()
        edit_address_form = PopUpUpdateShippingInformationForm(instance=updated_address if address_id else None)

        use_billing_as_shipping = request.POST.get('use_billing_as_shipping') == "true"
        request.session['use_billing_as_shipping'] = use_billing_as_shipping
        

        # If the form isn't valid, re-render the page with the forms filled in
        cart = Cart(request)
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)        
        address_form = PopUpUpdateShippingInformationForm(instance=address_instance)
        edit_address_form = PopUpUpdateShippingInformationForm()

        context = {
            "form": form,  # whichever one failed validation
            "edit_address_form": edit_address_form,
            "address_form": address_form,
            "saved_addresses": saved_addresses,
            "selected_address": selected_address,
            "use_billing_as_shipping": use_billing_as_shipping
        }
        return render(request, self.template_name, context)

    def get(self, request):
        user = request.user

        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        default_address = saved_addresses.filter(default=True).first()
        billing_address_id = request.session.get("selected_billing_address_id")
        billing_address = PopUpCustomerAddress.objects.filter(id=billing_address_id, customer=user).first()
        address_form = PopUpUpdateShippingInformationForm(instance=billing_address if billing_address else default_address)
        edit_address_form = PopUpUpdateShippingInformationForm()

        context = {
            "saved_addresses": saved_addresses,
            "address_form": address_form,
            "edit_address_form": edit_address_form
        }

        return render(request, self.template_name, context)





@require_POST
@login_required
def set_billling_address(request):
    data = json.load(request.body)
    address_id = data.get('address_id')
    address = get_object_or_404(PopUpCustomerAddress, id=address_id, user=request.user)
    request.uer.default = address
    request.user.save()
    return JsonResponse({"status": 'ok'})

        

@method_decorator(csrf_exempt, name='dispatch')
class CreatePaymentIntentView(View):
    def post(self, request, *args, **kwargs):
        user = request.user
        customer_id = request.user.stripe_customer_id
        cart = Cart(request)

        try:
            data = json.loads(request.body)
        
            amount = data.get('amount')

            if not amount:
                return JsonResponse({"error": "Missing amount"}, status=400)
            
            else:
        
                stripe.api_key = settings.STRIPE_SECRET_KEY

                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency='usd',
                    automatic_payment_methods={"enabled": True},  # Enable Apple Pay, Google Pay, etc.
                )
                return JsonResponse({'clientSecret': intent['client_secret']})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def stripe_webhook_view(request):
    print('stripe_webhook_view called')
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)
    
    # Reject test events in live mode
    if getattr(settings, "STRIPE_LIVE_MODE", False) and not event.get('livemode', False):
        logger.warning("⚠️ Received test webhook in live mode — rejecting")
        return HttpResponse(status=400)

    # Handle successful payment
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        payment_reference = intent['id']
        # 🛑 Warn if payment_reference not found in DB
        if not PopUpPayment.objects.filter(payment_reference=payment_reference).exists():
            logger.error(f"⚠️ Webhook received unknown payment_reference: {payment_reference}")
        


         # 🟨 SAFELY Extract AVS Results
        try:
            charge_data = intent['charges']['data'][0]
            checks = charge_data['payment_method_details']['card']['checks']
            avs_result = checks.get('address_line1_check', 'unavailable')
            zip_check = checks.get('address_postal_code_check', 'unavailable')
        except (KeyError, IndexError, TypeError):
            avs_result = 'unavailable'
            zip_check = 'unavailable'

        # 📝 Optionally: log/store/check AVS/ZIP results
        logger.info(f"AVS Check: {avs_result}, ZIP Check: {zip_check}")        

        # Update your payment record
        try:
            payment = PopUpPayment.objects.get(payment_reference=payment_reference)
            if payment.is_suspicious():
                payment.suspicious_flagged = payment.is_suspicious()
                payment.save()
                logger.warning(f"Suspicious payment: {payment.pk}")
                
            if payment.status != 'paid':
                payment.status = 'paid'
                # Optional: save AVS info
                payment.avs_result = avs_result
                payment.zip_check = zip_check
                payment.save()
        except PopUpPayment.DoesNotExist:
            pass
        
            # Trigger shipping workflow, email, etc.

    elif event['type'] == 'payment_intent.payment_failed':
        intent = event['data']['object']
        payment_reference = intent['id']

        # 🛑 Warn if payment_reference not found in DB
    if not PopUpPayment.objects.filter(payment_reference=payment_reference).exists():
        logger.error(f"⚠️ Webhook received unknown payment_reference: {payment_reference}")
        payment = PopUpPayment.objects.filter(payment_reference=payment_reference).first()

        if payment:
            payment.status = 'failed'
            payment.save()
    
    elif event['type'] == 'charge.dispute.created':
        charge = event['data']['object']['charge']
        payment = PopUpPayment.objects.filter(payment_reference=charge).first()
        if payment:
            payment.status = 'disputed'
            payment.save()
            send_dispute_alert_to_customer(payment.order)

    return HttpResponse(status=200)



@method_decorator(csrf_exempt, name='dispatch')
class ProcessVenmoPaymentView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            nonce = data.get('payment_method_nonce')
            amount = data.get('amount') / 100
            
            # Process payment with Braintree
            result = gateway.transaction.sale({
                "amount": str(amount),
                "payment_method_nonce": nonce,
                "options": {
                    "submit_for_settlement": True
                }
            })
            
            if result.is_success:
                transaction_id = result.transaction.id
                return JsonResponse({
                    'success': True, 
                    'transaction_id': transaction_id
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Payment failed'
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



class NowPaymentsService:
    """Service class for NowPayments API Interactions"""
    def __init__(self):
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.base_url = NOWPAYMENTS_BASE_URL
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_available_currencies(self):
        """Get list of available cryptocurrencies"""
        try:
            response = requests.get(f'{self.base_url}/currencies', headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'Error Fetching Currencies: {e}')
            return None
    
    def get_estimate(self, amount, currency_from='usd', currency_to='dai'):
        """Get payment estiamte"""
        try:
            params = {
                'amount': amount,
                'currency_from': currency_from,
                'currency_to': currency_to
            }
            response = requests.get(f'{self.base_url}/estimate', headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting estimate: {e}")
            return None
    
    def create_payment(self, payment_data):
        """Create a new payment"""
        try:
            response = requests.post(f'{self.base_url}/payment', headers=self.headers, json=payment_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error creating payment: {e}")
            return None
    
    def get_payment_status(self, payment_id):
        """Get payment status"""
        try:
            response = requests.get(f'{self.base_url}/payment/{payment_id}', headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting payment status: {e}")
            return None


@login_required
@require_http_methods(['POST'])
def create_nowpayments_payment(request):
    """Create Initial NowPayments Payment"""
    try:
        data = json.loads(request.body)
        print('create_nowpayments_payment data', data)

        #Validate required fields
        required_fields = ['price_amount', 'price_currency', 'order_id']
        for field in required_fields:
            if field not in data:
                return JsonResponse({ 'success': False, 'error': f'Missing required field: {field}'})
        
        # Intitialize NowPayments Service
        np_service = NowPaymentsService()

        # Get available currencies to verify DAI and USDC are supported
        currencies = np_service.get_available_currencies()
        if not currencies:
            return JsonResponse({
                'success': False, 'error': 'Unable to fetch available currencies'
            })

        # Check if DAI and USDC are available
        available_currencies = currencies.get('currencies', [])
        supported_stablecoins = ['dai', 'usdc']
        available_stablecoins = [curr for curr in supported_stablecoins if curr in available_currencies]

        if not available_stablecoins:
            return JsonResponse({
                'success': False,
                'error': 'DAI and USDC are not currently available'
            })
        
        # Store payment data in session for later user
        request.session['pending_payment'] = {
            'order_id': data['order_id'],
            'price_amount': data['price_amount'],
            'price_currency': data['price_currency'],
            'user_id': data.get('user_id'),
            'billing_address': data.get('billing_address'),
            'shipping_address': data.get('shipping_address'),
            'order_description': data.get('order_description', 'Purchase order')
        }
        return JsonResponse({
            'success': True, 'payment_data': {
                'available_currencies': available_stablecoins,
                'order_id': data['order_id'],
                'amount': data['price_amount']
                }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f'Error in create_nowpayments_payment: {e}')
        return JsonResponse({"success": False, "error": "Internal server error"})


@login_required
@require_http_methods(["POST"])
def finalize_nowpayments_payment(request):
    """Finalize NowPayments Payment With Selected Currency"""
    try:
        data = json.loads(request.body)

        # Get stored payment data from session
        pending_payment = request.session.get('pending_payment')
        if not pending_payment:
            return JsonResponse({
                'success': False,
                'error': 'No pending payment found'
            })
        pay_currency = data.get('pay_currency', '').lower()
        if pay_currency not in ['dai', 'usdc']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid Payment Currency'
            })
        
        # Initialize NowPayments service
        np_service =NowPaymentsService()

        # Get estimate for the payment
        estiamte = np_service.get_estimate(
            amount=pending_payment['price_amount'],
            currency_from=pending_payment['price_currency'].lower(),
            currency_to=pay_currency
        )

        if not estiamte:
            return JsonResponse({
                'success': False,
                'error': 'Unable to get payment estimate'
            })
        
        # Prepare payment data for NowPayments
        payment_data = {
            'price_amount': float(pending_payment['price_amount']),
            'price_currency': pending_payment['price_currency'].lower(),
            'pay_currency': pay_currency,
            'order_id': pending_payment['order_id'],
            'order_description': pending_payment['order_description'],
            'success_url': request.build_absolute_uri('/payment/success/'),
            'cancel_url': request.build_absolute_uri('/checkout/'),
            'case': 'success'
        }

        payment_response = np_service.create_payment(payment_data)
        if not payment_response:
            return JsonResponse({
                'success': False,
                'error': 'Failed to create payment with NowPayments'
            })
        
        # Store payment info in session
        request.session['active_payment'] = {
            'payment_id': payment_response['payment_id'],
            'order_id':  pending_payment['order_id'],
            'pay_currency': pay_currency,
            'pay_amount': payment_response['pay_amount'],
            'pay_address': payment_response['pay_address'],
            'price_anount': pending_payment['price_amount'],
            'user_id': pending_payment['user_id'],
            'billing_address': pending_payment['billing_address'],
            'shipping_address': pending_payment['shipping_address']
        }

        return JsonResponse({
            'success': True,
            'payment_info': {
                'payment_id': payment_response['payment_id'],
                'pay_amount': payment_response['pay_amount'],
                'pay_currency': pay_currency.upper(),
                'pay_address': payment_response['pay_address'],
                'price_amount': pending_payment['price_amount'],
                'time_limit': '15:00', # 15 minuts default
                'qr_code_url': payment_response.get('qr_code_url') 

            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Error in finalize_nowpayments_payment: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})


@login_required
@require_http_methods(["GET"])
def check_nowpayments_status(request, payment_id):
    """Check payment status"""
    try:
        # Verify this payment belongs to the current user's session
        active_payment = request.session.get('active_payment')
        
        if not active_payment or active_payment['payment_id'] != payment_id:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid payment ID'
            })
        
        # Initialize NowPayments service
        np_service = NowPaymentsService()
        
        # Get payment status from NowPayments
        status_response = np_service.get_payment_status(payment_id)
        
        if not status_response:
            return JsonResponse({
                'success': False, 
                'error': 'Unable to check payment status'
            })
        
        payment_status = status_response.get('payment_status', 'unknown')
        
        # Map NowPayments statuses to our frontend statuses
        status_mapping = {
            'waiting': 'waiting',
            'confirming': 'confirming', 
            'confirmed': 'confirmed',
            'sending': 'confirming',
            'partially_paid': 'waiting',
            'finished': 'finished',
            'failed': 'failed',
            'refunded': 'failed',
            'expired': 'expired'
        }
        
        mapped_status = status_mapping.get(payment_status, payment_status)
        
        return JsonResponse({
            'success': True,
            'status': mapped_status,
            'payment_info': {
                'payment_id': payment_id,
                'payment_status': payment_status,
                'pay_amount': status_response.get('pay_amount'),
                'actually_paid': status_response.get('actually_paid'),
                'pay_currency': status_response.get('pay_currency'),
                'created_at': status_response.get('created_at'),
                'updated_at': status_response.get('updated_at')
            }
        })
        
    except Exception as e:
        logger.error(f"Error in check_nowpayments_status: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

@csrf_exempt
@require_http_methods(["POST"])
def nowpayments_webhook(request):
    """Handle NowPayments webhook notifications"""
    try:
        # Verify webhook signature
        signature = request.headers.get('x-nowpayments-sig')
        if not signature:
            return JsonResponse({'error': 'Missing signature'}, status=400)
        
        # Calculate expected signature
        payload = request.body
        expected_signature = hmac.new(
            NOWPAYMENTS_IPN_SECRET.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid webhook signature")
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Parse webhook data
        webhook_data = json.loads(payload.decode('utf-8'))
        
        payment_id = webhook_data.get('payment_id')
        payment_status = webhook_data.get('payment_status')
        order_id = webhook_data.get('order_id')
        
        logger.info(f"Webhook received: payment_id={payment_id}, status={payment_status}")
        
        # Handle different payment statuses
        if payment_status in ['finished', 'confirmed']:
            # Payment successful - you might want to trigger order creation here
            # or update your database with the successful payment
            pass
        elif payment_status in ['failed', 'refunded', 'expired']:
            # Payment failed - log and potentially notify user
            logger.warning(f"Payment failed: {payment_id} - {payment_status}")
        
        # Always return 200 to acknowledge receipt
        return JsonResponse({'status': 'ok'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in nowpayments_webhook: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)



# Additional utility function for testing
@login_required
def test_nowpayments_connection(request):
    """Test NowPayments API connection"""
    try:
        np_service = NowPaymentsService()
        currencies = np_service.get_available_currencies()
        
        if currencies:
            return JsonResponse({
                'success': True,
                'message': 'NowPayments connection successful',
                'available_currencies': len(currencies.get('currencies', [])),
                'dai_available': 'dai' in currencies.get('currencies', []),
                'usdc_available': 'usdc' in currencies.get('currencies', [])
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to connect to NowPayments API'
            })
            
    except Exception as e:
        logger.error(f"Error testing NowPayments connection: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Connection test failed: {str(e)}'
        })
    


def generate_client_token(request):
    client_token = gateway.client_token.generate()
    return JsonResponse({'client_token': client_token})


# class PlacedOrderView(LoginRequiredMixin, View):
#     model = PopUpProduct
#     template_name = 'payment/placed-order.html'
#     context_object_name = 'product'

#     def get_queryset(self):
#         """Filter items based on slug if selected"""
#         base_queryset = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit")
#         slug = self.kwargs.get('slug')
#         if slug:
#             product_type = get_object_or_404(PopUpProduct, slug=slug)
#             return base_queryset.filter(product_type=product_type)
#         return base_queryset

#     def get_context_data(self, **kwargs):
#         """Add product type and product_types to context"""
#         context =  super().get_context_data(**kwargs)

#         """Always include all product_types"""
#         context['product_type'] = PopUpProductType.objects.all()
#         slug = self.kwargs.get('slug')
#         if slug:
#             context['product_type'] = get_object_or_404(PopUpProductType, slug=slug)
#         else:
#             context['product_type'] = None
        
#         return context



def placed_order(request):
    user = request.user
    cart = Cart(request)
    cart.clear()
    order = PopUpCustomerOrder.objects.filter(user=user).first()
    order_id = None
    if order:
        order_id = order.id
    print('order_id', order_id)
    base_queryset = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit")
    return render(request, 'payment/placed_order.html', {'user': user, 'order_id':order_id, 'product': base_queryset})



