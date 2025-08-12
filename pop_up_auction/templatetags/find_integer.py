from django import template

register = template.Library()

@register.filter
def is_val_integer(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False