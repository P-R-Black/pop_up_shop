from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from pop_accounts.models import PopUpCustomer, PopUpCustomerIP
from django.conf import settings
import stripe
from datetime import timedelta
import time
import logging
from django.utils.timezone import now
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.mail import send_mail
from django.core.cache import cache
from django.http import JsonResponse
from pop_accounts.models import PopUpCustomer, PopUpPasswordResetRequestLog
from ipware import get_client_ip as ipware_get_client_ip
import geoip2.database
import os

logger = logging.getLogger(__name__)
RESET_EMAIL_COOLDOWN = timedelta(minutes=5)
RATE_LIMIT_SECONDS = 120 # 2 minutes


def send_verification_email(request, user):
    """
    Send email verification link to user
    
    Args:
        request: HTTP request object (for building absolute URL)
        user: PopUpCustomer instance to send verification to
    """
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        verify_url = request.build_absolute_uri(reverse(
            'pop_accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
            )
      
        subject = "Verify Your Email"
        message = f"Hi {user.first_name}, \n\nPlease click the link below to verify your email:\n{verify_url}\n\nThanks!"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        return True
    except Exception as e:
        print(f'Error sending verification email: {e}')
        return False



def handle_password_reset_request(request, email: str):
    """Utility to handle sending a password reset link with rate limiting"""

    now_time = now()
    if not email:
        return JsonResponse({'success': False, 'error': 'An email address is required'}, status=400)
    

    if not validate_email_address(email):
        return JsonResponse({'success': False, 'error': 'Invalid email format'}, status=400)


    ip = get_client_ip(request)
    is_allowed, remaining = check_rate_limit(ip, 'password_reset', max_attempts=3)
    if not is_allowed:
        return JsonResponse({
            'success': False, 
            'error': 'Too many password reset attempts. Please try again later.'
        }, status=429)

    cache_key = f"password_reset_requested: {email}"
    if cache.get(cache_key):
        return JsonResponse({'success': False, 'error': 'Please wait before requesting another reset email'})

    try:
        user = PopUpCustomer.objects.get(email=email)
        user_exists = True
    except PopUpCustomer.DoesNotExist:
        user_exists = False
        time.sleep(1) # prevent timing attack
        # return JsonResponse({'success':True, 'error': 'If an account exists, a password reset link has been sent.'}, status=404)
    # After sending email, return same message

    # ✅ Always return same message regardless of whether user exists
    if not user_exists:
        return JsonResponse({
            'success': True,  # ✅ Changed to True
            'message': 'If an account exists, a password reset link has been sent.' })

    
    # Check user-specific rate limiting
    if user.last_password_reset and now_time - user.last_password_reset < RESET_EMAIL_COOLDOWN:
        return JsonResponse({
            'success': False, 
            'error': 'Reset already requested recently'
        }, status=429)
    
    # Increment rate limit
    increment_rate_limit(ip, 'password_reset')
    
    # Log the request
    PopUpPasswordResetRequestLog.objects.create(customer=user, ip_address=ip)

    # Generate reset link
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = request.build_absolute_uri(
        reverse('pop_accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )

    logger.info(f"Password reset requested: user={user.email}, ip={ip}, time={now_time}")

    try:
        send_mail(
            subject="Reset Your Password",
            message=f"Click the link below to reset your password:\n\n{reset_link}",
            from_email="no-reply@thepopup.com",
            recipient_list=[email],
            fail_silently=False
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'Unable to send email at this time. Please try again later.'
        }, status=500)

    user.last_password_reset = now_time
    user.save(update_fields=['last_password_reset'])

    # ✅ Return same message as non-existent user case
    return JsonResponse({
        'success': True, 
        'message': 'If an account exists, a password reset link has been sent.'
    })
    # # Rate Limiting: IP + User
    # recent_request = PopUpPasswordResetRequestLog.objects.filter(
    #     customer=user,
    #     ip_address=ip,
    #     requested_at__gte=now_time - RESET_EMAIL_COOLDOWN
    # ).exists()

    # if recent_request:
    #     return JsonResponse({'success': False, 'error': 'Reset already requested recently'}, status=429)
    
    # Session rate limiting
    # rate_limit_key = f"password_reset_cooldown_{ip}"
    # last_request_time = request.session.get(rate_limit_key)

    # if last_request_time:
    #     try:
    #         from django.utils import timezone
    #         last_time = timezone.datetime.fromisoformat(last_request_time)
    #         if (now_time - last_time) < RESET_EMAIL_COOLDOWN:
    #             return JsonResponse({'success': False, 'error': 'Reset already requested recently'}, status=429)
    #     except ValueError:
    #         pass
    
    # if user.last_password_reset and now_time - user.last_password_reset < RESET_EMAIL_COOLDOWN:
    #     return JsonResponse({'success': False, 'error': 'Reset already request recent'}, status=429)
    
    # # Save to session and log
    # request.session[rate_limit_key] = now_time.isoformat()
    # cache.set(cache_key, True, timeout=RATE_LIMIT_SECONDS)
    # PopUpPasswordResetRequestLog.objects.create(customer=user, ip_address=ip)

    # uid = urlsafe_base64_encode(force_bytes(user.pk))
    # token = default_token_generator.make_token(user)
    # reset_link = request.build_absolute_uri(reverse('pop_accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

    # logger.info(f"Password reset requested: user={user.email}, ip={ip}, time={now_time}")
    # try:
    #     send_mail(
    #         subject="Reset Your Password",
    #         message=f"Click the link below to reset your password:\n\n{reset_link}",
    #         from_email="no-reply@thepopup.com",
    #         recipient_list=[email],
    #         fail_silently=False
    #     )
    # except Exception as e:
    #     logger.error(f"Failed to send password reset email to {email}: {str(e)}")
    #     return JsonResponse({
    #         'success': False, 'error': 'Unable to send email at this time. Please try again later.'
    #     }, status=500)

    # user.last_password_reset = now_time
    # user.save(update_fields=['last_password_reset'])
    # # After sending email, return same message
    # return JsonResponse({
    #     'success': True, 
    #     'message': 'If an account exists, a password reset link has been sent.'
    # })
    # return JsonResponse({'success': True, 'message': 'Password reset link sent'})
    

def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def validate_password_strength(password):

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lower case letter")
        
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at lease one number.")
        
        if not re.search(f'[!@#$%^&*(),.?":|<>]', password):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*(),.?":|<>)')



def get_client_ip(request):
    """
    Retrieve client IP address from request headers, accounting for proxies.
    
    IMPORTANT: Only trust X-Forwarded-For if behind a trusted proxy/load balancer.
    In production behind nginx/AWS ALB/Cloudflare, this is safe.
    In development or direct-to-Django, only use REMOTE_ADDR.
    """
    client_ip, is_routable = ipware_get_client_ip(request)
    
    if client_ip is None:
        # Unable to get IP
        return '0.0.0.0'
    
    return client_ip



def add_specs_to_products(queryset):
    """Helper function to add specs dictionary to each product"""
    products = list(queryset)
    for product in products:
        product.specs = {
            spec.specification.name: spec.value
            for spec in product.popupproductspecificationvalue_set.all()
        }
    return products


def calculate_auction_progress(product, now):
    """Calculate what percentage of the auction time has passed"""
    if not product.auction_start_date or not product.auction_end_date:
        return 0
    
    total_duration = product.auction_end_date - product.auction_start_date
    elapsed_time = now - product.auction_start_date
    
    if total_duration.total_seconds() == 0:
        return 100
    
    progress = (elapsed_time.total_seconds() / total_duration.total_seconds()) * 100
    return min(max(progress, 0), 100)  # Clamp between 0 and 100


stripe.api_key = settings.STRIPE_SECRET_KEY
def get_stripe_payment_reference(user):
    """
    Fetch a user's saved payment methods (cards) from Stripe.
    Returns a list of dicts with brand, last4, and expiry info.
    """
    payment_methods = []
    customer_id = getattr(user, 'stripe_customer_id', None)

    if not customer_id:
        return payment_methods

    try:
        methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card"
        )

        for pm in methods['data']:
            payment_methods.append({
                'brand': pm.card.brand.title(), # e.g. "Visa"
                'last4': pm.card.last4,     # e.g. "4321"
                'exp_month': pm.card.exp_month,
                'exp_year': pm.card.exp_year,
                'wallet': getattr(pm.card, 'wallet', None),   # e.g. 'apple_pay' or None
            })
    except stripe.error.StripeError as e:
        # Optonal: log or handle errors gracefully
        print('stripe error: {e}')
        
    return payment_methods


def is_disposable_email(email):
    """
    Check if email is from a disposable/temporary email service.
    
    Args:
        email (str): Email address to check
        
    Returns:
        bool: True if disposable, False otherwise
    """
    with open('pop_accounts/utils/disposable_email_blocklist.conf') as blocklist:
        blocklist_content = {line.rstrip() for line in blocklist.readlines()}
        domain_parts = email.partition('@')[2].split(".")
        for i in range(len(domain_parts) - 1):
            if ".".join(domain_parts[i:]) in blocklist_content:
                return True
        return False
    
    

def check_rate_limit(ip_address, action_type, max_attempts=4, window_seconds=3600):
    """
    Check if IP has exceeded rate limit for a specific action.
    
    Args:
        ip_address (str): IP address to check
        action_type (str): Type of action (e.g., 'registration', 'password_reset')
        max_attempts (int): Maximum attempts allowed
        window_seconds (int): Time window in seconds
        
    Returns:
        tuple: (is_allowed: bool, attempts_remaining: int)
    """
    cache_key = f"{action_type}_attempt_{ip_address}"
    attempts = cache.get(cache_key, 0)
    if attempts >= max_attempts:
        return False, 0
    
    return True, max_attempts - attempts


def increment_rate_limit(ip_address, action_type, window_seconds=3600):
    """
    Increment rate limit counter for an IP and action.
    
    Args:
        ip_address (str): IP address
        action_type (str): Type of action
        window_seconds (int): Time window in seconds
    """
    print('increment_rate_limit called')
    cache_key = f"{action_type}_attempt_{ip_address}"
    print('cache_key', cache_key)
    attempts = cache.get(cache_key, 0)
    print('attempts', attempts)
    cache.set(cache_key, attempts + 1, window_seconds)


def log_registration_with_geo(request, user):
    """Log registratino with geogrpahic data"""
    ip = get_client_ip(request)
    try:
        # Use Django settings for the path
        # db_path = os.path.join(settings.GEOIP_PATH, GEOIP_CITY)
        db_path = "/Users/paulblack/VS Code/pop_up_shop/geoip/GeoLite2-City.mmdb"        
        reader = geoip2.database.Reader(db_path)
        response = reader.city(ip)
      
        country = response.country.iso_code
        city = response.city.name if response.city.name else "Unknown"


        # Update your IP Tracking Record
        PopUpCustomerIP.objects.filter(customer=user, ip_address=ip).update(country=country,city=city)

        # Alert if high-risk country
        if country in ['RU', 'CN', 'UA', 'KP']:
            logger.warning(
                f"Registration from high-risk country: "
                f"email={user.email}, ip={ip}, country={country}, city={city}"
            )
        reader.close()
    except FileNotFoundError:
        logger.error('GEOIP database not found. Please download GeoLite2-City.mmdb')
    except Exception as e:
        logger.error(f'GeoIp lookup failed: {e}')


def get_email_provider(email):
    """Extract email provider domain"""
    return email.split('@')[1].lower()