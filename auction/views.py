from django.contrib import messages
from django.views.generic import DetailView, ListView
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
# from .utils import get_state_tax_rate


# Create your views here.
class AllAuctionView(View):
    template_name = 'auction/auction.html'

    def get(self, request):
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
        context = {
            "in_auction": in_auction, "product_specifications": product_specifications, 
            "quick_bid_increments": quick_bid_increments, "user_zip":user_zip
        }
        return  render(request, self.template_name, context)
    
    def post(self, request):
        return render(request, self.template_name)
    


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
      


class ProductAuctionView(DetailView):
    model = PopUpProduct
    template_name = 'auction/product_auction.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        """Override to add the is_active filter"""
        return get_object_or_404(PopUpProduct, slug=self.kwargs['slug'], is_active=True)
    
    def get_context_data(self, **kwargs):
        """Add product specification to the context"""
        context = super().get_context_data(**kwargs)
        product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=self.object)}
        context['product_specifications'] = product_specifications
        return context
    


# class OptionalLoginMixin(AccessMixin):
#     """
#     Allow both authenticated and anonymous users.
#     Provides 'self.request.user.is_authenticated' for view logic.
#     """
#     def dispatch(self, request, *args, **kwargs):
#         # Dont redirect
#         return super().dispatch(request, *args, **kwargs)


# class ProductBuyView(OptionalLoginMixin, View):
#     template_name = 'auction/product_buy.html'
    
#     def get(self, request):
#         if not request.user.is_authenticated:
#             cart = Cart(request)
#             # 1. Collect product IDs in the cart
#             ids_in_cart = [int(pid) for pid in cart.cart.keys()]

#             # 2 Fetch products ounce with needed data
#             products = (
#                 PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
#                 .prefetch_related('popupproductspecificationvalue_set')
#             )

#             product_map = {p.id: p for p in products}

#             # 3 Build "enriched" cart rows
#             enriched_cart = []
#             for pid, item in cart.cart.items():
#                 pid_int = int(pid)
#                 product = product_map.get(pid_int)
#                 if not product:
#                     continue # shouldn't happen, but just to be safe

#                 enriched_cart.append({
#                     "product": product,
#                     "specs": list(product.popupproductspecificationvalue_set.all()),
#                     "qty": item["qty"],
#                     "unit_price": Decimal(item["price"]),
#                     "line_total": Decimal(item["price"]) * item["qty"],
#                 })

            
#             # 4 Item quantity in cart
#             cart_length = len(cart)

#             # 5. Shipping Standard
#             standard_shipping = 1499
        
#             # 6. Totals
#             subtotal = cart.get_subtotal_price()
            
#             # enriched_cart = build_enriched_cart(cart)  # helper you already have
#             cart_length = len(cart)

#             # Shared context for everyone (guest or auth'd)
#             context = {
#                 "cart_items": enriched_cart,
#                 "cart_length": cart_length,
#                 "cart_total": cart.get_total_price(),
#                 "cart_subtotal": subtotal
#             }
#             return render(request, self.template_name, context)
        
#         if request.user.is_authenticated:
#             user = request.user
#             cart = Cart(request)


#             saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
#             default_address = saved_addresses.filter(default=True).first()
#             address_form = PopUpUpdateShippingInformationForm(instance=default_address)
#             edit_address_form = PopUpUpdateShippingInformationForm()


#             selected_address = None
#             selected_address_id = request.session.get('selected_address_id')
            

#             if selected_address_id:
#                 try:
#                     selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
#                     address_form = PopUpUpdateShippingInformationForm(instance=selected_address)
#                 except PopUpCustomerAddress.DoesNotExist:
#                     selected_address = None        
            
#             total = "{:.2f}".format(cart.get_total_price())
#             total = total.replace('.', '')
#             total = int(total)


#             # user_state = selected_address.state if selected_address else default_address.state
#             user_state = (selected_address or default_address).state if (selected_address or default_address) else "FL"

#             tax_rate =  get_state_tax_rate(user_state)
        
#             # 1. Collect product IDs in the cart
#             ids_in_cart = [int(pid) for pid in cart.cart.keys()]

#             # 2 Fetch products ounce with needed data
#             products = (
#                 PopUpProduct.objects.filter(id__in=ids_in_cart, is_active=True, inventory_status='in_inventory')
#                 .prefetch_related('popupproductspecificationvalue_set')
#             )

#             product_map = {p.id: p for p in products}

#             # 3 Build "enriched" cart rows
#             enriched_cart = []
#             for pid, item in cart.cart.items():
#                 pid_int = int(pid)
#                 product = product_map.get(pid_int)
#                 if not product:
#                     continue # shouldn't happen, but just to be safe

#                 enriched_cart.append({
#                     "product": product,
#                     "specs": list(product.popupproductspecificationvalue_set.all()),
#                     "qty": item["qty"],
#                     "unit_price": Decimal(item["price"]),
#                     "line_total": Decimal(item["price"]) * item["qty"],
#                 })

            
#             # 4 Item quantity in cart
#             cart_length = len(cart)

#             # 5. Shipping Standard
#             standard_shipping = 1499
        
#             # 6. Totals
#             subtotal = cart.get_subtotal_price()
            
#             processing_fee = Decimal(2.50) if cart_length > 0 else Decimal(0.00)
#             sales_tax = subtotal * Decimal(tax_rate)
#             subtotal_plus_tax = subtotal + sales_tax
#             order_shipping_chart = (Decimal((standard_shipping) / 100) * cart_length)

#             grand_total =  subtotal_plus_tax +  order_shipping_chart + processing_fee if cart_length > 0 else 0
            
#             context = {"user": user, 
#                     "cart_items": enriched_cart, 
#                     "cart_subtotal": subtotal, 
#                     "shipping_cost": standard_shipping, 
#                     "cart_total": grand_total,
#                     "cart_length": cart_length,
#                     "sales_tax": f'{sales_tax:.2f}',
#                     "processing_fee": f'{processing_fee:.2f}',
#                     "grand_total": f"{grand_total:.2f}",
#                     "address": default_address,
#                     "address_form": address_form,
#                     "edit_address_form":edit_address_form,
#                     "saved_addresses": saved_addresses,
#                     "selected_address": selected_address,
#                     "tax_rate":tax_rate
#                     }
            
            
#             return render(request, self.template_name, context)
    

#     def post(self, request):
#         user = request.user
#         address_instance = None
#         address_id = request.POST.get('address_id')

#         shipping_choice = request.POST.get('shipping_choice')

#         # Case 1: User selected an existing address
#         selected_address_id = request.POST.get('selected_address')
        
       
#         if selected_address_id:
#             try:
#                 selected_address = PopUpCustomerAddress.objects.get(id=selected_address_id, customer=user)
#                 request.session['selected_address_id'] = str(selected_address.id)
#                 messages.success(request, "Address selected successfully")
#             except PopUpCustomerAddress.DoesNotExist:
#                 messages.error(request, "The selected address could not be found.")
#             return redirect('auction:product_buy')
       
#         # Case 2: User updates an existing address
#         if address_id:
#             try:
#                 address_instance = PopUpCustomerAddress.objects.get(id=address_id, customer=user)
#             except PopUpCustomerAddress.DoesNotExist:
#                 messages.error(request, "Address not found")
#                 return redirect('auction:product_buy')
            
#             form =  PopUpUpdateShippingInformationForm(request.POST, instance=address_instance)
#             if form.is_valid():
#                 print('"==== updating address ===', address_id)
#                 updated_address = form.save()
#                 request.session['selected_address_id'] = str(updated_address.id)
#                 messages.success(request, "Address updated successfully.")
#                 return redirect('auction:product_buy')
#             else:
#                 print('"==== Form errors ===', form.errors)
#                 messages.error(request, "Please correct the errors below.")
#         else:
#             # Case 3: User adds a new address
#             form = PopUpUpdateShippingInformationForm(request.POST)
#             if form.is_valid():
#                 new_address = form.save(commit=False)
#                 new_address.customer = user
#                 new_address.save()
#                 request.session["selected_address_id"] = str(new_address.id)
#                 messages.success(request, "Address added successfully.")
#                 return redirect('auction:product_buy')
#             else:
#                 messages.error(request, "Please correct the errors below.")
        

#         # If the form isn't valid, re-render the page with the forms filled in
#         cart = Cart(request)
#         saved_addresses = PopUpCustomerAddress.objects.filter(customer=user)
#         address_form = PopUpUpdateShippingInformationForm(instance=address_instance)
#         edit_address_form = PopUpUpdateShippingInformationForm()
                

#         context = {
#             "form": form,  # whichever one failed validation
#             "edit_address_form": edit_address_form,
#             "address_form": address_form,
#             "saved_addresses": saved_addresses,
#         # + other cart context
#         }
#         return render(request, self.template_name, context)
        



class ProductsView(ListView):
    model = PopUpProduct
    template_name = 'auction/products.html'
    context_object_name = 'product'

    def get_queryset(self):
        """Filter products based on slug if provided"""
        base_queryset = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=True, inventory_status="in_inventory")
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            return base_queryset.filter(product_type=product_type)
        return base_queryset
    
    def get_context_data(self, **kwargs):
        """Add product_types and product_type to context"""
        context = super().get_context_data(**kwargs)

        # Always include all product types
        context['product_types'] = PopUpProductType.objects.all()

        # Include the current product_type if slug is provided
        slug = self.kwargs.get('slug')
        if slug:
            context['product_type'] = get_object_or_404(PopUpProductType, slug=slug)
        else:
            context['product_type'] = None
        
        return context



class ComingSoonView(ListView):
    model = PopUpProduct
    template_name = "auction/coming_soon.html"
    context_object_name = "product"

    def get_queryset(self):
        """Filter items based on slug if selected"""
        base_queryset = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit")
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProduct, slug=slug)
            return base_queryset.filter(product_type=product_type)
        return base_queryset

    def get_context_data(self, **kwargs):
        """Add product type and product_types to context"""
        context =  super().get_context_data(**kwargs)

        """Always include all product_types"""
        context['product_type'] = PopUpProductType.objects.all()
        slug = self.kwargs.get('slug')
        if slug:
            context['product_type'] = get_object_or_404(PopUpProductType, slug=slug)
        else:
            context['product_type'] = None
        
        return context


class FutureReleases(ListView):
    model = PopUpProduct
    template_name = "auction/future_releases.html"
    context_object_name = "product"

    def get_queryset(self):
        """Filter items based on slug if selected"""
        base_queryset = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="anticipated")
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            return base_queryset.filter(product_type=product_type)
        return base_queryset
    
    def get_context_data(self, **kwargs):
        """Add product type and product_types to context"""
        context = super().get_context_data(**kwargs)

        """Always include all product_types"""
        context['product_type'] = PopUpProductType.objects.all()
        slug = self.kwargs.get('slug')
        if slug:
            context['product_type'] = get_object_or_404(PopUpProductType, slug=slug)
        else:
            context['product_typ'] = None
        
        return context


class ProductDetailView(DetailView):
    model = PopUpProduct
    template_name = "auction/product_detail.html"
    context_object_name = "product"
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


    def get_object(self, queryset=None):
        """Override to add the is_active filter"""
        return get_object_or_404(PopUpProduct, slug=self.kwargs['slug'], is_active=True)
    
    def get_context_data(self, **kwargs):
        """Add product specification to the context"""
        context = super().get_context_data(**kwargs)
        product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=self.object)}
        context['product_specifications'] = product_specifications
        return context






