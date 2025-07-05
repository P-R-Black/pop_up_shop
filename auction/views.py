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
from django.utils.timezone import now
from django.db.models import Q
from decimal import Decimal
from django.db import transaction
from cart.cart import Cart
from pop_accounts.forms import ThePopUpUserAddressForm, PopUpUpdateShippingInformationForm


# Create your views here.
class AllAuctionView(View):
    template_name = 'auction/auction.html'

    def get(self, request):
        addresses = PopUpCustomerAddress.objects.filter(customer=request.user.id, default=True)
        user_zip = "".join([a.postcode for a in addresses])

        in_auction = []
        product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(
            is_active=True, inventory_status="in_inventory")   
        product_specifications = None
    
        for p in product:
            if p.auction_status == "Ongoing":
                if p.is_auction_phase():
                    in_auction.append(p)
                    product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=p)}

        quick_bid_increments = [10, 20, 30]

        for a in in_auction:
            print('in_auct', a)

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
        floor_price = product.reserve_price
        print('floor_price', floor_price)

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
    
        

class ProductsView(ListView):
    model = PopUpProduct
    template_name = 'auction/products.html'
    context_object_name = 'product'

    def get_queryset(self):
        """Filter products based on slug if provided"""
        current_time = now()
        
        base_queryset = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set'
        ).filter(
            is_active=True,
            inventory_status__in=['in_inventory', 'reserved']
        ).filter(
            buy_now_start__lte=now(),
            buy_now_end__gte=now()
        )
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
        product = self.get_object
        print('get_context_data product', product)

        product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=self.object)}
        context['product_specifications'] = product_specifications

        # Buy Now Logic
        now_ = now()
        buy_now_start = getattr(product, "buy_now_start", None)
        buy_now_end = getattr(product, "buy_now_end", None)

        context['is_buy_now_available'] = (
            buy_now_start and buy_now_end and 
            buy_now_start <= now_ <= buy_now_end and not 
            getattr(product, "bought_now", False)
        )
        return context
