from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from pop_accounts.models import PopUpCustomer
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
    
    cache_key = f"password_reset_requested: {email}"
    if cache.get(cache_key):
        return JsonResponse({'success': False, 'error': 'Please waite before requesting another reset email'})

    try:
        user = PopUpCustomer.objects.get(email=email)
    except PopUpCustomer.DoesNotExist:
        time.sleep(1) # prevent timing attack
        return JsonResponse({'success':False, 'error': 'Email not found.'}, status=404)
    
    ip = get_client_ip(request)
    print('ip', ip)

    # Rate Limiting: IP + User
    recent_request = PopUpPasswordResetRequestLog.objects.filter(
        customer=user,
        ip_address=ip,
        requested_at__gte=now_time - RESET_EMAIL_COOLDOWN
    ).exists()

    if recent_request:
        return JsonResponse({'success': False, 'error': 'Reset already requested recently'}, status=429)
    
    # Session rate limiting
    rate_limit_key = f"password_reset_cooldown_{ip}"
    last_request_time = request.session.get(rate_limit_key)

    if last_request_time:
        try:
            from django.utils import timezone
            last_time = timezone.datetime.fromisoformat(last_request_time)
            if (now_time - last_time) < RESET_EMAIL_COOLDOWN:
                return JsonResponse({'success': False, 'error': 'Reset already requested recently'}, status=429)
        except ValueError:
            pass
    
    if user.last_password_reset and now_time - user.last_password_reset < RESET_EMAIL_COOLDOWN:
        return JsonResponse({'success': False, 'error': 'Reset already request recent'}, status=429)
    
    # Save to session and log
    request.session[rate_limit_key] = now_time.isoformat()
    cache.set(cache_key, True, timeout=RATE_LIMIT_SECONDS)
    PopUpPasswordResetRequestLog.objects.create(customer=user, ip_address=ip)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = request.build_absolute_uri(reverse('pop_accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

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
            'success': False, 'error': 'Unable to send email at this time. Please try again later.'
        }, status=500)

    user.last_password_reset = now_time
    user.save(update_fields=['last_password_reset'])

    return JsonResponse({'success': True, 'message': 'Password reset link sent'})
    

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
    Retrieve client IP address from request headers, accounting for proxies
    """
    x_forward_for = request.META.get('HTTP_X_FORWWARED_FOR')
    if x_forward_for:
        ip = x_forward_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



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
