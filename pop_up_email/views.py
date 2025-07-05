from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta, date, datetime
from django.http import HttpResponse
from auction.models import PopUpProduct
from pop_up_email.utils import send_auction_winner_email

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
    from orders.models import PopUpOrderItem, PopUpCustomerOrder
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
   
    
    # user = {"first_name": "Maya", "last_name": "Lopez"}

    # context = {
    #     "user": user,
    #     "order_id": order_id,
    #     "items": items
    # }
        
    # html = render_to_string('pop_up_email/order_confirmation.html', context)
    return HttpResponse(html)

"""
CreateOrderAfterPaymentView data {'payment_data_id': 'pi_3RgqvHQhRNo0vHR21iCpZQaw', 
'order_key': 'pi_3RgqvHQhRNo0vHR21iCpZQaw_secret_sKgH08T2NpcnrM4OIFofcMeAh', 
'user_id': '413be6d9-b858-4912-a23c-7214c2918327', 'total_paid': 358.29, 
'full_name': 'Bruce Banner', 'email': 'bbanner@avengers.com', 
'address1': '305 Harrison St', 'address2': '', 'postal_code': '98109', 
'apartment_suite_number': '', 'city': 'Seattle,', 'state': 'WA', 
'phone': '206-808-0102', 'shippingAddressId': 'c3e1d201-310a-4558-ae82-dc66a8259b40', 
'billingAddressId': 'c3e1d201-310a-4558-ae82-dc66a8259b40', 'coupon_id': '', 'discount': 0} 

payment_data_id pi_3RgqvHQhRNo0vHR21iCpZQaw
total_paid 358.29000000000002046363078989088535308837890625
item {'product': <PopUpProduct: Jordan 1 Retro High OG SP>, 'qty': 1, 'price': Decimal('320.00'), 
'total_price': Decimal('320.00')}
prod_data {'product': <PopUpProduct: Jordan 1 Retro High OG SP>, 'product_title': 'Jordan 1 Retro High OG SP', 
'secondary_title': 'Union LA Chicago Shadow', 'colorway': 'Varsity Red/Black-Sail-Shadow Grey-Muslin', 'size': '9'}
product in order Jordan 1 Retro High OG SP
"""


"""
ds_in_cart [2, 22]
product_qs <QuerySet [<PopUpProduct: Jordan 1 Retro High OG SP>, <PopUpProduct: Jordan 11 Retro>]>
CreateOrderAfterPaymentView data {'payment_data_id': 'pi_3Rgr7TQhRNo0vHR20DI4Xdke', 
'order_key': 'pi_3Rgr7TQhRNo0vHR20DI4Xdke_secret_NAy4IKPysxBsNMAbToULLGo4b', 
'user_id': '413be6d9-b858-4912-a23c-7214c2918327', 'total_paid': 724.73, 
'full_name': 'Bruce Banner', 'email': 'bbanner@avengers.com', 
'address1': '305 Harrison St', 'address2': '', 'postal_code': '98109', 
'apartment_suite_number': '', 'city': 'Seattle,', 'state': 'WA', 
'phone': '206-808-0102', 'shippingAddressId': 'c3e1d201-310a-4558-ae82-dc66a8259b40', 
'billingAddressId': 'c3e1d201-310a-4558-ae82-dc66a8259b40', 'coupon_id': '', 'discount': 0} 

payment_data_id pi_3Rgr7TQhRNo0vHR20DI4Xdke
total_paid 724.73000000000001818989403545856475830078125
1. item {'product': <PopUpProduct: Jordan 11 Retro>, 'qty': 1, 'price': Decimal('330.00'), 'total_price': Decimal('330.00')}
1. prod_data {'product': <PopUpProduct: Jordan 11 Retro>, 'product_title': 'Jordan 11 Retro', 'secondary_title': 'Legend Blue', 'colorway': 'White/Legend Blue/Black', 'size': '8'}

2. item {'product': <PopUpProduct: Jordan 1 Retro High OG SP>, 'qty': 1, 'price': Decimal('320.00'), 'total_price': Decimal('320.00')}
2. prod_data {'product': <PopUpProduct: Jordan 1 Retro High OG SP>, 'product_title': 'Jordan 1 Retro High OG SP', 'secondary_title': 'Union LA Chicago Shadow', 'colorway': 'Varsity Red/Black-Sail-Shadow Grey-Muslin', 'size': '9'}

product in order Jordan 11 Retro
product in order Jordan 1 Retro High OG SP
"""
# need picture, title, secondary title, shoe size