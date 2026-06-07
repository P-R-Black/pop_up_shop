# pop_up_payment/tests/test_service_payment.py

"""
Tests for ServicePayment model

Tests the procurement service fee payment model ($15 fee).
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from pop_up_bot.models import ScheduledRelease, ProcurementServiceRequest
from pop_up_payment.models import ServicePayment
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory, PopUpProductType

from pop_up_auction.tests.conftest import (create_test_user)


from django.contrib.auth import get_user_model

User = get_user_model()


class ServicePaymentModelTestCase(TestCase):
    """Base test case for ServicePayment tests"""
    
    def setUp(self):
        """Set up test data"""
    
        # Create test user
        self.user, self.user_profile = create_test_user(
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

        # self.brand = PopUpBrand.objects.create(name='Nike')
        # self.category = PopUpCategory.objects.create(name='Shoes')
        # self.product = PopUpProduct.objects.create(
        #     product_title='Air Jordan 1 Low',
        #     retail_price=Decimal('170.00'),
        #     brand=self.brand,
        #     category=self.category,
        #     is_active=True,
        # )
        
        # Create scheduled release
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


# ============================================================================
# TESTS: SERVICE PAYMENT CREATION
# ============================================================================

class TestServicePaymentCreation(ServicePaymentModelTestCase):
    """Test creating ServicePayment records"""
    
    def test_create_service_payment_stripe(self):
        """Test creating a Stripe service payment"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='processing',
            payment_reference='pi_1234567890'
        )

        
        self.assertIsNotNone(payment.id)
        self.assertEqual(payment.amount, Decimal('15.00'))
        self.assertEqual(payment.payment_method, 'stripe')
        self.assertEqual(payment.status, 'processing')
        self.assertEqual(payment.payment_reference, 'pi_1234567890')
    
    def test_create_service_payment_venmo(self):
        """Test creating a Venmo service payment"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='venmo',
            status='paid',
            payment_reference='txn_789456123'
        )
        
        self.assertEqual(payment.payment_method, 'venmo')
        self.assertEqual(payment.status, 'paid')
        self.assertIsNotNone(payment.paid_at)
    
    def test_create_service_payment_paypal(self):
        """Test creating a PayPal service payment"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='paypal',
            status='pending',
        )
        
        self.assertEqual(payment.payment_method, 'paypal')
        self.assertIsNone(payment.payment_reference)
    
    def test_default_amount_is_15_dollars(self):
        """Test that default service fee is $15"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            payment_method='stripe',
        )
        
        self.assertEqual(payment.amount, Decimal('15.00'))


# ============================================================================
# TESTS: STATUS TRANSITIONS
# ============================================================================

class TestServicePaymentStatusTransitions(ServicePaymentModelTestCase):
    """Test payment status transitions"""
    
    def test_mark_paid(self):
        """Test marking payment as paid"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='processing',
        )
        
        before_time = timezone.now()
        payment.mark_paid('pi_test123')
        after_time = timezone.now()
        
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'paid')
        self.assertEqual(payment.payment_reference, 'pi_test123')
        self.assertIsNotNone(payment.paid_at)
        self.assertGreaterEqual(payment.paid_at, before_time)
        self.assertLessEqual(payment.paid_at, after_time)
    

    def test_mark_failed(self):
        """Test marking payment as failed"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='processing',
        )
        
        error_msg = 'Card declined by issuer'
        payment.mark_failed(error_msg)
        
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.error_message, error_msg)
    
    def test_mark_refunded(self):
        """Test marking payment as refunded"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
            payment_reference='pi_test123',
        )
        
        before_time = timezone.now()
        payment.mark_refunded('refund_123')
        after_time = timezone.now()
        
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'refunded')
        self.assertEqual(payment.refund_reference, 'refund_123')
        self.assertIsNotNone(payment.refunded_at)
        self.assertGreaterEqual(payment.refunded_at, before_time)
        self.assertLessEqual(payment.refunded_at, after_time)


# ============================================================================
# TESTS: PROPERTIES
# ============================================================================

class TestServicePaymentProperties(ServicePaymentModelTestCase):
    """Test ServicePayment properties"""
    
    def test_is_paid_true(self):
        """Test is_paid property when status is 'paid'"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
        )
        
        self.assertTrue(payment.is_paid)
    
    def test_is_paid_false(self):
        """Test is_paid property when status is not 'paid'"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='pending',
        )
        
        self.assertFalse(payment.is_paid)
    
    def test_is_refunded_true(self):
        """Test is_refunded property when status is 'refunded'"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='refunded',
        )
        
        self.assertTrue(payment.is_refunded)
    
    def test_is_refunded_false(self):
        """Test is_refunded property when status is not 'refunded'"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
        )
        
        self.assertFalse(payment.is_refunded)


# ============================================================================
# TESTS: RELATIONSHIPS
# ============================================================================

class TestServicePaymentRelationships(ServicePaymentModelTestCase):
    """Test ServicePayment relationships"""
    
    def test_service_payment_links_to_service_request(self):
        """Test that ServicePayment correctly links to ProcurementServiceRequest"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
        )
        
        self.assertEqual(payment.service_request, self.service_request)
        self.assertTrue(hasattr(self.service_request, 'service_payment'))
        self.assertEqual(self.service_request.service_payment, payment)
    
    def test_one_to_one_relationship(self):
        """Test that ServicePayment is one-to-one with ServiceRequest"""
        # Create first payment
        payment1 = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
        )
        
        # Try to create second payment for same request
        # Should fail with integrity error
        with self.assertRaises(Exception):
            ServicePayment.objects.create(
                service_request=self.service_request,
                amount=Decimal('15.00'),
                payment_method='venmo',
            )


# ============================================================================
# TESTS: STRING REPRESENTATION
# ============================================================================

class TestServicePaymentStringRepresentation(ServicePaymentModelTestCase):
    """Test ServicePayment string representation"""
    
    def test_str_representation(self):
        """Test __str__ method"""
        payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
        )
        
        str_rep = str(payment)
        
        self.assertIn('ServicePayment', str_rep)
        self.assertIn(str(payment.id), str_rep)
        self.assertIn('test@example.com', str_rep)
        self.assertIn('15.00', str_rep)
        self.assertIn('paid', str_rep)


# ============================================================================
# TESTS: ORDERING
# ============================================================================

class TestServicePaymentOrdering(ServicePaymentModelTestCase):
    """Test ServicePayment ordering"""
    
    def test_ordered_by_created_at_descending(self):
        """Test that payments are ordered by created_at descending"""
        # Create multiple payments
        payment1 = ServicePayment.objects.create(
            service_request=self.service_request,
            payment_method='stripe',
        )
        
        # Create another service request for second payment
        service_request2 = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        payment2 = ServicePayment.objects.create(
            service_request=service_request2,
            payment_method='stripe',
        )
        
        # Get all payments ordered (default)
        payments = list(ServicePayment.objects.all())
        
        # Most recent should be first
        self.assertEqual(payments[0].id, payment2.id)
        self.assertEqual(payments[1].id, payment1.id)


# ============================================================================
# TESTS: FILTERING
# ============================================================================

class TestServicePaymentFiltering(ServicePaymentModelTestCase):
    """Test filtering ServicePayment records"""
    
    def test_filter_by_status_paid(self):
        """Test filtering by status='paid'"""
        # Create payments with different statuses
        payment1 = ServicePayment.objects.create(
            service_request=self.service_request,
            payment_method='stripe',
            status='paid',
        )
        
        service_request2 = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        payment2 = ServicePayment.objects.create(
            service_request=service_request2,
            payment_method='stripe',
            status='pending',
        )
        
        # Filter
        paid_payments = ServicePayment.objects.filter(status='paid')
        
        self.assertEqual(paid_payments.count(), 1)
        self.assertEqual(paid_payments.first().id, payment1.id)
    
    def test_filter_by_payment_method(self):
        """Test filtering by payment_method"""
        # Create Stripe payment
        payment1 = ServicePayment.objects.create(
            service_request=self.service_request,
            payment_method='stripe',
        )
        
        # Create another request
        service_request2 = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        # Create Venmo payment
        payment2 = ServicePayment.objects.create(
            service_request=service_request2,
            payment_method='venmo',
        )
        
        # Filter
        stripe_payments = ServicePayment.objects.filter(payment_method='stripe')
        venmo_payments = ServicePayment.objects.filter(payment_method='venmo')
        
        self.assertEqual(stripe_payments.count(), 1)
        self.assertEqual(venmo_payments.count(), 1)