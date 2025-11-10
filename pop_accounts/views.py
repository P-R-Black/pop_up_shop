from django.contrib import messages
from django.urls import reverse, reverse_lazy
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
    ADMIN_PRODUCTS_PAGE, ADMIN_PRODUCT_UPDATE, MOST_INTERESTED_COPY, MOST_ON_NOTICE_COPY, 
    ADMIN_SALES_COPY, ADMIN_TOTAL_OPEN_BIDS_COPY, ADMIN_TOTAL_ACCOUNTS_COPY, ADMIN_ACCOUNT_SIZE_COPY
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
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders

    """
    Class-based view for Admin En Route Products

    Displays products that have been ordered by the admin but are not yet in inventory.
    These items are marked as "in_transit" and represent stock that is on its way to the warehouse
    or fulfillment center. Allows filtering by product type and provides detailed product
    specifications for each en route item.

    Attributes:
        model (PopUpProduct): The product model representing items being tracked.
        template_name (str): The template used to render the en route products page.
        context_object_name (str): The variable name for the en route products in the template context.

    Methods:
        test_func():
            Ensures that only staff users (admin accounts) can access this view.

        get_queryset():
            Retrieves products that are inactive (`is_active=False`) and have an 
            `inventory_status` of `"in_transit"`.
            Optionally filters by `product_type` if a slug is provided in the URL.
            Adds product specifications to each product instance for richer template display.
            Returns a list of enriched product objects.

        get_context_data(**kwargs):
            Extends the template context with:
                - `product_types`: All available product categories.
                - `product_type`: The currently selected product type (if filtering by slug).
                - `coming_soon`: Additional products marked as "in_transit" to show upcoming arrivals.
            Returns the complete context for rendering the en route products page.
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
    

class SalesView(UserPassesTestMixin, TemplateView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Sales Dashboard

    Displays store-wide sales analytics and performance metrics for the admin dashboard.
    Provides aggregated, historical, and comparative sales data across multiple time periods,
    including daily, monthly, and yearly summaries. Designed to help administrators monitor
    revenue trends and visualize sales performance over time.

    Attributes:
        template_name (str): The template used to render the sales dashboard page.
        admin_sales_copy (dict): Static text and labels used for contextual display in the sales dashboard.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_current_date_info():
            Retrieves and formats the current year and month for display in the dashboard header.

        get_aggregate_sales():
            Returns aggregated revenue data for the current year, month, and week
            using helper functions (`get_yearly_revenue_aggregated`, `get_monthly_revenue`, `get_weekly_revenue`).

        get_historical_sales_data():
            Retrieves historical sales data for visualization charts, including:
                - Last 20 days
                - Last 12 months
                - Last 5 years
            Converts the data into safe JSON for frontend chart rendering.

        get_comparison_data():
            Provides comparative sales metrics for analyzing growth trends, including:
                - Day-over-day
                - Month-over-month
                - Year-over-year comparisons
            Returns data serialized as safe JSON for charting.

        get_context_data(**kwargs):
            Builds the full context for rendering the sales dashboard, combining:
                - Current date information
                - Aggregate totals
                - Historical chart data
                - Comparative metrics
                - Static display copy
            Returns the complete context for template rendering.
    """

    template_name = 'pop_accounts/admin_accounts/dashboard_pages/sales.html'
    admin_sales_copy = ADMIN_SALES_COPY

    def test_func(self):
        return self.request.user.is_staff
    

    def get_current_date_info(self):
        """Get Current Year and Month for Display"""
        current_date = date.today()
        return {
            'year': current_date.strftime('%Y'),
            'month': current_date.strftime('%B')
        }
    

    def get_aggregate_sales(self):
        """Get aggregate sales totals for different time periods"""
        return {
            'yearly_sales': get_yearly_revenue_aggregated(),
            'monthly_sales': get_monthly_revenue(),
            'weekly_sales': get_weekly_revenue(),
        }
    
    def get_historical_sales_data(self):
        """Get historical sales data for charts (as JSON)"""
        return {
            'past_twenty_day_sales_json': mark_safe(json.dumps(get_last_20_days_sales())),
            'past_twelve_months_sales_json': mark_safe(json.dumps(get_last_12_months_sales())),
            'past_five_years_sales_json': mark_safe(json.dumps(get_last_5_years_sales())),
        }
    
    def get_comparison_data(self):
        """Get sales comparison metrics (as JSON)"""
        return {
            'day_over_day_sales_comp_json': mark_safe(json.dumps(get_yoy_day_sales())),
            'year_over_year_comp_json': mark_safe(json.dumps(get_year_over_year_comparison())),
            'month_over_month_comp_json': mark_safe(json.dumps(get_month_over_month_comparison())),
        }
    
    def get_context_data(self, **kwargs):
        """Build context with all sales data"""
        context = super().get_context_data(**kwargs)

        # Add all sales data to context
        context.update(self.get_current_date_info())
        context.update(self.get_aggregate_sales())
        context.update(self.get_historical_sales_data())
        context.update(self.get_comparison_data())
        context.update({"admin_sales_copy": self.admin_sales_copy})
        return context



class MostOnNotice(UserPassesTestMixin, ListView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Most On Notice Products

    Displays products that users have requested to be notified about when available.
    This view helps the admin identify which products are generating the most user interest
    based on the number of "notify me" requests. Products are ranked in descending order
    of total notification requests and enriched with specification details.

    Attributes:
        model (PopUpProduct): The product model representing items users are tracking.
        template_name (str): The template used to render the most-on-notice products page.
        context_object_name (str): The variable name for the products list in the template context.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the current user is a staff member.

        get_queryset():
            Retrieves products annotated with the count of users who have requested notifications
            (`notification_count`).
            Filters to include only products with one or more notification requests.
            Orders products by descending notification count to prioritize most requested items.
            Prefetches specification data and enriches each product using `add_specs_to_products()`.
            Returns the processed queryset for display.
    """
    model = PopUpProduct
    template_name = "pop_accounts/admin_accounts/dashboard_pages/most_on_notice.html"
    context_object_name = 'most_notified'
    most_on_notice_copy = MOST_ON_NOTICE_COPY

    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = PopUpProduct.objects.annotate(notification_count=Count('notified_users')
        ).filter(
            notification_count__gt=0  # Only show products with at least 1 notification request
        ).prefetch_related(
            'popupproductspecificationvalue_set__specification'
        ).order_by('-notification_count')
    
        # Add specs to products
        queryset = add_specs_to_products(queryset)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            "most_on_notice_copy": self.most_on_notice_copy}
        )
        return context
    


class MostInterested(UserPassesTestMixin, ListView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Most Interested Products

    Displays products that users have marked as "interested in," allowing the admin to
    identify high-demand or trending items based on direct user engagement. Products are
    annotated and ranked by the total number of interested users and enriched with detailed
    product specifications for display.

    Attributes:
        model (PopUpProduct): The product model representing items of user interest.
        template_name (str): The template used to render the most-interested products page.
        context_object_name (str): The variable name for the list of interested products in the template context.
        most_interested_copy (dict): Static text or UI copy used to provide contextual information in the view.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_queryset():
            Retrieves products annotated with the number of users who marked them as interested
            (`interest_count`).
            Filters to include only products with one or more interested users.
            Orders the products in descending order of interest count.
            Prefetches related specification data and enriches each product with `add_specs_to_products()`.
            Returns the annotated and enriched queryset for display.

        get_context_data(**kwargs):
            Extends the template context with:
                - `total_interest_instances`: The total number of interest marks across all displayed products.
                - `most_interested_copy`: Predefined static copy or context text for the page.
            Returns the complete context for rendering the admin’s “Most Interested Products” page.
    """
    model = PopUpProduct
    template_name = "pop_accounts/admin_accounts/dashboard_pages/most_interested.html"
    context_object_name = 'most_interested'
    most_interested_copy = MOST_INTERESTED_COPY

    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = PopUpProduct.objects.annotate(
            interest_count=Count('interested_users')
            ).filter(
                interest_count__gt=0  # Only show products with at least 1 interested user
            ).prefetch_related(
                'popupproductspecificationvalue_set__specification'
            ).order_by('-interest_count')
        
        # Add specs to products
        queryset = add_specs_to_products(queryset)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Total number of interest instances across all products
        most_interested = context['most_interested']
        total_interest_instances = sum(product.interest_count for product in most_interested)
        
        context.update({
            "total_interest_instances": total_interest_instances,
            "most_interested_copy": self.most_interested_copy}
        )

        return context



class TotalOpenBidsView(UserPassesTestMixin, ListView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Total Open Bids

    Displays all products currently involved in active auctions, allowing the admin to
    monitor live bidding activity. Provides detailed information such as the number of
    active bids, highest bid amount, time remaining, and auction progress for each product.

    Attributes:
        model (PopUpProduct): The product model representing auctioned items.
        template_name (str): The template used to render the open bids dashboard page.
        context_object_name (str): The variable name for the list of products currently in auction.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_queryset():
            Retrieves products that are currently under auction based on `auction_start_date` and `auction_end_date`.
            Annotates each product with:
                - `active_bid_count`: Number of active bids.
                - `highest_bid`: The highest active bid amount.
            Prefetches related specification and bidder data for optimization.
            Enriches each product with:
                - `latest_bid`: The most recent active bid.
                - `time_remaining`: Time left until auction closes.
                - `auction_progress`: Calculated percentage of elapsed auction duration.
            Returns the fully annotated and enriched queryset for display.

        get_context_data(**kwargs):
            Extends the template context with:
                - `total_open_bids`: Total number of active bids across all products.
                - `total_auction_value`: Combined highest bid values for all open auctions.
                - `total_products_in_auction`: Count of products currently being bid on.
                - `admin_total_open_bids_copy`: Static content and labels for page display.
            Returns the complete context for rendering the admin’s open bids overview.
    """

    model = PopUpProduct
    template_name = 'pop_accounts/admin_accounts/dashboard_pages/total_open_bids.html'
    context_object_name = 'open_auction_products'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        now = timezone.now()
        queryset = PopUpProduct.objects.filter(
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
        queryset = add_specs_to_products(queryset)
        
        # Add additional auction info to each product
        for product in queryset:
            # Get the latest bid for this product
            latest_bid = PopUpBid.objects.filter(
                product=product,
                is_active=True
            ).order_by('-timestamp').first()
            
            product.latest_bid = latest_bid
            product.time_remaining = product.auction_end_date - now
            product.auction_progress = calculate_auction_progress(product, now)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        open_auction_products = context['open_auction_products']

        # Calculate totals
        context['total_open_bids'] = sum(
            product.active_bid_count for product in open_auction_products
        )
        context['total_auction_value'] = sum(
            product.highest_bid or 0 for product in open_auction_products
        )
        context['total_products_in_auction'] = len(open_auction_products)
        context['admin_total_open_bids_copy'] = ADMIN_TOTAL_OPEN_BIDS_COPY
        
        return context    


class TotalAccountsView(UserPassesTestMixin, TemplateView):
    # 🛑 Need to test after google analytics connected
    # ✅ Mobile / Tablet Media Query Completed
    template_name = 'pop_accounts/admin_accounts/dashboard_pages/total_accounts.html'

    def test_func(self):
        return self.request.user.is_staff
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get today's data range
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

        # Total active accounts
        context['total_active_accounts'] = PopUpCustomer.objects.filter(
            is_active=True
        ).count()
        
        # New accounts created today
        context['new_accounts_today'] = PopUpCustomer.objects.filter(
            created__gte=today_start,
            created__lte=today_end
        ).count()
        
        # Site visitors today (assuming you track this via a Visit/Session model)
        # Adjust this based on how you track visitors
        # Option 1: If you have a Visit/Session model
        # context['site_visitors_today'] = Visit.objects.filter(
        #     timestamp__gte=today_start,
        #     timestamp__lte=today_end
        # ).values('user').distinct().count()
        
        # Option 2: If you track via User.last_login
        context['site_visitors_today'] = PopUpCustomer.objects.filter(
            last_login__gte=today_start,
            last_login__lte=today_end
        ).count()
        
        # Add copy text
        context['admin_total_accounts_copy'] = ADMIN_TOTAL_ACCOUNTS_COPY

        print('context', context)
        return context


class AccountSizesView(UserPassesTestMixin, TemplateView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Account Size Distribution

    Displays aggregated statistics of registered users based on their selected shoe size
    and size gender. This view helps the admin analyze customer size demographics and
    inventory demand by showing how many active accounts fall into each size category.

    Attributes:
        template_name (str): The template used to render the account size distribution page.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_context_data(**kwargs):
            Builds the context containing:
                - `size_counts`: A queryset of user counts grouped by `shoe_size` and `size_gender`,
                annotated with the number of users per group and ordered by descending count.
                - `admin_account_size_copy`: Static copy or content used for display in the page.
            Returns the complete context for rendering the admin’s account size analytics page.
    """
    template_name = "pop_accounts/admin_accounts/dashboard_pages/account_sizes.html"

    def test_func(self):
        return self.request.user.is_staff
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Query to get counts grouped by shoe_size and size_gender
        context['size_counts'] = PopUpCustomer.objects.values('shoe_size', 'size_gender').annotate(
                count=Count('id')).order_by('-count')
        context['admin_account_size_copy'] = ADMIN_ACCOUNT_SIZE_COPY

        return context
        

class PendingOkayToShipView(UserPassesTestMixin, ListView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Pending Payment Approval (Okay to Ship)

    Displays orders that are pending payment verification before they can be approved
    for shipment. This view helps the admin monitor transactions that have not yet been
    cleared for fulfillment, ensuring that no items are shipped before successful payment
    confirmation.

    Attributes:
        model (PopUpPayment): The payment model representing transactions for customer orders.
        template_name (str): The template used to render the pending payment approval page.
        context_object_name (str): The variable name for the list of pending payments in the template context.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_queryset():
            Retrieves all payment records where `notified_ready_to_ship` is False,
            indicating that the payment has not yet been approved or marked ready for shipment.
            Returns the filtered queryset for display.

        get_context_data(**kwargs):
            Extends the template context with:
                - `admin_pending_shipping_copy`: Static copy or display text for the page.
            Returns the complete context for rendering the admin’s pending payment approval view.
    """

    model = PopUpPayment
    template_name = "pop_accounts/admin_accounts/dashboard_pages/pending_okay_to_ship.html"
    context_object_name = "payment_status_pending"

    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return PopUpPayment.objects.filter(notified_ready_to_ship=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admin_pending_shipping_copy'] = ADMIN_SHIPING_OKAY_PENDING
        return context



class PendingOrderShippingDetailView(UserPassesTestMixin, DetailView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Pending Order Shipping Details

    Displays detailed information about a specific customer order that is pending the 
    "okay_to_ship" status update. When a new order is created, it enters a 48-hour verification
    period to ensure that no fraudulent payment activity has occurred. If no issues are detected
    within that window, a webhook from the respective payment provider (e.g., Stripe, Venmo, PayPal)
    automatically updates the payment status to "paid" and sets the `notified_ready_to_ship` flag to True.

    Attributes:
        model (PopUpCustomerOrder): The customer order model being displayed.
        context_object_name (str): The variable name for the selected order in the template context.
        pk_url_kwarg (str): The URL parameter used to identify the specific order by its ID.
        template_name (str): The template used to render the pending order detail view.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_context_data(**kwargs):
            Builds the context containing:
                - `user_order`: The specific order record being reviewed.
                - `order_item`: All items associated with the given order.
                - `payment_status`: Payment details and current verification status for the order.
            Returns the full context for rendering the admin’s pending order detail page.
    """
    context_object_name = 'user_order'
    model = PopUpCustomerOrder
    pk_url_kwarg = 'order_no'
    template_name = "pop_accounts/admin_accounts/dashboard_pages/partials/pending_order_details.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """Add order items and payment status to context"""
        context = super().get_context_data(**kwargs)
        order_no = self.kwargs['order_no']

        context['user_order'] = PopUpCustomerOrder.objects.filter(id=order_no)

        # Get order items for this order
        context['order_item'] = PopUpOrderItem.objects.filter(order=order_no)

        # Get payment status for this order
        context['payment_status'] = PopUpPayment.objects.filter(order=order_no)

        return context



class UpdateShippingView(UserPassesTestMixin, ListView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Class-based view for Admin Orders Ready to Ship

    Displays all customer orders that have successfully passed the 48-hour payment verification 
    window and have been automatically updated to "okay_to_ship". These orders have cleared 
    fraud checks and payment disputes and are now ready for fulfillment and shipping.

    Attributes:
        model (PopUpShipment): The shipment model used to retrieve orders pending shipment.
        template_name (str): Template used to render the "okay to ship" orders page.
        context_object_name (str): Name of the queryset variable in the template context.

    Methods:
        test_func():
            Restricts access to staff users only. Returns True if the requesting user is a staff member.

        get_queryset():
            Retrieves all shipment records with:
                - `status='pending'`
                - An associated order whose payment (`notified_ready_to_ship=True`) 
                indicates it has cleared the 48-hour verification period.
            Prefetches related `order` objects for efficient query performance.

        get_context_data(**kwargs):
            Adds the static admin copy (`ADMIN_SHIPPING_UPDATE`) to the context for template rendering.
            Returns the final context dictionary for the "Orders Ready to Ship" admin view.
    """
    model = PopUpShipment
    template_name = 'pop_accounts/admin_accounts/dashboard_pages/update_shipping.html'
    context_object_name = "pending_shipments"

    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return PopUpShipment.objects.filter(
            status='pending', order__popuppayment__notified_ready_to_ship=True
        ).select_related('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admin_shipping'] = ADMIN_SHIPPING_UPDATE
        return context



class GetOrderShippingDetail(UserPassesTestMixin, DetailView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Retrieves and displays detailed shipping information for a specific order
    within the admin dashboard.  
    This view renders a partial template used to show and update shipping details
    for a selected order (via AJAX or inline page rendering).

    Purpose:
        - Allows admin users to view and manage shipment details for a specific order.
        - Provides order item information and a shipping update form in a single partial.
        - Used as a subcomponent (partial) in broader shipping management views.

    Template:
        pop_accounts/admin_accounts/dashboard_pages/partials/shipping_detail_partial.html

    Context Data:
        - shipment: The `PopUpShipment` instance corresponding to the shipment being managed.
        - order_item: A queryset of `PopUpOrderItem` objects linked to the shipment’s order.
        - form: A pre-populated instance of `ThePopUpShippingForm` bound to the shipment record.

    Access Control:
        - Restricted to staff users only (validated via `UserPassesTestMixin`).
        - Non-staff users attempting to access this view are denied.

    Workflow:
        1. The admin selects an order to view shipping details.
        2. The system retrieves the associated shipment and order items.
        3. The form is rendered with the shipment’s existing data, allowing updates
           to fields such as carrier, tracking number, or status.
        4. The partial is loaded dynamically into the page (via JavaScript or HTMX).

    Example Use:
        Triggered by selecting “View Shipping Details” in the admin panel,
        which loads this partial view dynamically into a modal or inline section.

    Notes:
        - The rendered form posts updates to `UpdateShippingPostView`.
        - Includes a link to generate and print the shipping label for the order.
    """
    model = PopUpOrderItem
    form_class = ThePopUpShippingForm
    pk_url_kwarg = 'shipment_id'
    template_name = 'pop_accounts/admin_accounts/dashboard_pages/partials/shipping_detail_partial.html'

    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shipment_id = self.kwargs['shipment_id']

        shipment = get_object_or_404(PopUpShipment, pk=shipment_id)
        context['shipment'] = shipment
        context['order_item'] = PopUpOrderItem.objects.filter(order=shipment.order)
        context['form'] = ThePopUpShippingForm(instance=shipment)

        return context


class UpdateShippingPostView(UserPassesTestMixin, UpdateView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Handles updates to an order’s shipping information from the admin dashboard.  
    This view processes the shipping form submission, validates input, saves updates
    to the `PopUpShipment` record, and triggers related post-update actions.

    Purpose:
        - Allows staff users to update shipment details such as carrier, tracking number,
          shipment and delivery dates, and shipment status.
        - Ensures consistency between order, shipment, and payment data.
        - Sends an automated email notification to the customer when their order is marked as shipped.

    Template:
        pop_accounts/admin_accounts/dashboard_pages/partials/shipping_detail_partial.html

    Behavior:
        - On form submission (`POST`), the shipment record is retrieved and updated.
        - If the status is changed to `"shipped"` and the order was previously unshipped,
          an email is sent to the customer with tracking and shipping details.
        - If the status is changed to `"delivered"`, the `delivered_at` timestamp is set.
        - If the status is changed away from `"delivered"`, the `delivered_at` field is cleared.
        - The associated payment (`PopUpPayment`) record is marked as `"paid"` upon successful update.

    Context Data:
        - shipment: The `PopUpShipment` object being updated.
        - order_items: A queryset of `PopUpOrderItem` objects linked to the shipment’s order.

    Access Control:
        - Restricted to staff users only (validated via `UserPassesTestMixin`).
        - Non-staff users are denied access automatically.

    Workflow:
        1. Admin loads the order’s shipping detail partial.
        2. Updates shipping info via the form and submits.
        3. View validates and saves changes.
        4. Triggers an update to payment status and optionally sends a shipment notification email.
        5. Redirects to the shipping management page upon success.

    Notes:
        - The form used is `ThePopUpShippingForm`.
        - The redirect target after successful submission is `'pop_accounts:update_shipping'`.
        - Exceptions during payment updates are gracefully handled and surfaced via Django messages.
    """
    model = PopUpShipment
    form_class = ThePopUpShippingForm
    template_name = "pop_accounts/admin_accounts/dashboard_pages/partials/shipping_detail_partial.html"
    pk_url_kwarg = "shipment_id"

    def test_func(self):
        return self.request.user.is_staff
    

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['order_items'] = PopUpOrderItem.objects.filter(order=self.object.order)
        context['shipment'] = self.get_object()
        return context
    
    def form_valid(self, form):
        shipment = self.get_object()
        original_status = shipment.status
        
        updated_shipment = form.save(commit=False)
        was_unshipped = shipment.status != 'shipped'


        # Check if status is being updated to delivered
        if updated_shipment.status == 'delivered' and not updated_shipment.delivered_at:
            updated_shipment.delivered_at = timezone.now()
        
        # Clear delivered at if the status is changed away from "delivered"
        if updated_shipment.status != "delivered" and updated_shipment.delivered_at:
            updated_shipment.delivered_at = None
        
        updated_shipment.save()
        
        # Updated PopUpPayment to "paid"
        try:
            payment = PopUpPayment.objects.get(order=shipment.order)
            payment.status = 'paid'
            payment.save()
        except PopUpPayment.DoesNotExist:
            messages.warning(self.request, "Payment record not found for this order.")
        except Exception as e:
            print(f'Payment status update failed: {e}')
        
        # Send shipping email if shipment was recently marked as shipped
        if was_unshipped and updated_shipment.status == "shipped":
       
            send_customer_shipping_details(
                user=shipment.order.user,
                order=shipment.order,
                carrier=updated_shipment.carrier,
                tracking_no=updated_shipment.tracking_number,
                shipped_at=updated_shipment.shipped_at,
                estimated_deliv=updated_shipment.estimated_delivery,
                status=updated_shipment.status
            )

        messages.success(self.request, "Shipping Information Updated.")
        return redirect('pop_accounts:update_shipping')

    def form_invalid(self, form):
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('pop_accounts:updated_shipping')
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class ViewShipmentsView(UserPassesTestMixin, TemplateView):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Displays the admin dashboard page showing all customer shipments and their statuses.

    Purpose:
        - Provides staff users with a comprehensive overview of all shipments in the system.
        - Allows filtering shipments by status — pending delivery or delivered.
        - Enables admins to click on a shipment to view full shipping details and update 
          shipment information such as tracking number, carrier, or delivery status.

    Template:
        pop_accounts/admin_accounts/dashboard_pages/shipments.html

    Behavior:
        - Retrieves all shipments (`PopUpShipment`) linked to paid orders 
          (where `notified_ready_to_ship=True` in `PopUpPayment`).
        - Categorizes shipments into three groups:
            • `all_shipments` — All shipments ready to ship or already shipped.
            • `pending_delivery` — Shipments with status `"shipped"`, not yet marked as delivered.
            • `delivered` — Shipments where the delivery has been completed.
        - Provides contextual admin text via `ADMIN_SHIPMENTS` for display in the template.

    Context Data:
        - all_shipments: Queryset of all qualifying `PopUpShipment` objects.
        - pending_delivery: Queryset of shipments currently in transit.
        - delivered: Queryset of completed deliveries.
        - admin_shipping: Text or instructions for the admin interface.

    Access Control:
        - Restricted to staff users only (checked via `UserPassesTestMixin`).
        - Non-staff users are denied access automatically.

    Workflow:
        1. Admin visits the Shipments dashboard.
        2. The view loads categorized shipment lists for quick access.
        3. Admin can click on a shipment entry to view details or update its status (e.g., mark as delivered).
    """
    
    template_name = "pop_accounts/admin_accounts/dashboard_pages/shipments.html"

    def test_func(self):
        return self.request.user.is_staff
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = PopUpShipment.objects.filter(
            order__popuppayment__notified_ready_to_ship=True).select_related('order')

        # All Shipments
        context['all_shipments'] = base_queryset

        # Pending Delivery
        context['pending_delivery'] = base_queryset.filter(status='shipped')

        # Delivered shipments
        context['delivered'] = base_queryset.filter(status='delivered')

        # Admin copy text
        context['admin_shipping'] = ADMIN_SHIPMENTS

        return context




class UpdateProductView(UserPassesTestMixin, View):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
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



# class UpdateProductPostView(UserPassesTestMixin, View):
#     """
#     View for product updates
#     """
#     def test_func(self):
#         return self.request.user.is_staff
    
#     def post(self, request, product_id):
#         product = get_object_or_404(PopUpProduct, id=product_id)
#         form = PopUpAddProductForm(request.POST, instance=product)

#         if form.is_valid():
#             try:
#                 updated_product = form.save()

#                 PopUpProductSpecificationValue.objects.filter(product=updated_product).delete()

#                 # Save the new specifications
#                 self.save_existing_specifications(request, updated_product)
#                 self.save_custom_specifications(request, updated_product)
#                 messages.success(request, f'Product "{updated_product.product_title} {updated_product.secondary_product_title} updated successfully!')
#                 return redirect('pop_accounts:update_product')
#             except Exception as e:
#                 messages.error(request, 'An error occurred while updating the product.')
#                 print('Update error:', e)
#         else:
#             messages.error(request, 'Please correct the errors in the form.')
#             print('Form errors', form.errors)
#         return redirect('pop_accounts:updated_product')


class AddProductsView(UserPassesTestMixin, View):
    # 🟢 View Test Completed
    # ✅ Mobile / Tablet Media Query Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
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



class AddProductsGetView(UserPassesTestMixin, View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Handles AJAX requests from the admin panel to dynamically load product specifications
    based on a selected product type when adding a new product.

    This view is used in the custom admin "Add Product" interface (outside the Django admin site).
    When the admin selects a product type from a dropdown, a JavaScript function (`loadProductSpecifications`)
    sends an AJAX GET request to this view to retrieve all specification fields associated
    with that product type.

    The view returns a JSON response containing:
        - success (bool): Whether the request was successful.
        - specifications (list): A list of dictionaries, each containing 'id' and 'name' keys
          representing product specification fields (e.g., "Color", "Size", "Material").
        - error (str): Included only if an exception occurs.

    Example Frontend Flow (AJAX Trigger):
        In "Add_Product.html", the JavaScript function:
            fetch(`/pop_accounts/add-products-admin/${productTypeId}/`)
        calls this view when a product type is selected.
        The returned JSON data is then passed to `displaySpecifications()` to render
        the specification input fields dynamically.

    URL Parameters:
        product_type_id (int): The ID of the product type selected by the admin.

    Permissions:
        - Only staff (admin) users can access this view. Non-staff users are denied access.

    Example Response:
        {
            "success": True,
            "specifications": [
                {"id": 1, "name": "Color"},
                {"id": 2, "name": "Size"}
            ]
        }

    Error Response:
        {
            "success": False,
            "error": "Database connection error"
        }
    """
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request, product_type_id):
        try:
            specifications = PopUpProductSpecification.objects.filter(
                product_type_id=product_type_id).values('id', 'name')
            return JsonResponse({ 'success': True, 'specifications': list(specifications)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})



"""
Log in / Registration Views
"""

class EmailCheckView(View):
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Handles AJAX-based email verification for the pop-up authentication flow.

    This view is triggered when a user enters their email in the login/registration modal.
    It checks whether the provided email is already associated with an existing account
    and determines the next step in the authentication process:

        - If the email exists in the database:
            → The user is redirected to the password entry screen.
            → The email is stored in the session for later authentication.

        - If the email does not exist:
            → The user is directed to the registration form to create a new account.

        - If the email is invalid or missing:
            → Returns an error response with status 400.

    The response is returned as a JSON object indicating whether the user is new (`status=True`)
    or existing (`status=False`).

    Expected POST data:
        - email (str): The email address entered by the user.

    JSON Response:
        - {'status': True}  → Email not found (new user, show registration form)
        - {'status': False} → Email found (existing user, show password form)
        - {'status': False, 'error': 'Invalid or missing email'} → Invalid input

    Example usage:
        POST /check-email/
        Data: {'email': 'user@example.com'}
        Response: {'status': False}

    """
    def post(self, request):
        NewUser = False
        email = request.POST.get('email', '').strip().lower()

        if email and validate_email_address(email):
            user_exists = PopUpCustomer.objects.filter(email__iexact=email).exists()
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
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Handles the second step of the two-factor authentication (2FA) login process.  
    This view validates the user's email and password combination and, upon successful 
    authentication, sends a six-digit verification code to the user's registered email address.

    Workflow:
    1. The user first submits their email through the login modal.
       - If the email exists, it is saved in the session under 'auth_email'.
    2. This view is triggered when the user submits their password.
       - The email is retrieved from the session, and authentication is attempted.
    3. If the email/password combination is valid:
       - A 6-digit 2FA code is generated using `generate_2fa_code()`.
       - The code is stored in the session and sent via email to the user.
       - The view returns a JSON response indicating that 2FA verification is required.
    4. If authentication fails:
       - The number of failed login attempts is tracked in the session.
       - After 5 failed attempts, the user is temporarily locked out for 15 minutes.
       - The lockout timer and attempts counter are also stored in the session.
    5. If the user account is inactive:
       - The login attempt is treated as invalid for security consistency.

    Responses:
        200: {"authenticated": True, "2fa_required": True} — password verified, 2FA code sent  
        401: {"authenticated": False, "error": "Invalid Credentials."} — invalid password  
        403: {"authenticated": False, "locked_out": True} — too many failed attempts  
        429: {"authenticated": False, "error": "Locked out"} — temporary lockout still active  

    Security:
        - Rate-limits password attempts to mitigate brute-force attacks.
        - Stores only minimal session data between steps (no plaintext passwords).
        - Sends 2FA codes using secure email delivery.

    Session Keys Used:
        - 'auth_email': email address entered in step one
        - 'pending_login_user_id': temporarily stores user ID after valid password
        - '2fa_code' / '2fa_code_created_at': the generated verification code and timestamp
        - 'login_attempts', 'first_attempt_time', 'locked_until': track login attempt and lockout state
    """
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = timedelta(minutes=15)

    def post(self, request):

        email = request.session.get('auth_email', '').strip().lower()
        password = request.POST.get('password')
        now_time = now()


        # Check session lockout
        attempts = request.session.get('login_attempts', 0)
        first_try = request.session.get('first_attempt_time')
        locked_until = request.session.get('locked_until')

        if locked_until and now_time < datetime.fromisoformat(locked_until):
            return JsonResponse({'authenticated': False, 'error': 'Locked out'}, status=429)
        
        user = authenticate(request, username=email, password=password)

        # ADDED: Explicitly check if user is active
        if user and not user.is_active:
            user = None
            # # Treat inactive user same as invalid credentials
            # # Don't increment attempts counter for inactive users (optional - see note below)
            # return JsonResponse({
            #     'authenticated': False, 
            #     'error': 'Account not activated. Please check your email.'
            # }, status=401)
        

        if user:
            request.session['pending_login_user_id'] = str(user.id)
            request.session.pop('login_attempts', None)
            request.session.pop('first_attempt_time', None)
            request.session.pop('locked_until', None)

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
    # 🟢 View Test Completed
    # 🔴 No Model Test Needed, Since Models will be tested pop_up_orders
    """
    Handles verification of the 6-digit two-factor authentication (2FA) code sent to the user’s email.  
    This view is called after the user successfully enters their password and receives a verification code.

    Workflow:
    1. The user enters the 6-digit code sent to their email address.
    2. The code, along with session data (`2fa_code`, `2fa_code_created_at`, and `pending_login_user_id`),
       is validated to ensure authenticity and freshness.
    3. If the code matches and is within the valid time window (5 minutes):
       - The user is retrieved from the database and logged in using the custom `EmailBackend`.
       - Session data related to 2FA is cleared.
       - A JSON response confirming successful verification is returned.
    4. If the code is invalid, expired, or the session is missing required data:
       - A corresponding error message is returned, and the user is not logged in.

    Security:
        - 2FA codes are valid for 5 minutes to prevent replay attacks.
        - All 2FA-related session data is deleted after verification or expiration.
        - Only numeric, 6-digit codes are accepted.
        - No sensitive data (like passwords) is transmitted in this step.

    Responses:
        200: {"verified": True, "user_name": "<first_name>"} — code valid, user successfully logged in  
        400: {"verified": False, "error": "Invalid Code"} — code incorrect or improperly formatted  
        400: {"verified": False, "error": "Verification code has expired"} — code too old  
        400: {"verified": False, "error": "Invalid timestamp format"} — session data corrupted  
        404: {"verified": False, "error": "User not found"} — user no longer exists  
        200: {"verified": False, "error": "Session expired or invalid"} — session data missing  

    Session Keys Used:
        - '2fa_code': the six-digit code previously generated and emailed
        - '2fa_code_created_at': timestamp when the code was generated
        - 'pending_login_user_id': ID of the authenticated user awaiting 2FA verification

    Notes:
        - This view is only accessible after a successful password check in `Login2FAView`.
        - On success, the user is fully authenticated and logged into the system.
    """
    def post(self, request):
        code_entered = request.POST.get('code', '').strip()
        session_code = request.session.get('2fa_code', '')
        created_at_str = request.session.get('2fa_code_created_at')
        user_id = request.session.get('pending_login_user_id')

        if not all([session_code, created_at_str, user_id]):
            return JsonResponse({"verified": False, "error": "Session expired or invalid"})

        # Check if code is 6 digits
        if not code_entered or not code_entered.isdigit() or len(code_entered) != 6:
            return JsonResponse({'verified': False, 'error': 'Invalid Code'}, status=400)
        

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

                # Check if user is active before login
                if not user.is_active:
                    # clean up session data
                    for key in ['2fa_code', '2fa_code_created_at', 'pending_login_user_id']:
                        request.session.pop(key, None)
                    return JsonResponse({'verified': False, 'error': 'Account is not active'}, status=403)
                login(request, user, backend='pop_accounts.backends.EmailBackend')
                request.session.save()

                for key in ['2fa_code', '2fa_code_created_at', 'pending_login_user_id']:
                    request.session.pop(key, None)

                return JsonResponse({'verified': True, 'user_name': user.first_name})
            except PopUpCustomer.DoesNotExist:
                return JsonResponse({'verified': False, 'error': 'User not found'}, status=404)
        else:
            return JsonResponse({'verified': False, 'error': 'Invalid Code'}, status=400)



class Resend2FACodeView(View):
    def post(self, request):
        """
        Resends 6-digit code at users request
        """
        email = request.session.get('auth_email')        
        user_id = request.session.get('pending_login_user_id')

        if not email or not user_id:
            return JsonResponse({'success': False, 'error': 'Session expired'}, status = 400)
        
        # Verifiy user exisits
        try:
            user = PopUpCustomer.objects.get(id=user_id)
            if not user.is_active:
                return JsonResponse({'success': False, 'error': 'Account not active'}, status=403)
        except PopUpCustomer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
        
        code = generate_2fa_code()
        request.session['2fa_code'] = code
        request.session['2fa_code_created_at'] = timezone.now().isoformat()

        send_mail(
            subject = "Your New Verification Code",
            message=f"Your new code is {code}",
            from_email= "no-reply@thepopup.com",
            recipient_list = [email],
            fail_silently = False
        )

        return JsonResponse({'success': True})


class SendPasswordResetLink(View):
    def post(self, request):
        email = request.POST.get('email')
        return handle_password_reset_request(request, email)


# @require_POST
# def send_password_reset_link(request):
#     """
#     Emails link to user's email address to reset password
#     """
#     email = request.POST.get('email')
#     return handle_password_reset_request(request, email)
    
    

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


