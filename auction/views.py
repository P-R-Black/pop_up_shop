from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import PopUpProduct, PopUpProductSpecificationValue, PopUpProductType
from pop_accounts.models import PopUpBid, PopUpCustomerAddress
from django.utils.text import slugify
import json
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.views import View
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from cart.cart import Cart
from pop_accounts.forms import ThePopUpUserAddressForm, PopUpUpdateShippingInformationForm
from .utils import get_state_tax_rate

# Create your views here.
def all_auction_view(request):
    addresses = PopUpCustomerAddress.objects.filter(customer=request.user.id, default=True)
    user_zip = "".join([a.postcode for a in addresses])

    in_auction = []
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=True, inventory_status="in_inventory")   
    product_specifications = None
    
    for p in product:
        if p.auction_status == "Ongoing":
            in_auction.append(p)
            product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=p)}

    quick_bid_increments = [10, 20, 30]

    return render(request, 'auction/auction.html', {
        'in_auction': in_auction, 'product_specifications': product_specifications, 
        'quick_bid_increments': quick_bid_increments, 'user_zip': user_zip})


class AjaxLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'You must be logged in to place a bid'}, status=403)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class PlaceBidView(AjaxLoginRequiredMixin, View):
    """
    Recieves POST of bid_amount & product_id, creates a PopUpbids, and updates the products 
    bid_count and current_highest_bid
    """

    def post(self, request):            
        product_id = request.POST.get('product_id')
        bid_amount = request.POST.get('bid_amount')

        if not product_id or not bid_amount:
            return JsonResponse({"status": "error", "message": "Missing product or amount."}, status=400)
        
        try:
            bid_amount = Decimal(bid_amount)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid bid amount.'}, status=400)
        
        product = get_object_or_404(PopUpProduct, pk=product_id, is_active=True)
    
        # 2. Enforce that bid is strictly higher than current_highest_bid
        current = product.current_highest_bid or 0
        retail_price = product.retail_price

        if bid_amount <= float(retail_price):
            return JsonResponse({'status': 'error', 'message': f'Your bid must be better than ${retail_price:.2f}.',
                                },
                                status=400,
                                )

        elif bid_amount <= current:
            return JsonResponse({'status': 'error', 'message': f'Your bid must be better than ${current:.2f}.',
                                },
                                status=400,
                                )
        # 3. Create the bid
        bid = PopUpBid.objects.create(
            customer=request.user, 
            product=product,
            amount=bid_amount,
            timestamp=timezone.now()
        )            

        # 4 update product counters
        product.current_highest_bid = bid_amount            
        product.bid_count = product.bids.count()  # PopUpProduct.objects.filter(pk=product_id).count()
        product.save(update_fields=['current_highest_bid', 'bid_count'])
    

        return JsonResponse({
            'status': 'success',
            'new_highest': f'{bid_amount:.2f}',
            'bid_count': product.bid_count,
        })
      



def product_auction_view(request, slug, id=id):
    product = get_object_or_404(PopUpProduct, slug=slug, is_active=True)
    product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=product)
    }
    return render(request, 'auction/product_auction.html', {'product': product, 'product_specifications': product_specifications})



class ProductBuyView(LoginRequiredMixin, View):
    template_name = 'auction/product_buy.html'
    
    def get(self, request):
        user = request.user
        cart = Cart(request)

        saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
        default_address = saved_addresses.filter(default=True).first()
        address_form = PopUpUpdateShippingInformationForm(instance=default_address)
        edit_address_form = PopUpUpdateShippingInformationForm()


        selected_address = None
        selected_address_id = request.session.get('selected_address_id', None)
        
        if selected_address_id:
            try:
                selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
                address_form = PopUpUpdateShippingInformationForm(instance=selected_address)
            except PopUpCustomerAddress.DoesNotExist:
                selected_address = None        
        
        total = "{:.2f}".format(cart.get_total_price())
        total = total.replace('.', '')
        total = int(total)


        user_state = selected_address.state if selected_address else default_address.state
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
        shipping_cost = (Decimal(standard_shipping) * cart_length) / 100
        processing_fee = Decimal(2.50)

        sales_tax = subtotal * Decimal(tax_rate)
        subtotal_plus_tax = subtotal + sales_tax
        grand_total =  subtotal_plus_tax + shipping_cost + processing_fee

        
        context = {"user": user, 
                   "cart_items": enriched_cart, 
                   "cart_subtotal": subtotal, 
                   "shipping_cost": shipping_cost, 
                   "cart_total": grand_total,
                   "cart_length": cart_length,
                   "sales_tax": f'{sales_tax:.2f}',
                   "processing_fee": f'{processing_fee:.2f}',
                   "grand_total": "{:.2f}".format(grand_total),
                   "address": default_address,
                   "address_form": address_form,
                   "edit_address_form":edit_address_form,
                   "saved_addresses": saved_addresses,
                   "selected_address": selected_address
                   }

        return render(request, self.template_name, context)
    
    def post(self, request):
        user = request.user
        print('post called on ProductBuyView')
        address_id = request.POST.get('address_id')
       
        if address_id:
            try:
                address_instance = PopUpCustomerAddress.objects.get(id=address_id, customer=user)
            except PopUpCustomerAddress.DoesNotExist:
                messages.error(request, "Address not found")
                return redirect('auction:product_buy')
            
            form =  PopUpUpdateShippingInformationForm(request.POST, instance=address_instance)
            if form.is_valid():
                updated_address = form.save()
                request.session['selected_address_id'] = str(updated_address.id)
                messages.success(request, "Address updated successfully.")
                return redirect('auction:product_buy')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = PopUpUpdateShippingInformationForm(request.POST)
            if form.is_valid():
                new_address = form.save(commit=False)
                new_address.customer = user
                new_address.save()
                request.session["selected_address_id"] = str(new_address.id)
                messages.success(request, "Address added successfully")
                return redirect('auction:product_buy')
            else:
                messages.error(request, "Please correct the errors below.")
        

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
        # + other cart context
        }
        return render(request, self.template_name, context)
        



def products(request, slug=None):
    product_type = None
    product_types = PopUpProductType.objects.all()
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=True, inventory_status="in_inventory")
    if slug:
        product_type = get_object_or_404(PopUpProductType, slug=slug)
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=True, inventory_status="in_inventory", product_type=product_type)
    else:
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=True, inventory_status="in_inventory")
    
    return render(request, 'auction/products.html', {'product': product,  'product_types': product_types, 'product_type': product_type})


def coming_soon(request, slug=None):
    product_type = None
    product_types = PopUpProductType.objects.all()
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit")
    if slug:
        product_type = get_object_or_404(PopUpProductType, slug=slug)
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit", product_type=product_type)
    else:
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit")
    return render(request, 'auction/coming_soon.html', {'product': product, 'product_types': product_types, 'product_type': product_type})
        
        
        
def future_releases(request, slug=None):
    product_type = None
    product_types = PopUpProductType.objects.all()
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="anticipated")
    if slug:
        product_type = get_object_or_404(PopUpProductType, slug=slug)
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="anticipated", product_type=product_type)
    else:
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="anticipated")

    return render(request, 'auction/future_releases.html', {'product': product, 'product_types': product_types, 'product_type': product_type}) 


def product_detail(request, slug, id=id):
    product = get_object_or_404(PopUpProduct, slug=slug, is_active=True)
    product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=product)
    }
    return render(request, 'auction/product_detail.html', {'product': product, 'product_specifications':product_specifications})




