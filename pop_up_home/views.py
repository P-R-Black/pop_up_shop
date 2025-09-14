from django.shortcuts import render
from django.http import HttpResponse
import os
import environ
from .pop_up_home_copy.site_info_copy.site_info_copy import (
    ABOUT_US_COPY, HOW_IT_WORKS_COPY, VERIFICATION_COPY, CONTACT_US_COPY, HELP_CENTER_COPY, 
    HELP_CENTER_PAGE_BUYING, HELP_CENTER_PAGE_SELLING, HELP_CENTER_PAGE_ACCOUNT, HELP_CENTER_PAGE_SHIPPING,
    HELP_CENTER_PAGE_PAYMENT, HELP_CENTER_PAGE_FEE, TERMS_AND_CONDITIONS_COPY, PRIVACY_POLICY_COPY,
    PRIVACY_CHOICES_COPY)

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
    help_center_copy = HELP_CENTER_COPY
    return render(request, 'pop_up_home/site_info/help_center.html', {'help_center_copy': help_center_copy})

def terms_and_conditions(request):
    terms_and_condition_copy = TERMS_AND_CONDITIONS_COPY
    return render(request, 'pop_up_home/footer_links/terms_and_conditions.html', 
                            { "terms_and_condition_copy": terms_and_condition_copy}
                            )

def privacy_policy(request):
    privacy_policy_copy = PRIVACY_POLICY_COPY
    return render(request, 'pop_up_home/footer_links/privacy.html', {
        "privacy_policy_copy": privacy_policy_copy})

def privacy_choice(request):
    privacy_choices = PRIVACY_CHOICES_COPY
    # Need to add functionality for user to opt out of tracking
    return render(request, 'pop_up_home/footer_links/privacy_choices.html', {
        "privacy_choices": privacy_choices})

def site_map(request):
    return render(request, 'pop_up_home/site_info/site_map.html')

# help_center_pages
def buying_help(request):
    help_center_page_buying = HELP_CENTER_PAGE_BUYING
    return render(request, 'pop_up_home/site_info/help_center_pages/buying_page.html', 
                  {"help_center_page_buying": help_center_page_buying})

def selling_help(request):
    help_center_page_selling = HELP_CENTER_PAGE_SELLING
    return render(request, 'pop_up_home/site_info/help_center_pages/selling_page.html',
                  {"help_center_page_selling": help_center_page_selling})

def account_help(request):
    help_center_page_account = HELP_CENTER_PAGE_ACCOUNT
    return render(request, 'pop_up_home/site_info/help_center_pages/my_account_page.html', {
        "help_center_page_account":help_center_page_account
    })

def shipping_help(request):
    help_center_page_shipping = HELP_CENTER_PAGE_SHIPPING
    return render(request, 'pop_up_home/site_info/help_center_pages/shipping_page.html', {
        "help_center_page_shipping":help_center_page_shipping
    })

def payment_help(request):
    help_center_page_payment = HELP_CENTER_PAGE_PAYMENT
    return render(request, 'pop_up_home/site_info/help_center_pages/payment_options_page.html',
                  {"help_center_page_payment": help_center_page_payment})

def fees_help(request):
    help_center_page_fee = HELP_CENTER_PAGE_FEE
    return render(request, 'pop_up_home/site_info/help_center_pages/fees_page.html', {
        "help_center_page_fee": help_center_page_fee
    })

def friend_invite_success(request):
    return render(request, 'pop_up_home/confirmations/friend_invite_success.html')

def friend_invite_failure(request):
    return render(request, 'pop_up_home/error/friend_invite_fail.html')