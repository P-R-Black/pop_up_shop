from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from cart.cart import Cart
from django.http import JsonResponse
from auction.models import PopUpProduct, PopUpProductSpecificationValue, PopUpProductType
from pop_accounts.models import PopUpBid, PopUpCustomerAddress
from pop_accounts.forms import ThePopUpUserAddressForm, PopUpUpdateShippingInformationForm
import stripe
from django.conf import settings
import json
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.views import payment_confirmation
import os
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.views import View
from decimal import Decimal
from .utils.tax_utils import get_state_tax_rate
from .utils.address_form_handler import(handle_new_address, handle_selected_address, handle_update_address)




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
            # 1. Collect product IDs in the cart
            ids_in_cart = [int(pid) for pid in cart.cart.keys()]

            # 2 Fetch products ounce with needed data
            products = (
                PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
                .prefetch_related('popupproductspecificationvalue_set')
            )

            product_map = {p.id: p for p in products}

            # 3 Build "enriched" cart rows
            enriched_cart = []
            for pid, item in cart.cart.items():
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


            # Shared context for everyone (guest or auth'd)
            context = {
                "cart_items": enriched_cart,
                "cart_length": cart_length,
                "cart_total": cart.get_total_price(),
                "cart_subtotal": subtotal
            }
            return render(request, self.template_name, context)
        
        """ Cart view for user who is signed in"""
        if request.user.is_authenticated:
            user = request.user
            cart = Cart(request)
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
            ids_in_cart = [int(pid) for pid in cart.cart.keys()]

            # 2 Fetch products ounce with needed data
            products = (
                PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
                .prefetch_related('popupproductspecificationvalue_set')
            )

            product_map = {p.id: p for p in products}

            # 3 Build "enriched" cart rows
            enriched_cart = []
            for pid, item in cart.cart.items():
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
            # print('grand_total Decimal', f"{Decimal(grand_total):.2f}")
            # print('grand_total int', int(grand_total * 100))
            
            stripe.api_key = settings.STRIPE_SECRET_KEY

           
            print('grand_total_adjusted', grand_total_adjusted)

            # intent = stripe.PaymentIntent.create(
            #     amount=grand_total_adjusted,
            #     currency='usd',
            #     # customer=user.stripe_customer_id,
            #     payment_method_types=['card'],
            #     metadata={'userid': request.user.id}
            # )

            # print('intent', intent.client_secret)

            # setup_intent = stripe.SetupIntent.create(
            #     usage="on_session",
            #     amount=grand_total_adjusted,
            #     currency='usd',
            #     # customer=user.stripe_customer_id,
            #     payment_method_types=['card'],
            #     metadata={'userid': request.user.id}
            # )

            
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
                    # "client_secret": setup_intent.client_secret,
                    "STRIPE_PUBLIC_KEY": os.environ.get('STRIPE_PUBLIC_KEY'),
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
        


        # If the form isn't valid, re-render the page with the forms filled in
        cart = Cart(request)
        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        address_form = PopUpUpdateShippingInformationForm(instance=address_instance)
        edit_address_form = PopUpUpdateShippingInformationForm()

        context = {
            # "form": form,  # whichever one failed validation
            "billing_address":billing_address,
            "edit_address_form": edit_address_form,
            "address_form": address_form,
            "saved_addresses": saved_addresses,
            "selected_address": selected_address,
            "use_billing_as_shipping": use_billing_as_shipping
        }
        return render(request, self.template_name, context)
    



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



        # # Default to first saved address
        # selected_address = saved_addresses.first()
        


        # # Case 1: User selected an existing address
        # selected_address_id = request.POST.get('selected_address') 
        # if selected_address_id:
        #     try:
        #         selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
        #         request.session['selected_address_id'] = str(selected_address.id)
        #         messages.success(request, "Shipping Address selected successfully")
        #     except PopUpCustomerAddress.DoesNotExist:
        #         messages.error(request, "The selected address could not be found.")
        #     return redirect('payment:payment_home')
       
        # # Case 2: User updates an existing address
        # if address_id:
        #     try:
        #         address_instance = PopUpCustomerAddress.objects.get(id=address_id, customer=user)
        #     except PopUpCustomerAddress.DoesNotExist:
        #         messages.error(request, "Address not found")
        #         return redirect('payment:payment_home')
            
        #     form =  PopUpUpdateShippingInformationForm(request.POST, instance=address_instance)
        #     if form.is_valid():
        #         updated_address = form.save(commit=False)
        #         if form.cleaned_data.get('is_default_shipping'):
        #             # Unset previous default billing address for this user
        #             PopUpCustomerAddress.objects.filter(customer=user, is_default_shipping=True).update(is_default_shipping=False)
        #             updated_address.is_default_shipping = True
        #         else:
        #             updated_address.is_default_shipping = False
                
        #         updated_address.save()
        #         request.session['selected_address_id'] = str(updated_address.id)
        #         messages.success(request, "Shipping Address updated successfully.")
        #         return redirect('payment:payment_home')
        #     else:
        #         messages.error(request, "Please correct the errors below.")
        # else:
        #     # Case 3: User adds a new address
        #     form = PopUpUpdateShippingInformationForm(request.POST)
        #     if form.is_valid():
        #         new_address = form.save(commit=False)
        #         new_address.customer = user
        #         if form.cleaned_data.get('is_default_shipping'):
        #             # Unset previous default billing address for this user
        #             PopUpCustomerAddress.objects.filter(customer=user, is_default_shipping=True).update(is_default_shipping=False)
        #             new_address.is_default_shipping = True
        #         else:
        #             new_address.is_default_shipping = False
        #         new_address.save()
        #         request.session["selected_address_id"] = str(new_address.id)
        #         messages.success(request, "Shipping Address added successfully.")
        #         return redirect('payment:payment_home')
        #     else:
        #         messages.error(request, "Please correct the errors below.")
        

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

        # user = request.user
        # address_instance = None
        # address_id = request.POST.get('address_id')
        # saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)

        # # Default to first saved address
        # selected_address = saved_addresses.first()
        # use_billing_as_shipping = False
        
        # use_billing_as_shipping = request.POST.get('use_billing_as_shipping') == "true"
        # request.session['use_billing_as_shipping'] = use_billing_as_shipping


        # # Case 1: User selected an existing address
        # selected_address_id = request.POST.get('selected_address') 
        # if selected_address_id:
        #     try:
        #         selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
        #         request.session['selected_billing_address_id'] = str(selected_address.id)
        #         messages.success(request, "Billing Address selected successfully")
        #     except PopUpCustomerAddress.DoesNotExist:
        #         messages.error(request, "The selected address could not be found.")
        #     return redirect('payment:payment_home')
       
        # # Case 2: User updates an existing address
        # if address_id:
        #     try:
        #         address_instance = PopUpCustomerAddress.objects.get(id=address_id, customer=user)
        #     except PopUpCustomerAddress.DoesNotExist:
        #         messages.error(request, "Address not found")
        #         return redirect('payment:payment_home')
            
        #     form =  PopUpUpdateShippingInformationForm(request.POST, instance=address_instance)
        #     if form.is_valid():
        #         updated_address = form.save(commit=False)
        #         if form.cleaned_data.get('is_default_billing'):
        #             # Unset previous default billing address for this user
        #             PopUpCustomerAddress.objects.filter(customer=user, is_default_billing=True).update(is_default_billing=False)
        #             updated_address.is_default_billing = True
        #         else:
        #             updated_address.is_default_billing = False
                
        #         updated_address.save()
        #         request.session['selected_billing_address_id'] = str(updated_address.id)
        #         messages.success(request, "Billing Address updated successfully.")
        #         return redirect('payment:payment_home')
        #     else:
        #         messages.error(request, "Please correct the errors below.")
        # else:
        #     # Case 3: User adds a new address
        #     form = PopUpUpdateShippingInformationForm(request.POST)
        #     if form.is_valid():
        #         new_address = form.save(commit=False)
        #         new_address.customer = user
        #         if form.cleaned_data.get('is_default_billing'):
        #             # Unset previous default billing address for this user
        #             PopUpCustomerAddress.objects.filter(customer=user, is_default_billing=True).update(is_default_billing=False)
        #             new_address.is_default_billing = True
        #         else:
        #             new_address.is_default_billing = False
        #         new_address.save()
        #         request.session["selected_billing_address_id"] = str(new_address.id)
        #         messages.success(request, "Address added successfully.")
        #         return redirect('payment:payment_home')
        #     else:
        #         messages.error(request, "Please correct the errors below.")
        

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




@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    event = None

    try: 
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        print(e)
        return HttpResponse(status=400)

    # Hande the event
    if event.type == 'payment_intent.succeeded':
        payment_confirmation(event.data.object.client_secret)
    else:
        print('Unhandled event type{}'.format(event.type))
    
    return HttpResponse(status=200)


def placed_order(request):
    cart = Cart(request)
    cart.clear()
    return render(request, 'payment/placed_order.html')