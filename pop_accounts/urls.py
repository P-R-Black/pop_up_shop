from django.urls import path
from . import views

app_name = 'pop_accounts'
urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('personal-information', views.personal_info, name='personal_info')
]