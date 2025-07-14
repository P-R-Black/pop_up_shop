from django.shortcuts import render, get_object_or_404
from orders.models import PopUpCustomerOrder, PopUpOrderItem
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import weasyprint
from django.conf import settings
from pop_up_shipping.pop_shipping_copy.pop_up_shipping_copy import ADMIN_SHIPPING
from orders.utils.utils import admin_shipments, admin_orders

# Create your views here.



def generate_shipping_label(request, order_id):
    order = get_object_or_404(PopUpCustomerOrder, id=order_id)
    admin_shipping = ADMIN_SHIPPING
    shipping_details = admin_shipments(order_id)

    order_details = admin_orders(order_id)

    context = {'order': order,  'admin_shipping': admin_shipping, 'shipping_details': shipping_details, 'order_details': order_details}
    return render(request, 'pop_up_shipping/shipping_details.html', context)


def generate_shipping_pdf(request, order_id):
    order = get_object_or_404(PopUpCustomerOrder, id=order_id)
    html_string = render_to_string('pop_up_shipping/pdf.html', {'order', order})
    pdf_file = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=shipping_pdf_{order.id}.pdf'
    weasyprint.HTML(string=html_string).write_pdf(response, stylesheets=[weasyprint.CSS(
        settings.STATIC_ROOT + 'css/pdf.css')
    ])
    return response