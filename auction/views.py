from django.shortcuts import render, get_object_or_404, redirect
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


class AjaxLoginRequiredMixing(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'You must be logged in to place a bid'}, status=403)
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class PlaceBidView(AjaxLoginRequiredMixing, View):
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

def product_buy_view(request):
    # need payment option attached to account  | # shopping cart length
    # shopping cart amount  |  # state tax info  | # ship to info  |  # product pic 
    # product title  |  # product size  |  # product buy now price  |  # quantity
    # estimated delivery info  |  # delivery address
    return render(request, 'auction/product_buy.html')

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




