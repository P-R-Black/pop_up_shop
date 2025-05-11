from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from .token import account_activation_token
from orders.views import user_orders
from django.http import JsonResponse, HttpResponse
from .models import PopUpCustomer, PopUpPasswordResetRequestLog, PopUpCustomerAddress
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import PopUpRegistrationForm, PopUpUserLoginForm, PopUpUserEditForm, ThePopUpUserAddressForm
import random
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
import secrets
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.tokens import default_token_generator
import time
from django.core.cache import cache
from django.utils.timezone import now
from django.contrib.auth import logout
from django.views import View
from .utils import validate_email_address
from django.conf import settings
import hashlib

import logging



logger  = logging.getLogger('security')


# Create your views here.
class UserLoginView(View):
    template_name = 'pop_accounts/login/login.html'
    form_class = PopUpUserLoginForm
    success_url = '/dashboard/'  # Change to wherever you want to redirect on success

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect(self.get_success_url())
        else:
            form.add_error(None, 'Invalid email or password')
            return self.form_invalid(form)
        


class UserLogOutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/')

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('/')
    


def user_password_reset(request):
    if request.method == "POST":
        email  = request.POST.get('email')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not email or not new_password or not confirm_password:
            return JsonResponse({'success': False, 'error': 'All fields are requred'})
        
        if new_password != confirm_password:
            return JsonResponse({'sucess': False, 'error': 'Passwords do not match.'})
        
        try:
            user = PopUpCustomer.objects.get(email=email)
        except PopUpCustomer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid email address.'})
        
        # Set new password
        user.set_password(new_password)
        user.save()
        return JsonResponse({'success': True, 'message': 'Password has been reset successfully.'})
    
    return render(request, 'pop_accounts/login/password_reset.html')



def user_password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = PopUpCustomer.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, PopUpCustomer.DoesNotExist) as e:
        user = None
    
    if request.method == 'GET':
        if user is not None and default_token_generator.check_token(user, token):
            return render(request, 'pop_accounts/login/password_reset_confirm.html', {
                'validlink': True, 
                'uidb64': uidb64, 
                'token': token
                })
        else:
            return render(request, 'pop_accounts/login/password_reset_confirm.html', {'validlink': False})
        
    elif request.method == 'POST':
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
    template_name = 'pop_accounts/user_accounts/dashboard_pages/dashboard.html'
    def get(self, request):
        user = request.user
        addresses = user.address.all()
        context = {'user': user, 'addresses': addresses}
        return render(request, self.template_name, context)

    def post(self, request):
        return render(request, self.template_name)


@login_required
def personal_info(request):
    user = request.user
    addresses = PopUpCustomerAddress.objects.filter(customer=user)

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

    if request.method == "POST":

        # Determine which form as been submitted
        if 'first_name' in request.POST:

            # It's the personal info form
            personal_form = PopUpUserEditForm(request.POST)
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

                messages.success(request, "Your profile has been updated.")
                return redirect('pop_accounts:personal_info')
            
        elif 'street_address_1' in request.POST:

            address_id = request.POST.get('address_id')
            print('address_id', address_id)
            
            if address_id:
                # Edit existing address
                address= get_object_or_404(PopUpCustomerAddress, id=address_id, customer=user)
                address_form = ThePopUpUserAddressForm(request.POST, instance=address)
            else:
                address_form= ThePopUpUserAddressForm(request.POST)
                # print('else address', address)
            
            # It's the address form          
            address_form.is_valid()
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.customer = user
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
                messages.success(request,msg)
                # messages.success(request, "Address has been added.")
                return redirect('pop_accounts:personal_info')
           
        
    # else:
    #     personal_form = PopUpUserEditForm(initial={
    #         'first_name': user.first_name,
    #         'middle_name': user.middle_name,
    #         'last_name': user.last_name,
    #         'shoe_size': user.shoe_size,
    #         'size_gender': user.size_gender,
    #         'favorite_brand': user.favorite_brand,
    #         'mobile_phone': user.mobile_phone,
    #         'mobile_notification': user.mobile_notification
    #         })


    return render(request, 'pop_accounts/user_accounts/dashboard_pages/personal_info.html', {
        'form': personal_form, 'address_form': address_form, 'addresses': addresses, 'user': user})


@login_required
def get_address(request, address_id):
    address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=request.user)
    return JsonResponse({
        'address_line': address.address_line,
        'address_line2': address.address_line2,
        'apartment_suite_number': address.apartment_suite_number,
        'town_city': address.town_city,
        'state': address.state,
        'postcode': address.postcode,
        'delivery_instructions': address.delivery_instructions,
    })

@login_required
def delete_address(request, address_id):
    if request.method == "POST":
        address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=request.user)
        address.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid Request'}, status=400)


@login_required
def set_default_address(request, address_id):
    user = request.user
    try:
        address = get_object_or_404(PopUpCustomerAddress, id=address_id, customer=request.user, deleted_at__isnull=True)
        # Unset all other address
        PopUpCustomerAddress.objects.filter(customer=user, default=True).update(default=False)

        # Set selected address as default
        address.default = True
        address.save()

        return JsonResponse({'success': True})
    except PopUpCustomerAddress.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)






# @login_required
def interested_in(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/interested_in.html')

# @login_required
def on_notice(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/on_notice.html')

# @login_required
def open_bids(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/open_bids.html')

# @login_required
def past_bids(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/past_bids.html')

# @login_required
def past_purchases(request):
    orders = user_orders(request)
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/past_purchases.html')

# ADMIN DASHBOARD
# @login_required
def dashboard_admin(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/dashboard.html')

# @login_required
def inventory(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/inventory.html')

# @login_required
def sales(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/sales.html')

# @login_required
def most_on_notice(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_on_notice.html')

# @login_required
def most_interested(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_interested.html')

# @login_required
def total_open_bids(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_open_bids.html')

# @login_required
def total_accounts(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_accounts.html')

# @login_required
def account_sizes(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/account_sizes.html')


class EmailCheckView(View):
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
    def post(self, request):
        email = request.session.get('auth_email') or request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # email = request.session.get('auth_email') or request.POST.get('email')
        # print('we\'ve got email', email)

        # data = request.POST.copy()
        # data['email'] = email

        # print('data', data)
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
                try:
                    self.send_verification_email(request, user)
                except Exception as e:
                    print('Error sending verification email', e)
                # login(request, user)
                return JsonResponse({'registered': True, 'message': 'Check your email to confirm your account'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
            
        elif email and password:
            return JsonResponse({'success': False, 'errors': 'Please confirm password'}, status=400)
    
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
    print('Login2FAView called!')
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




# @require_POST
# def verify_2fa_code(request):
#     code_entered = request.POST.get('code')
#     session_code = request.session.get('2fa_code')
#     created_at_str = request.session.get('2fa_code_created_at')
#     user_id = request.session.get('pending_login_user_id')
#     # user_id = request.session.get('2fa_user_id')

#     if not all([session_code, created_at_str, user_id]):
#         return JsonResponse({"verified": False, "error": "Session expired or invalid"})

#     try:
#         code_created_at = timezone.datetime.fromisoformat(created_at_str)
#         if timezone.is_naive(code_created_at):
#             code_created_at = timezone.make_aware(code_created_at)
#     except Exception:
#         return JsonResponse({'verified': False, 'error': 'Invalid timestamp format'}, status=400)

    
#     # code_created_at = timezone.datetime.fromisoformat(created_at_str)

#     # Check if more than 5 minutes have passed
#     if timezone.now() > code_created_at + timedelta(minutes=5):
#         request.session.pop('2fa_code', None)
#         request.session.pop('2fa_code_created_at', None)
#         request.session.pop('pending_login_user_id', None)
#         return JsonResponse({'verified': False, 'error': 'Verification code has expired'}, status=400)

    
#     if str(code_entered).strip() == str(session_code).strip():
#         try:
#             user = PopUpCustomer.objects.get(id=user_id)
#             login(request, user, backend='pop_accounts.backends.EmailBackend')
#             request.session.save()
#             # request.session.modified = True
#             # request.session['just_logged_in'] = True  # Force session to be saved
#             # request.session.save()    

#             print("Session key after login:", request.session.session_key)
#             print("Authenticated in view?", request.user.is_authenticated)
#             print("User ID in session:", request.session.get('_auth_user_id'))

#             # login(request, user)

#             # clean up session 
#             for key in ['2fa_code', '2fa_code_created_at', 'pending_login_user_id']:
#                 print('key', key)
#                 request.session.pop(key, None)
     

#             return JsonResponse({'verified': True, 'user_name': user.first_name})
#             # return render(request, 'home.html', {'user': user})
#             # print('user is after verif', user, user.first_name)
#         except PopUpCustomer.DoesNotExist:
#             return JsonResponse({'verified': False, 'error': 'User not found'}, status=404)
        
#     else:

#         return JsonResponse({'verified': False, 'error': 'Invalid Code'}, status=400)


@require_POST
def resend_2fa_code(request):
    email = request.session.get('auth_email')
    user_id = request.session.get('2fa_user_id')

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


# Get IP address
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
    


@require_POST
def send_password_reset_link(request):
    RESET_EMAIL_COOLDOWN = timedelta(minutes=5)
    RATE_LIMIT_SECONDS = 120 # 300 # 5 minutes

    email = request.POST.get('email')
    now_time = now()

    if not email:
        return JsonResponse({'success': False, 'error': 'An email address is required'}, status=400)
    

    cache_key = f'password_reset_requested:{email}'
    if cache.get(cache_key):
        return JsonResponse({'success': False, 'error': 'Please wait before requesting another reset email.'}, status=429)

    try:
        user = PopUpCustomer.objects.get(email=email)
    except PopUpCustomer.DoesNotExist:
        time.sleep(1)  # To prevent user enumeration
        return JsonResponse({'success': False, 'error': 'Email not found.'}, status=404)
    

    ip = get_client_ip(request)
    now_time = now()

    # Rate limiting: IP + User
    recent_request = PopUpPasswordResetRequestLog.objects.filter(
        customer=user,
        ip_address=ip,
        requested_at__gte=now_time - RESET_EMAIL_COOLDOWN
    ).exists()

    print('recent_request', recent_request)
    if recent_request:
        return JsonResponse({'success': False, 'error': 'Reset already requested recently.'}, status=429)
   
    # Session rate limiting
    rate_limit_key = f'password_reset_cooldown_{ip}'
    last_request_time = request.session.get(rate_limit_key)

    if last_request_time:
        try:
            last_time = timezone.datetime.fromisoformat(last_request_time) 
            if (now_time - last_time) < RESET_EMAIL_COOLDOWN:
                return JsonResponse({'success': False, 'error': 'Reset already requested recently.'}, status=429)
        except ValueError:
            pass  # Ignore malformed session data
    
    # User-based cooldown
    if user.last_password_reset and now_time - user.last_password_reset < RESET_EMAIL_COOLDOWN:
        return JsonResponse({'success': False, 'error': 'Reset already requested recently.'}, status=429)

    # Save to session and log
    request.session[rate_limit_key] = now_time.isoformat()
    cache.set(cache_key, True, timeout=RATE_LIMIT_SECONDS)
    PopUpPasswordResetRequestLog.objects.create(customer=user, ip_address=ip)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = request.build_absolute_uri(reverse('pop_accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

    logger.info(f"Password reset requested: user={user.email}, ip={ip}, time={now_time}")

    send_mail(
        subject="Reset Your Password",
        message=f"Click the link below to reset your password:\n\n{reset_link}",
        from_email="no-reply@thepopup.com",
        recipient_list=[email],
        fail_silently=False,
    )

    user.last_password_reset = now_time
    user.save(update_fields=['last_password_reset'])

    return JsonResponse({'success': True, 'message': 'Password reset link sent.'})
    

class VerifyEmailView(View):
    template_name = 'pop_accounts/registration/verify_email.html'

    def get(self, request, uidb64, token):
        login_form = PopUpUserLoginForm()   
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None

        
        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return render(request, self.template_name, {'email_verified': True, 'form': login_form, 'uidb64': uidb64, 'token': token })
        else:
            return render(request, self.template_name, {'invalid_link': True, 'form': login_form})
    
    def post(self, request, uidb64, token):
        form = PopUpUserLoginForm()
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

