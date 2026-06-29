from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from pop_up_auction.models import PopUpProduct, PopUpProductType
from pop_up_bot.models import ProcurementServiceRequest, ScheduledRelease
from pop_up_bot.forms import ServicePaymentForm
from pop_accounts.utils.pop_accounts_utils import (add_specs_to_products)
from datetime import datetime, timedelta, date
from django.utils import timezone as django_timezone
from decimal import Decimal
from pop_up_bot.utils import get_sizes_for_product_type
from pop_up_cart.models import ProcurementCartItem
from django.contrib import messages



# Create your views here.
SERVICE_FEE = Decimal('15.00')
 
 
class ProcurementRequestView(View):  # LoginRequiredMixin
    """
    Display procurement form for a specific product.
    """
 
    context_object_name = 'product'
    model = PopUpProduct
    template_name = 'procurement/procure_product.html'
 
    def get(self, request, product_id):
        """Display procurement form — UNCHANGED from working version"""
        product = get_object_or_404(PopUpProduct, id=product_id)
 
        products = add_specs_to_products([product])
        product = products[0]
 
        release_date_str = product.specs.get('release_date') if product.specs else None
        if not release_date_str:
            return redirect('pop_up_auction:future_releases')
 
        try:
            release_date = datetime.strptime(release_date_str, '%m/%d/%Y')
            release_date = django_timezone.make_aware(release_date)
        except (ValueError, TypeError):
            return redirect('pop_up_auction:future_releases')
 
        now = django_timezone.now()
        ten_days_from_now = now + timedelta(days=10)
        if not (now <= release_date <= ten_days_from_now):
            return redirect('pop_up_auction:future_releases')
 
        return render(request, self.template_name, self._build_context(product, release_date=release_date))
 
    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
 
    def post(self, request, product_id):
        product = get_object_or_404(PopUpProduct, id=product_id)
        products = add_specs_to_products([product])
        product = products[0]
 
        size = request.POST.get('size', '').strip()
        sex = request.POST.get('sex', '').strip()  # only relevant for shoes
        understand_not_guaranteed = request.POST.get('understand_not_guaranteed')
        agree_terms = request.POST.get('agree_terms')
        product_type = product.product_type.name.lower()
        is_shoe = 'shoe' in product_type or 'sneaker' in product_type
 
        # --- Validation ---
        if not size:
            return self._render_with_error(request, product, 'Please select a size.')
 
        if is_shoe and not sex:
            return self._render_with_error(request, product, "Please select Men's or Women's sizing.")
 
        if not understand_not_guaranteed or not agree_terms:
            return self._render_with_error(
                request, product,
                'Please accept the terms before proceeding.'
            )
 
        # --- ScheduledRelease ---
        release_date_str = product.specs.get('release_date')
        try:
            release_date = datetime.strptime(release_date_str, '%m/%d/%Y')
            release_date = django_timezone.make_aware(release_date)
        except (ValueError, TypeError):
            return redirect('pop_up_auction:future_releases')
 
        sku = product.specs.get('style_number') or f"PENDING-{product.id}"
 
        scheduled_release, _ = ScheduledRelease.objects.get_or_create(
            product=product,
            defaults={
                'sku': sku,
                'release_date': release_date,
                'procurement_window_minutes': 30,
                'search_method': 'direct_url',
                'product_url': f"https://example.com/product/{product.id}",
                'status': 'scheduled',
                'retail_price': product.retail_price,
            }
        )
 
        # --- ProcurementServiceRequest ---
        # For shoes: (user, scheduled_release, size, sex) must be unique
        # For everything else: (user, scheduled_release, size) is enough
        lookup = {
            'user': request.user,
            'scheduled_release': scheduled_release,
            'size': size,
        }
        if is_shoe:
            lookup['sex'] = sex
 
        try:
            procurement_service_request, created = ProcurementServiceRequest.objects.get_or_create(
                **lookup,
                defaults={
                    'sex': sex if is_shoe else None,
                    'service_fee': SERVICE_FEE,
                    'fee_paid_at': django_timezone.now(),
                    'status': 'pending_payment',
                    'strategy': 'fastest',
                }
            )
 
            if not created:
                size_display = f"{sex} size {size}" if is_shoe else f"size {size}"
                return self._render_with_error(
                    request, product,
                    f"You already have a procurement request for "
                    f"{product.product_title} in {size_display}. "
                    f"Only one procurement request per product and size is allowed at this time."
                )
 
        except Exception as e:
            return self._render_with_error(
                request, product,
                'Something went wrong creating your procurement request. Please try again.'
            )
 
        # --- ProcurementCartItem ---
        cart_item, cart_created = ProcurementCartItem.objects.get_or_create(
            user=request.user,
            procurement_service_request=procurement_service_request,
            defaults={'fee_amount': SERVICE_FEE}
        )
 
        if not cart_created:
            messages.info(request, 'This procurement is already in your cart.')
 
        return redirect('pop_up_payment:payment_home')
 
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
 
    def get_available_sizes(self, product):
        """Plain size numbers — sex is now a separate field."""
        product_type = product.product_type.name.lower()
 
        if 'shoe' in product_type or 'sneaker' in product_type:
            return [
                '5', '5.5', '6', '6.5', '7', '7.5', '8', '8.5',
                '9', '9.5', '10', '10.5', '11', '11.5', '12', '12.5',
                '13', '13.5', '14', '14.5', '15', '15.5', '16',
                '16.5', '17', '17.5', '18', '18.5', '19'
            ]
 
        elif 'clothing' in product_type or 'clothes' in product_type:
            return ['Small', 'Medium', 'Large', 'Extra Large']
 
        elif 'ticket' in product_type or 'concert' in product_type:
            return ['General Admission', 'VIP', 'Front Row']
 
        elif 'console' in product_type or 'gaming' in product_type:
            return ['Standard Edition', 'Digital Edition', 'Pro Edition']
 
        return ['Standard']
 
    def get_available_sex(self, product):
        product_type = product.product_type.name.lower()
        if 'shoe' in product_type or 'sneaker' in product_type:
            return ['Mens', 'Womens']
        return []
 
    def _build_context(self, product, release_date=None, error=None, selected_size=None, selected_sex=None):
        """
        Single source of truth for template context.
        Keeps get(), post() validation blocks, and _render_with_error consistent.
        """
        context = {
            'product': product,
            'product_type': product.product_type.name.lower() if product.product_type else '',
            'sizes': self.get_available_sizes(product),
            'sexes': self.get_available_sex(product),
            'service_fee': SERVICE_FEE,
            'retail_price': product.retail_price,
            'total_price': product.retail_price + SERVICE_FEE,
            # Preserve user's selections on validation errors
            'selected_size': selected_size,
            'selected_sex': selected_sex,
        }
        if release_date:
            context['release_date'] = release_date
        if error:
            context['error'] = error
        return context
 
    def _render_with_error(self, request, product, error_msg, selected_size=None, selected_sex=None):
        """Re-render the procurement form with an error message."""
        # Re-attach specs in case product was modified
        products = add_specs_to_products([product])
        product = products[0]
        context = self._build_context(
            product,
            error=error_msg,
            selected_size=selected_size,
            selected_sex=selected_sex
        )
        return render(request, self.template_name, context)
    

    #     product = get_object_or_404(PopUpProduct, id=product_id)
 
    #     products = add_specs_to_products([product])
    #     product = products[0]
 
    #     release_date_str = product.specs.get('release_date') if product.specs else None
    #     if not release_date_str:
    #         return redirect('pop_up_auction:future_releases')
 
    #     if isinstance(release_date_str, str):
    #         try:
    #             release_date = datetime.strptime(release_date_str, '%m/%d/%Y')
    #             release_date = django_timezone.make_aware(release_date)
    #         except (ValueError, TypeError):
    #             return redirect('pop_up_auction:future_releases')
 
    #     now = django_timezone.now()
    #     ten_days_from_now = now + timedelta(days=10)
    #     if not (now <= release_date <= ten_days_from_now):
    #         return redirect('pop_up_auction:future_releases')
 
    #     context = {
    #         'product': product,
    #         'release_date': release_date,
    #         'product_type': product.product_type.name.lower(),
    #         'sizes': self.get_available_sizes(product),
    #         'sexes': self.get_available_sex(product),
    #         'service_fee': 15.00,
    #         'retail_price': float(product.retail_price),
    #         'total_price': float(product.retail_price) + 15,
    #     }
    #     return render(request, self.template_name, context)
 
    # def post(self, request, product_id):
    #     """Create procurement request and add service fee to cart"""
    #     product = get_object_or_404(PopUpProduct, id=product_id)
 
    #     products = add_specs_to_products([product])
    #     product = products[0]
 
    #     size = request.POST.get('size')
    #     understand_not_guaranteed = request.POST.get('understand_not_guaranteed')
    #     agree_terms = request.POST.get('agree_terms')
 
    #     # --- Validation ---
    #     if not size:
    #         context = {
    #             'product': product,
    #             'product_type': product.product_type.name.lower(),
    #             'sizes': self.get_available_sizes(product),
    #             'sexes': self.get_available_sex(product),
    #             'service_fee': 15.00,
    #             'retail_price': float(product.retail_price),
    #             'total_price': float(product.retail_price) + 15,
    #             'error': 'Please select a size.',
    #         }
    #         return render(request, self.template_name, context)
 
    #     if not understand_not_guaranteed or not agree_terms:
    #         context = {
    #             'product': product,
    #             'product_type': product.product_type.name.lower(),
    #             'sizes': self.get_available_sizes(product),
    #             'sexes': self.get_available_sex(product),
    #             'service_fee': 15.00,
    #             'retail_price': float(product.retail_price),
    #             'total_price': float(product.retail_price) + 15,
    #             'error': 'Please accept the terms before proceeding.',
    #         }
    #         return render(request, self.template_name, context)
 
    #     # --- Get or create ScheduledRelease (unchanged from working version) ---
    #     release_date_str = product.specs.get('release_date')
    #     try:
    #         release_date = datetime.strptime(release_date_str, '%m/%d/%Y')
    #         release_date = django_timezone.make_aware(release_date)
    #     except (ValueError, TypeError):
    #         return redirect('pop_up_auction:future_releases')
 
    #     sku = product.specs.get('style_number') if product.specs else None
 
    #     scheduled_release, _ = ScheduledRelease.objects.get_or_create(
    #         product=product,
    #         defaults={
    #             'sku': sku,
    #             'release_date': release_date,
    #             'procurement_window_minutes': 30,
    #             'search_method': 'direct_url',
    #             'product_url': f"https://example.com/product/{product.id}",
    #             'status': 'scheduled',
    #             'retail_price': product.retail_price,
    #         }
    #     )
    #     # --- Create or retrieve ProcurementServiceRequest ---
    #     SERVICE_FEE = Decimal('15.00')



    #     try:
    #         procurement_service_request, created = ProcurementServiceRequest.objects.get_or_create(
    #             user=request.user,
    #             scheduled_release=scheduled_release,
    #             size=size,
    #             defaults={
    #                 'service_fee': SERVICE_FEE,
    #                 'fee_paid_at': django_timezone.now(),
    #                 'status': 'pending_payment',
    #                 'strategy': 'fastest',
    #             }
    #         )

    #         if not created:
    #             return self._render_with_error(
    #                 request, product, 
    #                 f"You've already secured a procurement request for "
    #                 f"{product.product_title} in size {size}. "
    #                 f"Only one procurement request per product and size allowed at this time."
    #             )
    #     except Exception as e:
    #         print('DEBUG ProcurementRequestView', e)
 
    #     # --- Add service fee to cart ---
    #     cart_item, cart_created = ProcurementCartItem.objects.get_or_create(
    #         user=request.user,
    #         procurement_service_request=procurement_service_request,
    #         defaults={'fee_amount': SERVICE_FEE}
    #     )

 
    #     if not cart_created:
    #         messages.info(request, 'This procurement is already in your cart.')
 
    #     return redirect('pop_up_payment:payment_home')
 
    # def get_available_sizes(self, product):
    #     """Get available sizes based on product type — UNCHANGED"""
    #     product_type = product.product_type.name.lower()
        
    #     if 'shoe' in product_type or 'sneaker' in product_type:
    #         return [
    #             '5', '5.5', '6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10', 
    #             '10.5', '11', '11.5', '12', '12.5', '13', '13.5', '14', '14.5', 
    #             '15', '15.5', '16', '16.5', '17', '17.5', '18', '18.5', '19'
    #             ]

    #     elif 'clothing' in product_type or 'clothes' in product_type:
    #         return ['Small', 'Medium', 'Large', 'Extra Large' ]
        
    #     elif 'ticket' in product_type or 'concert' in product_type:
    #         return ['General Admission', 'VIP', 'Front Row']
 
    #     elif 'console' in product_type or 'gaming' in product_type:
    #         return ['Standard Edition', 'Digital Edition', 'Pro Edition']
 
    #     else:
    #         return ['Standard']
    

    # def get_available_sex(self, product):
    #     """Get available sizes based on product type — UNCHANGED"""
    #     product_type = product.product_type.name.lower()
    #     if 'shoe' in product_type or 'sneaker' in product_type:
    #         return ['Mens', 'Womens']


    # def _render_with_error(self, request, product, error_msg):
    #     """Re-render the procurement form with an error message."""
    #     products = add_specs_to_products([product])
    #     product = products[0]

    #     context = {
    #         'product': product,
    #         'product_type': product.product_type.name.lower() if product.product_type else '',
    #         'sizes': self.get_available_sizes(product),
    #         'sexes': self.get_available_sex(product),
    #         'service_fee': 15.00,
    #         'retail_price': float(product.retail_price),
    #         'total_price': float(product.retail_price) + 15.00,
    #         'error': error_msg,
    #     }
    #     return render(request, self.template_name, context)





# Create your views here.
# class ProcurementRequestView(View): # LoginRequiredMixin
#     """
#     Display procurement form for a specific product.
    
#     Handles:
#     - Product details display (dynamic based on type)
#     - Size/option selection (varies by product type)
#     - Service fee display
#     - Payment method selection
#     - Procurement request creation
#     """
    
#     context_object_name = 'product'
#     model = PopUpProduct
#     template_name = 'procurement/procure_product.html'

    
#     def get(self, request, product_id):
#         """Display procurement form"""
#         print('product_id:', product_id)
#         product = get_object_or_404(PopUpProduct, id=product_id)
#         print('get product', product)
        
#         # Add specs to product (includes release_date)
#         products = add_specs_to_products([product])

#         product = products[0]
#         print('product:', product)
        
#         # Get release_date from product specs
#         release_date_str = product.specs.get('release_date') if product.specs else None
#         print('release_date_str:', release_date_str)


#         if not release_date_str:
#             return redirect('pop_up_auction:future_releases')
        
#         # Convert string to datetime if needed
#         if isinstance(release_date_str, str):
#             try:
#                 release_date = datetime.strptime(release_date_str, '%m/%d/%Y')
#                 release_date = timezone.make_aware(release_date)
#                 print('parsed release_date:', release_date)
#             except (ValueError, TypeError) as e:
#                 print(f'Date parsing error: {e}')
#                 return redirect('pop_up_auction:future_releases')
        
#         # Check if within 10-day procurement window
#         now = timezone.now()
#         ten_days_from_now = now + timedelta(days=10)
#         print(f'now: {now}')
#         print(f'release_date: {release_date}')
#         print(f'ten_days_from_now: {ten_days_from_now}')
#         print(f'within window: {now <= release_date <= ten_days_from_now}')
        
        
#         if not (now <= release_date <= ten_days_from_now):
#             print('Outside 10-day window, redirecting')
#             return redirect('pop_up_auction:future_releases')
        
#         context = {
#             'product': product,
#             'release_date': release_date,
#             'product_type': product.product_type.name.lower(),
#             'sizes': self.get_available_sizes(product),
#             'service_fee': 15.00,
#             'retail_price': float(product.retail_price),
#             'total_price': float(product.retail_price) + 15,
#         }
        
#         print('Rendering template with context')
#         return render(request, self.template_name, context)
    
#     def post(self, request, product_id):
#         """Create procurement request"""
#         product = get_object_or_404(PopUpProduct, id=product_id)
        
#         # Add specs
#         products = add_specs_to_products([product])
#         product = products[0]
        
#         # Get form data
#         size = request.POST.get('size')
#         payment_method = request.POST.get('payment_method')
        
#         # Validate
#         if not size:
#             products = add_specs_to_products([product])
#             product = products[0]
#             context = {
#                 'product': product,
#                 'error': 'Please select a size',
#             }
#             return render(request, self.template_name, context)
        
#         # Get release date for ScheduledRelease
#         release_date_str = product.specs.get('release_date')
#         try:
#             release_date = datetime.strptime(release_date_str, '%m/%d/%Y')
#             release_date = timezone.make_aware(release_date)
#         except (ValueError, TypeError):
#             return redirect('pop_up_auction:future_releases')
        
#         # Get SKU
#         sku = product.specs.get('style_number') if product.specs else None
#         print('post sku', sku)
        
#         # Get or create ScheduledRelease
#         scheduled_release, created = ScheduledRelease.objects.get_or_create(
#             product=product,
#             defaults={
#                 'sku': sku,
#                 'release_date': release_date,
#                 'procurement_window_minutes': 30,
#                 'search_method': 'direct_url',
#                 'product_url': f"https://example.com/product/{product.id}",
#                 'status': 'scheduled',
#                 'retail_price': product.retail_price,
#             }
#         )
        
#         # Create ProcurementServiceRequest with all required fields
#         service_request = ProcurementServiceRequest.objects.create(
#             user=request.user,
#             scheduled_release=scheduled_release,  # Use scheduled_release, not product
#             size=size,
#             service_fee=15.00,
#             fee_paid_at=timezone.now(),  # Required field
#             status='pending',
#             strategy='fastest',  # Required field with default
#         )
        
#         # TODO: Redirect to payment page
#         # return redirect('pop_up_payment:create_service_fee_payment', 
#         #                service_request_id=service_request.id)
        
#         return redirect('pop_up_auction:future_releases')
    
#     def get_available_sizes(self, product):
#         """Get available sizes based on product type"""
#         product_type = product.product_type.name.lower()
        
#         if 'shoe' in product_type or 'sneaker' in product_type:
#             return ['US 5', 'US 6', 'US 7', 'US 8', 'US 9', 'US 10', 
#                     'US 11', 'US 12', 'US 13', 'US 14', 'US 15']
        
#         elif 'ticket' in product_type or 'concert' in product_type:
#             return ['General Admission', 'VIP', 'Front Row']
        
#         elif 'console' in product_type or 'gaming' in product_type:
#             return ['Standard Edition', 'Digital Edition', 'Pro Edition']
        
#         else:
#             return ['Standard']


