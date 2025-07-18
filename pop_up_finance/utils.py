from django.utils import timezone
from datetime import timedelta, date
from django.utils.timezone import now
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import PopUpFinance
from collections import OrderedDict
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear, ExtractYear, ExtractMonth
from dateutil.relativedelta import relativedelta
import calendar

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


def get_last_5_years_sales():
    today = now().date()
    five_years_ago = today - relativedelta(years=4)

    sales_qs = (
        PopUpFinance.objects
        .filter(sold_at__date__gte=five_years_ago.replace(month=1, day=1))
        .annotate(year=TruncYear('sold_at'))
        .values('year')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
        .order_by('year')
    )

    year_totals = OrderedDict()
    current_year = today.year
    for y in range(current_year - 4, current_year + 1):
        year_totals[str(y)] = 0
    
    for entry in sales_qs:
        year_str = entry['year'].year
        year_totals[str(year_str)] = float(entry['total_sales'])
    
    return {
        'labels': list(year_totals.keys()),
        'data': list(year_totals.values())
            }



def get_last_12_months_sales():
    today = now().date()
    twelve_months_ago = today - relativedelta(months=11)

    sales_qs = (
        PopUpFinance.objects
        .filter(sold_at__date__gte=twelve_months_ago)
        .annotate(month=TruncMonth('sold_at'))
        .values('month')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
        .order_by('month')
    )

    # Fill in missing months with 0 sales
    month_totals = OrderedDict()
    current = twelve_months_ago.replace(day=1)
    for _ in range(12):
        month_totals[current.strftime("%Y-%m")] = 0
        current += relativedelta(months=1)
    
    for entry in sales_qs:
        month_str = entry['month'].strftime("%Y-%m")
        month_totals[month_str] = float(entry['total_sales'])
    
    return {
        'labels': list(month_totals.keys()),
        'data': list(month_totals.values())
    }



def get_last_20_days_sales():
    today = now().date()
    twenty_days_ago = today - timedelta(days=19)

    sales_qs = (
        PopUpFinance.objects
            .filter(sold_at__date__gte=twenty_days_ago)
            .annotate(day=TruncDate('sold_at'))
            .values('day')
            .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
            .order_by('day')
    )

    # Fill in missing days with 0 sales
    day_totals = OrderedDict()
    for i in range(20):
        day = twenty_days_ago + timedelta(days = i)
        day_totals[day.strftime("%Y-%m-%d")] = 0
    
    for entry in sales_qs:
        day_str = entry['day'].strftime("%Y-%m-%d")
        day_totals[day_str] = float(entry['total_sales'])
    
    return {
        'labels': list(day_totals.keys()),
        'data': list(day_totals.values()),
    }


def get_yoy_day_sales(days=20):
    today = now().date()
    start_date = today - timedelta(days=days - 1)

    # Prepare dates for current and previous year
    date_pairs = [(start_date + timedelta(days=i)) for i in range(days)]

    current_year_sales = {d.strftime("%Y-%m-%d"): 0 for d in date_pairs}
    last_year_sales = {(d - timedelta(days=365)).strftime("%Y-%m-%d") for d in date_pairs}
    
    # Get sales for current year
    current_qs = (
        PopUpFinance.objects
        .filter(sold_at__date__in=date_pairs)
        .values('sold_at__date')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
    )

    for entry in current_qs:
        date_str = entry['sold_at__date'].strftime("%Y-%m-%d")
        current_year_sales[date_str] = float(entry['total_sales'])

    # Get sales for same days in the previous year
    prev_year_dates = [d - timedelta(days=365) for d in date_pairs]
    previous_year_sales = {d.strftime("%Y-%m-%d"): 0 for d in prev_year_dates}

    prev_qs = (
        PopUpFinance.objects
        .filter(sold_at__date__in=prev_year_dates)
        .values('sold_at__date')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
    )

    for entry in prev_qs:
        date_str = entry['sold_at__date'].strftime("%Y-%m-%d")
        previous_year_sales[date_str] = float(entry['total_sales'])

    return {
        'labels': [d.strftime("%m-%d") for d in date_pairs],  # X-axis: just the day/month
        'current_year': list(current_year_sales.values()),
        'previous_year': list(previous_year_sales.values())
    }


def get_year_over_year_comparison():
    today = now().date()
    current_year = today.year
    previous_year = current_year - 1

    # Get all months Jan–Dec
    months = [i for i in range(1, 13)]
    month_labels = [calendar.month_abbr[m] for m in months]  # ['Jan', 'Feb', ..., 'Dec']

    # Initialize dictionaries for both years
    current_year_sales = OrderedDict((m, 0) for m in months)
    previous_year_sales = OrderedDict((m, 0) for m in months)

    # Query sales for both years
    sales_qs = (
        PopUpFinance.objects
        .filter(sold_at__year__in=[current_year, previous_year])
        .annotate(year=ExtractYear('sold_at'), month=ExtractMonth('sold_at'))
        .values('year', 'month')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
    )

    for entry in sales_qs:
        year = entry['year']
        month = entry['month']
        total = float(entry['total_sales'])

        if year == current_year:
            current_year_sales[month] = total
        elif year == previous_year:
            previous_year_sales[month] = total

    return {
        'labels': month_labels,  # X-axis: month names
        'current_year': list(current_year_sales.values()),
        'previous_year': list(previous_year_sales.values()),
    }



def get_month_over_month_comparison():
    today = now().date()
    start_month = today.replace(day=1) - relativedelta(months=11)

    # Current year data
    current_qs = (
        PopUpFinance.objects
        .filter(sold_at__date__gte=start_month)
        .annotate(month=TruncMonth('sold_at'))
        .values('month')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
    )

    # Previous year, same range
    last_year_start = start_month.replace(year=start_month.year - 1)
    last_year_end = today.replace(year=today.year - 1)

    previous_qs = (
        PopUpFinance.objects
        .filter(sold_at__date__range=(last_year_start, last_year_end))
        .annotate(month=TruncMonth('sold_at'))
        .values('month')
        .annotate(total_sales=Sum(F('final_price') - F('refunded_amount')))
    )

    # Prepare the data
    current_data = {entry['month'].strftime("%Y-%m"): float(entry['total_sales']) for entry in current_qs}
    previous_data = {entry['month'].replace(year=entry['month'].year + 1).strftime("%Y-%m"): float(entry['total_sales']) for entry in previous_qs}

    labels = []
    current_year = []
    previous_year = []

    for i in range(12):
        month = start_month + relativedelta(months=i)
        key = month.strftime("%Y-%m")
        labels.append(key)
        current_year.append(current_data.get(key, 0))
        previous_year.append(previous_data.get(key, 0))

    return {
        'labels': labels,
        'current_year': current_year,
        'previous_year': previous_year
    }