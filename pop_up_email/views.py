from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta, date, datetime
from django.http import HttpResponse
from auction.models import PopUpProduct
from pop_up_email.utils import send_auction_winner_email

# Create your views here.


def preview_email(request):
    product = PopUpProduct.objects.first()
    user = request.user
    html = send_auction_winner_email(user, product)
    return HttpResponse(html)


def preview_email_confirmation(request):
    current_date = date.today()
    user = request.user
    user_email = request.user.email   
    year = current_date.strftime("%Y")
    context = {
        "user": user,
        "user_email": user_email,
        "year": year,
    }

    html = render_to_string('pop_up_email/email_confirm.html', context)
    return HttpResponse(html)

def preview_two_factor_auth(request):
    # 6 digit code
    six_digit_code = "123456"

    # user & user_email
    user  =request.user
    user_email = request.user.email

    # year
    current_date = date.today()
    year = current_date.strftime("%Y")

    # context
    context = {
        "user": user,
        "user_email": user_email,
        "code": six_digit_code,
        "year": year
    }

    # html
    html = render_to_string('pop_up_email/two_factor.html', context)

    # HttpResponse
    return HttpResponse(html)

