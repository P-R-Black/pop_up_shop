from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.timezone import now
from datetime import timedelta, date, datetime
from django.http import HttpResponse
from pop_up_auction.models import PopUpProduct
from pop_up_email.utils import send_auction_winner_email, send_friend_invite_email
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin, UserPassesTestMixin
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages

# Create your views here.


def preview_email(request):
    product = PopUpProduct.objects.first()
    user = request.user
    html = send_auction_winner_email(user, product)
    return HttpResponse(html)


def preview_email_confirmation(request):
    current_date = date.today()
    user = request.user
    user_email = request.user.email   
    year = current_date.strftime("%Y")
    context = {
        "user": user,
        "user_email": user_email,
        "year": year,
    }

    html = render_to_string('pop_up_email/email_confirm.html', context)
    return HttpResponse(html)

def preview_two_factor_auth(request):
    # 6 digit code
    six_digit_code = "123456"

    # user & user_email
    user  =request.user
    user_email = request.user.email

    # year
    current_date = date.today()
    year = current_date.strftime("%Y")

    # context
    context = {
        "user": user,
        "user_email": user_email,
        "code": six_digit_code,
        "year": year
    }

    # html
    html = render_to_string('pop_up_email/two_factor.html', context)

    # HttpResponse
    return HttpResponse(html)


def preview_order_confirmation(request):
    from pop_up_order.models import PopUpOrderItem, PopUpCustomerOrder
    user = request.user
    order = PopUpCustomerOrder.objects.filter(user=user).last()
    # items = PopUpOrderItem.objects.filter(order=order)
    items =[
        {"Product id": "53", "product_title": "Jordan 1 Retro High OG SP", 
         "secondary_product_title":"Union LA Chicago Shadow",
           "size":"9", "product_sex": "Male"},  {"Product id": "42", "product_title": "Jordan 11 Retro", 
         "secondary_product_title": "Gamma Blue",
           "size":"9", "product_sex": "Male"} ]

    print('items', items)

    order_id = "54f8f292-fd25-47dd-a7aa-a9a81b4a1c6a"
    total_paid =  "724.73"
    payment_status = "pending"
    html = render_to_string('pop_up_email/order_confirmation.html', {
        'user': user,
        'order_id': order.id,
        'items': items,
        'order_id': order_id,
        'total_paid':total_paid,
        'payment_status': payment_status
    })
   
    
    return HttpResponse(html)


def preview_send_customer_shipping_details(request):

    user = request.user
    user_email = request.user.email  

    order_id = "b62171e6-cb4b-48f6-be14-20d971393059"
    carrier = "UPS"
    tracking_no = "6547382910"
    shipped_at = datetime(2025, 7, 11)
    estimated_deliv = datetime(2025, 7, 15)
    status = 'Shipped'

    links_to_track_shipment = {
            "USPS": "https://tools.usps.com/go/TrackConfirmAction_input?_gl=1*ctcvbi*_ga*MjA2NDExMTY3Ni4xNzUxNTA0NzI3*_ga_QM3XHZ2B95*czE3NTI3MDA0MzkkbzExJGcxJHQxNzUyNzAwNTM0JGo2MCRsMCRoMA..",
            "UPS": "https://www.ups.com/us/en/home",
            "FedEx": "https://www.fedex.com/en-us/tracking.html"
    }

  
    html = render_to_string('pop_up_email/send_customer_shipping_details.html', {
        'user': user,
        'order_id': order_id,
        'carrier': carrier,
        'tracking_no': tracking_no,
        'shipped_at':shipped_at,
        'estimated_deliv': estimated_deliv,
        'status':status,
        'tracker_link': links_to_track_shipment[carrier]
    })

    return HttpResponse(html)


def preview_invite_friend_email(request):
    user = 'Peter'
    friend_name = 'Tom'
    html = render_to_string('pop_up_email/invite_friend.html', {
        'user': user,
        'friend_name': friend_name,
        'invite_link': "https://7c90b7218718.ngrok-free.app/?show_auth_modal=true"
    
    })
    return HttpResponse(html)

def preview_send_interested_in_and_coming_soon_product_update_to_users_email(request):
    product = PopUpProduct.objects.get(id=5)
    user = request.user
    product_id = 5
    buy_now_start_date = ""
    auction_start_date = datetime(2025, 8, 17, 18, 00)
    message_key = 'buy_now_update'
   

    html = render_to_string('pop_up_email/update_interested_users.html', {
       'user': user,
        'product': product, 
        'buy_now_start_date': buy_now_start_date if buy_now_start_date else "", 
        'auction_start_date': auction_start_date if auction_start_date else "", 
    
    })
    return HttpResponse(html)



class InviteFriendView(LoginRequiredMixin, View):

    def post(self, request):
        friend_name = request.POST.get('friend_name')
        friend_email = request.POST.get('friend_email')

        # verifiy good email address
        try:
            validate_email(friend_email)
        except ValidationError as e:
            return redirect(reverse('pop_up_home:invite_failed'))
        
        send_friend_invite_email(
            user=f"{request.user.first_name} {request.user.last_name}",
            user_email=request.user.email, 
            friend_name=friend_name, 
            friend_email=friend_email
            )

        messages.success(request, f'🎉  An invite has been sent to {friend_name}.  🎉')

        # Render success HTML page
        return redirect(reverse('pop_up_home:invite_success'))
        
