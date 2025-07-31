from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re


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
    print('add_specs_to_products queryset', queryset)
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