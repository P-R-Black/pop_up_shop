# pop_up_bot/tests/test_procurement_execution.py

"""
Tests for ProcurementExecution model

Tests the updated ProcurementExecution model with error_type field.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from pop_up_bot.models import (
    ScheduledRelease,
    ProcurementRequest,
    ProcurementExecution,
)
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory, PopUpProductType
from pop_up_auction.tests.conftest import (create_test_user)

from django.contrib.auth import get_user_model

User = get_user_model()


class ProcurementExecutionModelTestCase(TestCase):
    """Base test case for ProcurementExecution tests"""
    
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

        
        # Create procurement request
        self.proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 10',
            target_color='Red',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )


# ============================================================================
# TESTS: ERROR TYPE CHOICES
# ============================================================================

class TestProcurementExecutionErrorTypes(ProcurementExecutionModelTestCase):
    """Test ProcurementExecution error_type field and choices"""
    
    def test_create_execution_with_bot_crash_error(self):
        """Test creating execution with bot_crash error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='bot_crash',
            error_message='Unhandled exception in main loop',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'bot_crash')
        self.assertEqual(execution.status, 'failed')
    
    def test_create_execution_with_rate_limited_error(self):
        """Test creating execution with rate_limited error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='rate_limited',
            error_message='Site returned 429 Too Many Requests',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'rate_limited')
    
    def test_create_execution_with_site_structure_changed_error(self):
        """Test creating execution with site_structure_changed error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='site_structure_changed',
            error_message='Selectors no longer match site HTML',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'site_structure_changed')
    
    def test_create_execution_with_out_of_stock_error(self):
        """Test creating execution with out_of_stock error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='out_of_stock',
            error_message='Item not available on any site',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'out_of_stock')
    
    def test_create_execution_with_lost_to_bots_error(self):
        """Test creating execution with lost_to_bots error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='lost_to_bots',
            error_message='Item was available but another bot got it first',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'lost_to_bots')
    
    def test_create_execution_with_item_not_found_error(self):
        """Test creating execution with item_not_found error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='item_not_found',
            error_message='Could not find item on any site',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'item_not_found')
    
    def test_create_execution_with_success_error_type(self):
        """Test creating execution with success error type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='success',
            error_type='success',
            order_id='ORD-12345',
            item_price=Decimal('170.00'),
            winning_site='nike',
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, 'success')
        self.assertEqual(execution.status, 'success')


# ============================================================================
# TESTS: ERROR TYPE FILTERING
# ============================================================================

class TestProcurementExecutionErrorTypeFiltering(ProcurementExecutionModelTestCase):
    """Test filtering executions by error_type"""
    
    def test_filter_refundable_errors(self):
        """Test filtering refundable errors (code issues)"""
        # Create refundable errors
        exec1 = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='bot_crash',
            started_at=timezone.now(),
        )
        
        proc_request2 = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 11',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        exec2 = ProcurementExecution.objects.create(
            procurement_request=proc_request2,
            status='failed',
            error_type='rate_limited',
            started_at=timezone.now(),
        )
        
        # Filter refundable
        refundable = ProcurementExecution.objects.filter(
            error_type__in=['bot_crash', 'rate_limited', 'site_structure_changed']
        )
        
        self.assertEqual(refundable.count(), 2)
    
    def test_filter_non_refundable_errors(self):
        """Test filtering non-refundable errors (market issues)"""
        # Create non-refundable errors
        exec1 = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='out_of_stock',
            started_at=timezone.now(),
        )
        
        proc_request2 = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 11',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        exec2 = ProcurementExecution.objects.create(
            procurement_request=proc_request2,
            status='failed',
            error_type='lost_to_bots',
            started_at=timezone.now(),
        )
        
        # Filter non-refundable
        non_refundable = ProcurementExecution.objects.filter(
            error_type__in=['out_of_stock', 'lost_to_bots', 'item_not_found']
        )
        
        self.assertEqual(non_refundable.count(), 2)


# ============================================================================
# TESTS: ERROR TYPE WITH STATUS
# ============================================================================

class TestProcurementExecutionErrorTypeWithStatus(ProcurementExecutionModelTestCase):
    """Test error_type field with status field"""
    
    def test_failed_status_has_error_type(self):
        """Test that failed status should have an error_type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='out_of_stock',
            error_message='Item out of stock',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.status, 'failed')
        self.assertIsNotNone(execution.error_type)
    
    def test_success_status_with_success_error_type(self):
        """Test that success status should have success error_type"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='success',
            error_type='success',
            order_id='ORD-12345',
            item_price=Decimal('170.00'),
            winning_site='nike',
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        
        self.assertEqual(execution.status, 'success')
        self.assertEqual(execution.error_type, 'success')
    
    def test_running_status_may_have_no_error_type(self):
        """Test that running status may not have error_type yet"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='running',
            error_type=None,
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.status, 'running')
        self.assertIsNone(execution.error_type)


# ============================================================================
# TESTS: ERROR TYPE NULL HANDLING
# ============================================================================

class TestProcurementExecutionErrorTypeNullHandling(ProcurementExecutionModelTestCase):
    """Test error_type field with null/blank values"""
    
    def test_error_type_can_be_null(self):
        """Test that error_type can be null"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='running',
            error_type=None,
            started_at=timezone.now(),
        )
        
        self.assertIsNone(execution.error_type)
    
    def test_error_type_can_be_blank(self):
        """Test that error_type can be blank string"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='running',
            error_type='',
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_type, '')


# ============================================================================
# TESTS: ERROR REASON WITH ERROR TYPE
# ============================================================================

class TestProcurementExecutionErrorReasonWithErrorType(ProcurementExecutionModelTestCase):
    """Test error_reason field with error_type"""
    
    def test_error_reason_with_bot_crash(self):
        """Test error_reason is captured with bot_crash error_type"""
        error_msg = "NoneType object is not subscriptable at line 42"
        
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='bot_crash',
            error_message=error_msg,
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_message, error_msg)
        self.assertEqual(execution.error_type, 'bot_crash')
    
    def test_error_reason_with_rate_limited(self):
        """Test error_reason is captured with rate_limited error_type"""
        error_msg = "HTTP 429: Too Many Requests"
        
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='rate_limited',
            error_message=error_msg,
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_message, error_msg)
    
    def test_error_reason_with_out_of_stock(self):
        """Test error_reason with out_of_stock error_type"""
        error_msg = "Item not available in requested size"
        
        execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='failed',
            error_type='out_of_stock',
            error_message=error_msg,
            started_at=timezone.now(),
        )
        
        self.assertEqual(execution.error_message, error_msg)


# ============================================================================
# TESTS: ALL ERROR TYPES VALID
# ============================================================================

class TestAllErrorTypesValid(ProcurementExecutionModelTestCase):
    """Test that all documented error types are valid"""
    
    def test_all_refundable_error_types(self):
        """Test all refundable error types can be created"""
        refundable_types = [
            'bot_crash',
            'rate_limited',
            'site_structure_changed',
            'exception',
            'unknown_error',
        ]
        
        for error_type in refundable_types:
            execution = ProcurementExecution.objects.create(
                procurement_request=self.proc_request,
                status='failed',
                error_type=error_type,
                started_at=timezone.now(),
            )
            
            self.assertEqual(execution.error_type, error_type)
            
            # Clean up for next iteration
            execution.delete()
    
    def test_all_non_refundable_error_types(self):
        """Test all non-refundable error types can be created"""
        non_refundable_types = [
            'out_of_stock',
            'lost_to_bots',
            'item_not_found',
            'sold_out',
            'coming_soon',
            'payment_already_exists',
        ]
        
        for error_type in non_refundable_types:
            execution = ProcurementExecution.objects.create(
                procurement_request=self.proc_request,
                status='failed',
                error_type=error_type,
                started_at=timezone.now(),
            )
            
            self.assertEqual(execution.error_type, error_type)
            
            # Clean up
            execution.delete()