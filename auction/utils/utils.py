from auction.models import PopUpProduct
from pop_accounts.models import PopUpCustomer, PopUpPurchase, PopUpBid
from django.core.mail import send_mail
from django.db.models import Max
from django.utils import timezone


def get_customer_bid_history_context(customer_id):
    """
    Get the customer's last bid per product with formatted context.
    Perfect for dashboard widgets and detailed bid history pages.
    
    Returns a dictionary with:
    - bid_history: List of formatted bid data
    - statistics: Summary stats for dashboard use
    """
    # Get the latest bid for each product by this customer
    latest_bids_data = (
        PopUpBid.objects
        .filter(customer_id=customer_id, is_active=True)
        .values('product_id')
        .annotate(last_bid_time=Max('timestamp'))
    )
    
    # Get the actual bid records
    product_ids = [bid['product_id'] for bid in latest_bids_data]
    # PostgreSQL Version
    # latest_bids = (
    #     PopUpBid.objects
    #     .filter(customer_id=customer_id, is_active=True, product_id__in=product_ids)
    #     .select_related('product')
    #     .order_by('product_id', '-timestamp')
    #     .distinct('product_id')  # PostgreSQL - for other DBs, use the alternative below
    # )
    
    # Alternative for non-PostgreSQL databases:
    latest_bids = []
    for product_id in product_ids:
        last_bid = PopUpBid.objects.filter(
            customer_id=customer_id, 
            product_id=product_id, 
            is_active=True
        ).select_related('product').order_by('-timestamp').first()
        if last_bid:
            latest_bids.append(last_bid)
    
    # Format the data for template use
    bid_history = []
    winning_count = 0
    total_bid_amount = 0
    auto_bid_count = 0
    
    for bid in latest_bids:
        # Check if product auction is still active using your auction methods
        is_auction_active = bid.product.is_auction_phase()

        # Build MPTT specifications dictionary (similar to your add_specs_to_products function)
        mptt_specs = {
            spec.specification.name: spec.value
            for spec in bid.product.popupproductspecificationvalue_set.all()
        }
        
        bid_data = {
            'id': bid.id,
            'product': bid.product,
            'product_name': bid.product.product_title,
            'product_slug': bid.product.slug,
            'bid_amount': bid.amount,
            'bid_time': bid.timestamp,
            'is_winning': bid.is_winning_bid,
            'status': 'Winning' if bid.is_winning_bid else 'Outbid',
            'status_class': 'success' if bid.is_winning_bid else 'danger',
            'has_auto_bid': bid.max_auto_bid is not None,
            'max_auto_bid': bid.max_auto_bid,
            'bid_increment': bid.bid_increment,
            'is_auction_active': is_auction_active,
            'auction_status': bid.product.auction_status,
            'sale_outcome': bid.product.sale_outcome,
            'is_finalized': bid.product.auction_finalized,
            'current_highest_bid': bid.product.current_highest_bid,
            'time_since_bid': timezone.now() - bid.timestamp,
            # Product specifications - now accessible without additional queries
            'specifications': {
                'brand': bid.product.brand.name if bid.product.brand else None,
                'category': bid.product.category.name if bid.product.category else None,
                'product_type': bid.product.product_type.name if bid.product.product_type else None,
                'retail_price': bid.product.retail_price,
                'description': bid.product.description,
                'secondary_title': bid.product.secondary_product_title,
                'inventory_status': bid.product.get_inventory_status_display(),
                'weight': bid.product.product_weight_lbs,
                'storage_location': bid.product.zip_code_stored,
                'reserve_price': bid.product.reserve_price,
                'buy_now_price': bid.product.buy_now_price,
            },
            # MPTT specifications from your specification system
            'mptt_specs': mptt_specs,
            # Combined specifications for easy template access
            'all_specs': {
                **{
                    'Brand': bid.product.brand.name if bid.product.brand else None,
                    'Category': bid.product.category.name if bid.product.category else None,
                    'Product Type': bid.product.product_type.name if bid.product.product_type else None,
                    'Retail Price': f"${bid.product.retail_price}" if bid.product.retail_price else None,
                    'Weight (lbs)': bid.product.product_weight_lbs,
                    'Reserve Price': f"${bid.product.reserve_price}" if bid.product.reserve_price else None,
                },
                **mptt_specs  # MPTT specs will override if there are naming conflicts
            }
        }
        
        bid_history.append(bid_data)
        
        # Calculate statistics
        if bid.is_winning_bid:
            winning_count += 1
        total_bid_amount += bid.amount
        if bid.max_auto_bid:
            auto_bid_count += 1
    
    # Sort by timestamp (most recent first) for display
    bid_history.sort(key=lambda x: x['bid_time'], reverse=True)
    
    # Prepare statistics for dashboard
    statistics = {
        'total_products': len(bid_history),
        'winning_count': winning_count,
        'losing_count': len(bid_history) - winning_count,
        'win_rate': round((winning_count / len(bid_history) * 100) if bid_history else 0, 1),
        'total_bid_amount': total_bid_amount,
        'average_bid': round(total_bid_amount / len(bid_history), 2) if bid_history else 0,
        'auto_bid_count': auto_bid_count,
        'manual_bid_count': len(bid_history) - auto_bid_count,
    }
    
    return {
        'bid_history': bid_history,
        'statistics': statistics
    }



# def notify_winner(customer, product, amount, purchase):

#     subject = f"You won the auction for {product.product_titile}"
#     message = f"Congrats!\n\nYour winning bid: ${amount:2f}.\nPlease complete payment within 48 hours: {settings.SITE_URL}/checkout/{purchase.id}"

    
#     send_mail(
#         subject,
#         message,
#         from_email = settings.DEFAULT_FROM_EMAIL,
#         recipient_list = [customer.email],
#     )

#     # SMS
#     if customer.mobile_notification and customer.mobile_phone:
#         twilio_client.messages.create(
#             to = customer.mobile_phone,
#             from_ = settings.TWILIO_FROM,
#             body = f"You won {product.product_title}! Complete payment in your account."
#         )


# def close_auction(product: PopUpProduct):
#     highest = product.bids.filter(is_active=True).order_by('-amount').first()
#     if not highest:
#         return
    
#     highest.is_winning_bid = True
#     highest.save(update_fields=['is_winning_bid'])
#     customer = highest.customer
#     amount = highest.amount

#     # build / reuse Stripe customer
#     if not customer.stripe_customer_id:
#         stripe_customer = stripe.Customer.create(
#             email = customer.email,
#             phone = customer.mobile_phone or None,
#             name = f"{customer.first_name} {customer.last_name}"
#         )
#         customer.stripe_customer_id = stripe_customer.id
#         customer.save(update_fields=['stripe_customer_id'])
    
#     pi = stripe.PaymentIntent.create(
#         customer = customer.stripe_customer_id,
#         amount = int(amount * 100), # cents
#         currency = 'usd',
#         capture_method = 'automatic',
#         metadata = {'product_id': str(product.id), 'bid_id': str(highest.id)}
#     )

#     purchase = PopUpPurchase.objects.create(
#         customer = customer,
#         product = product,
#         bid = highest,
#         stripe_pi = pi.id
#     )

#     notify_winner(customer, product, amount, purchase)
