import stripe
import braintree
import paypalrestsdk
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_fees_by_payment(payment_method: str,  payment_data_id: str) -> Decimal:
    """Get payment processing fees by payment method"""
    fee_handlers = {
        'stripe': fetch_stripe_fees,
        'paypal': fetch_paypal_fees,
        'venmo': fetch_venmo_fees,
        'google_pay': fetch_paypal_fees,
        'apple_pay': fetch_apple_pay_fees,
        'now_payment': fetch_now_payments_fees,
    }
    
    handler = fee_handlers.get(payment_method)
    if handler:
        return handler(payment_data_id)
    else:
        logger.warning(f'Unknown payment method: {payment_method}')
        return Decimal('0.00')



def fetch_stripe_fees(payment_data_id: str) -> Decimal:
    try:
        # Retrieve the payment intent
        intent = stripe.PaymentIntent.retrieve(payment_data_id)
        charge_id = intent['charges']['data'][0]['id']
        charge = stripe.Charge.retrieve(charge_id)

        # Get balance transaction to access fee
        balance_tx_id = charge['balance_transaction']
        balance_tx = stripe.BalanceTransaction.retrieve(balance_tx_id)

        # Stripe fees are in cents
        fee = Decimal(balance_tx['fee']) / 100
    except Exception as e:
        logger.error(f'Error getting Stripe fee: {e}')
        return Decimal('0.00')



def fetch_paypal_fees(payment_data_id):
    try:
        payment = paypalrestsdk.Payment.find(payment_data_id)
        transactions = payment['transactions'][0]
        related_resources = transactions['related_resources'][0]
        sale = related_resources['sale']
        fee = Decimal(sale['transaction_fee']['value'])
        return fee
    except Exception as e:
        logger.error(f'Error getting PayPal fee: {e}')
        return Decimal("0.00")

def fetch_apple_pay_fees(order_id):
    payment_fee = 0
    return payment_fee


def fetch_now_payments_fees(order_id):
    payment_fee = 0
    return payment_fee

def fetch_venmo_fees(payment_data_id):
    try:
        transaction = braintree.Transaction.find(payment_data_id)
        # Braintree doesn't directly expose the fee via the SDK, unless using their Marketplace.
        # You might have to configure it to return processing fee details (requires partnership/advanced access).
        fee_detail = transaction.service_fee_amount
        if fee_detail:
            return Decimal(fee_detail)
        return Decimal('0.00')
    except Exception as e:
        logger.error(f"Error getting Braintree (Venmo) fee: {e}")
        return Decimal("0.00")


