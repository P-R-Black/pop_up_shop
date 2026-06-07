# pop_up_payment/tests/test_service_fee_handler.py

"""
Tests for ServiceFeePaymentHandler

Tests payment processing for Stripe, Venmo, and PayPal.
Mocks payment processor APIs to avoid real charges.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import timedelta

from pop_up_bot.models import ScheduledRelease, ProcurementServiceRequest
from pop_up_payment.models import ServicePayment
from pop_up_payment.handlers.service_fee_handler import ServiceFeePaymentHandler
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory, PopUpProductType

from pop_up_auction.tests.conftest import (create_test_user)


from django.contrib.auth import get_user_model
User = get_user_model()


class ServiceFeePaymentHandlerTestCase(TestCase):
    """Base test case for ServiceFeePaymentHandler tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create user with profile
        self.user, self.profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )

        # Create a minimal PopUpProduct for testing
        self.product_type = PopUpProductType.objects.create(
            name="Sneakers",
            slug="sneakers"
        )
        self.category = PopUpCategory.objects.create(
            name="Jordan 1",
            slug="jordan-1"
        )
        self.brand = PopUpBrand.objects.create(
            name="Jordan",
            slug="jordan"
        )

        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 1 Low",
            secondary_product_title="OG University Blue",
            retail_price=Decimal("170.00"),
            is_active=True
        )
       
        
        # Create release
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='DJ0646-610',
            release_date=timezone.now() - timedelta(minutes=5),
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com/t/air-jordan-1/553558-404',
            status='scheduled',
            retail_price=Decimal('170.00'),
        )
        
        # Create service request
        self.service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 10',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        # Initialize handler
        self.handler = ServiceFeePaymentHandler()


# ============================================================================
# TESTS: STRIPE PAYMENTS
# ============================================================================

class TestStripePaymentIntent(ServiceFeePaymentHandlerTestCase):
    """Test Stripe PaymentIntent creation"""
    
    @patch('stripe.Customer.create')
    @patch('stripe.PaymentIntent.create')
    def test_create_stripe_payment_intent_new_customer(
        self, 
        mock_payment_intent, 
        mock_customer_create
    ):
        """Test creating Stripe PaymentIntent for new customer"""
        # Mock customer creation
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer
        
        # Mock payment intent
        mock_intent = MagicMock()
        mock_intent.id = 'pi_test456'
        mock_intent.client_secret = 'pi_test456_secret'
        mock_intent.status = 'requires_payment_method'
        mock_payment_intent.return_value = mock_intent
        
        # Call handler
        result = self.handler.create_stripe_payment_intent(self.service_request)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_intent_id'], 'pi_test456')
        self.assertEqual(result['client_secret'], 'pi_test456_secret')
        self.assertEqual(result['amount'], Decimal('15.00'))
        
        # Verify customer was created
        mock_customer_create.assert_called_once()
        
        # Verify payment intent was created with correct amount
        call_kwargs = mock_payment_intent.call_args[1]
        self.assertEqual(call_kwargs['amount'], 1500)  # $15.00 in cents
        self.assertEqual(call_kwargs['currency'], 'usd')
    
    @patch('stripe.Customer.create')
    @patch('stripe.PaymentIntent.create')
    def test_create_stripe_payment_intent_existing_customer(
        self,
        mock_payment_intent,
        mock_customer_retrieve
        ):
        """Test creating Stripe PaymentIntent for existing customer"""
        # Set profile with existing customer ID
        self.profile.stripe_customer_id = 'cus_existing123'
        self.profile.save()
        
        # Mock customer retrieval
        mock_customer = MagicMock()
        mock_customer.id = 'cus_existing123'
        mock_customer_retrieve.return_value = mock_customer
        
        # Mock payment intent
        mock_intent = MagicMock()
        mock_intent.id = 'pi_test456'
        mock_intent.client_secret = 'pi_test456_secret'
        mock_payment_intent.return_value = mock_intent
        
        # Mock the profile getter in the handler's scope
        with patch('pop_up_payment.handlers.service_fee_handler.stripe.Customer.retrieve') as mock_retrieve, \
            patch('pop_up_payment.handlers.service_fee_handler.stripe.PaymentIntent.create') as mock_create:
            
            mock_retrieve.return_value = mock_customer
            mock_create.return_value = mock_intent
            
            # Call handler
            result = self.handler.create_stripe_payment_intent(self.service_request)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_intent_id'], 'pi_test456')
    
    @patch('pop_up_payment.handlers.service_fee_handler.stripe.PaymentIntent.create')
    def test_stripe_payment_intent_with_metadata(self, mock_payment_intent):
        """Test PaymentIntent includes correct metadata"""
        # Mock customer
        with patch('pop_up_payment.handlers.service_fee_handler.stripe.Customer.create') as mock_customer:
            mock_customer.return_value = MagicMock(id='cus_test123')
            
            # Mock intent
            mock_intent = MagicMock()
            mock_intent.id = 'pi_test456'
            mock_intent.client_secret = 'pi_test456_secret'
            mock_payment_intent.return_value = mock_intent
            
            # Call handler
            result = self.handler.create_stripe_payment_intent(self.service_request)
            
            # Verify metadata
            call_kwargs = mock_payment_intent.call_args[1]
            self.assertEqual(call_kwargs['description'], f"Procurement Service Fee - {self.service_request.id}")
            self.assertIn('service_request_id', call_kwargs['metadata'])
            self.assertIn('user_email', call_kwargs['metadata'])


    @patch('stripe.Customer.create')
    @patch('stripe.PaymentIntent.create')
    def test_stripe_payment_intent_failure(self, mock_payment_intent, mock_customer_create):
        """Test handling Stripe API errors"""
        # Mock API error
        mock_customer_create.side_effect = Exception("API Error: Invalid API Key")
        
        # Call handler
        result = self.handler.create_stripe_payment_intent(self.service_request)
        
        # Verify error handling
        self.assertFalse(result['success'])
        self.assertIn('error', result)


# ============================================================================
# TESTS: STRIPE CONFIRMATION
# ============================================================================

class TestStripePaymentConfirmation(ServiceFeePaymentHandlerTestCase):
    """Test Stripe payment confirmation"""
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_stripe_payment_succeeded(self, mock_retrieve):
        """Test confirming successful Stripe payment"""
        # Mock intent
        mock_intent = MagicMock()
        mock_intent.status = 'succeeded'
        mock_retrieve.return_value = mock_intent
        
        # Confirm payment
        success, payment_ref = self.handler.confirm_stripe_payment(
            self.service_request,
            'pi_test123'
        )
        
        self.assertTrue(success)
        self.assertEqual(payment_ref, 'pi_test123')
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_stripe_payment_processing(self, mock_retrieve):
        """Test confirming processing Stripe payment"""
        # Mock intent still processing
        mock_intent = MagicMock()
        mock_intent.status = 'processing'
        mock_retrieve.return_value = mock_intent
        
        # Confirm payment
        success, payment_ref = self.handler.confirm_stripe_payment(
            self.service_request,
            'pi_test123'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_ref)
    
    @patch('stripe.PaymentIntent.retrieve')
    def test_confirm_stripe_payment_api_error(self, mock_retrieve):
        """Test Stripe API error during confirmation"""
        # Mock API error
        mock_retrieve.side_effect = Exception("API Error")
        
        # Confirm payment
        success, payment_ref = self.handler.confirm_stripe_payment(
            self.service_request,
            'pi_invalid'
        )
        
        self.assertFalse(success)
        self.assertIsNone(payment_ref)


# ============================================================================
# TESTS: STRIPE REFUNDS
# ============================================================================

class TestStripeRefund(ServiceFeePaymentHandlerTestCase):
    """Test Stripe refund processing"""
    
    def setUp(self):
        """Set up refund test"""
        super().setUp()
        
        # Create paid service payment
        self.service_payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
            payment_reference='pi_test123',
        )
    
    @patch('stripe.Refund.create')
    def test_refund_stripe_payment_success(self, mock_refund_create):
        """Test successful Stripe refund"""
        # Mock refund
        mock_refund = MagicMock()
        mock_refund.id = 're_test789'
        mock_refund_create.return_value = mock_refund
        
        # Process refund
        success, refund_id = self.handler.refund_stripe_payment(self.service_payment)
        
        self.assertTrue(success)
        self.assertEqual(refund_id, 're_test789')
        
        # Verify API call
        mock_refund_create.assert_called_once()
        call_kwargs = mock_refund_create.call_args[1]
        self.assertEqual(call_kwargs['payment_intent'], 'pi_test123')
    
    def test_refund_stripe_payment_no_reference(self):
        """Test refund fails when no payment reference"""
        # Create a NEW service request (so we don't conflict with self.service_payment)
        service_request2 = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )

        # Create payment without reference
        service_payment = ServicePayment.objects.create(
            service_request=service_request2,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
            payment_reference=None,
        )
        
        # Process refund
        success, refund_id = self.handler.refund_stripe_payment(service_payment)
        
        self.assertFalse(success)
    
    @patch('stripe.Refund.create')
    def test_refund_stripe_payment_api_error(self, mock_refund_create):
        """Test handling Stripe refund API error"""
        # Mock API error
        mock_refund_create.side_effect = Exception("Refund failed: Invalid charge")
        
        # Process refund
        success, error = self.handler.refund_stripe_payment(self.service_payment)
        self.assertFalse(success)
        self.assertIn('failed to refund', str(error).lower())


# ============================================================================
# TESTS: VENMO PAYMENTS
# ============================================================================

class TestVenmoPaymentProcessing(ServiceFeePaymentHandlerTestCase):
    """Test Venmo payment processing via Braintree"""
    
    def setUp(self):
        """Set up Venmo test"""
        super().setUp()
        
        # Patch Braintree gateway
        self.braintree_patcher = patch.object(
            self.handler,
            'braintree_gateway'
        )
        self.mock_gateway = self.braintree_patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        self.braintree_patcher.stop()
        super().tearDown()
    
    def test_process_venmo_payment_success(self):
        """Test successful Venmo payment processing"""
        # Mock transaction
        mock_transaction = MagicMock()
        mock_transaction.id = 'venmo_txn_123'
        
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.transaction = mock_transaction
        
        self.mock_gateway.transaction.sale.return_value = mock_result
        
        # Process payment
        success, txn_id, error = self.handler.process_venmo_payment(
            self.service_request,
            'nonce_test123'
        )
        
        self.assertTrue(success)
        self.assertEqual(txn_id, 'venmo_txn_123')
        self.assertEqual(error, "")
    
    def test_process_venmo_payment_failure(self):
        """Test failed Venmo payment"""
        # Mock failed transaction
        mock_result = MagicMock()
        mock_result.is_success = False
        mock_result.message = 'Invalid payment method'
        
        self.mock_gateway.transaction.sale.return_value = mock_result
        
        # Process payment
        success, txn_id, error = self.handler.process_venmo_payment(
            self.service_request,
            'nonce_invalid'
        )
        
        self.assertFalse(success)
        self.assertEqual(error, 'Invalid payment method')
    
    def test_process_venmo_payment_exception(self):
        """Test Venmo API exception"""
        # Mock exception
        self.mock_gateway.transaction.sale.side_effect = Exception("Connection error")
        
        # Process payment
        success, txn_id, error = self.handler.process_venmo_payment(
            self.service_request,
            'nonce_test123'
        )
        
        self.assertFalse(success)
        self.assertIn('Connection error', error)


# ============================================================================
# TESTS: VENMO REFUNDS
# ============================================================================

class TestVenmoRefund(ServiceFeePaymentHandlerTestCase):
    """Test Venmo refund processing"""
    
    def setUp(self):
        """Set up Venmo refund test"""
        super().setUp()
        
        # Create paid Venmo payment
        self.service_payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='venmo',
            status='paid',
            payment_reference='venmo_txn_123',
        )
        
        # Patch Braintree
        self.braintree_patcher = patch.object(
            self.handler,
            'braintree_gateway'
        )
        self.mock_gateway = self.braintree_patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        self.braintree_patcher.stop()
        super().tearDown()
    
    def test_refund_venmo_payment_success(self):
        """Test successful Venmo refund"""
        # Mock refund transaction
        mock_refund_txn = MagicMock()
        mock_refund_txn.id = 'venmo_refund_456'
        
        mock_result = MagicMock()
        mock_result.is_success = True
        mock_result.transaction = mock_refund_txn
        
        self.mock_gateway.transaction.refund.return_value = mock_result
        
        # Process refund
        success, refund_id = self.handler.refund_venmo_payment(self.service_payment)
        
        self.assertTrue(success)
        self.assertEqual(refund_id, 'venmo_refund_456')
    
    def test_refund_venmo_payment_failure(self):
        """Test failed Venmo refund"""
        # Mock failed refund
        mock_result = MagicMock()
        mock_result.is_success = False
        mock_result.message = 'Transaction already refunded'
        
        self.mock_gateway.transaction.refund.return_value = mock_result
        
        # Process refund
        success, error = self.handler.refund_venmo_payment(self.service_payment)
        
        self.assertFalse(success)
        self.assertIn('already refunded', error)
    
    def test_refund_venmo_payment_no_reference(self):
        """Test refund fails when no transaction ID"""
        # Create payment without reference
        service_request_two = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 9',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )

        service_payment = ServicePayment.objects.create(
            service_request=service_request_two,
            amount=Decimal('15.00'),
            payment_method='venmo',
            status='paid',
            payment_reference=None,
        )
        
        # Process refund
        success, error = self.handler.refund_venmo_payment(service_payment)
        
        self.assertFalse(success)


# ============================================================================
# TESTS: GENERIC REFUND
# ============================================================================

class TestGenericRefund(ServiceFeePaymentHandlerTestCase):
    """Test generic refund method that routes to correct processor"""
    
    def setUp(self):
        """Set up refund test"""
        super().setUp()
    
    def test_generic_refund_stripe(self):
        """Test generic refund routes to Stripe"""
        # Create Stripe payment
        service_payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
            payment_reference='pi_test123',
        )
        
        # Mock Stripe refund
        with patch.object(
            self.handler,
            'refund_stripe_payment',
            return_value=(True, 're_test123')
        ) as mock_refund:
            success, refund_id = self.handler.refund_payment(service_payment)
        
        self.assertTrue(success)
        mock_refund.assert_called_once_with(service_payment)
    
    def test_generic_refund_venmo(self):
        """Test generic refund routes to Venmo"""
        # Create Venmo payment
        service_payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='venmo',
            status='paid',
            payment_reference='venmo_txn_123',
        )
        
        # Mock Venmo refund
        with patch.object(
            self.handler,
            'refund_venmo_payment',
            return_value=(True, 'venmo_refund_456')
        ) as mock_refund:
            success, refund_id = self.handler.refund_payment(service_payment)
        
        self.assertTrue(success)
        mock_refund.assert_called_once_with(service_payment)
    
    def test_generic_refund_unknown_method(self):
        """Test generic refund fails for unknown payment method"""
        # Create payment with unknown method
        service_payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='invalid_method',
            status='paid',
            payment_reference='test_123',
        )
        
        # Attempt refund
        success, error = self.handler.refund_payment(service_payment)
        
        self.assertFalse(success)
        self.assertIn('Unknown payment method', error)


# ============================================================================
# TESTS: SERVICE FEE AMOUNT
# ============================================================================

class TestServiceFeeAmount(ServiceFeePaymentHandlerTestCase):
    """Test that service fee is always $15"""
    
    def test_service_fee_constant(self):
        """Test SERVICE_FEE constant is $15"""
        self.assertEqual(self.handler.SERVICE_FEE, Decimal('15.00'))
    
    @patch('stripe.PaymentIntent.create')
    def test_stripe_amount_is_1500_cents(self, mock_intent):
        """Test Stripe payment is created for $15.00 (1500 cents)"""
        # Mock customer
        with patch.object(self.handler, 'braintree_gateway'):
            with patch('stripe.Customer.create') as mock_customer:
                mock_customer.return_value = MagicMock(id='cus_test123')
                
                # Mock intent
                mock_intent.return_value = MagicMock(
                    id='pi_test123',
                    client_secret='secret'
                )
                
                # Create intent
                self.handler.create_stripe_payment_intent(self.service_request)
        
        # Verify amount
        call_kwargs = mock_intent.call_args[1]
        self.assertEqual(call_kwargs['amount'], 1500)