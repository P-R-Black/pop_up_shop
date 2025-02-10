from django.shortcuts import render

# Create your views here.
def user_login(request):
    return render(request, 'pop_accounts/login/login.html')

def user_password_reset(request):
    return render(request, 'pop_accounts/login/password_reset.html')

def dashboard(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/dashboard.html')

def personal_info(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/personal_info.html')

def interested_in(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/interested_in.html')

def on_notice(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/on_notice.html')

def open_bids(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/open_bids.html')

def past_bids(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/past_bids.html')
    
def past_purchases(request):
    return render(request, 'pop_accounts/user_accounts/dashboard_pages/past_purchases.html')

# ADMIN DASHBOARD

def dashboard_admin(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/dashboard.html')

def inventory(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/inventory.html')

def sales(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/sales.html')

def most_on_notice(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_on_notice.html')

def most_interested(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/most_interested.html')

def total_open_bids(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_open_bids.html')

def total_accounts(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/total_accounts.html')

def account_sizes(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard_pages/account_sizes.html')