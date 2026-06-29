# pop_up_auction/templatetags/date_filters.py

from django import template
from django.utils import timezone
from datetime import timedelta
from dateutil import parser  # pip install python-dateutil

register = template.Library()

@register.filter
def is_within_days(release_date, days=10):
    """Check if release date is within N days from now"""
    if not release_date:
        return False
    
    # Convert string to datetime if needed
    if isinstance(release_date, str):
        try:
            release_date = parser.parse(release_date)
        except (ValueError, TypeError):
            return False
    
    now = timezone.now()
    future_date = now + timedelta(days=days)
    
    # Make sure we're comparing timezone-aware datetimes
    if release_date.tzinfo is None:
        release_date = timezone.make_aware(release_date)
    
    return now <= release_date <= future_date

@register.filter
def days_until_release(release_date):
    """Calculate days until release"""
    if not release_date:
        return None
    
    # Convert string to datetime if needed
    if isinstance(release_date, str):
        try:
            release_date = parser.parse(release_date)
        except (ValueError, TypeError):
            return None
    
    now = timezone.now()
    
    # Make sure we're comparing timezone-aware datetimes
    if release_date.tzinfo is None:
        release_date = timezone.make_aware(release_date)
    
    delta = release_date - now
    return delta.days