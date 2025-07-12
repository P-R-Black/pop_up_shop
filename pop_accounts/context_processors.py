from .forms import (PopUpEmailOnlyForm, PopUpPasswordOnlyForm, PopUpRegistrationForm, 
                    PopUpEmailPasswordResetForm, PopUpPasswordResetForm)

from django.db.models import Sum, Count
from .models import PopUpProduct, PopUpCustomer
from pop_accounts.models import PopUpBid
from django.utils import timezone

def auth_forms(request):
    email_form = PopUpEmailOnlyForm()
    password_form = PopUpPasswordOnlyForm()
    registration_form = PopUpRegistrationForm()
    email_password_reset_form = PopUpEmailPasswordResetForm()
    password_reset_form = PopUpPasswordResetForm()
    return {
        'email_form': email_form, 'password_form':password_form, 
        'registration_form': registration_form, 'email_password_reset_form': email_password_reset_form, 
        'password_reset_form': password_reset_form
        }


def admin_status(request):
    """Add admin statistics to every template context"""
    if request.user.is_staff:
        # Most Intereted products count
        # Most interested products count
        total_interest_instances = PopUpProduct.objects.annotate(
            interest_count=Count('interested_users')
        ).filter(interest_count__gt=0).aggregate(
            total=Count('interest_count')
        )['total'] or 0
        
        # Most notified products count
        total_notification_instances = PopUpProduct.objects.annotate(
            notification_count=Count('notified_users')
        ).filter(notification_count__gt=0).aggregate(
            total=Count('notification_count')
        )['total'] or 0
        
        # Total open bids (when you add this model)
        now = timezone.now()
        total_open_bids = PopUpBid.objects.filter(
            product__auction_start_date__isnull=False,
            product__auction_end_date__isnull=False,
            product__auction_start_date__lte=now,
            product__auction_end_date__gte=now,
            is_active=True
        ).count()

        
        # Total active accounts
        total_active_accounts = PopUpCustomer.objects.filter(is_active=True).count()
        
        # Most common shoe size among active accounts
        most_common_size = PopUpCustomer.objects.filter(
            is_active=True
        ).values('shoe_size').annotate(
            count=Count('shoe_size')
        ).order_by('-count').first()
        
        return {
            'admin_stats': {
                'total_interest_instances': total_interest_instances,
                'total_notification_instances': total_notification_instances,
                'total_open_bids': total_open_bids,
                'total_active_accounts': total_active_accounts,
                'most_common_size': most_common_size['shoe_size'] if most_common_size else 'N/A',
                'most_common_size_count': most_common_size['count'] if most_common_size else 0,
            }
        }
    return {}
