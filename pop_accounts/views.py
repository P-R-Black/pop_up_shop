from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from .forms import PopUpRegistrationForm, PopUpUserLoginForm
from .token import account_activation_token
from orders.views import user_orders


# Create your views here.
def user_registration(request):
    register_form = "Register"
    if request.user.is_authenticated:
        return redirect('pop_accounts/admin_accounts/dashboard_pages/dashboard.html')
    
    # if request.method == 'POST':
    #     register_form = PopUpRegistrationForm(request.POST)
    #     if register_form.is_valid():
    #         user = register_form.save(commit=False)
    #         user.email = register_form.cleaned_data['email']
    #         user.set_password(register_form.cleaned_data['password'])
    #         user.is_active = False
    #         user.save()

    #         # setup email
    #         current_site = get_current_site(request)
    #         subject = 'Activate your Account'
    #         message = render_to_string('pop_accounts/registration/account_activation_email.html',{
    #             'user': user,
    #             'domain': current_site.domain,
    #             'uid': urlsafe_base64_encode(force_bytes(user.pk)),
    #             'token': account_activation_token.make_token(user),
    #         })
    #         user.email_user(subject=subject, message=message)

    # else:
    #     register_form = PopUpRegistrationForm()
        return render(request, 'pop_accounts/registration/register.html', {'form', register_form})


def user_login(request):
    login_form = "login"
    # login_form = PopUpUserLoginForm()
    # if request.method == 'POST':
    #     login_form = PopUpUserLoginForm(request.POST)
         
    #     email = request.POST.get('email')
    #     password = request.POST.get('password')
     
    #     print('email', email)
    #     print('password', password)
    
    return render(request, 'pop_accounts/login/login.html', {'form': login_form})


# @login_required
def user_password_reset(request):
    return render(request, 'pop_accounts/login/password_reset.html')

# @login_required
def dashboard(request):
    orders = user_orders(request)
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/dashboard.html')

# @login_required
def personal_info(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/personal_info.html')

# @login_required
def interested_in(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/interested_in.html')

# @login_required
def on_notice(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/on_notice.html')

# @login_required
def open_bids(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/open_bids.html')

# @login_required
def past_bids(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/past_bids.html')

# @login_required
def past_purchases(request):
    orders = user_orders(request)
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/past_purchases.html')

# ADMIN DASHBOARD
# @login_required
def dashboard_admin(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/dashboard.html')
# @login_required
def inventory(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/inventory.html')

# @login_required
def sales(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/sales.html')

# @login_required
def most_on_notice(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_on_notice.html')

# @login_required
def most_interested(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_interested.html')

# @login_required
def total_open_bids(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_open_bids.html')
@login_required
def total_accounts(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_accounts.html')

# @login_required
def account_sizes(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/account_sizes.html')