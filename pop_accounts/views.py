from django.shortcuts import render

# Create your views here.
def dashboard(request):
    return render(request, ('pop_accounts/user_accounts/dashboard.html'))

def personal_info(request):
    return render(request, 'pop_accounts/user_accounts/personal_info.html')

def interested_in(request):
    return render(request, 'pop_accounts/user_accounts/interested_in.html')

def on_notice(request):
    return render(request, 'pop_accounts/user_accounts/on_notice.html')

def open_bids(request):
    return render(request, 'pop_accounts/user_accounts/open_bids.html')

def past_bids(request):
    return render(request, 'pop_accounts/user_accounts/past_bids.html')
    
def past_purchases(request):
    return render(request, 'pop_accounts/user_accounts/past_purchases.html')

# ADMIN DASHBOARD

def dashboard_admin(request):
    return render(request, 'pop_accounts/admin_accounts/dashboard.html')

def inventory(request):
    return render(request, 'pop_accounts/admin_accounts/inventory.html')