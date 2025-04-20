from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
# from .models import Product, Bid
from .models import PopUpProduct, PopUpProductSpecificationValue, PopUpProductType
from django.utils.text import slugify


# Create your views here.
def all_auction_view(request):
    in_auction = []
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=True, inventory_status="in_inventory")   
    product_specifications = None
    
    for p in product:
        if p.auction_status == "Ongoing":
            in_auction.append(p)
            product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=p)}
    return render(request, 'auction/auction.html', {'in_auction': in_auction, 'product_specifications': product_specifications})


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
