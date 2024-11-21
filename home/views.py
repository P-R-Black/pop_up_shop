from django.shortcuts import render
from django.http import HttpResponse
import os
import environ

# Create your views here.
def home_page(request):
    
    # return HttpResponse("<h1>Bonjour tout le monde</<h1")
    return render(request, 'home/index.html')