# pop_up_bot/tests/test_refund_policy.py

"""
Tests for Refund Policy Logic

Tests the should_refund_service_fee() and auto_refund_service_fee() functions.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import timedelta
import logging

from pop_up_bot.models import (
    ScheduledRelease,
    ProcurementServiceRequest,
    ProcurementRequest,
    ProcurementExecution,
)
from pop_up_bot.tasks import should_refund_service_fee, auto_refund_service_fee
from pop_up_payment.models import ServicePayment
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory, PopUpProductType
from pop_up_auction.tests.conftest import (create_test_user)


from django.contrib.auth import get_user_model
User = get_user_model()


class RefundPolicyTestCase(TestCase):
    """Base test case for refund policy tests"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
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
        
        # Create procurement request
        self.proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 10',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        # Link them
        self.service_request.procurement_request = self.proc_request
        self.service_request.save()
        
        # Create paid service payment
        self.service_payment = ServicePayment.objects.create(
            service_request=self.service_request,
            amount=Decimal('15.00'),
            payment_method='stripe',
            status='paid',
            payment_reference='pi_test123',
        )


# ============================================================================
# TESTS: SHOULD REFUND DECISION LOGIC
# ============================================================================

class TestShouldRefundDecisionLogic(RefundPolicyTestCase):
    """Test should_refund_service_fee() decision function"""
    
    # REFUNDABLE ERRORS (return True)
    
    def test_should_refund_bot_crash(self):
        """Test should refund on bot_crash"""
        self.assertTrue(should_refund_service_fee('bot_crash'))
    
    def test_should_refund_rate_limited(self):
        """Test should refund on rate_limited"""
        self.assertTrue(should_refund_service_fee('rate_limited'))
    
    def test_should_refund_site_structure_changed(self):
        """Test should refund on site_structure_changed"""
        self.assertTrue(should_refund_service_fee('site_structure_changed'))
    
    def test_should_refund_exception(self):
        """Test should refund on exception"""
        self.assertTrue(should_refund_service_fee('exception'))
    
    def test_should_refund_unknown_error(self):
        """Test should refund on unknown_error"""
        self.assertTrue(should_refund_service_fee('unknown_error'))
    
    # NON-REFUNDABLE ERRORS (return False)
    
    def test_should_not_refund_out_of_stock(self):
        """Test should NOT refund on out_of_stock"""
        self.assertFalse(should_refund_service_fee('out_of_stock'))
    
    def test_should_not_refund_lost_to_bots(self):
        """Test should NOT refund on lost_to_bots"""
        self.assertFalse(should_refund_service_fee('lost_to_bots'))
    
    def test_should_not_refund_item_not_found(self):
        """Test should NOT refund on item_not_found"""
        self.assertFalse(should_refund_service_fee('item_not_found'))
    
    def test_should_not_refund_sold_out(self):
        """Test should NOT refund on sold_out"""
        self.assertFalse(should_refund_service_fee('sold_out'))
    
    def test_should_not_refund_coming_soon(self):
        """Test should NOT refund on coming_soon"""
        self.assertFalse(should_refund_service_fee('coming_soon'))
    
    def test_should_not_refund_payment_already_exists(self):
        """Test should NOT refund on payment_already_exists"""
        self.assertFalse(should_refund_service_fee('payment_already_exists'))
    
    def test_should_not_refund_success(self):
        """Test should NOT refund on success"""
        self.assertFalse(should_refund_service_fee('success'))
    
#     # EDGE CASES
    
    def test_should_refund_case_insensitive(self):
        """Test that error type checking is case-insensitive"""
        self.assertTrue(should_refund_service_fee('BOT_CRASH'))
        self.assertTrue(should_refund_service_fee('Rate_Limited'))
    
    def test_should_refund_none_error_type(self):
        """Test that None error type returns False"""
        self.assertFalse(should_refund_service_fee(None))
    
    def test_should_refund_empty_string(self):
        """Test that empty string returns False"""
        self.assertFalse(should_refund_service_fee(''))
    
    def test_should_refund_unknown_error_type(self):
        """Test that unknown error type returns False"""
        self.assertFalse(should_refund_service_fee('some_random_error'))


# ============================================================================
# TESTS: AUTO REFUND EXECUTION
# ============================================================================

class TestAutoRefundExecution(RefundPolicyTestCase):
    """Test auto_refund_service_fee() execution"""
    
    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler.refund_payment')
    def test_auto_refund_bot_crash(self, mock_refund):
        """Test auto-refund on bot_crash"""
        # Mock successful refund
        mock_refund.return_value = (True, 're_test123')
        
        # Call auto-refund
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='NoneType object'
        )
        
        # Verify refund was processed
        self.assertTrue(result)
        mock_refund.assert_called_once()
        
        # Verify payment status updated
        self.service_payment.refresh_from_db()
        self.assertEqual(self.service_payment.status, 'refunded')
        self.assertEqual(self.service_payment.refund_reference, 're_test123')
    
    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler.refund_payment')
    def test_auto_refund_rate_limited(self, mock_refund):
        """Test auto-refund on rate_limited"""
        mock_refund.return_value = (True, 're_test456')
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='rate_limited',
            reason='429 Too Many Requests'
        )
        
        self.assertTrue(result)
        mock_refund.assert_called_once()
    
    def test_auto_refund_out_of_stock_no_refund(self):
        """Test NO refund on out_of_stock"""
        # Should return False, not call refund
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='out_of_stock',
            reason='Item not available'
        )
        
        self.assertFalse(result)
        
        # Verify payment NOT refunded
        self.service_payment.refresh_from_db()
        self.assertEqual(self.service_payment.status, 'paid')
    
    def test_auto_refund_lost_to_bots_no_refund(self):
        """Test NO refund on lost_to_bots"""
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='lost_to_bots',
            reason='Another bot got it first'
        )
        
        self.assertFalse(result)
        
        # Verify payment NOT refunded
        self.service_payment.refresh_from_db()
        self.assertEqual(self.service_payment.status, 'paid')
    
    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler.refund_payment')
    def test_auto_refund_failure_handling(self, mock_refund):
        """Test handling of refund failure"""
        # Mock refund failure
        mock_refund.return_value = (False, 'Refund API error')
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Bot crashed'
        )
        
        # Should return False since refund failed
        self.assertFalse(result)


# ============================================================================
# TESTS: AUTO REFUND - NO SERVICE REQUEST
# ============================================================================

class TestAutoRefundNoServiceRequest(RefundPolicyTestCase):
    """Test auto-refund when service request not linked"""
    
    def test_auto_refund_no_service_request(self):
        """Test auto-refund when procurement_request has no service_request"""
        # Create proc request without service request
        proc_req = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Test Product',
            target_size='US 10',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        result = auto_refund_service_fee(
            proc_req,
            error_type='bot_crash',
            reason='Test'
        )
        
        # Should return False
        self.assertFalse(result)


# ============================================================================
# TESTS: AUTO REFUND - NO SERVICE PAYMENT
# ============================================================================

class TestAutoRefundNoServicePayment(RefundPolicyTestCase):
    """Test auto-refund when service payment doesn't exist"""
    
    def test_auto_refund_no_payment_record(self):
        """Test auto-refund when no ServicePayment exists"""
        # Delete service payment
        self.service_payment.delete()
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Test'
        )
        
        # Should return False
        self.assertFalse(result)


# ============================================================================
# TESTS: AUTO REFUND - ALREADY REFUNDED
# ============================================================================

class TestAutoRefundAlreadyRefunded(RefundPolicyTestCase):
    """Test auto-refund when already refunded"""
    
    def test_auto_refund_already_refunded(self):
        """Test auto-refund when already refunded"""
        # Mark as refunded
        self.service_payment.mark_refunded('re_already123')
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Test'
        )
        
        # Should return False (already done)
        self.assertFalse(result)


# ============================================================================
# TESTS: AUTO REFUND - PAYMENT NOT YET PAID
# ============================================================================

class TestAutoRefundPaymentNotPaid(RefundPolicyTestCase):
    """Test auto-refund when payment not yet paid"""
    
    def test_auto_refund_payment_pending(self):
        """Test auto-refund when payment still pending"""
        # Mark as pending
        self.service_payment.status = 'pending'
        self.service_payment.save()
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Test'
        )
        
        # Should return False (not paid yet)
        self.assertFalse(result)
    
    def test_auto_refund_payment_processing(self):
        """Test auto-refund when payment processing"""
        # Mark as processing
        self.service_payment.status = 'processing'
        self.service_payment.save()
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Test'
        )
        
        # Should return False (not paid yet)
        self.assertFalse(result)


# ============================================================================
# TESTS: AUTO REFUND - PAYMENT FAILED
# ============================================================================

class TestAutoRefundPaymentFailed(RefundPolicyTestCase):
    """Test auto-refund when original payment failed"""
    
    def test_auto_refund_payment_failed_status(self):
        """Test auto-refund when payment was failed"""
        # Mark as failed
        self.service_payment.mark_failed('Card declined')
        
        result = auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Test'
        )
        
        # Should return False (no refund needed)
        self.assertFalse(result)


# ============================================================================
# TESTS: AUTO REFUND - LOGGING
# ============================================================================

class TestAutoRefundLogging(RefundPolicyTestCase):
    """Test auto-refund logging"""
    
    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler.refund_payment')
    @patch('pop_up_bot.tasks.logger')
    def test_auto_refund_success_logged(self, mock_logger, mock_refund):
        """Test successful refund is logged"""
        mock_refund.return_value = (True, 're_test123')
        
        auto_refund_service_fee(
            self.proc_request,
            error_type='bot_crash',
            reason='Test crash'
        )
        
        # Verify info log
        mock_logger.info.assert_called()
        call_args = str(mock_logger.info.call_args)
        self.assertIn('Refunded', call_args)
    
    @patch('pop_up_bot.tasks.logger')
    def test_auto_refund_non_refundable_logged(self, mock_logger):
        """Test non-refundable error is logged"""
        auto_refund_service_fee(
            self.proc_request,
            error_type='out_of_stock',
            reason='Item not available'
        )
        
        # Verify info log about keeping fee
        mock_logger.info.assert_called()
        call_args = str(mock_logger.info.call_args)
        self.assertIn('SERVICE FEE NOT REFUNDED', call_args.upper())


# ============================================================================
# TESTS: INTEGRATION - FULL REFUND FLOW
# ============================================================================

class TestFullRefundFlow(RefundPolicyTestCase):
    """Test complete refund flow"""
    
    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler.refund_payment')
    def test_full_flow_crash_and_refund(self, mock_refund):
        """Test full flow: bot crashes → auto-refund"""
        mock_refund.return_value = (True, 're_test123')
        
        # Bot crashes
        error_type = 'bot_crash'
        reason = 'NoneType at line 42'
        
        # Auto-refund
        refund_success = auto_refund_service_fee(
            self.proc_request,
            error_type=error_type,
            reason=reason
        )
        
        # Verify
        self.assertTrue(refund_success)
        
        self.service_payment.refresh_from_db()
        self.assertEqual(self.service_payment.status, 'refunded')
        self.assertEqual(self.service_payment.refund_reference, 're_test123')
    
    def test_full_flow_lost_item_no_refund(self):
        """Test full flow: lost to bots → NO refund"""
        # Bot loses item
        error_type = 'lost_to_bots'
        reason = 'Another bot was faster'
        
        # Try auto-refund
        refund_success = auto_refund_service_fee(
            self.proc_request,
            error_type=error_type,
            reason=reason
        )
        
        # Verify no refund
        self.assertFalse(refund_success)
        
        self.service_payment.refresh_from_db()
        self.assertEqual(self.service_payment.status, 'paid')