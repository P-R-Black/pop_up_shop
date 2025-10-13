from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin, UserPassesTestMixin
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import UpdateView, FormView
from .token import account_activation_token
from pop_up_order.utils.utils import user_orders, user_shipments 
from pop_up_order.models import PopUpOrderItem, PopUpCustomerOrder
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponse
from .models import PopUpCustomer, PopUpPasswordResetRequestLog, PopUpCustomerAddress, PopUpBid, PopUpCustomerIP
from pop_up_auction.models import PopUpProduct, PopUpProductSpecification, PopUpProductSpecificationValue, PopUpProductType
from pop_up_auction.utils.utils import get_customer_bid_history_context
from django.views.decorators.http import require_http_methods
from pop_up_payment.models import PopUpPayment
from pop_up_shipping.models import PopUpShipment
from pop_up_finance.utils import (get_yearly_revenue_aggregated, get_monthly_revenue, get_last_20_days_sales, 
                                  get_last_12_months_sales, get_last_5_years_sales, get_yoy_day_sales, 
                                  get_year_over_year_comparison, get_month_over_month_comparison, get_weekly_revenue)
from pop_up_email.utils import (send_customer_shipping_details, send_interested_in_and_coming_soon_product_update_to_users)

from .utils.add_products_util import  handle_simple_form_submission, handle_full_product_save
from .utils.edit_products_util import save_existing_specifications, save_custom_specifications

from pop_up_auction.forms import (PopUpBrandForm, PopUpCategoryForm, PopUpProductTypeForm, PopUpProductSpecificationForm, 
                           PopUpAddProductForm, PopUpProductSpecificationValueForm, PopUpProductImageForm)
from pop_up_shipping.models import PopUpShipment
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import (PopUpRegistrationForm, PopUpUserLoginForm, PopUpUserEditForm, 
                    ThePopUpUserAddressForm, SocialProfileCompletionForm, PopUpEmailPasswordResetForm
                    )
from pop_up_shipping.forms import ThePopUpShippingForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import secrets
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError
import time
from django.core.cache import cache
from django.utils.timezone import now
from django.contrib.auth import logout
from django.views import View
from .utils.utils import (validate_email_address, get_client_ip, add_specs_to_products, 
                          calculate_auction_progress, handle_password_reset_request)
from django.conf import settings
import json
from django.utils.safestring import mark_safe
import logging
from django.db.models import OuterRef, Subquery, F
from decimal import Decimal
from .pop_accounts_copy.admin_copy.admin_copy import (
    ADMIN_DASHBOARD_COPY, ADMIN_SHIPPING_UPDATE, ADMIN_SHIPING_OKAY_PENDING, ADMIN_SHIPMENTS, 
    ADMIN_PRODUCTS_PAGE, ADMIN_PRODUCT_UPDATE
    )
from .pop_accounts_copy.user_copy.user_copy import (
    USER_SHIPPING_TRACKING, TRACKING_CATEGORIES, USER_ORDER_DETAILS_PAGE,USER_DASHBOARD_COPY, USER_INTERESTED_IN_COPY,
    USER_ON_NOTICE_COPY, PERSONAL_INFO_COPY, USER_PASSWORD_RESET_PAGE, USER_OPEN_BIDS_COPY, USER_PAST_BIDS_COPY,
    USER_PAST_PURCHASES_COPY)
from django.db.models import Count, Max, Q
from django.http import Http404
from social_django.utils import load_strategy, load_backend
from social_django.views import _do_login
from pop_accounts.utils.utils import get_stripe_payment_reference 


logger  = logging.getLogger('security')

# 🟢 View Test Completed
# ⚪️ Model Test Completed
# ✅ Mobile / Tablet Media Query Completed


# Create your views here.
# class UserLoginAfterPasswordResetView(FormView):
#     """
#     Simple Login Form
#     """
#     template_name = 'pop_accounts/login/login.html'
#     form_class = PopUpUserLoginForm
#     success_url = '/dashboard/'  # Change to wherever you want to redirect on success

#     def form_valid(self, form):
#         email = form.cleaned_data['email']
#         password = form.cleaned_data['password']

#         user = authenticate(self.request, username=email, password=password)
#         if user is not None:
#             login(self.request, user)
#             return redirect(self.get_success_url())
#         else:
#             form.add_error(None, 'Invalid email or password')
#             return self.form_invalid(form)
        


class UserLogOutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/')

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('/')
    

class UserPasswordResetConfirmView(View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested in later view
    # ✅ Mobile / Tablet Media Query Completed
    """
    Handles user password reset confirmation via a password reset link.

    - GET: Verify the reset link validity and renders the rest form
    - POST: Validate and updates the user's password
    """
    template_name = "pop_accounts/login/password_reset_confirm.html"
    user_password_rest_page = USER_PASSWORD_RESET_PAGE

    def _get_user_form_uid(self, uidb64):
        """
        Decode UID and fetch the user. Returns None if invalid
        """
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return PopUpCustomer.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, PopUpCustomer.DoesNotExist) as e:
            return None
    
    def get(self, request, uidb64, token, *args, **kwargs):
        """
        Validate the password reset token and render the form
        """
        user = self._get_user_form_uid(uidb64)

        if user is not None and default_token_generator.check_token(user, token):
            context = {"validlink": True, "uidb64": uidb64, "token": token, 'user_password_rest_page': self.user_password_rest_page}
        else:
            context = {"validlink": False, 'user_password_rest_page': self.user_password_rest_page}

        return render(request, self.template_name, context)
    

    def post(self, request, uidb64, token, *args, **kwargs):
        """
        Process the password reset form submission
        """
        user = self._get_user_form_uid(uidb64)
        if user is None:
            return JsonResponse({'success': False, 'error': 'Invalid reset link.'})
        
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('password2')


        if not new_password or not confirm_password:
            return JsonResponse({'success': False, 'error': 'All fields are required.'})
        
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'Passwords do not match.'})
        

        user.set_password(new_password)
        user.save()

        return JsonResponse({'success': True, 'message': 'Password reset successful.'})



class UserDashboardView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested in later view
    # ✅ mobile / tablet media query completed
    """
    Class-based view for User Dashboard 

    Provides a snapshot of the user's account, including:
    - Default shipping addresses
    - Products the user is interested in (future releases)
    - Products the user has on notice
    - Highest bids for active auctions
    - Recent orders
    - Recent shipments
    - Bid history and related statistics

    Attributes:
        template_name (str): Template used to render the dashboard page.
        user_dashboard_copy (dict): Static copy/content used in dashboard display (from USER_DASHBOARD_COPY).

    Methods:
        get(request):
            Retrieves and prepares all context data for rendering the dashboard, including:
                - Addresses (default only)
                - Top 3 interested products
                - Top 3 products on notice
                - Highest active bids and enriched product info
                - Recent orders and shipments
                - Bid history and statistics
            Renders the template with the prepared context.

        post(request):
            Currently returns the template with static dashboard copy only.
            Can be extended to handle POST requests from dashboard actions in the future.
    """

    template_name = 'pop_accounts/user_accounts/dashboard_pages/dashboard.html'
    user_dashboard_copy = USER_DASHBOARD_COPY

    def get(self, request):
        """
        Build context for the user dashboard page.

        Args:
            request (HttpRequest): The current request object.

        Returns:
            HttpResponse: Rendered HTML response with user interest data and product specs.
        """
        user = request.user
        addresses = user.address.filter(default=True)
        prod_interested_in = user.prods_interested_in.all()[:3]
        prods_on_notice_for = user.prods_on_notice_for.all()[:3]

        subquery = PopUpBid.objects.filter(
            customer_id=user.id,
            product=OuterRef('product'),
            is_active=True
        ).order_by('-amount').values('amount')[:1]
       
        # This queryset contains a reference to an outer query and may only be used in a subquery.
        highest_bid_objects = PopUpBid.objects.filter(
            customer_id=user.id,
            is_active=True,
            amount=Subquery(subquery)
        ).select_related('product')  # This will fetch the related product data
        
        product_ids = highest_bid_objects.values_list('product_id', flat=True)

        products = (
            PopUpProduct.objects.filter(id__in=product_ids, is_active=True, inventory_status='in_inventory')
            .prefetch_related('popupproductspecificationvalue_set')
        )

        # user orders
        orders = user_orders(request.user.id)
        
        # user shipments
        shipments = user_shipments(request.user.id)

        # past bids
        bid_data = get_customer_bid_history_context(user.id)
    
       

        product_map = {p.id: p for p in products}

        enriched_data = []
        for bid in highest_bid_objects:
            product = product_map.get(bid.product_id)
            if not product:
                continue
                
            enriched_data.append({
                "highest_user_bid": bid,
                "product": product,
                'specs': list(product.popupproductspecificationvalue_set.all()),
                "current_highest": product.current_highest_bid,
                "bid_count": product.bid_count,
                "duration": product.auction_duration,
                'retail_price': product.retail_price,
                
                })

    
        quick_bid_increments = [10, 20, 30]
        context = {'user': user, 'addresses': addresses, 'prod_interested_in': prod_interested_in, 
                   'prods_on_notice_for': prods_on_notice_for, 'highest_bid_objects': highest_bid_objects, 
                   'quick_bid_increments':quick_bid_increments, 'open_bids':enriched_data, 'orders': orders,
                   'shipments': shipments, 'bid_history': bid_data['bid_history'],
                   'statistics': bid_data['statistics'], "user_dashboard_copy": self.user_dashboard_copy
                   }
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Handle POST requests by re-rendering the page.

        Args:
            request (HttpRequest): The current request object.

        Returns:
            HttpResponse: Rendered template with static copy context.
        """
        return render(request, self.template_name, {"user_dashboard_copy": self.user_dashboard_copy})



class UserInterestedInView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # ⚪️ Model Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    """
    Display all products that the authenticated user has marked as "interested in."

    This view represents potential future releases. If enough users mark interest, 
    the product may be secured for auction.

    Attributes:
        template_name (str): Path to the template used for rendering the view.
        product (QuerySet): Prefetched queryset of anticipated (inactive) products.
        product_specifications (dict): Cached mapping of specification names to values 
            for products (built in `get`).
        user_intested_in_copy (str): Static copy text for the "Interested In" page.

    Methods:
        get(request):
            Renders the list of products the user is interested in and their specifications.
        post(request):
            Handles post requests (currently just re-renders the template).
    """
   
    template_name = 'pop_accounts/user_accounts/dashboard_pages/interested_in.html'
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="anticipated")   
    product_specifications = None
    user_intested_in_copy = USER_INTERESTED_IN_COPY

    def get(self, request):
        """
        Build context for the "interested in" page.

        Args:
            request (HttpRequest): The current request object.

        Returns:
            HttpResponse: Rendered HTML response with user interest data and product specs.
        """
        user = request.user
        prod_interested_in = user.prods_interested_in.all()

        for p in self.product:
            self.product_specifications = { 
                spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=p)}
        
        context = {
            'user': user, 'prod_interested_in': prod_interested_in, 
            'product_specifications': self.product_specifications, 
            'user_intested_in_copy': self.user_intested_in_copy}
        return render(request, self.template_name, context)


    def post(self, request):
        """
        Handle POST requests by re-rendering the page.

        Args:
            request (HttpRequest): The current request object.

        Returns:
            HttpResponse: Rendered template with static copy context.
        """
        return render(request, self.template_name, {'user_intested_in_copy': self.user_intested_in_copy})
    


class MarkProductInterestedView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    """
    Handles adding or removing products from a user's "interested in" list.

    This view is triggered via an AJAX/JSON POST request. The request body must 
    include a `product_id` and optionally an `action`. If the product exists:
    
    - If the product is already in the user's interested list, it is removed.
    - If the product is not in the user's interested list, it is added.

    If `product_id` is missing, an error response is returned.
    If the given product does not exist, a 404 response is returned.

    Requires:
        - User must be authenticated (LoginRequiredMixin).

    Request body (JSON):
        {
            "product_id": "id number",
            "action": "add" | "remove"  # optional, defaults to "add"
        }

    Responses:
        200 OK:
            {"status": "added", "message": "Product added to interested list."}
            {"status": "removed", "message": "Product removed from interested list."}
            {"status": "error", "message": "Product ID missing"}
        
        404 Not Found:
            {"status": "error", "message": "Product not found"}

    Models involved:
        - PopUpProduct: The product being marked as interested or not interested.
        - PopUpCustomer (request.user): The authenticated user whose list is updated.
        - M2M relationship: user.prods_interested_in

    Example usage:
        POST /mark-interested/
        Body: {"product_id": "123e4567-e89b-12d3-a456-426614174000", "action": "add"}
    """

    def post(self, request, *args, **kwargs):
     
        data = json.loads(request.body)
        product_id = data.get('product_id')
        action = data.get("action", "add")

        if not product_id:
            return JsonResponse({"status": "error", "message": "Product ID missing"})
            
        try:
            product = PopUpProduct.objects.get(id=product_id)
            user = request.user
            if product in user.prods_interested_in.all():
                user.prods_interested_in.remove(product)
                return JsonResponse({'status': 'removed', 'message': 'Product removed from interested list.'})
            else:
                user.prods_interested_in.add(product)
                return JsonResponse({'status': 'added', 'message': 'Product added to interested list.'})
            
        except PopUpProduct.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)


class UserOnNoticeView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # ⚪️ Model Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    """
    Display all products that the authenticated user has marked as "nofity me."

    This view represents products that will be in inventory soon. 
    If enough users mark notify me, the user will be notified when 
    the product is available for purchases or auction.

    Attributes:
        template_name (str): Path to the template used for rendering the view.
        product (QuerySet): Prefetched queryset of anticipated (inactive) products.
        product_specifications (dict): Cached mapping of specification names to values 
            for products (built in `get`).
        user_intested_in_copy (str): Static copy text for the "On Notice" page.

    Methods:
        get(request):
            Renders the list of products the user is interested in and their specifications.
        post(request):
            Handles post requests (currently just re-renders the template).
    """
     
    template_name = 'pop_accounts/user_accounts/dashboard_pages/on_notice.html'
    product = PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set').filter(is_active=False, inventory_status="in_transit")   
    product_specifications = None
    user_on_notice_copy = USER_ON_NOTICE_COPY

    def get(self, request):
        user = request.user
        prods_on_notice_for = user.prods_on_notice_for.all()

        for p in self.product:
            self.product_specifications = { spec.specification.name: spec.value for spec in PopUpProductSpecificationValue.objects.filter(product=p)}
        
        context = {'user': user, 'prods_on_notice_for': prods_on_notice_for, 
                   'product_specifications': self.product_specifications, 
                   "user_on_notice_copy": self.user_on_notice_copy}

        return render(request, self.template_name, context)
    
    def post(self, request):
        return render(request, self.template_name, {"user_on_notice_copy": self.user_on_notice_copy})


class MarkProductOnNoticeView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    """
    Handles adding or removing products from a user's "notify me list" list.

    This view is triggered via an AJAX/JSON POST request. The request body must 
    include a `product_id` and optionally an `action`. If the product exists:
    
    - If the product is already in the user's notify-me list, it is removed.
    - If the product is not in the user's notify-me list, it is added.

    If `product_id` is missing, an error response is returned.
    If the given product does not exist, a 404 response is returned.

    Requires:
        - User must be authenticated (LoginRequiredMixin).

    Request body (JSON):
        {
            "product_id": "id number",
            "action": "add" | "remove"  # optional, defaults to "add"
        }

    Responses:
        200 OK:
            {"status": "added", "message": "Product added to notify-me list."}
            {"status": "removed", "message": "Product removed from notify-me list."}
            {"status": "error", "message": "Product ID missing"}
        
        404 Not Found:
            {"status": "error", "message": "Product not found"}

    Models involved:
        - PopUpProduct: The product being marked as notify-me or not notify-me.
        - PopUpCustomer (request.user): The authenticated user whose list is updated.
        - M2M relationship: user.prods_interested_in

    Example usage:
        POST /mark-on-notice//
        Body: {"product_id": "123e4567-e89b-12d3-a456-426614174000", "action": "add"}
    """

    def post(self, request, *args, **kwargs):

        data = json.loads(request.body)
        product_id = data.get('product_id')
        action = data.get("action", "add")

        if not product_id:
            return JsonResponse({"status": "error", "message": "Product ID missing"})
            
        try:
            product = PopUpProduct.objects.get(id=product_id)
            user = request.user
            if product in user.prods_on_notice_for.all():
                user.prods_on_notice_for.remove(product)
                return JsonResponse({'status': 'removed', 'message': 'Product removed from notify me list.'})
            else:
                user.prods_on_notice_for.add(product)
                return JsonResponse({'status': 'added', 'message': 'Product added to notify me list.'})
        except PopUpProduct.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)



class PersonalInfoView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # ⚪️ Model Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    """
    Handles display and updates of a user's personal information and addresses
    within their dashboard.

    This view provides two forms:
      1. Personal Info Form – allows users to update their profile details
         such as name, shoe size, favorite brand, and mobile preferences.
      2. Address Form – allows users to add or update delivery addresses.

    Features:
        - GET request:
            Renders the personal info page with the user's current details,
            available addresses, and blank address form.
        - POST request:
            Determines whether the submission is for personal info or
            address updates, validates the data, and either saves changes
            (with a success message and redirect) or re-renders the page
            with validation errors.

    Submethods:
        - get_context_data():
            Collects common context data including forms and user info.
        - _is_personal_form_submission():
            Identifies if the POST data belongs to the personal info form.
        - _is_address_form_submission():
            Identifies if the POST data belongs to the address form.
        - _handle_personal_form(user):
            Validates and updates user profile data, or returns form errors.
        - _handle_address_form(user):
            Validates and saves a new or existing address, or returns errors.

    Template:
        pop_accounts/user_accounts/dashboard_pages/personal_info.html

    Access:
        Requires the user to be logged in.
    """

    template_name = "pop_accounts/user_accounts/dashboard_pages/personal_info.html"
    personal_info_copy = PERSONAL_INFO_COPY

    def get_context_data(self):
        """Get common context data for both GET and POST"""
        user = self.request.user
        addressess = PopUpCustomerAddress.objects.filter(customer=user)
        # payment_methods = get_stripe_payment_reference(user)

        personal_form = PopUpUserEditForm(initial={
            'first_name': user.first_name,
            'middle_name': user.middle_name,
            'last_name': user.last_name,
            'shoe_size': user.shoe_size,
            'size_gender': user.size_gender,
            'favorite_brand': user.favorite_brand,
            'mobile_phone': user.mobile_phone,
            'mobile_notification': user.mobile_notification
        })
    
        address_form = ThePopUpUserAddressForm()

        return {'form': personal_form, 'address_form': address_form, 'addresses': addressess, 'user': user, 
                'personal_info_copy': self.personal_info_copy}
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests"""
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle POST requests"""
        user = request.user

        # Determine which form was submitted
        if self._is_personal_form_submission():
            return self._handle_personal_form(user)
        elif self._is_address_form_submission():
            return self._handle_address_form(user)
        
        # If neighter form matches, render with errors
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def _is_personal_form_submission(self):
        """Check if personal form was submitted"""
        return 'street_address_1' not in self.request.POST and 'first_name' in self.request.POST

    def _is_address_form_submission(self):
        """Check if address form was submitted"""
        return 'street_address_1' in self.request.POST
    
    def _handle_personal_form(self, user):
        """Handle personal information form submission"""
        personal_form = PopUpUserEditForm(self.request.POST)
        if personal_form.is_valid():
                # Manually update user fields
                data = personal_form.cleaned_data
                user.first_name = data.get('first_name', '')
                user.middle_name = data.get('middle_name', '')
                user.last_name = data.get('last_name', '')
                user.shoe_size = data.get('shoe_size', '')
                user.size_gender = data.get('size_gender', '')
                user.favorite_brand = data.get('favorite_brand', '')
                user.mobile_phone = data.get('mobile_phone', '')
                user.mobile_notification = data.get('mobile_notification', '')
                user.save()

                messages.success(self.request, "Your profile has been updated.")
                return redirect('pop_accounts:personal_info')

        # If form is invalid, render with errors
        context = self.get_context_data()
        context['form'] = personal_form
        return render(self.request, self.template_name, context)
    
    def _handle_address_form(self, user):
        """Handle address form submission"""
        address_id = self.request.POST.get('address_id')

        if address_id:
            # Edit existing address
            address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=user)
            address_form = ThePopUpUserAddressForm(self.request.POST, instance=address)
        else:
            address_form = ThePopUpUserAddressForm(self.request.POST)
        
        try:         
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.customer = user
                address.prefix = address_form.cleaned_data['prefix']
                address.first_name = address_form.cleaned_data['first_name']
                address.middle_name = address_form.cleaned_data['middle_name']
                address.last_name = address_form.cleaned_data['last_name']
                address.suffix = address_form.cleaned_data['suffix']
                address.address_line = address_form.cleaned_data['street_address_1']
                address.address_line2 = address_form.cleaned_data['street_address_2']
                address.apartment_suite_number = address_form.cleaned_data['apt_ste_no']
                address.town_city = address_form.cleaned_data['city_town']
                address.state = address_form.cleaned_data['state']
                address.postcode = address_form.cleaned_data['postcode']
                address.delivery_instructions = address_form.cleaned_data['delivery_instructions']
                address.default = address_form.cleaned_data.get('address_default', False)
                address.save()
                msg = "Address has been updated." if address_id else "Address has been added."
                messages.success(self.request, msg)
                return redirect('pop_accounts:personal_info')
        except Exception as e:
            print('e', e)
            messages.error(self.request, 'An error occurred while saving the address')

        # If form is invalid or exception occured, render with errors
        context = self.get_context_data()
        context['address_form'] = address_form
        return render(self.request, self.template_name, context)



class GetAddressView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    """
    Handles retrieval of a user's saved address.

    This view ensures that the requested address belongs to the currently
    authenticated user. If the address exists, it returns the address fields
    in JSON format, which can be consumed by frontend code (e.g., for
    pre-filling an address edit form in a modal).

    Methods:
        get(request, address_id):
            Returns a JSON response with the address details for the given ID.
            Raises 404 if the address does not exist or does not belong to the user.
    """

    def get(self, request, address_id, *args, **kwargs):
        address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=request.user)
        return JsonResponse({
            'prefix': address.prefix,
            'first_name': address.first_name,
            'middle_name': address.middle_name,
            'last_name': address.last_name,
            'suffix': address.suffix,
            'address_line': address.address_line,
            'address_line2': address.address_line2,
            'apartment_suite_number': address.apartment_suite_number,
            'town_city': address.town_city,
            'state': address.state,
            'postcode': address.postcode,
            'delivery_instructions': address.delivery_instructions,
        })


class DeleteAddressView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    """
    Allows a logged-in user to delete one of their addresses.
    Accepts only POST requests. 
    Returns JSON response indicating success or failure.
    """
    def post(self, request, address_id, *args, **kwargs):
        address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=request.user)
        address.delete()
        return JsonResponse({'status': 'success'})
    
    def get(self, request, *args, **kwargs):
        """Reject GET requests explicitly"""
        return JsonResponse({'error': 'Invalid Request'}, status=400)


class SetDefaultAddressView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    """
    Allows user to make address a default address.
    Accepts only POST requests.
    Returns JSON response indicating success or failure
    """

    def post(self, request, address_id, *args, **kwargs):
        user = request.user
        try:
            address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=request.user, 
                                        deleted_at__isnull=True)
            # Unset all other address
            PopUpCustomerAddress.objects.filter(customer=user, default=True).update(default=False)

            # Set selected address as default
            address.default = True
            address.save()
            return JsonResponse({'success': True})
        except PopUpCustomerAddress.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Address not found'}, status=400)
    
    def get(self, request, *args, **kwargs):
        """Reject GET requests explicitly"""
        return JsonResponse({'success': False, 'error': 'Invalid Request'}, status=400)



class DeleteAccountView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    def post(self, request, *args, **kwargs):
        user = request.user
        user.soft_delete()
        # logout(request)
        return redirect('pop_accounts:account_deleted')
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'error':'Invalid Request'}, status=400)



class AccountDeletedView(View):
    # ⚪️ No View Test, Testing Done In Deleted Account View
    # ✅ Mobile / Tablet Media Query Completed
    """
    View to confirm account deletion
    """
    template_name = 'pop_accounts/user_accounts/dashboard_pages/account_deleted.html'
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    


class OpenBidsView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be Pop Up Auction App
    # ✅ Mobile / Tablet Media Query Completed
    """
    Displays all active bids that the authenticated user has placed.

    This view retrieves all products on which the user currently holds open (active) bids,
    enriches each bid with product and auction-related metadata, and renders them in
    the user's "Open Bids" dashboard page.

    ---
    **GET Request:**
        - Retrieves:
            • User's default shipping address.
            • Products the user is interested in (`prods_interested_in`).
            • Products the user is on notice for (`prods_on_notice_for`).
            • All active bids placed by the user, filtered to show only the highest bid
              per product (via `Subquery` and `OuterRef` optimization).
        - Enriches bid data with:
            • Related product details.
            • Product specifications.
            • Current highest bid.
            • Total number of bids on that product.
            • Auction duration and retail price.
        - Adds quick-bid increment options (e.g., +10, +20, +30).

        Returns:
            Rendered HTML page:
            `pop_accounts/user_accounts/dashboard_pages/open_bids.html`

    **POST Request:**
        - Currently a placeholder.
        - Simply re-renders the same template (can be extended for AJAX interactions later).

    ---
    **Context Variables:**
        - `user`: Authenticated user.
        - `addresses`: User’s default shipping address(es).
        - `prod_interested_in`: Products user has shown interest in.
        - `prods_on_notice_for`: Products user is monitoring.
        - `highest_bid_objects`: Queryset of user's highest active bids.
        - `open_bids`: Enriched list of product and bid data dictionaries.
        - `quick_bid_increments`: Predefined bid increment options.

    **Template:**
        `pop_accounts/user_accounts/dashboard_pages/open_bids.html`
    """
    template_name = 'pop_accounts/user_accounts/dashboard_pages/open_bids.html'
    user_open_bids_copy = USER_OPEN_BIDS_COPY
    def get(self, request):
        user = request.user
        addresses = user.address.filter(default=True)
        prod_interested_in = user.prods_interested_in.all()
        prods_on_notice_for = user.prods_on_notice_for.all()

        subquery = PopUpBid.objects.filter(
            customer_id=user.id,
            product=OuterRef('product'),
            is_active=True
        ).order_by('-amount').values('amount')[:1]
       
        # This queryset contains a reference to an outer query and may only be used in a subquery.
        highest_bid_objects = PopUpBid.objects.filter(
            customer_id=user.id,
            is_active=True,
            amount=Subquery(subquery)
        ).select_related('product')  # This will fetch the related product data
        
        product_ids = highest_bid_objects.values_list('product_id', flat=True)

        products = (
            PopUpProduct.objects.filter(id__in=product_ids, is_active=True, inventory_status='in_inventory')
            .prefetch_related('popupproductspecificationvalue_set')
        )

        product_map = {p.id: p for p in products}

        enriched_data = []
        for bid in highest_bid_objects:
            product = product_map.get(bid.product_id)
            if not product:
                continue
                
            enriched_data.append({
                "highest_user_bid": bid,
                "product": product,
                'specs': list(product.popupproductspecificationvalue_set.all()),
                "current_highest": product.current_highest_bid,
                "bid_count": product.bid_count,
                "duration": product.auction_duration,
                'retail_price': product.retail_price,
                
                })
    
        quick_bid_increments = [10, 20, 30]
        context = {'user': user, 'addresses': addresses, 'prod_interested_in': prod_interested_in, 
                   'prods_on_notice_for': prods_on_notice_for, 'highest_bid_objects': highest_bid_objects, 
                   'quick_bid_increments':quick_bid_increments, 'open_bids':enriched_data, 
                   'user_open_bids_copy': self.user_open_bids_copy
                   }
        return render(request, self.template_name, context)

    def post(self, request):
        return render(request, self.template_name)
    

class PastBidView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested PopUpCustomer
    # ✅ Mobile / Tablet Media Query Completed
    """
    Displays the user's past bidding activity and summary statistics.

    This view retrieves all closed or inactive bids associated with the
    authenticated user and presents them alongside aggregated statistics
    (e.g., total bids placed, won/lost counts, or average bid amounts)
    in the user's "Past Bids" dashboard page.

    ---
    **GET Request:**
        - Fetches the user’s complete bid history via
          `get_customer_bid_history_context(user_id)`, which returns:
            • `bid_history`: A list or queryset of the user’s previous bids.
            • `statistics`: Aggregated metrics summarizing the user’s bidding behavior.
        - Populates static page copy from `USER_PAST_BIDS_COPY` for display text.

        Returns:
            Rendered HTML page:
            `pop_accounts/user_accounts/dashboard_pages/past_bids.html`

    ---
    **Context Variables:**
        - `bid_history`: List or queryset of the user’s previous bids.
        - `statistics`: Summary data of the user’s past bidding activity.
        - `user_past_bids_copy`: Static text or copy for the past bids page.

    **Template:**
        `pop_accounts/user_accounts/dashboard_pages/past_bids.html`
    """
    template_name = 'pop_accounts/user_accounts/dashboard_pages/past_bids.html'
    user_past_bids_copy = USER_PAST_BIDS_COPY

    def get(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        bid_data = get_customer_bid_history_context(user_id)
        context= {'bid_history': bid_data['bid_history'], 'statistics': bid_data['statistics'], 
                  'user_past_bids_copy':self.user_past_bids_copy}
        
        return render(request, self.template_name, context)



class PastPurchaseView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested PopUpCustomer
    # ✅ Mobile / Tablet Media Query Completed

    """
    Displays the user's past purchase history in their account dashboard.

    This view retrieves all completed orders associated with the authenticated user
    and renders them on the "Past Purchases" dashboard page. It allows users to
    review items they’ve previously bought, including order details such as
    products, dates, and totals.

    ---
    **GET Request:**
        - Fetches the user’s order history via the `user_orders(request)` helper function.
        - Loads static page copy from `USER_PAST_PURCHASES_COPY` for display content.

        Returns:
            Rendered HTML page:
            `pop_accounts/user_accounts/dashboard_pages/past_purchases.html`

    ---
    **Context Variables:**
        - `orders`: A list or queryset of the user’s past completed orders.
        - `user_past_purchase_copy`: Static copy or metadata used for page content.

    **Template:**
        `pop_accounts/user_accounts/dashboard_pages/past_purchases.html`
    """
    template_name = 'pop_accounts/user_accounts/dashboard_pages/past_purchases.html'
    user_past_purchase_copy = USER_PAST_PURCHASES_COPY

    def get(self, request, *args, **kwargs):
        orders = user_orders(request.user.id)
        context = {'orders': orders, 'user_past_purchase_copy': self.user_past_purchase_copy}
        return render(request, self.template_name, context)



class ShippingTrackingView(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_shpping
    # ✅ Mobile / Tablet Media Query Completed
    template_name = 'pop_accounts/user_accounts/dashboard_pages/shipping_tracking.html'
    user_shipping_copy = USER_SHIPPING_TRACKING
    tracking_categories = TRACKING_CATEGORIES
    def get(self, request, *args, **kwargs):
        shipments = user_shipments(request.user.id)

        context = {'shipments': shipments, 'user_shipping_copy': self.user_shipping_copy, 
                    'tracking_categories': self.tracking_categories}

        return render(request, self.template_name, context)


class UserOrderPager(LoginRequiredMixin, View):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Displays the details of a specific user order, including all products,
    their specifications, and related shipment/billing info.

    ---
    **GET Request:**
        - Retrieves the order by `order_id` for the logged-in user.
        - Prefetches related product data and specifications for efficiency.
        - Combines product and order item details for rich display.

        Returns:
            Rendered HTML page:
            `pop_accounts/user_accounts/dashboard_pages/user_orders.html`

    ---
    **Context Variables:**
        - `order`: The selected `PopUpCustomerOrder` instance.
        - `items`: List of order items, each enriched with:
            - product details and specifications
            - model year, product sex, featured image
            - item total
        - `total_cost`: The order’s total cost.
        - `shipment`: Shipment details, if available.
        - `user_order_details_page`: Static copy for page content.

    ---
    **Template:**
        `pop_accounts/user_accounts/dashboard_pages/user_orders.html`
    """

    template_name = 'pop_accounts/user_accounts/dashboard_pages/user_orders.html'
    user_order_details_page = USER_ORDER_DETAILS_PAGE
    def get(self, request, order_id, *args, **wargs):
        user = request.user
    
        order = get_object_or_404(
            PopUpCustomerOrder.objects.select_related(
                'shipping_address',
                'billing_address',
                'coupon',
                'shipment'
            ).prefetch_related(
                Prefetch(
                    'items__product',
                    queryset=PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set__specification'),
                )
            ),
            id=order_id,
            user=user
        )
        
        # Get products with specs
        products_in_order = [item.product for item in order.items.all()]
        products_with_specs = add_specs_to_products(products_in_order)
    
        
        # Combine order items with product details
        items_with_details = []
        for order_item in order.items.all():
            product_with_specs = next(p for p in products_with_specs if p.id == order_item.product.id)
            # Get the featured image
            featured_image = order_item.product.product_image.filter(is_feature=True).first()
            items_with_details.append({
                'order_item': order_item,
                'product': product_with_specs,
                'model_year': product_with_specs.specs.get('model_year'),
                'product_sex': product_with_specs.specs.get('product_sex'),
                'featured_image': featured_image,
                'item_total': order_item.get_cost(),
            })

        # Check if shipment exists
        shipment = getattr(order, 'shipment', None)
        
        context = {
            'order': order,
            'items': items_with_details,
            'total_cost': order.get_total_cost(),
            'shipment': shipment,
            'user_order_details_page': self.user_order_details_page
        }


        return render(request, self.template_name, context)
        



class AdminDashboardView(UserPassesTestMixin, TemplateView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Dashboard 

    Provides a snapshot of Admin Items:
    - Pending skay to ship (2 business day window for payment to process before item shipped)
    - Okay to ship: 2 business day window closed, no payment dispute, okay to ship item
    - En Route: Items ordered for inventory but not yet in inventory
    - Inventory: Items in inventory
    - Most on Notice: Items users have put on notice the most
    - Most Interested: Items users have marked as interested in the most
    - Total Open Bids: How many opend bids
    - Sales: Yearly Sales Number
    - Total Accounts: Total Active Accouts
    - Account Sizes; Active users grouped by shoe size

    Attributes:
        template_name (str): Template used to render the dashboard page.
        admin_dashboard_copy (dict): Static copy/content used in dashboard display (from ADMIN_DASHBOARD_COPY).

    Methods:
        get(request):
            Retrieves and prepares all context data for rendering the dashboard, including:
                - Orders pending shipping
                - Recent orders and shipments
                - Items en route
                - Inventory
                - Top 3 most interested products
                - Top 3 products on notice
                - Number of active bids and enriched product info
                - Recent orders and shipments
                - Sales History
            Renders the template with the prepared context.

        post(request):
            Currently returns the template with static dashboard copy only.
            Can be extended to handle POST requests from dashboard actions in the future.
    """
    template_name = "pop_accounts/admin_accounts/dashboard_pages/dashboard.html"
    admin_dashboard_copy = ADMIN_DASHBOARD_COPY

    def test_func(self):
        return self.request.user.is_staff
    
    def get_product_inventory(self):
        """Get top 3 products in inventory"""
        # Get product inventory
        product_inventory_qs = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set__specification'
        ).filter(
            is_active=True,
            inventory_status__in=['in_inventory', 'reserved']
        )[:3]
        return add_specs_to_products(product_inventory_qs)

    def get_en_route_products(self):
        """ Get top 3 products in transit"""
        # Get en route products
        en_route_qs = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set__specification'
        ).filter(
            is_active=False, 
            inventory_status="in_transit"
        )[:3]
        
        # Convert to list and add specs
        return add_specs_to_products(en_route_qs)

    def get_most_interested_products(self):
        """Get top 3 product with most user interest"""
        # Most interested products - ONLY show products with at least 1 interested user
        most_interested_products = PopUpProduct.objects.annotate(
            interest_count=Count('interested_users')
        ).filter(
            interest_count__gt=0  # Only products with actual interest
        ).prefetch_related(
            'popupproductspecificationvalue_set__specification'
        ).order_by('-interest_count')[:3] 

        return add_specs_to_products(most_interested_products)


    def get_most_notified_products(self):
        # Most notification requested products - ONLY show products with at least 1 notification request
        most_notified_products = PopUpProduct.objects.annotate(
            notification_count=Count('notified_users')
        ).filter(
            notification_count__gt=0  # Only products with actual notification requests
        ).prefetch_related(
            'popupproductspecificationvalue_set__specification'
        ).order_by('-notification_count')[:3]


        return add_specs_to_products(most_notified_products)

    def get_size_distribution(self):
        """Get top 3 most common shoe sizes amoung customers"""
        # Query to get counts grouped by shoe_size and size_gender
        return PopUpCustomer.objects.values('shoe_size', 'size_gender').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        

    def get_active_accounts_count(self):
        """Get total number of active customer accounts"""
        return PopUpCustomer.objects.filter(is_active=True).count()


    def get_pending_shipments(self):
        """Get top 3 payments pending 'Okay to Ship' notification"""
        # Pending 'Okay' to Ship
        return PopUpPayment.objects.filter(notified_ready_to_ship=False)[:2]

    def get_cleared_shipments(self):
        """Get top 3 payments cleared to ship but not yet shipped/delivered"""
        # Okay to Ship
        return PopUpPayment.objects.filter( notified_ready_to_ship=True
            ).exclude(
                order__shipment__status='shipped'
            ).exclude(order__shipment__status='delivered').select_related('order')[:3]


    def get_context_data(self, **kwargs):
        """Build context with all dashboard data"""
        context = super().get_context_data(**kwargs)
        context.update({
            'product_inventory': self.get_product_inventory(),
            'en_route': self.get_en_route_products(),
            'top_interested_products': self.get_most_interested_products(),
            'top_notified_products': self.get_most_notified_products(),
            'total_active_accounts': self.get_active_accounts_count(),
            'size_counts': self.get_size_distribution(),
            'yearly_sales': get_yearly_revenue_aggregated(),
            'payment_status_pending': self.get_pending_shipments(),
            'payment_status_cleared': self.get_cleared_shipments(),
            'admin_dashboard_copy': self.admin_dashboard_copy
        })

        return context



class AdminInventoryView(UserPassesTestMixin, ListView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Admin Inventory View
    """
    model = PopUpProduct
    template_name = "pop_accounts/admin_accounts/dashboard_pages/inventory.html"
    context_object_name = 'inventory'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):

        base_queryset = PopUpProduct.objects.prefetch_related(
        'popupproductspecificationvalue_set__specification'
        ).filter(
            is_active=True,
            inventory_status__in=['in_inventory', 'reserved']
        )

        inventory = add_specs_to_products(base_queryset)

    
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            base_queryset = base_queryset.filter(product_type=product_type)
        
        return inventory

    def get_context_data(self, **kwargs):
        """Add product_types, product_type, and coming_soon products to context"""
        context = super().get_context_data(**kwargs)

        # Get coming soon products
        coming_soon_queryset = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set'
            ).filter(is_active=False, inventory_status="in_transit")


        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            coming_soon_queryset = coming_soon_queryset.filter(product_type=product_type)
            context['product_type'] = product_type
        else:
            context['product_type'] = None

        # Add to context
        context['product_types'] = PopUpProductType.objects.all()
        
        return context
    

class EnRouteView(UserPassesTestMixin, ListView):
    """
    Admin view that shows items that have been ordered, but not yet in inventory
    """
    model = PopUpProduct
    template_name = "pop_accounts/admin_accounts/dashboard_pages/en_route.html"
    context_object_name = 'en_route'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        base_queryset = PopUpProduct.objects.prefetch_related(
        'popupproductspecificationvalue_set'
        ).filter(is_active=False, inventory_status="in_transit")
    
    
        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            base_queryset = base_queryset.filter(product_type=product_type)
    
        # Convert to list to force evaluation and add specs
        products = list(base_queryset)
        for product in products:
            product.specs = {
                spec.specification.name: spec.value
                for spec in product.popupproductspecificationvalue_set.all()
            }
        
        return products

    def get_context_data(self, **kwargs):
        """Add product_types, product_type, and coming_soon products to context"""
        context = super().get_context_data(**kwargs)

        # Get coming soon products
        coming_soon_queryset = PopUpProduct.objects.prefetch_related(
            'popupproductspecificationvalue_set'
            ).filter(is_active=False, inventory_status="in_transit")


        slug = self.kwargs.get('slug')
        if slug:
            product_type = get_object_or_404(PopUpProductType, slug=slug)
            coming_soon_queryset = coming_soon_queryset.filter(product_type=product_type)
            context['product_type'] = product_type
        else:
            context['product_type'] = None

        # Convert to list and add specs
        coming_soon_products = list(coming_soon_queryset)
        for csp in coming_soon_products:
            csp.specs = {
                spec.specification.name: spec.value
                for spec in csp.popupproductspecificationvalue_set.all()
            }

        # Add to context
        context['coming_soon'] = coming_soon_products
        context['product_types'] = PopUpProductType.objects.all()
        
        return context
    


@staff_member_required
def sales(request):
    """
    Admin view that shows sales
    """
    current_date = date.today()
    year = current_date.strftime("%Y")
    month = current_date.strftime("%B")
    yearly_sales = get_yearly_revenue_aggregated()
    monthly_sales = get_monthly_revenue()
    weekly_sales = get_weekly_revenue()
    past_twenty_day_sales = get_last_20_days_sales()
    past_twelve_months_sales = get_last_12_months_sales()
    past_five_years_sales = get_last_5_years_sales()
    day_over_day_sales_comp = get_yoy_day_sales()
    year_over_year_comp = get_year_over_year_comparison()
    month_over_month_comp = get_month_over_month_comparison()

    context = {'yearly_sales': yearly_sales, 'monthly_sales': monthly_sales, 'weekly_sales': weekly_sales,
               'year': year, 'month': month, 'past_twenty_day_sales_json': mark_safe(json.dumps(past_twenty_day_sales)),
               'past_twelve_months_sales_json': mark_safe(json.dumps(past_twelve_months_sales)),
               'past_five_years_sales_json': mark_safe(json.dumps(past_five_years_sales)),
               'day_over_day_sales_comp_json': mark_safe(json.dumps(day_over_day_sales_comp)),
               'year_over_year_comp_json': mark_safe(json.dumps(year_over_year_comp)),
               'month_over_month_comp_json': mark_safe(json.dumps(month_over_month_comp))}

    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/sales.html', context)


@staff_member_required
def most_on_notice(request):
    """
    Admin view that displays items users have on notice
    """
    # Get all products with notification counts, ordered by most requested
    most_notified = PopUpProduct.objects.annotate(
        notification_count=Count('notified_users')
    ).filter(
        notification_count__gt=0  # Only show products with at least 1 notification request
    ).prefetch_related(
        'popupproductspecificationvalue_set__specification'
    ).order_by('-notification_count')
    
    # Add specs to products
    most_notified = add_specs_to_products(most_notified)
    
    context = {
        'most_notified': most_notified,
    }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_on_notice.html', context)


@staff_member_required
def most_interested(request):
    """
    Admin view that displays items users are interested in, which tells bots what items to purchase
    """
    # Get all products with interest counts, ordered by most interested
    most_interested = PopUpProduct.objects.annotate(
        interest_count=Count('interested_users')
    ).filter(
        interest_count__gt=0  # Only show products with at least 1 interested user
    ).prefetch_related(
        'popupproductspecificationvalue_set__specification'
    ).order_by('-interest_count')

    
    # Add specs to products
    most_interested = add_specs_to_products(most_interested)

    # Total number of interest instances across all products
    total_interest_instances = sum(product.interest_count for product in most_interested)
    
    context = {
        'most_interested': most_interested,
        'total_interest_instances': total_interest_instances
    }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_interested.html', context)


@staff_member_required
def total_open_bids(request):
    """
    Admin view that display all products currently in auction with their bid counts and details
    """
    now = timezone.now()
    
    # Get all products with ongoing auctions, annotated with bid counts
    open_auction_products = PopUpProduct.objects.filter(
        auction_start_date__isnull=False,
        auction_end_date__isnull=False,
        auction_start_date__lte=now,
        auction_end_date__gte=now
    ).annotate(
        active_bid_count=Count('bids', filter=Q(bids__is_active=True)),
        highest_bid=Max('bids__amount', filter=Q(bids__is_active=True))
    ).prefetch_related(
        'popupproductspecificationvalue_set__specification',
        'bids__customer'  # For getting bidder info if needed
    ).order_by('-active_bid_count', '-highest_bid')
    
    # Add specs to products
    open_auction_products = add_specs_to_products(open_auction_products)
    
    # Add additional auction info to each product
    for product in open_auction_products:
        # Get the latest bid for this product
        latest_bid = PopUpBid.objects.filter(
            product=product,
            is_active=True
        ).order_by('-timestamp').first()
        
        product.latest_bid = latest_bid
        product.time_remaining = product.auction_end_date - now
        product.auction_progress = calculate_auction_progress(product, now)
    
    # Calculate totals
    total_open_bids = sum(product.active_bid_count for product in open_auction_products)
    total_auction_value = sum(product.highest_bid or 0 for product in open_auction_products)
    
    context = {
        'open_auction_products': open_auction_products,
        'total_open_bids': total_open_bids,
        'total_auction_value': total_auction_value,
        'total_products_in_auction': len(open_auction_products)
    }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_open_bids.html', context)


@staff_member_required
def total_accounts(request):
    """
    Admin view that shows total number of active accounts
    """
    # Total active accounts
    total_active_accounts = PopUpCustomer.objects.filter(is_active=True).count()
    context = {
        'total_active_accounts':total_active_accounts
    }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_accounts.html', context)


@staff_member_required
def account_sizes(request):
    """
    Admin view that shows user sizes.
    """
    # Query to get counts grouped by shoe_size and size_gender
    size_counts = PopUpCustomer.objects.values('shoe_size', 'size_gender').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'size_counts':size_counts
    }

    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/account_sizes.html', context)


@staff_member_required
def pending_okay_to_ship(request):
    """
    View that displays ttems that have been purchased, but in waiting period to verify payment clears
    """
    pending_shipping = ADMIN_SHIPING_OKAY_PENDING

    # Pending 'Okay' to Ship
    payment_status_pending = PopUpPayment.objects.filter(notified_ready_to_ship=False)
    
    context = {
        'pending_shipping': pending_shipping,
        'payment_status_pending': payment_status_pending
    }

    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/pending_okay_to_ship.html', context)


@staff_member_required
def get_pending_order_shipping_detail(request, order_no):
    order_item = PopUpOrderItem.objects.filter(order=order_no)
    context = {
        "order_item": order_item,
    }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/partials/pending_order_details.html', context)


@staff_member_required
def update_shipping(request):
    """
    - show orders that have not been shipped: do i need a shipped/fullfilled tag on the orders model or ..
        can i get unshipped orders by querying PopUpShipment odrders with status 'pending'. That would require
        creating a shipping instance at every order with just the order_no and pending status. 
        All other fields left blank. Here, can query all pending orders
    - able to click on order and see order info and add shipping details to order
    """
    admin_shipping = ADMIN_SHIPPING_UPDATE
    pending_shipments = PopUpShipment.objects.filter(
        status='pending', order__popuppayment__notified_ready_to_ship=True
        ).select_related('order')

    context = {
        "admin_shipping": admin_shipping,
        "pending_shipments":pending_shipments
        }
    
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/update_shipping.html', context)


@staff_member_required
def get_order_shipping_detail(request, shipment_id):
    shipment = get_object_or_404(PopUpShipment, pk=shipment_id)
    order_item = PopUpOrderItem.objects.filter(order=shipment.order)
    form = ThePopUpShippingForm(instance=shipment)

    context = {
        "shipment":  shipment,
        "order_item": order_item,
        'form': form
        }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/partials/shipping_detail_partial.html', context)



@staff_member_required
@require_POST
def update_shipping_post(request, shipment_id):
    shipment = get_object_or_404(PopUpShipment, pk=shipment_id)
    form = ThePopUpShippingForm(request.POST, instance=shipment)
    payment = PopUpPayment.objects.get(order=shipment.order)

    """
    Figure out where to put this. Can I get this information from the "updated_shipment" form, or do I have to...
    ... query database again after shipping info saved and updated?
    send_customer_shipping_details(user, order=shipment, carrier, tracking_no, shipped_at=timezone.now(), estimated_deliv, status="shipped")
    """
    if form.is_valid():
        #Keep track of whether order was previously shipped
        was_unshipped = shipment.status != 'shipped'

        # update PopUpShipment to "shipped"
        updated_shipment = form.save(commit=False)

        # Check if status is being updated to "delivered"
        if updated_shipment.status == 'delivered' and not updated_shipment.delivered_at:
            updated_shipment.delivered_at = timezone.now()
        
        # Clear delivered_at if the status is changed away from "delivered"
        if updated_shipment.status != 'delivered' and updated_shipment.delivered_at:
            updated_shipment.delivered_at = None
        
        updated_shipment.save()
        
        # update PopUpPayment to "paid"
        try:
            payment.status = 'paid'
            payment.save()
        except Exception as e:
            print('payment status update failed', e)
        
        # Send shipping email if shipment was recently marked as shipped
        if was_unshipped and updated_shipment.status == 'shipped':
            send_customer_shipping_details(
                user=request.user,
                order=shipment.order,
                carrier=updated_shipment.carrier,
                tracking_no=updated_shipment.tracking_number,
                shipped_at=updated_shipment.shipped_at,
                estimated_deliv=updated_shipment.estimated_delivery,
                status=updated_shipment.status
            )


        messages.success(request, "Shipping Information Updated.")
        return redirect('pop_accounts:update_shipping')
    else:
        order_items = PopUpOrderItem.objects.filter(order=shipment.order)
        return render(request, 'pop_accounts/admin_accounts/dashboard_pages/partials/shipping_detail_partial.html', {
            'shipment': shipment,
            'form': form,
            'order_items': order_items
        })
    
   
    
@staff_member_required
def view_shipments(request):
    """
    - shows orders that have been shipped : admin can use this view to view shipped items
    - shows orders that have been shipped : admin can use this view to update delivery status
    """
    admin_shipping = ADMIN_SHIPMENTS
    all_shipments = PopUpShipment.objects.filter(order__popuppayment__notified_ready_to_ship=True).select_related('order')
    pending_delivery = PopUpShipment.objects.filter(status='shipped', order__popuppayment__notified_ready_to_ship=True).select_related('order')
    delivered = PopUpShipment.objects.filter(status='delivered', order__popuppayment__notified_ready_to_ship=True).select_related('order')


    context = {
        "admin_shipping": admin_shipping,
        "all_shipments": all_shipments,
        "pending_delivery":pending_delivery,
        "delivered": delivered,
        }
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/shipments.html', context)



class UpdateProductView(UserPassesTestMixin, View):
    """
    - shows all products added to database.
    - shows all products that are comming soon.
    - shows all products in inventory.
    - Can update status from "coming soon" to "in inventory"
    - Displays form for specific product
    """
    template_name = 'pop_accounts/admin_accounts/dashboard_pages/update_product.html'
    product_copy = ADMIN_PRODUCT_UPDATE

    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request, product_id=None):
        context = self.get_context_data(product_id)
        return render(request, self.template_name, context)
    
    def post(self, request, product_id=None):
        print('UpdateProductView post method hit!')
        if product_id:
            # Handle form submission for updating a product
            product = get_object_or_404(PopUpProduct, id=product_id)
            form = PopUpAddProductForm(request.POST, instance=product)
            image_form = PopUpProductImageForm(request.POST, request.FILES, instance=product)

            old_buy_now_start = product.buy_now_start                
            old_auction_start = product.auction_start_date

            if form.is_valid():
                form.save()


                # save image if present
                image_file = request.FILES.get('image')  # or whatever field name you use
                image_url = request.POST.get('image_url') 
                if image_file or image_url:
                    if image_form.is_valid():
                        image_instance = image_form.save(commit=False)
                        image_instance.product = product
                        image_instance.save()
                    else:
                        messages.error(request, "There was an error with the image upload.")
                        print("Product Image Form Errors", image_form.errors)

                # Handle specifications if they exist
                self._handle_specifications(request, product)

                # notify interested users based on changes
                print('product.buy_now_start', product.buy_now_start)
                if product.buy_now_start and product.buy_now_start != old_buy_now_start:
                    send_interested_in_and_coming_soon_product_update_to_users(
                        product=product,
                        buy_now_start_date=product.buy_now_start
                    )
                
                if product.auction_start_date and product.auction_start_date != old_auction_start:
                    send_interested_in_and_coming_soon_product_update_to_users(
                        product=product,
                        auction_start_date=product.auction_start_date
                    )

                # Redirect or show success message
                context =self.get_context_data(product_id)
                context['success_message'] = 'Product updated successfully.'
                return render(request, self.template_name, context)
            else:
                # One or both forms has errors, show them
                if not image_form:
                    messages.error(request, 'Please check the image form for errors.')
                context = self.get_context_data(product_id)
                context['form'] = form # This will contain the errors
                context['product_image_form'] = image_form # Include image form with errors
                return render(request, self.template_name, context)
        else:
            # No product selected, just show the lsit
            context = self.get_context_data()
            return render(request, self.template_name, context)
        
    
    def get_context_data(self, product_id=None):
        all_products = PopUpProduct.objects.all()
        products_coming_soon = PopUpProduct.objects.filter(inventory_status="in_transit")
        products_in_inventory = PopUpProduct.objects.filter(inventory_status="in_inventory")

        
        context = {
            'product_copy': self.product_copy,
            'all_products': all_products,
            'products_coming_soon': products_coming_soon,
            'products_in_inventory': products_in_inventory
        }
    
        # If a product is selected, add form data
        if product_id:
            try:
                product = PopUpProduct.objects.get(id=product_id)
                form = PopUpAddProductForm(instance=product)
                product_image_form = PopUpProductImageForm(instance=product)

                # Get existing specifications
                existing_specs = PopUpProductSpecificationValue.objects.filter(
                    product=product
                ).select_related('specification')

                existing_spec_values = {
                    spec_value.specification.id: spec_value.value for spec_value in existing_specs
                }

                context.update({
                    'selected_product': product,
                    'form': form,
                    'product_image_form': product_image_form,
                    'existing_spec_values': existing_spec_values,
                    'existing_spec_values_json': json.dumps(existing_spec_values),
                    'product_type_id': product.product_type.id if product.product_type else None,
                    'show_form': True
                })
            except PopUpProduct.DoesNotExist:
                context['error_message'] = 'Product note found'
        return context
    
    def _handle_specifications(self, request, product):
        """Handle updating product specifications"""
        # Get all specification fields from the POST data
        for key, value in request.POST.items():
            if key.startswith('spec_') and value.strip():
                try:
                    spec_id = int(key.replace('spec_', ''))
                    
                    # Get or create the specification value
                    spec_value, created = PopUpProductSpecificationValue.objects.get_or_create(
                        product=product,
                        specification_id=spec_id,
                        defaults={'value': value}
                    )
                    
                    if not created:
                        spec_value.value = value
                        spec_value.save()
                        
                except (ValueError, TypeError):
                    continue  # Skip invalid specification IDs



class UpdateProductPostView(UserPassesTestMixin, View):
    """
    View for product updates
    """
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, product_id):
        product = get_object_or_404(PopUpProduct, id=product_id)
        form = PopUpAddProductForm(request.POST, instance=product)

        if form.is_valid():
            try:
                updated_product = form.save()

                PopUpProductSpecificationValue.objects.filter(product=updated_product).delete()

                # Save the new specifications
                self.save_existing_specifications(request, updated_product)
                self.save_custom_specifications(request, updated_product)
                messages.success(request, f'Product "{updated_product.product_title} {updated_product.secondary_product_title} updated successfully!')
                return redirect('pop_accounts:update_product')
            except Exception as e:
                messages.error(request, 'An error occurred while updating the product.')
                print('Update error:', e)
        else:
            messages.error(request, 'Please correct the errors in the form.')
            print('Form errors', form.errors)
        return redirect('pop_accounts:updated_product')


class AddProductsView(UserPassesTestMixin, View):
    """
    Admin view to add products to database
    """
    template_name = 'pop_accounts/admin_accounts/dashboard_pages/add_product.html'
    product_copy = ADMIN_PRODUCTS_PAGE

    def test_func(self):
        return self.request.user.is_staff
    

    def get(self, request): 
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def post(self, request):
        form_type = request.POST.get('form_type')

        if form_type == "Add Product Type":
            success, _ = handle_simple_form_submission(request, PopUpProductTypeForm, "Product type", "Product type {name} added successfully")
            if success:
                return redirect('pop_accounts:add_products')
        
        elif form_type == "Add Category":
            success, _ = handle_simple_form_submission(request, PopUpCategoryForm, "Category", "Category {name} added successfully")
            if success:
                return redirect('pop_account:add_products')
        elif form_type == "Add Brand":
            success, _ = handle_simple_form_submission(request, PopUpBrandForm, "Brand", "Brand {name} added successfully")
            if success:
                return redirect('pop_account:add_products')
        elif form_type == "Save Product":
            success = handle_full_product_save(request)
            if success:
                return redirect('pop_accounts:add_products')
        
        # If we reach here, return context with forms populated
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self):
        return {
            'brand_form': PopUpBrandForm(), 
            'category_form': PopUpCategoryForm(),
            'product_type_form': PopUpProductTypeForm(),
            'product_specification_form': PopUpProductSpecificationForm(),
            'product_add_form': PopUpAddProductForm(),
            'product_specification_value_form': PopUpProductSpecificationValueForm(),
            'product_image_form': PopUpProductImageForm(),
            'product_copy': self.product_copy
        }



@require_http_methods(['GET'])
def add_products_get(request, product_type_id):
    try:
        specifications = PopUpProductSpecification.objects.filter(
            product_type_id=product_type_id).values('id', 'name')
        return JsonResponse({
            'success': True,
            'specifications': list(specifications)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
            })


"""
Log in / Registration Views
"""

class EmailCheckView(View):
    """
    In login/registration modal, verifies that email is on file
    if email on file, user taken to password entry screen
    if email not on file, user taken to registration form.
    """
    def post(self, request):
        NewUser = False
        email = request.POST.get('email')
        if email and validate_email_address(email):

            user_exists = PopUpCustomer.objects.filter(email=email).exists()
            if not user_exists:
                NewUser = True
                return JsonResponse({'status': NewUser})
            
            request.session['auth_email'] = email
            return JsonResponse({'status': not user_exists})
        return JsonResponse({'status': False, 'error': 'Invalid or missing email'}, status=400)


class RegisterView(View):
    """
    In login/ registration modal. This view is for the registration form for users registering with email
    Email verification sent to user upon form submission
    """
    def post(self, request):
        email = request.session.get('auth_email') or request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if email and password and password2:
            # email = request.session.get('auth_email') or request.POST.get('email')
            data = request.POST.copy()
            data['email'] = email
            try:
                form = PopUpRegistrationForm(data)
            except Exception as e:
                return JsonResponse({'error': 'Form init failed', 'details': str(e)}, status=500)

            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.is_active = False  # Disable account until email is confirmed
                user.save()
                # capture and store the IP address
                ip_address = get_client_ip(request)
                if not PopUpCustomerIP.objects.filter(customer=user, ip_address=ip_address).exists():
                    PopUpCustomerIP.objects.create(customer=user, ip_address=ip_address)
                try:
                    self.send_verification_email(request, user)
                except Exception as e:
                    print('Error sending verification email', e)
                return JsonResponse({'registered': True, 'message': 'Check your email to confirm your account'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            
        elif email and password:
            return JsonResponse({'success': False, 'errors': 'Please confirm password'}, status=400)

        return JsonResponse({'success': False, 'errors': 'Missing required fields'}, status=400)
    
    def send_verification_email(self, request, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_url = request.build_absolute_uri(reverse('pop_accounts:verify_email', kwargs={'uidb64': uid, 'token': token}))

        subject = "Verify Your Email"
        message = f"Hi {user.first_name}, \n\nPlease click the link below to verify your email:\n{verify_url}\n\nThanks!"
        send_mail(
            subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


class Login2FAView(View):
    """
    Creates 2 factor auth by sending user six digit code
    If email on file, user prompted to enter password
    Class accepts password, verifies correct email-password and sends 6 digit code
    """
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = timedelta(minutes=15)

    def post(self, request):

        email = request.session.get('auth_email')
        password = request.POST.get('password')
        now_time = now()


        # Check session lockout
        attempts = request.session.get('login_attempts', 0)
        first_try = request.session.get('first_attempt_time')
        locked_until = request.session.get('locked_until')

        if locked_until and now_time < datetime.fromisoformat(locked_until):
            return JsonResponse({'authenticated': False, 'error': 'Locked out'}, status=429)
        
        user = authenticate(request, username=email, password=password)
        if user:
            request.session['pending_login_user_id'] = str(user.id)
            request.session.pop('login_attempts', None)
            request.session.pop('first_attempt_time', None)
            request.session.pop('locked_utnil', None)

            code = generate_2fa_code()
            request.session['2fa_code'] = code
            request.session['2fa_code_created_at'] = now_time.isoformat()

            send_mail(
                subject = "Your Verification Code",
                message = f"Your code is {code}.",
                from_email = "no-reply@thepopup.com",
                recipient_list = [ email],
                fail_silently = False
            )

            return JsonResponse({'authenticated': True, '2fa_required': True})
        
        # Handle Failure and Lockout
        if not first_try:
            request.session['first_attempt_time'] = now_time.isoformat()
            attempts = 1
        else:
            first_try_time = datetime.fromisoformat(first_try)
            if now_time - first_try_time > self.LOCKOUT_TIME:
                attempts = 1
                request.session['first_attempt_time'] = now_time.isoformat()
            else:
                attempts += 1

        
        request.session['login_attempts'] = attempts
        if attempts >= self.MAX_ATTEMPTS:
            request.session[locked_until] = (now_time + self.LOCKOUT_TIME).isoformat()
            return JsonResponse({'authenticated': False, 'locked_out': True}, status=403)
        
        return JsonResponse({'authenticated': False, 'error': f'Invalid Credentials. Attempt {attempts}/{self.MAX_ATTEMPTS}'}, status=401)


def generate_2fa_code():
    return f"{secrets.randbelow(10**6):06}"


class Verify2FACodeView(View):
    """
    Verifies six-digit code for 2FA.
    """
    def post(self, request):
        code_entered = request.POST.get('code')
        session_code = request.session.get('2fa_code')
        created_at_str = request.session.get('2fa_code_created_at')
        user_id = request.session.get('pending_login_user_id')

        if not all([session_code, created_at_str, user_id]):
            return JsonResponse({"verified": False, "error": "Session expired or invalid"})

        try:
            code_created_at = timezone.datetime.fromisoformat(created_at_str)
            if timezone.is_naive(code_created_at):
                code_created_at = timezone.make_aware(code_created_at)
                
        except Exception:
            return JsonResponse({'verified': False, 'error': 'Invalid timestamp format'}, status=400)

        # Check if Code is Expired
        if timezone.now() > code_created_at + timedelta(minutes=5):
            for key in ['2fa_code', '2fa_code_created_at', 'pending_login_user_id']:
                request.session.pop(key, None)
            return JsonResponse({'verified': False, 'error': 'Verification code has expired'}, status=400)

        # Login if code matches and user is verified
        if str(code_entered).strip() == str(session_code).strip():
            try:
                user = PopUpCustomer.objects.get(id=user_id)
                login(request, user, backend='pop_accounts.backends.EmailBackend')
                request.session.save()

                for key in ['2fa_code', '2fa_code_created_at', 'pending_login_user_id']:
                    request.session.pop(key, None)

                return JsonResponse({'verified': True, 'user_name': user.first_name})
            except PopUpCustomer.DoesNotExist:
                return JsonResponse({'verified': False, 'error': 'User not found'}, status=404)
        else:
            return JsonResponse({'verified': False, 'error': 'Invalid Code'}, status=400)




@require_POST
def resend_2fa_code(request):
    """
    Resends 6-digit code at users request
    """
    email = request.session.get('auth_email')
    print(f'email: {email}')
    
    user_id = request.session.get('pending_login_user_id')
    print(f'user_id: {user_id}')

    if not email or not user_id:
        return JsonResponse({'success': False, 'error': 'Session expired'}, status = 400)
    
    code = generate_2fa_code()
    request.session['2fa_code'] = code
    request.session['2fa_code_timestamp'] = timezone.now().isoformat()

    send_mail(
        subject = "Your New Verification Code",
        message=f"Your new code is {code}",
        from_email= "no-reply@thepopup.com",
        recipient_list = [email],
        fail_silently = False
    )

    return JsonResponse({'success': True})


@require_POST
def send_password_reset_link(request):
    """
    Emails link to user's email address to reset password
    """
    email = request.POST.get('email')
    return handle_password_reset_request(request, email)
    
    

class VerifyEmailView(View):
    """
    Verifiies Email for user's who are requesting a password reeset.
    """
    template_name = 'pop_accounts/registration/verify_email.html'

    def get(self, request, uidb64, token):
        login_form = PopUpUserLoginForm()

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = PopUpCustomer.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, PopUpCustomer.DoesNotExist):
            user = None

        
        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return render(request, self.template_name, {'email_verified': True, 'form': login_form, 'uidb64': uidb64, 'token': token })
        else:
            return render(request, self.template_name, {'invalid_link': True, 'form': login_form})
    
    def post(self, request, uidb64, token):
     
        form = PopUpUserLoginForm(request.POST)
        
        email = request.session.get('auth_email') or request.POST.get('email')
        password = request.POST.get('password')

        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('pop_accounts:personal_info')
            else:
                form.add_error(None, "Invalid email or password")
        
        return render(request, self.template_name, {'form': form, 'email_verified': True, 'login_failed': True, 'uidb64':  uidb64, 'token': token})



class CompleteProfileView(UpdateView):
    """
    View for user to complete profile if they login using Facebook or Google.
    """
    model = PopUpCustomer
    form_class = SocialProfileCompletionForm
    template_name = 'pop_accounts/registration/complete_profile.html'

    def get_object(self, queryset=None):
        # Already authenticated? Use that instance
        if self.request.user.is_authenticated:
            return self.request.user

        # Otherwise, get pending social user from session
        user_id = self.request.session.get('social_profile_user_id')
        if not user_id:
            raise Http404("No social profile pending completion.")
        try:
            return PopUpCustomer.objects.get(pk=user_id)
        except PopUpCustomer.DoesNotExist:
            raise Http404("Pending social user not found.")

    def form_valid(self, form):
        # 1️Save form updates
        user = form.save()

        # Log in user immediately so they appear authenticated
        if not user.is_active:
            user.is_active = True  # mark as active
            user.save(update_fields=['is_active'])

        # 2️⃣ Try to resume the social-auth pipeline (if any)
        strategy = load_strategy(self.request)
        partial = strategy.session_get('partial_pipeline')
        if partial:
            backend_name = partial.get('backend')
            if backend_name:
                backend = load_backend(strategy, backend_name, redirect_uri=None)

                # Remove our temp session key so it doesn’t loop
                self.request.session.pop('social_profile_user_id', None)

                # Continue pipeline; may return HttpResponse (redirect)
                result = backend.continue_pipeline(partial)
                if result:
                    # If social-auth returns a redirect, use it
                    # But we still log in the user afterward
                    login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
                    return result

        # 3️⃣ Fallback: if pipeline wasn’t present or didn’t redirect
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Get response to incorporate into sign-in registration modal
        if self.request.headers.get("x-request-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "next": "dashboard",
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "email": user.email,
                }
            })
        
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        # If modal, send bck errors as JSON
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("pop_accounts:dashboard")


def social_login_complete(request):
    """
    Final step for popup logins — closes the popup and refreshes parent.
    """

    # Check if this is an AJAX request for user info
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        
        response_data = {
            'authenticated': request.user.is_authenticated,
            'firstName': request.user.first_name if request.user.is_authenticated else '',
            'lastName': request.user.last_name if request.user.is_authenticated else '',
            'email': request.user.email if request.user.is_authenticated else '',
            'isStaff': request.user.is_staff if request.user.is_authenticated else False,
            'userId': request.user.id if request.user.is_authenticated else None,
        }
        

        return JsonResponse({
            'authenticated': request.user.is_authenticated,
            'firstName': request.user.first_name if request.user.is_authenticated else '',
            'isStaff': request.user.is_staff if request.user.is_authenticated else False
        })
  
    return render(request, "pop_accounts/registration/social_login_complete.html")


def get_user_info(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'firstName': request.user.first_name,
            'isStaff': request.user.is_staff
        })
    return JsonResponse({'authenticated': False})


