from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import PopUpFinance


def get_yearly_revenue_aggregated():
    now = timezone.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    revenue_expression = ExpressionWrapper(
        F('final_price') - F('refunded_amount'),
        output_field=DecimalField()
    )

    result =  (
        PopUpFinance.objects
        .filter(sold_at__gte=start_of_year)
        .aggregate(total=Sum(revenue_expression))['total'] or 0
    )

    return round(result or 0, 2)




def get_current_year_revenue():
    now = timezone.now()
    start_of_year = now.replace(month=1, days=1, hour=0, minute=0, second=0, microsecond=0)
    finances = PopUpFinance.objects.filter(sold_at__gte=start_of_year)
    return sum(f.calculate_revenue() for f in finances)


def get_monthly_revenue():
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    finances = PopUpFinance.objects.filter(sold_at__gte=start_of_month)
    return sum(f.calculate_revenue() for f in finances)



def get_weekly_revenue():
    now = timezone.now()
    start_of_week = now - timedelta(days=now.weekday())  # Monday start
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    finances = PopUpFinance.objects.filter(sold_at__gte=start_of_week)
    return sum(f.calculate_revenue() for f in finances)


def get_revenue_by_payment_method(payment_method):
    finances = PopUpFinance.objects.filter(payment_method=payment_method)
    return sum(f.calculate_revenue() for f in finances)