from pop_up_order.models import PopUpCustomerOrder, PopUpOrderItem
from pop_accounts.models import PopUpCustomerProfile, PopUpCustomerAddress
from pop_up_auction.models import PopUpProduct, WinnerReservation
from pop_up_shipping.models import PopUpShipment
from pop_accounts.utils.utils import add_specs_to_products
from django.db.models import Prefetch


def admin_orders(order_id):
    
    orders = (
        PopUpCustomerOrder.objects
        .filter(id=order_id, billing_status=True)
        .prefetch_related('items')  # load PopUpOrderItems efficiently
        .only('id', 'created_at', 'city', 'state', 'postal_code')  # minimize selected fields
    )
    return orders


def admin_shipments(order_id):

    """Get shipped products for a specific user with specs, shipment info, and shipping address"""
    
    orders = PopUpCustomerOrder.objects.select_related(
        'shipment',
        'shipping_address'
    ).prefetch_related(
        Prefetch(
            'items__product',  # Changed from 'order_items' to 'items'
            queryset=PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set__specification')
        )
    ).filter(
        id=order_id,
    )
    
    result = []
    
    for order in orders:
        # Get products with specs
        products_in_order = [item.product for item in order.items.all()]  # Changed to 'items'
        products_with_specs = add_specs_to_products(products_in_order)
        
        for order_item in order.items.all():
            product = order_item.product
            # Find the corresponding product with specs
            product_with_specs = next(p for p in products_with_specs if p.id == product.id)
            
            result.append(
                {
                'order_id': order.id,
                'order_item_id': order_item.id,
                'product_id': product_with_specs.id,
                'product_title': product_with_specs.product_title,
                'secondary_product_title': product_with_specs.secondary_product_title,
                'model_year': product_with_specs.specs.get('model_year'),
                'all_specs': product_with_specs.specs,
                'order_item': {
                    'quantity': order_item.quantity,
                    'price': order_item.price,
                    'size': order_item.size,
                    'color': order_item.color,
                },
                'shipment': {
                    'carrier': order.shipment.carrier,
                    'tracking_number': order.shipment.tracking_number,
                    'shipped_at': order.shipment.shipped_at,
                    'estimated_delivery': order.shipment.estimated_delivery,
                    'delivered_at': order.shipment.delivered_at,
                    'status': order.shipment.status,
                },
                'billing_address': {
                    'full_name': order.full_name,
                    'address1': order.address1,
                    'address2': order.address2,
                    'city': order.city,
                    'state': order.state,
                    'postal_code': order.postal_code,
                    'apartment_suite_number': order.apartment_suite_number,
                },
                'shipping_address': {
                    'prefix': order.shipping_address.prefix if order.shipping_address else None,
                    'first_name': order.shipping_address.first_name if order.shipping_address else None,
                    'middle_name': order.shipping_address.middle_name if order.shipping_address else None,
                    'last_name': order.shipping_address.last_name if order.shipping_address else None,
                    'suffix': order.shipping_address.suffix if order.shipping_address else None,
                    'address_line': order.shipping_address.address_line if order.shipping_address else None,
                    'address_line2': order.shipping_address.address_line2 if order.shipping_address else None,
                    'town_city': order.shipping_address.town_city if order.shipping_address else None,
                    'state': order.shipping_address.state if order.shipping_address else None,
                    'postcode': order.shipping_address.postcode if order.shipping_address else None,
                    'apartment_suite_number': order.shipping_address.apartment_suite_number if order.shipping_address else None,
                    'delivery_instructions': order.shipping_address.delivery_instructions if order.shipping_address else None,
                } if order.shipping_address else None
            })
    
    return result


def user_orders(customer_id):
    user_id = customer_id
    orders = (
        PopUpCustomerOrder.objects
        .filter(user=user_id, billing_status=True)
        .prefetch_related('items')  # load PopUpOrderItems efficiently
        .only('id', 'created_at', 'city', 'state', 'postal_code')  # minimize selected fields
    )
    return orders


def user_shipments(customer_id):
    user_id = customer_id
    """Get shipped products for a specific user with specs, shipment info, and shipping address"""
    
    orders = PopUpCustomerOrder.objects.select_related(
        'shipment',
        'shipping_address'
    ).prefetch_related(
        Prefetch(
            'items__product',  # Changed from 'order_items' to 'items'
            queryset=PopUpProduct.objects.prefetch_related('popupproductspecificationvalue_set__specification')
        )
    ).filter(
        user=user_id,
        shipment__isnull=False
    )
    
    result = []
    
    for order in orders:
        # Get products with specs
        products_in_order = [item.product for item in order.items.all()]  # Changed to 'items'
        products_with_specs = add_specs_to_products(products_in_order)
        
        for order_item in order.items.all():
            product = order_item.product
            # Find the corresponding product with specs
            product_with_specs = next(p for p in products_with_specs if p.id == product.id)
            
            result.append(
                {
                'order_id': order.id,
                'order_item_id': order_item.id,
                'product_id': product_with_specs.id,
                'product_title': product_with_specs.product_title,
                'secondary_product_title': product_with_specs.secondary_product_title,
                'model_year': product_with_specs.specs.get('model_year'),
                'all_specs': product_with_specs.specs,
                'order_item': {
                    'quantity': order_item.quantity,
                    'price': order_item.price,
                    'size': order_item.size,
                    'color': order_item.color,
                },
                'shipment': {
                    'carrier': order.shipment.carrier,
                    'tracking_number': order.shipment.tracking_number,
                    'shipped_at': order.shipment.shipped_at,
                    'estimated_delivery': order.shipment.estimated_delivery,
                    'delivered_at': order.shipment.delivered_at,
                    'status': order.shipment.status,
                },
                'billing_address': {
                    'full_name': order.full_name,
                    'address1': order.address1,
                    'address2': order.address2,
                    'city': order.city,
                    'state': order.state,
                    'postal_code': order.postal_code,
                    'apartment_suite_number': order.apartment_suite_number,
                },
                'shipping_address': {
                    'prefix': order.shipping_address.prefix if order.shipping_address else None,
                    'first_name': order.shipping_address.first_name if order.shipping_address else None,
                    'middle_name': order.shipping_address.middle_name if order.shipping_address else None,
                    'last_name': order.shipping_address.last_name if order.shipping_address else None,
                    'suffix': order.shipping_address.suffix if order.shipping_address else None,
                    'address_line': order.shipping_address.address_line if order.shipping_address else None,
                    'address_line2': order.shipping_address.address_line2 if order.shipping_address else None,
                    'town_city': order.shipping_address.town_city if order.shipping_address else None,
                    'state': order.shipping_address.state if order.shipping_address else None,
                    'postcode': order.shipping_address.postcode if order.shipping_address else None,
                    'apartment_suite_number': order.shipping_address.apartment_suite_number if order.shipping_address else None,
                    'delivery_instructions': order.shipping_address.delivery_instructions if order.shipping_address else None,
                } if order.shipping_address else None
            })
    
    return result
