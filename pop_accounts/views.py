from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate, login
from .token import account_activation_token
from orders.views import user_orders
from django.http import JsonResponse
from .models import PopUpCustomer, PasswordResetRequestLog
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import PopUpRegistrationForm
import random
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
import secrets
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.tokens import default_token_generator
from .token_generator import custom_token_generator
import time
from django.core.cache import cache
from django.utils.timezone import now
import logging

logger  = logging.getLogger('security')


# Create your views here.
def user_registration(request):
    register_form = "Register"
    if request.user.is_authenticated:
        return redirect('pop_accounts/admin_accounts/dashboard_pages/dashboard.html')
    
    # if request.method == 'POST':
    #     register_form = PopUpRegistrationForm(request.POST)
    #     if register_form.is_valid():
    #         user = register_form.save(commit=False)
    #         user.email = register_form.cleaned_data['email']
    #         user.set_password(register_form.cleaned_data['password'])
    #         user.is_active = False
    #         user.save()

    #         # setup email
    #         current_site = get_current_site(request)
    #         subject = 'Activate your Account'
    #         message = render_to_string('pop_accounts/registration/account_activation_email.html',{
    #             'user': user,
    #             'domain': current_site.domain,
    #             'uid': urlsafe_base64_encode(force_bytes(user.pk)),
    #             'token': account_activation_token.make_token(user),
    #         })
    #         user.email_user(subject=subject, message=message)

    # else:
    #     register_form = PopUpRegistrationForm()
        return render(request, 'pop_accounts/registration/register.html', {'form', register_form})


def user_login(request):
    login_form = "login"
    # login_form = PopUpUserLoginForm()
    # if request.method == 'POST':
    #     login_form = PopUpUserLoginForm(request.POST)
         
    #     email = request.POST.get('email')
    #     password = request.POST.get('password')
     
    #     print('email', email)
    #     print('password', password)
    
    return render(request, 'pop_accounts/login/login.html', {'form': login_form})



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
        print('POST CALLED!!!')
        if user is None:
            return JsonResponse({'success': False, 'error': 'Invalid reset link.'})
        
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('password2')

        print('new_password', new_password)
        print('confirm_password', confirm_password)

        if not new_password or not confirm_password:
            return JsonResponse({'success': False, 'error': 'All fields are required.'})
        
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'Passwords do not match.'})
        

        user.set_password(new_password)
        user.save()

        return JsonResponse({'success': True, 'message': 'Password reset successful.'})


# @login_required
def dashboard(request):
    orders = user_orders(request)
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/dashboard.html')

# @login_required
def personal_info(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/personal_info.html')

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
@login_required
def total_accounts(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_accounts.html')

# @login_required
def account_sizes(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/account_sizes.html')



def register_modal_view(request):
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = timedelta(minutes=15)
    NewUser = False
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        print('email', email)
        print('password', password)
        print('password2', password2)

        # Registration Form Submit
        if email and password and password2:
            email = request.session.get('auth_email') or request.POST.get('email')
            data = request.POST.copy()
            data['email'] = email
            form = PopUpRegistrationForm(data)

            if form.is_valid():
                new_user = form.save(commit=False)
                new_user.set_password(form.cleaned_data['password'])
                new_user.save()

                # Still log the user in immediately after registration (optional)
                login(request, new_user)
                return JsonResponse({'registered': True})
            else:
                # Return error dict in JSON
                errors = form.errors.as_json()
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            # errors = form.errors.as_json()
            # return JsonResponse({'registered': False, 'errors': errors})


        # Handle Email Check
        if email and not password:
            if validate_email_address(email):
                user_exists = PopUpCustomer.objects.filter(email=email).exists()
                if not user_exists:
                    NewUser = True
                    return JsonResponse({'status': NewUser})
                request.session['auth_email'] = email
                return JsonResponse({'status': NewUser})
        
        # Handle Email and Password Submitted (defer login)
        if password and password2 is None:
            email = request.session.get('auth_email')
            now = timezone.now()
            print('handle sign in email', email)
            print('handle sign in password', password)


            # Initialize session values if not present
            login_attempts = request.session.get('login_attempts', 0)
            first_attempt_time_str = request.session.get('first_attempt_time')
            first_attempt_time = datetime.fromisoformat(first_attempt_time_str) if first_attempt_time_str else now
            locked_until_str = request.session.get('locked_until')
            locked_until = datetime.fromisoformat(locked_until_str) if locked_until_str else None

            # Check for lockout
            if locked_until and now < locked_until:
                return JsonResponse({'authenticated': False, 'error': 'Invalid credentials.'}, status=429)
            

            # Attempt authentication
            user = authenticate(request, email=email, password=password)
            if user:
                # login(request, user)

                # DEFER login until after 2FA is verifief
                request.session['pending_login_user_id'] = str(user.id)

                # Reset session counters
                request.session.pop('login_attempts', None)
                request.session.pop('first_attempt_time', None)
                request.session.pop('locked_until', None)

                # Login is successful, generate and send 2FA code
                code = generate_2fa_code()
                request.session['2fa_code'] = code
                request.session['2fa_code_created_at'] = timezone.now().isoformat()
                # request.session['2fa_user_id'] = str(user.id)


                # send email
                send_mail(
                    subject = "Your Verification Code",
                    message = f"Your code is {code}.",
                    from_email= "no-reply@thepopup.com",
                    recipient_list = [email],
                    fail_silently = False
                )

                return JsonResponse({'authenticated': True, '2fa_required': True})
                # return JsonResponse({'authenticated': True})

            else:
                # Failed login
                if now - first_attempt_time > LOCKOUT_TIME:
                    login_attempts = 1
                    first_attempt_time = now
                else:
                    login_attempts += 1
                
                request.session['login_attempts'] = login_attempts
                request.session['first_attempt_time'] = first_attempt_time.isoformat()

                if login_attempts >= MAX_ATTEMPTS:
                    locked_until = now + LOCKOUT_TIME
                    request.session['locked_until'] = locked_until.isoformat()
                    return JsonResponse({
                        'authenticated': False,
                        'locked_out': True,
                        'error': 'Too many failed attempts. Try again in 15 minutes'
                    }, status=403)
                
                return JsonResponse({'authenticated': False, 'error': f'Invalid credentials. Attempt {login_attempts}/{MAX_ATTEMPTS}'}, status=401)

    return redirect(request.META.get('HTTP_REFERER', '/'))


def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def generate_2fa_code():
    return f"{secrets.randbelow(10**6):06}"


@require_POST
def verify_2fa_code(request):
    code_entered = request.POST.get('code')
    session_code = request.session.get('2fa_code')
    created_at_str = request.session.get('2fa_code_created_at')
    user_id = request.session.get('pending_login_user_id')
    # user_id = request.session.get('2fa_user_id')

    if not all([session_code, created_at_str, user_id]):
        return JsonResponse({"verified": False, "error": "Session expired or invalid"})

    try:
        code_created_at = timezone.datetime.fromisoformat(created_at_str)
        if timezone.is_naive(code_created_at):
            code_created_at = timezone.make_aware(code_created_at)
    except Exception:
        return JsonResponse({'verified': False, 'error': 'Invalid timestamp format'}, status=400)

    
    # code_created_at = timezone.datetime.fromisoformat(created_at_str)

    # Check if more than 5 minutes have passed
    if timezone.now() > code_created_at + timedelta(minutes=5):
        request.session.pop('2fa_code', None)
        request.session.pop('2fa_code_created_at', None)
        request.session.pop('pending_login_user_id', None)
        return JsonResponse({'verified': False, 'error': 'Verification code has expired'}, status=400)
    
        # del request.session['2fa_code']
        # del request.session['2fa_code_created_at']
        # del request.session['2fa_user_id']
        # return JsonResponse({'verified': False, 'error': 'Verification code has expired'}, status=400)


    if str(code_entered).strip() == str(session_code).strip():
        try:
            user = PopUpCustomer.objects.get(id=user_id)
            login(request, user)

            # clean up session 
            for key in ['2fa_code', '2fa_code_created_at', '2fa_user_id']:
                request.session.pop(key, None)
            # request.session.pop('2fa_code', None)
            # request.session.pop('2fa_code_created_at', None)
            # request.session.pop('2fa_user_id', None)

            return JsonResponse({'verified': True, 'user_name': user.first_name})
            # return render(request, 'home.html', {'user': user})
            # print('user is after verif', user, user.first_name)
        except PopUpCustomer.DoesNotExist:
            return JsonResponse({'verified': False, 'error': 'User not found'}, status=404)
        
    else:

        return JsonResponse({'verified': False, 'error': 'Invalid Code'}, status=400)


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
    RATE_LIMIT_SECONDS = 300 # 5 minutes
    
    RESET_EMAIL_COOLDOWN = timedelta(minutes=15)
    email = request.POST.get('email')
    cache_key = f'password_reset_requested: {email}'


    if cache.get(cache_key):
        return JsonResponse(
            {'success': False,  
             'error': 'Please wait before requesting another reset email'}, status=429)
   
    cache.set(cache_key, True, timeout=RATE_LIMIT_SECONDS)
    
    if not email:
        return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)
    
    try:
        user = PopUpCustomer.objects.get(email=email)
    except PopUpCustomer.DoesNotExist:
        time.sleep(1)
        return JsonResponse({'success': False, 'error': 'Email not found'}, status=404)
    

    ip = get_client_ip(request)
    now_time = now()

    # Rate limit based on log history
    recent_request = PasswordResetRequestLog.objects.filter(
    customer=user,
    ip_address=ip,
    requested_at__gte=now_time - RESET_EMAIL_COOLDOWN).exists()

    if recent_request:
        return JsonResponse({'success': False, 'error': 'Reset already requested recently.'}, status=429)

    # Log this reset request
    PasswordResetRequestLog.objects.create(customer=user, ip_address=ip)

    # Build session key
    rate_limit_key = f"password_reset_cooldown_{ip}"

    # Check if this IP has requested recently
    last_request_time = request.session.get(rate_limit_key)
    if last_request_time:
        last_time = timezone.datetime.fromisoformat(last_request_time)

    if now_time - last_time < RESET_EMAIL_COOLDOWN:
        return JsonResponse({'success': False, 'error': 'Reset recently requested. Please wait.'}, status=429)

    # Store current time to session
    request.session[rate_limit_key] = now_time.isoformat()

    # Rate-Limiting Check
    if user.last_password_reset and now_time - user.last_password_reset < RESET_EMAIL_COOLDOWN:
        return JsonResponse({'success': False, 'error': 'Reset already requested recently.'}, status=429)
    
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    logger.info(f"Password reset requested: user={user.email}, ip={get_client_ip(request)}, time={now()}")


    # Build reset URL
    # reset_link = request.build_absolute_uri(reverse('pop_accounts:password_reset') + f'?email={email}')
    reset_link = request.build_absolute_uri(reverse('pop_accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )

    # Send Email
    send_mail(
        subject = "Reset Your Password",
        message=f"Click the link below to reset your password:\n\n{reset_link}",
        from_email= "no-reply@thepopup.com",
        recipient_list = [email],
        fail_silently = False
    )

    user.last_password_reset = now_time
    user.save(update_fields=['last_password_reset'])

    return JsonResponse({'success': True, 'message': 'Password reset link sent.'})

