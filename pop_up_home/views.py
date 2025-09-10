from django.shortcuts import render
from django.http import HttpResponse
import os
import environ
from .pop_up_home_copy.site_info_copy.site_info_copy import (ABOUT_US_COPY, HOW_IT_WORKS_COPY, 
                                                             VERIFICATION_COPY, CONTACT_US_COPY)

# Create your views here.
def home_page(request):
    return render(request, 'pop_up_home/index.html')

# site and usage info
def about_us(request):
    about_us_copy = ABOUT_US_COPY
    return render(request, 'pop_up_home/site_info/about_us.html', {'about_us_copy': about_us_copy})

def how_it_works(request):
    how_it_works_copy = HOW_IT_WORKS_COPY
    return render(request, 'pop_up_home/site_info/how_it_works.html', {"how_it_works_copy": how_it_works_copy })

def verification(request):
    verification_copy = VERIFICATION_COPY
    return render(request, 'pop_up_home/site_info/verification.html', {"verification_copy": verification_copy})

def contact_us(request):
    contact_us_copy = CONTACT_US_COPY
    return render(request, 'pop_up_home/site_info/contact_us.html', {"contact_us_copy": contact_us_copy})

def help_center(request):
    return render(request, 'pop_up_home/site_info/help_center.html')

def terms_and_conditions(request):
    return render(request, ('pop_up_home/footer_links/terms_and_conditions.html'))

def privacy_policy(request):
    return render(request, 'pop_up_home/footer_links/privacy.html')

def privacy_choice(request):
    # Need to add functionality for user to opt out of tracking
    return render(request, 'pop_up_home/footer_links/privacy_choices.html')

# help_center_pages
def buying_help(request):
    return render(request, 'pop_up_home/site_info/help_center_pages/buying_page.html')

def selling_help(request):
    return render(request, 'pop_up_home/site_info/help_center_pages/selling_page.html')

def account_help(request):
    return render(request, 'pop_up_home/site_info/help_center_pages/my_account_page.html')

def shipping_help(request):
    return render(request, 'pop_up_home/site_info/help_center_pages/shipping_page.html')

def payment_help(request):
    return render(request, 'pop_up_home/site_info/help_center_pages/payment_options_page.html')

def fees_help(request):
    return render(request, 'pop_up_home/site_info/help_center_pages/fees_page.html')

def friend_invite_success(request):
    return render(request, 'pop_up_home/confirmations/friend_invite_success.html')

def friend_invite_failure(request):
    return render(request, 'pop_up_home/error/friend_invite_fail.html')