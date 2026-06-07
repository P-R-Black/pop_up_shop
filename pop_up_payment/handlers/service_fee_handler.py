# pop_up_payment/handlers/service_fee_handler.py

"""
Service Fee Payment Handler

Handles charging and refunding the $15 procurement service fee.
Supports Stripe, PayPal, and Venmo (via Braintree).
"""

import logging
import stripe
import braintree
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class ServiceFeePaymentHandler:
    """
    Handle procurement service fee payments ($15).
    
    Supports:
    - Stripe (PaymentIntent)
    - PayPal
    - Venmo (via Braintree)
    """
    
    SERVICE_FEE = Decimal('15.00')
    WEBHOOK_TIMEOUT = 30  # seconds to wait for webhook confirmation
    
    def __init__(self):
        """Initialize payment processors"""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        self.braintree_gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                braintree.Environment.Sandbox,
                merchant_id=settings.BRAINTREE_MERCHANT_ID,
                public_key=settings.BRAINTREE_PUBLIC_KEY,
                private_key=settings.BRAINTREE_PRIVATE_KEY,
            )
        )
    
    # =====================================================================
    # STRIPE PAYMENTS
    # =====================================================================
    
    def create_stripe_payment_intent(self, service_request) -> Dict:
        """
        Create a Stripe PaymentIntent for service fee.
        
        Frontend will use clientSecret to complete payment.
        
        Args:
            service_request: ProcurementServiceRequest instance
        
        Returns:
            dict with clientSecret and PaymentIntent ID
        """
        try:
            user = service_request.user
            profile = user.popupcustomerprofile
            
            # Ensure Stripe customer exists
            if not profile.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}"
                )
                profile.stripe_customer_id = customer.id
                profile.save(update_fields=['stripe_customer_id'])
            
            # Amount in cents
            amount_cents = int(self.SERVICE_FEE * 100)
            
            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=profile.stripe_customer_id,
                description=f"Procurement Service Fee - {service_request.id}",
                metadata={
                    'service_request_id': str(service_request.id),
                    'user_email': user.email,
                    'release_sku': service_request.scheduled_release.sku,
                },
                automatic_payment_methods={"enabled": True},
                setup_future_usage="off_session"
            )
            
            logger.info(
                f"Created Stripe PaymentIntent {intent.id} "
                f"for {user.email} - ${self.SERVICE_FEE}"
            )
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': self.SERVICE_FEE,
                'status': 'requires_payment_method'
            }
        
        except Exception as e:
            error_msg = f"Failed to create Stripe intent: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def confirm_stripe_payment(self, service_request, payment_intent_id: str) -> Tuple[bool, str]:
        """
        Confirm Stripe payment succeeded (called from webhook).
        
        Args:
            service_request: ProcurementServiceRequest instance
            payment_intent_id: Stripe PaymentIntent ID
        
        Returns:
            (success, payment_reference)
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                logger.info(
                    f"Stripe payment {payment_intent_id} confirmed "
                    f"for {service_request.user.email}"
                )
                return True, payment_intent_id
            else:
                logger.warning(
                    f"Stripe payment {payment_intent_id} status: {intent.status}"
                )
                return False, None
        
        except Exception as e:
            logger.error(f"Failed to confirm Stripe payment: {str(e)}")
            return False, None
    
    def refund_stripe_payment(self, service_payment) -> Tuple[bool, str]:
        """
        Refund Stripe payment.
        
        Args:
            service_payment: ServicePayment instance
        
        Returns:
            (success, refund_id)
        """
        try:
            if not service_payment.payment_reference:
                return False, "No payment reference found"
            
            # Refund the PaymentIntent
            refund = stripe.Refund.create(
                payment_intent=service_payment.payment_reference,
                reason='requested_by_customer'
            )
            
            logger.info(
                f"Stripe refund {refund.id} issued for "
                f"{service_payment.service_request.user.email}"
            )
            
            return True, refund.id
        
        except Exception as e:
            error_msg = f"Failed to refund Stripe payment: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # =====================================================================
    # VENMO PAYMENTS (via Braintree)
    # =====================================================================
    
    def process_venmo_payment(
        self, 
        service_request, 
        payment_method_nonce: str
    ) -> Tuple[bool, str, str]:
        """
        Process Venmo payment via Braintree.
        
        Args:
            service_request: ProcurementServiceRequest instance
            payment_method_nonce: Braintree nonce from frontend
        
        Returns:
            (success, transaction_id, error_message)
        """
        try:
            amount = str(self.SERVICE_FEE)
            
            result = self.braintree_gateway.transaction.sale({
                "amount": amount,
                "payment_method_nonce": payment_method_nonce,
                "options": {
                    "submit_for_settlement": True
                },
                "custom_fields": {
                    "service_request_id": str(service_request.id),
                }
            })
            
            if result.is_success:
                transaction_id = result.transaction.id
                logger.info(
                    f"Venmo payment {transaction_id} processed "
                    f"for {service_request.user.email} - ${self.SERVICE_FEE}"
                )
                return True, transaction_id, ""
            else:
                error_msg = result.message or "Payment processing failed"
                logger.error(f"Venmo payment failed: {error_msg}")
                return False, "", error_msg
        
        except Exception as e:
            error_msg = f"Venmo payment error: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def refund_venmo_payment(self, service_payment) -> Tuple[bool, str]:
        """
        Refund Venmo payment via Braintree.
        
        Args:
            service_payment: ServicePayment instance
        
        Returns:
            (success, refund_id)
        """
        try:
            if not service_payment.payment_reference:
                return False, "No transaction ID found"
            
            result = self.braintree_gateway.transaction.refund(
                service_payment.payment_reference
            )
            
            if result.is_success:
                refund_id = result.transaction.id
                logger.info(
                    f"Venmo refund {refund_id} issued for "
                    f"{service_payment.service_request.user.email}"
                )
                return True, refund_id
            else:
                error_msg = result.message or "Refund failed"
                logger.error(f"Venmo refund failed: {error_msg}")
                return False, error_msg
        
        except Exception as e:
            error_msg = f"Venmo refund error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # =====================================================================
    # PAYPAL PAYMENTS (placeholder)
    # =====================================================================
    
    def create_paypal_payment(self, service_request) -> Dict:
        """
        Create PayPal payment.
        
        To be implemented with PayPal SDK.
        
        Args:
            service_request: ProcurementServiceRequest instance
        
        Returns:
            dict with payment details
        """
        # This would use PayPal Checkout or similar
        logger.warning("PayPal integration not yet implemented")
        return {
            'success': False,
            'error': 'PayPal integration pending'
        }
    
    def confirm_paypal_payment(self, service_request, paypal_order_id: str) -> Tuple[bool, str]:
        """
        Confirm PayPal payment succeeded.
        
        To be implemented with PayPal SDK.
        
        Args:
            service_request: ProcurementServiceRequest instance
            paypal_order_id: PayPal order ID
        
        Returns:
            (success, order_id)
        """
        logger.warning("PayPal confirmation not yet implemented")
        return False, None
    
    def refund_paypal_payment(self, service_payment) -> Tuple[bool, str]:
        """
        Refund PayPal payment.
        
        To be implemented with PayPal SDK.
        
        Args:
            service_payment: ServicePayment instance
        
        Returns:
            (success, refund_id)
        """
        logger.warning("PayPal refund not yet implemented")
        return False, "PayPal refund pending"
    
    # =====================================================================
    # REFUND (Generic)
    # =====================================================================
    
    def refund_payment(self, service_payment) -> Tuple[bool, str]:
        """
        Refund payment using appropriate processor.
        
        Called when bot execution fails (out of stock, rate limited, etc.)
        
        Args:
            service_payment: ServicePayment instance
        
        Returns:
            (success, refund_id_or_error)
        """
        payment_method = service_payment.payment_method
        
        if payment_method == 'stripe':
            return self.refund_stripe_payment(service_payment)
        
        elif payment_method == 'venmo':
            return self.refund_venmo_payment(service_payment)
        
        elif payment_method == 'paypal':
            return self.refund_paypal_payment(service_payment)
        
        else:
            error = f"Unknown payment method: {payment_method}"
            logger.error(error)
            return False, error