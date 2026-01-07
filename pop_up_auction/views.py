from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import PopUpProduct, PopUpProductSpecificationValue, PopUpProductType
from pop_accounts.models import  PopUpCustomerAddress, PopUpCustomerProfile, PopUpBid
# from pop_up_auction.models import PopUpBid
from django.utils.text import slugify
import json
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.views import View
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q
from decimal import Decimal, DecimalException
from django.db import transaction
from pop_accounts.utils.utils import  add_specs_to_products
from pop_up_order.models import PopUpOrderItem
from django.http import Http404
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='pop_up_auction.log', level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# Create your views here.
class AjaxLoginRequiredMixin(AccessMixin):
    # 🟢 View Test Completed
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated AND active
        if not request.user.is_authenticated or not request.user.is_active:
            if request.headers.get('X-requested-with') == 'XMLHttpRequest':
                # Provide error message
                if not request.user.is_authenticated:
                    message = "You must be logged in to place a bid"
                else:
                    message = "Your account is inactive. Please verify your email"
                return JsonResponse({'status': 'error', 'message': message}, status=403)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)



class AllAuctionView(View):
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 Mobile / Tablet Media Query Completed 

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

        context = {
            "in_auction": in_auction, "product_specifications": product_specifications, 
            "quick_bid_increments": quick_bid_increments, "user_zip":user_zip
        }
        return  render(request, self.template_name, context)
    
    def post(self, request):
        return render(request, self.template_name)
    


class PlaceBidView(AjaxLoginRequiredMixin, View):
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 Mobile / Tablet Media Query Completed
    """
    Handle AJAX bid submissions for an active product.

    This view:
      • Accepts a POST request containing `product_id` and `bid_amount`.
      • Validates that both fields exist and that `bid_amount` is a valid Decimal.
      • Fetches the active product or returns 404 if the product does not exist.
      • Ensures the bid is strictly higher than:
            - the product's retail_price, and
            - the current highest bid (if one exists).
      • Creates a new PopUpBid associated with the authenticated user.
      • Updates the product’s `current_highest_bid` and `bid_count`.
      • Returns a JSON response containing:
            - success/error status
            - validation messages when appropriate
            - the updated highest bid
            - the updated bid count

    This endpoint is intended for frontend AJAX usage and requires the user to be
    authenticated (via AjaxLoginRequiredMixin).
    """
   
    def post(self, request):            
        product_id = request.POST.get('product_id')
        bid_amount = request.POST.get('bid_amount')

        

        if not product_id or not bid_amount:
            return JsonResponse({"status": "error", "message": "Missing product or amount."}, status=400)
        
        try:
            bid_amount = Decimal(bid_amount)
        except (ValueError, DecimalException):
            return JsonResponse({'status': 'error', 'message': 'Invalid bid amount.'}, status=400)
        
        product = get_object_or_404(PopUpProduct, pk=product_id, is_active=True)
    
        # 2. Enforce that bid is strictly higher than current_highest_bid
        current = product.current_highest_bid or 0
        retail_price = product.retail_price
        floor_price = product.reserve_price
    

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
        profile = request.user.popupcustomerprofile
        bid = PopUpBid.objects.create(
            customer=profile, 
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
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 Mobile / Tablet Media Query Completed
    """
    Class-based view for displaying a product's auction page.

    Provides full product details along with real-time auction information, including:
    - Product description, images, and specifications
    - Current highest bid
    - Total number of bids placed
    - Auction timing information (e.g., remaining days/hours)
    - Additional product-specific attributes enriched through the specs utility

    Attributes:
        model (PopUpProduct): The product model used for the detail view.
        template_name (str): Template used to render the auction page.
        context_object_name (str): Name of the product variable in the template.
        slug_field (str): Field used to look up the product by slug.
        slug_url_kwarg (str): URL keyword argument used to retrieve the slug.

    Methods:
        get_object(queryset=None):
            Retrieves the requested product, ensuring:
                - The product exists
                - The product is active (is_active=True)
                - Product specifications are prefetched for performance
            Returns the fully populated PopUpProduct instance.

    get_context_data(**kwargs):
        Adds additional auction-related context to the page, including:
            - Structured product specifications (via add_specs_to_products)
            - A {spec_name: value} dictionary for template use
        Returns the complete context for rendering.
    """
    model = PopUpProduct
    template_name = 'auction/product_auction.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        """Override to add the is_active filter"""
        return get_object_or_404(PopUpProduct.objects.prefetch_related(
                'popupproductspecificationvalue_set__specification'
            ), 
            slug=self.kwargs['slug'], 
            is_active=True)
    
    def get_context_data(self, **kwargs):
        """Add product specification to the context"""
        context = super().get_context_data(**kwargs)
        
        # Apply the utility function to a single-item queryset
        products_with_specs = add_specs_to_products([self.object])
        context['product'] = products_with_specs[0]  # Get the single product back

        product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=self.object)}
        context['product_specifications'] = product_specifications
        
        return context
    
        

class ProductsView(ListView):
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 Mobile / Tablet Media Query Completed
    """
    Class-based view for displaying products available for immediate purchase.

    Shows all active products that are currently eligible for “Buy Now,” including
    items that are either fully in inventory or temporarily reserved. Supports
    optional filtering by product type via slug and enriches all products with
    their associated specification data for front-end display.

    Attributes:
        model (PopUpProduct): The product model used for the list view.
        template_name (str): Template used to render the product listing page.
        context_object_name (str): Name of the product list variable in the template.

    Methods:
        get_queryset():
            Retrieves the list of purchasable products by applying filters:
                - is_active=True
                - inventory_status in ["in_inventory", "reserved"]
                - buy_now_start <= current time <= buy_now_end
            Prefetches product specification values for performance.
            If a product-type slug is provided in the URL, filters the list to only
            include products belonging to that type.

        get_context_data(**kwargs):
            Adds additional context data for rendering, including:
                - The list of products enriched with specifications via
                add_specs_to_products
                - All product types (for category navigation or user filtering)
                - The currently selected product type, if a slug was specified
            Returns the complete context dictionary for template rendering.
    """
    model = PopUpProduct
    template_name = 'auction/products.html'
    context_object_name = 'product'

    def get_queryset(self):
        """Filter products based on slug if provided"""

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
        logger.debug("slug is", slug if slug else "No slug")
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            # return product_with_specs.filter(product_type=product_type)
            return base_queryset.filter(product_type=product_type)
        return base_queryset

    def get_context_data(self, **kwargs):
        """Add product_types and product_type to context"""
        context = super().get_context_data(**kwargs)
        logger.debug("get_context_data", context)

        # Apply add_specs_to_products utility function
        context['product'] = add_specs_to_products(context['product'])

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
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 Mobile / Tablet Media Query Completed
    """
    Class-based view for displaying products that are “coming soon.”

    Shows users products that are not yet available for purchase but are already
    ordered, in transit, and expected to arrive in inventory soon. This view
    supports optional filtering by product type and enriches products with
    their associated specifications.

    Attributes:
        model (PopUpProduct): The product model displayed in the list view.
        template_name (str): Template used to render the coming-soon product page.
        context_object_name (str): Name of the product list variable in the template.

    Methods:
        get_queryset():
            Retrieves products that:
                - Are inactive (is_active=False)
                - Have an inventory_status of "in_transit"
            If a slug is present in the URL, filters the list to only include products
            belonging to the specified product type. Prefetches related product
            specifications for performance.

        get_context_data(**kwargs):
            Adds additional context required for rendering, including:
                - Products enriched with specification data via add_specs_to_products
                - A list of all product types (used for category navigation or filters)
                - The currently selected product type (if a slug was provided)
            Returns the fully prepared context dictionary for template rendering.
    """

    model = PopUpProduct
    template_name = "auction/coming_soon.html"
    context_object_name = "product"

    def get_queryset(self):
        """Filter items based on slug if selected"""
        base_queryset = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set'
            ).filter(is_active=False, inventory_status="in_transit")
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            return base_queryset.filter(product_type=product_type)
        return base_queryset


    def get_context_data(self, **kwargs):
        """Add product type and product_types to context"""
        context =  super().get_context_data(**kwargs)

        # Apply add_specs_to_products utility function
        context['product'] = add_specs_to_products(context['product'])

        # Always include all product types
        context['product_types'] = PopUpProductType.objects.all()

        # Include the current product_type if slug is provided
        slug = self.kwargs.get('slug')
        if slug:
            context['product_type'] = get_object_or_404(PopUpProductType, slug=slug)
        else:
            context['product_type'] = None
        
        return context


class FutureReleases(ListView):
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 NEEDED -> Mobile / Tablet Media Query Completed
    """
    Class-based view for displaying products expected to release in the future.

    Shows items that are not yet active and not yet in inventory, but are marked as
    "anticipated"—indicating that they are planned for a future release.  
    Users can browse upcoming products by category or filter by product type.

    Attributes:
        template_name (str): Template used to render the future releases page.
        context_object_name (str): The name under which the product list is exposed
            to the template.

    Methods:
        get_queryset():
            Retrieves all products where:
                - is_active=False
                - inventory_status="anticipated"
            If a product type slug is provided, returns only items matching that type.
            Prefetches product specification values for performance.

        get_context_data(**kwargs):
            Enhances template context with:
                - Enriched product data via add_specs_to_products()
                - A list of all product types for filter navigation
                - The currently selected product type (if a slug was provided)
            Returns a context dictionary used by the template.
    """

    model = PopUpProduct
    template_name = "auction/future_releases.html"
    context_object_name = "product"

    def get_queryset(self):
        """Filter items based on slug if selected"""
        base_queryset = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set'
            ).filter(is_active=False, inventory_status="anticipated")
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            return base_queryset.filter(product_type=product_type)
        return base_queryset
    

    def get_context_data(self, **kwargs):
        """Add product type and product_types to context"""
        context = super().get_context_data(**kwargs)

        # Apply add_specs_to_products utility function
        context['product'] = add_specs_to_products(context['product'])

        # Always include all product types
        context['product_types'] = PopUpProductType.objects.all()
        slug = self.kwargs.get('slug')
        if slug:
            context['product_type'] = get_object_or_404(PopUpProductType, slug=slug)
        else:
            context['product_type'] = None
        
        return context


class ProductDetailView(DetailView):
    # 🟢 View Test Completed
    # 🟢 Model Test Completed
    # 🟢 NEEDED -> Mobile / Tablet Media Query Completed
    """
    Class-based view for displaying detailed information about a product available for immediate sale.

    Provides a full product detail page for items that are active and eligible for
    Buy Now purchasing. Includes product specifications, availability logic, and
    buy-window timing checks.

    Attributes:
        model (PopUpProduct): The product model used for the detail view.
        template_name (str): Template used to render the product detail page.
        context_object_name (str): The name of the product variable passed to the template.
        slug_field (str): The model field used to match the product slug.
        slug_url_kwarg (str): The URL keyword that carries the slug value.

    Methods:
        get_object(queryset=None):
            Retrieves the product matching the slug from the URL, ensuring:
                - The product exists
                - The product is_active=True
            Raises 404 if the product is inactive or missing.

        get_context_data(**kwargs):
            Adds additional metadata required for the product detail page, including:
                - Product specifications (flattened as a dict: {name: value})
                - Buy Now availability, based on:
                    * buy_now_start <= current_time <= buy_now_end
                    * product has not already been purchased via Buy Now
            Returns a context dictionary used by the template.
    """

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
        product = self.get_object()

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


def past_product_detail(request, item_id):

    item = get_object_or_404(PopUpOrderItem, id=item_id, order__user=request.user)
    product = item.product

    product_with_specs = None
    if product:
        product_with_specs = add_specs_to_products([product])[0]
    else:
        product_with_specs = None
        
    context = {
        'item': item, 'product': product_with_specs

    }

    return render(request, 'auction/past_purchase_detail.html', context)


def past_bid_product_detail_by_product(request, product_id):
    """
    Alternative view that uses product_id.
    Shows product details. Created for past bids view
    """
    user = request.user
    user_id = user.id
    product = get_object_or_404(PopUpProduct, id=product_id)

    # Verify the user has bid on this product
    user_bids = PopUpBid.objects.filter(customer=request.user,product=product).order_by('-timestamp')

    if not user_bids.exists():
        raise Http404("You haven't bid on this product")
    
    # Get the user's highest bid
    highest_user_bid = user_bids.first()
    
    # Get product with specifications
    product_with_specs = add_specs_to_products([product])[0]
    
    # Get the final winning bid
    final_winning_bid = PopUpBid.objects.filter(
        product=product,
        is_winning_bid=True
    ).first()
    
    context = {
        'product': product_with_specs,
        'user_bids': user_bids,
        'highest_user_bid': highest_user_bid,
        'final_winning_bid': final_winning_bid,
        'is_past_bid': True,
    }
    
    return render(request, 'auction/past_bid_detail.html', context)
