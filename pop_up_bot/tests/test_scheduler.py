# pop_up_bot/tests/test_scheduler.py

import pytest
from django.test import TestCase
from django.utils import timezone as django_timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
from pop_up_bot.orchestrator import ExecutionResult, ExecutionStatus


from pop_up_bot.models import (
    ScheduledRelease,
    ProcurementServiceRequest,
    ProcurementRequest,
    ReleaseExecutionBatch,
    ProcurementExecution,
)
from pop_up_bot.tasks import (
    process_scheduled_releases,
    process_release,
    execute_procurement_request,
)
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory, PopUpProductType

from pop_up_auction.tests.conftest import (create_test_user)


from django.contrib.auth import get_user_model


User = get_user_model()


class TestSchedulerTasks(TestCase):
    """Test scheduler tasks"""
    
    def setUp(self):
        """Create test data"""
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
            product_title="Test Shoe",
            secondary_product_title="Tarheel",
            retail_price=Decimal("100.00"),
            is_active=True
        )
        
        # Release that's currently active (within window)
        self.active_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='TEST-001',
            release_date=django_timezone.now() - timedelta(minutes=10),
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
            status='scheduled',
            retail_price=Decimal("100.00")
        )
        
        # Release that's in the future
        self.future_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='TEST-002',
            release_date=django_timezone.now() + timedelta(days=1),
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
            status='scheduled',
        )
        
        self.user, self.user_profile = create_test_user(
            "test@test.com", "testpass!23", "Test", "User", "10", "male"
        )
    
    def test_process_scheduled_releases_no_active(self):
        """Test scheduler when no releases are active"""
        # Use only future release
        self.active_release.delete()
        
        result = process_scheduled_releases()
        
        assert result['status'] == 'ok'
        assert result['releases_processed'] == 0
        assert result['message'] == 'No active releases'
    
    def test_process_scheduled_releases_finds_active(self):
        """Test scheduler finds active releases"""
        # Create pending service request
        ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.active_release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=django_timezone.now(),
            status='pending',
        )
        
        with patch('pop_up_bot.tasks.process_release') as mock_process:
            mock_process.return_value = {
                'total_attempts': 1,
                'successful': 1,
                'failed': 0,
                'errors': [],
            }
            
            result = process_scheduled_releases()
        
        assert result['releases_processed'] == 1
        assert result['total_attempts'] == 1
    
    def test_process_release_creates_batch(self):
        """Test process_release creates ReleaseExecutionBatch"""
        # Create pending service request
        service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.active_release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=django_timezone.now(),
            status='pending',
        )
        
        with patch('pop_up_bot.tasks.execute_procurement_request.delay') as mock_task:
            mock_task.return_value = MagicMock(id='task-123')
            
            result = process_release(self.active_release)
        
        # Check batch was created
        batch = ReleaseExecutionBatch.objects.filter(
            scheduled_release=self.active_release
        ).first()
        
        assert batch is not None
        assert batch.total_attempts == 1
        assert batch.started_at is not None
    
    def test_process_release_creates_procurement_request(self):
        """Test process_release creates ProcurementRequest"""
        service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.active_release,
            size='US 10',
            color='Red',
            max_price=150.00,
            service_fee=15.00,
            fee_paid_at=django_timezone.now(),
            status='pending',
        )
        
        with patch('pop_up_bot.tasks.execute_procurement_request.delay'):
            process_release(self.active_release)
        
        # Check ProcurementRequest was created
        proc_request = ProcurementRequest.objects.filter(
            user=self.user
        ).first()
        
        assert proc_request is not None
        assert proc_request.product_name == self.product.product_title
        assert proc_request.target_size == 'US 10'
        assert proc_request.target_color == 'Red'
        assert proc_request.max_price == 150.00
        
        # Check it was linked to service request
        service_request.refresh_from_db()
        assert service_request.procurement_request == proc_request
        assert service_request.status == 'active'
    
    def test_process_release_no_pending_requests(self):
        """Test process_release with no pending requests"""
        result = process_release(self.active_release)
        
        assert result['total_attempts'] == 0
        assert result['successful'] == 0
        assert result['failed'] == 0
    
    def test_process_release_handles_error(self):
        """Test process_release handles errors gracefully"""
        # Create service request that will fail
        service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.active_release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=django_timezone.now(),
            status='pending',
        )
        
        with patch.object(
            service_request.__class__,
            'create_procurement_request',
            side_effect=Exception("DB Error")
        ):
            result = process_release(self.active_release)
        
        assert len(result['errors']) > 0
        assert result['failed'] > 0


class TestExecuteProcurementRequest(TestCase):
    """Test execute_procurement_request task"""
    
    def setUp(self):
        """Create test data"""
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
            product_title="Test Shoe",
            secondary_product_title="Tarheel",
            retail_price=Decimal("100.00"),
            is_active=True
        )

        
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='TEST-001',
            release_date=django_timezone.now(),
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
        )
        
        self.user, self.user_profile = create_test_user(
            "test@test.com", "testpass!23", "Test", "User", "10", "male"
        )

        self.proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Test Shoe',
            target_size='US 10',
            max_price=150.00,
            procurement_type='inventory',
        )
        
        self.service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=django_timezone.now(),
            status='active',
            procurement_request=self.proc_request,
        )
        
        self.batch = ReleaseExecutionBatch.objects.create(
            scheduled_release=self.release,
            total_attempts=1,
            started_at=django_timezone.now(),
        )
    
    @patch('pop_up_bot.tasks.asyncio.run')
    @patch('pop_up_bot.tasks.PlaywrightScraperEngine')
    @patch('pop_up_bot.tasks.SessionManager')
    @patch('pop_up_bot.tasks.ProcurementLock')
    @patch('pop_up_bot.tasks.StrategyFactory')
    @patch('pop_up_bot.tasks.BotOrchestrator')
    def test_execute_procurement_success(
        self, 
        mock_orchestrator_class,
        mock_strateggy_class,
        mock_lock_class,
        mock_session_class, 
        mock_scraper_class,
        mock_asyncio
        ):

        """Test successful execution"""
        # Mock successful execution
        # execution = ProcurementExecution.objects.create(
        #     procurement_request=self.proc_request,
        #     status='success',
        #     strategy_used='fastest',
        #     winning_site='nike',
        #     order_id='ORD-123',
        #     item_price=100.00,
        #     started_at=django_timezone.now(),
        #     completed_at=django_timezone.now(),
        # )
        
        # Mock the orchestrator
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator_instance
        
        # Mock the async run to return success
        mock_asyncio.return_value = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            product_name='Test Shoe',
            site='nike',
            order_id='ORD-MOCK-456',
            item_price=100.00,
            error_type='success',
            duration_seconds=5.0,
        )
        # mock_asyncio.return_value = {
        #     'status': 'success',
        #     'execution': execution,
        # }
        
        with patch('pop_up_bot.tasks.send_success_notification'):
            result = execute_procurement_request(
                str(self.proc_request.id),
                str(self.service_request.id),
                str(self.batch.id),
            )
        

        self.service_request.refresh_from_db()
        assert self.service_request.status == 'success'
        assert self.service_request.procurement_execution is not None
        assert self.service_request.procurement_execution.order_id == 'ORD-MOCK-456'
        assert self.service_request.procurement_execution.winning_site == 'nike'
        assert self.service_request.procurement_execution.status == 'success'
        
        # assert result['status'] == 'success'
        # assert result['order_id'] == 'ORD-MOCK-456'
        
        # # Check service request updated
        # self.service_request.refresh_from_db()
        # assert self.service_request.status == 'success'
        # assert self.service_request.procurement_execution == execution

        
        # # Check procurement request updated
        # self.proc_request.refresh_from_db()
        # assert self.proc_request.status == 'fulfilled'
        # assert self.proc_request.fulfilled_at is not None
        
        # # Check batch updated
        # self.batch.refresh_from_db()
        # assert self.batch.successful_count == 1
        # assert self.batch.completed_at is not None



    @patch('pop_up_bot.tasks.asyncio.run')
    @patch('pop_up_bot.tasks.PlaywrightScraperEngine')
    @patch('pop_up_bot.tasks.SessionManager')
    @patch('pop_up_bot.tasks.ProcurementLock')
    @patch('pop_up_bot.tasks.StrategyFactory')
    @patch('pop_up_bot.tasks.BotOrchestrator')
    def test_execute_procurement_failure(
        self,
        mock_orchestrator_class,
        mock_strateggy_class,
        mock_lock_class,
        mock_session_class,
        mock_scraper_class,
        mock_asyncio
    ):
        """Test failed execution"""
        # Mock the orchestrator
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_class.return_value = mock_orchestrator_instance
        
        # mock_asyncio.return_value = {
        #     'status': 'failed',
        #     'execution': None,
        #     'error': 'Out of stock',
        # }

        mock_asyncio.return_value = ExecutionResult(
            status=ExecutionStatus.FAILED,
            product_name='Test Shoe',
            site='nike',
            order_id=None,
            item_price=None,
            error='Out of stock',
            error_type='out_of_stock',
            duration_seconds=3.0,
        )
        
        with patch('pop_up_bot.tasks.send_failure_notification'):
            result = execute_procurement_request(
                str(self.proc_request.id),
                str(self.service_request.id),
                str(self.batch.id),
            )
        
        assert result['status'] == 'failed'
        assert result['order_id'] is None
        
        # Check service request updated
        self.service_request.refresh_from_db()
        assert self.service_request.status == 'failed'
        
        # Check procurement request updated
        self.proc_request.refresh_from_db()
        assert self.proc_request.status == 'cancelled'
        
        # Check batch updated
        self.batch.refresh_from_db()
        assert self.batch.failed_count == 1


class TestSchedulerIntegration(TestCase):
    """Integration tests for full scheduler flow"""
    
    def setUp(self):
        """Create test data"""

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
            product_title="Test Shoe",
            secondary_product_title="Tarheel",
            retail_price=Decimal("170.00"),
            is_active=True
        )

        
        # Create multiple users with service requests
        self.users = []
        self.service_requests = []
        
        for i in range(3):
            user, user_profile = create_test_user(f"test-{i}@test.com", "testpass!23", "Test{i}", "User{i}", "10", "male"
                )
            
            self.users.append(user)
        
        # Release that's active
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='DJ0646-610',
            release_date=django_timezone.now() - timedelta(minutes=5),
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com/t/air-jordan-1',
            status='scheduled',
            retail_price=170.00,
        )
        
        # Create service requests for all users
        for user in self.users:
            sr = ProcurementServiceRequest.objects.create(
                user=user,
                scheduled_release=self.release,
                size='US 10',
                service_fee=15.00,
                fee_paid_at=django_timezone.now(),
                status='pending',
            )
            self.service_requests.append(sr)
    
    @patch('pop_up_bot.tasks.execute_procurement_request.delay')
    def test_full_release_processing(self, mock_task):
        """Test full flow from release to batch creation"""
        mock_task.return_value = MagicMock(id='task-123')
        
        # Run scheduler
        result = process_scheduled_releases()
        
        # Should find 1 release
        assert result['releases_processed'] == 1
        
        # Should create batch
        batch = ReleaseExecutionBatch.objects.filter(
            scheduled_release=self.release
        ).first()
        
        assert batch is not None
        assert batch.total_attempts == 3  # 3 users
        
        # Should create 3 ProcurementRequests
        proc_requests = ProcurementRequest.objects.filter(
            target_size='US 10'
        )
        
        assert proc_requests.count() == 3
        
        # All service requests should be linked
        for sr in self.service_requests:
            sr.refresh_from_db()
            assert sr.procurement_request is not None
            assert sr.status == 'active'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])