from django import template
import re

register = template.Library()

@register.filter
def obfuscate_email(value):
    try:
        username, domain = value.split('@')
        if len(username) <= 2:
            masked_username = username[0] + "*" * (len(username) - 1)
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    except Exception:
        return value