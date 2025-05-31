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