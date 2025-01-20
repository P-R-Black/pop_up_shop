from django.shortcuts import render

# Create your views here.
def dashboard(request):
    return render(request, ('pop_accounts/user_accounts/dashboard.html'))

def personal_info(request):
    return render(request, 'pop_accounts/user_accounts/personal_info.html')

def interested_in(request):
    pass

def on_notice(request):
    pass

def open_bids(request):
    pass

def past_bids(request):
    pass

def past_purchases(request):
    pass