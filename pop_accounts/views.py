from django.shortcuts import render

# Create your views here.
def dashboard(request):
    return render(request, ('pop_accounts/user_accounts/dashboard.html'))