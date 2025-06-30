from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta
from django.http import HttpResponse
from auction.models import PopUpProduct
from pop_up_email.utils import send_auction_winner_email

# Create your views here.


def preview_email(request):
    product = PopUpProduct.objects.first()
    user = request.user
    html = send_auction_winner_email(user, product)
    return HttpResponse(html)

