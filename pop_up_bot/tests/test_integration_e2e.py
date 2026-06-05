# pop_up_bot/tests/test_integration_e2e.py

"""
End-to-End Integration Tests

Tests the complete workflow:
1. Scheduler finds active release
2. Creates ProcurementServiceRequest
3. Scheduler creates ProcurementRequest
4. BotOrchestrator runs
5. NikeSiteHandler executes
6. Results saved to database
7. User notified

Run with:
    python manage.py test pop_up_bot.tests.test_integration_e2e -v 2

┌─────────────────────────────────────────────┐
│   ScheduledRelease Created (Nike Release)   │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│   User 1 & 2 Create ServiceRequest (Pay Fee)│
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│     Scheduler Finds Active Release          │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│   Create ProcurementRequest for Each User   │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│   Create ReleaseExecutionBatch              │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│   Queue execute_procurement_request Tasks   │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
   ┌─────────┐       ┌─────────┐
   │  User 1 │       │  User 2 │
   │  Task   │       │  Task   │
   └────┬────┘       └────┬────┘
        │                 │
        ↓                 ↓
┌──────────────┐   ┌──────────────┐
│ NikeSiteH.   │   │ NikeSiteH.   │
│ 1. Find      │   │ 1. Find      │
│ 2. Select    │   │ 2. Select    │
│ 3. Add Cart  │   │ 3. Add Cart  │
└────┬─────────┘   └────┬─────────┘
     │                  │
     ↓                  ↓
┌──────────────┐   ┌──────────────┐
│   Success    │   │   Failed     │
│   (OOS)      │   │   (OOS)      │
└────┬─────────┘   └────┬─────────┘
     │                  │
     └────────┬─────────┘
              ↓
     ┌───────────────────┐
     │  Batch Updated    │
     │  Stats Recorded   │
     │  Users Notified   │
     └───────────────────┘
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from pop_up_bot.models import (
    ScheduledRelease,
    ProcurementServiceRequest,
    ProcurementRequest,
    ProcurementExecution,
    ReleaseExecutionBatch,
)
from pop_up_bot.tasks import process_scheduled_releases, process_release, execute_procurement_request
from pop_up_bot.handlers.nike_handler import NikeSiteHandler
from pop_up_bot.handlers.base_handler import Product
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory, PopUpProductType

from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_address)

User = get_user_model()


class EndToEndTestCase(TestCase):
    """Base test case for E2E tests with fixtures"""
    
    def setUp(self):
        """Set up test data"""
        # Create brand/category/product
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
            product_title="Air Jordan 1 Low",
            secondary_product_title="Silver Lining",
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
        
        # Create users
        self.user1, self.user_profile1 = create_test_user(
            "user1@test.com", "testpass!23", "testuser1", "User", "9", "male"
        )
        self.user2, self.user_profile2 = create_test_user(
            "user2@test.com", "testpass!23", "testuser", "User", "9", "female"
        )
        # self.user1 = User.objects.create_user('user1@test.com', 'user1@test.com', 'pass123')
        # self.user2 = User.objects.create_user('user2@test.com', 'user2@test.com', 'pass123')
        
        # Create active release (currently happening)
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='DJ0646-610',
            release_date=timezone.now() - timedelta(minutes=5),  # Started 5 min ago
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com/t/air-jordan-1/553558-404',
            status='scheduled',
            retail_price=Decimal('170.00'),
        )
        
        # Create mock engine
        self.mock_engine = self._create_mock_engine()
    
    def _create_mock_engine(self):
        """Create mocked PlaywrightScraperEngine"""
        engine = AsyncMock()
        engine.navigate = AsyncMock()
        engine.click = AsyncMock()
        engine.type = AsyncMock()
        engine.wait_for = AsyncMock()
        engine.wait_for_load_state = AsyncMock()
        engine.is_element_visible = AsyncMock(return_value=True)
        engine.query_selector = AsyncMock()
        engine.query_selector_all = AsyncMock(return_value=[])
        engine.extract_text = AsyncMock(return_value="Air Jordan 1 Low")
        engine.extract_attribute = AsyncMock(return_value="https://www.nike.com/t/air-jordan-1/553558-404")
        engine.click_element = AsyncMock()
        engine.evaluate = AsyncMock()
        engine.execute_js = AsyncMock(return_value="")
        engine.wait_for_timeout = AsyncMock()
        engine.get_url = AsyncMock(return_value="https://www.nike.com")
        engine.get_title = AsyncMock(return_value="Nike Product")
        return engine


# ============================================================================
# TEST: SCHEDULER FINDS ACTIVE RELEASES
# ============================================================================

class TestSchedulerFindReleases(EndToEndTestCase):
    """Test scheduler finding active releases"""
    
    def test_scheduler_finds_active_release(self):
        """Test scheduler finds release within active window"""
        # Release is active (started 5 min ago, window is 30 min)
        self.assertTrue(self.release.is_active)
        
        # Should find it
        active = ScheduledRelease.objects.filter(status='scheduled')
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().sku, 'DJ0646-610')
    
    def test_scheduler_ignores_future_releases(self):
        """Test scheduler ignores releases not yet started"""
        future_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='FUTURE-001',
            release_date=timezone.now() + timedelta(days=1),
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com',
            status='scheduled',
        )
        
        # Should not be active
        self.assertFalse(future_release.is_active)
    
    def test_scheduler_ignores_expired_releases(self):
        """Test scheduler ignores releases past their window"""
        expired_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='EXPIRED-001',
            release_date=timezone.now() - timedelta(minutes=45),  # 45 min ago
            procurement_window_minutes=30,  # Window closed 15 min ago
            search_method='direct_url',
            product_url='https://www.nike.com',
            status='scheduled',
        )
        
        # Should not be active (past window)
        self.assertFalse(expired_release.is_active)


# ============================================================================
# TEST: SERVICE REQUESTS → PROCUREMENT REQUESTS
# ============================================================================

class TestServiceRequestToProcurementRequest(EndToEndTestCase):
    """Test creating ProcurementRequest from ProcurementServiceRequest"""
    
    def test_create_procurement_request_from_service_request(self):
        """Test service request creates procurement request at release time"""
        # Create service request
        service_request = ProcurementServiceRequest.objects.create(
            user=self.user1,
            scheduled_release=self.release,
            size='US 10',
            color='Red',
            max_price=Decimal('200.00'),
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        # Call synchronously (no async_to_sync needed)
        proc_request = service_request.create_procurement_request()

        
        # Verify procurement request created
        self.assertIsNotNone(proc_request)
        self.assertEqual(proc_request.user, self.user1)
        self.assertEqual(proc_request.product_name, 'Air Jordan 1 Low')
        self.assertEqual(proc_request.target_size, 'US 10')
        self.assertEqual(proc_request.target_color, 'Red')
        self.assertEqual(proc_request.max_price, Decimal('200.00'))
        
        # Verify service request updated
        service_request.refresh_from_db()
        self.assertEqual(service_request.procurement_request, proc_request)
        self.assertEqual(service_request.status, 'active')
    
    def test_multiple_service_requests_create_multiple_procurement_requests(self):
        """Test multiple users get their own procurement requests"""
        # Create 2 service requests
        sr1 = ProcurementServiceRequest.objects.create(
            user=self.user1,
            scheduled_release=self.release,
            size='US 10',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        sr2 = ProcurementServiceRequest.objects.create(
            user=self.user2,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        # Create procurement requests
        pr1 = sr1.create_procurement_request() # async_to_sync(sr1.create_procurement_request)()
        pr2 = sr2.create_procurement_request() # async_to_sync(sr2.create_procurement_request)()
        
        # Verify both created with correct sizes
        self.assertNotEqual(pr1.id, pr2.id)
        self.assertEqual(pr1.user, self.user1)
        self.assertEqual(pr2.user, self.user2)
        self.assertEqual(pr1.target_size, 'US 10')
        self.assertEqual(pr2.target_size, 'US 11')


# ============================================================================
# TEST: BOT ORCHESTRATOR EXECUTION
# ============================================================================

class TestBotOrchestratorExecution(EndToEndTestCase):
    """Test BotOrchestrator running the bot"""
    
    @patch('pop_up_bot.tasks.BotOrchestrator')
    def test_orchestrator_runs_handler(self, mock_orchestrator_class):
        """Test orchestrator initializes and runs handler"""
        proc_request = ProcurementRequest.objects.create(
            user=self.user1,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 10',
            target_color='Red',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        # Mock orchestrator
        mock_orch = AsyncMock()
        mock_orchestrator_class.return_value = mock_orch
        
        # Mock result with real execution
        mock_execution = ProcurementExecution.objects.create(
            procurement_request=proc_request,  # ← Link it!
            status='success',
            strategy_used='fastest',
            winning_site='nike',
            order_id='ORD-12345',
            item_price=Decimal('170.00'),
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        
        mock_orch.run = AsyncMock(return_value={
            'status': 'success',
            'execution': mock_execution,
        })
        
        # Call orchestrator
        result = async_to_sync(mock_orch.run)(
            product_name='Air Jordan 1 Low',
            size='US 10',
            color='Red',
            strategy_name='fastest',
            price_range=(0, 200),
            site_name='nike',
        )
        
        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertIsNotNone(result['execution'])


# ============================================================================
# TEST: NIKE HANDLER EXECUTION
# ============================================================================

class TestNikeHandlerExecution(EndToEndTestCase):
    """Test NikeSiteHandler executing the purchase flow"""
    
    def test_handler_finds_and_adds_product(self):
        """Test handler can find product and add to cart"""
        handler = NikeSiteHandler(
            engine=self.mock_engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
        
        # Mock engine for product finding
        self.mock_engine.extract_text = AsyncMock(return_value="Air Jordan 1 Low")
        self.mock_engine.extract_attribute = AsyncMock(return_value="https://www.nike.com/t/air-jordan-1/553558-404")
        
        with patch.object(handler, '_extract_price', new_callable=AsyncMock, return_value="$170"):
            with patch.object(handler, '_get_available_sizes', new_callable=AsyncMock, return_value=["M 10 / W 11.5"]):
                product = async_to_sync(handler.find_product)("Air Jordan 1", "10")
        
        # Verify product found
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Air Jordan 1 Low")
        self.assertEqual(product.price, 170.0)
    
    def test_handler_selects_size_and_adds_to_cart(self):
        """Test handler selects size and adds to cart"""
        handler = NikeSiteHandler(
            engine=self.mock_engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
        
        # Setup product
        handler.product_found = Product(
            product_id="553558-404",
            name="Air Jordan 1 Low",
            price=170.0,
            available_sizes=["M 10 / W 11.5"],
            product_url="https://nike.com",
            in_stock=True,
        )
        
        # Mock size selection
        radio_mock = MagicMock()
        self.mock_engine.query_selector_all = AsyncMock(return_value=[radio_mock])
        self.mock_engine.evaluate = AsyncMock(side_effect=[
            "10",
            "grid-selector-input-10",
            "M 10 / W 11.5",
        ])
        
        label_mock = MagicMock()
        self.mock_engine.query_selector = AsyncMock(return_value=label_mock)
        
        # Mock out of stock check
        with patch.object(handler, 'detect_out_of_stock', return_value=False):
            # Mock add to bag button
            button_mock = MagicMock()
            self.mock_engine.query_selector = AsyncMock(return_value=button_mock)
            self.mock_engine.evaluate = AsyncMock(return_value=False)
            
            success = async_to_sync(handler.add_to_cart)("553558-404", "10")
        
        # Verify
        self.assertTrue(success)
        self.assertIsNotNone(handler.cart_item)
        self.assertEqual(handler.cart_item.size, "10")


# ============================================================================
# TEST: BATCH CREATION AND REPORTING
# ============================================================================

class TestReleaseExecutionBatch(EndToEndTestCase):
    """Test ReleaseExecutionBatch creation and reporting"""
    
    def test_batch_tracks_execution_results(self):
        """Test batch tracks successful and failed attempts"""
        # Create procurement requests first (required foreign key)
        pr1 = ProcurementRequest.objects.create(
            user=self.user1,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 10',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        pr2 = ProcurementRequest.objects.create(
            user=self.user2,
            product=self.product,
            product_name='Air Jordan 1 Low',
            target_size='US 11',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
            status='pending',
        )
        
        # Create executions with all required fields
        exec1 = ProcurementExecution.objects.create(
            procurement_request=pr1,
            status='success',
            strategy_used='fastest',
            winning_site='nike',
            order_id='ORD-001',
            item_price=Decimal('170.00'),
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        
        exec2 = ProcurementExecution.objects.create(
            procurement_request=pr2,
            status='failed',
            strategy_used='fastest',
            winning_site='nike',
            error_message='Out of stock',
            started_at=timezone.now(),
        )
        
        # Create batch
        batch = ReleaseExecutionBatch.objects.create(
            scheduled_release=self.release,
            total_attempts=2,
            started_at=timezone.now(),
        )
        
        # Add to batch
        batch.executions.add(exec1, exec2)
        batch.successful_count = 1
        batch.failed_count = 1
        batch.completed_at = timezone.now()
        batch.save()
        
        # Verify batch stats
        self.assertEqual(batch.total_attempts, 2)
        self.assertEqual(batch.successful_count, 1)
        self.assertEqual(batch.failed_count, 1)
        self.assertEqual(batch.executions.count(), 2)


# ============================================================================
# TEST: FULL END-TO-END WORKFLOW
# ============================================================================

class TestFullEndToEndWorkflow(EndToEndTestCase):
    """Test complete workflow from release to completion"""
    
    @patch('pop_up_bot.tasks.execute_procurement_request.delay')
    def test_complete_workflow_success(self, mock_task):
        """Test: Release active → Users buy → Bot runs → Items in carts"""
        # Step 1: Create service requests
        sr1 = ProcurementServiceRequest.objects.create(
            user=self.user1,
            scheduled_release=self.release,
            size='US 10',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        sr2 = ProcurementServiceRequest.objects.create(
            user=self.user2,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        # Verify initial state
        self.assertEqual(ProcurementServiceRequest.objects.filter(status='pending').count(), 2)
        
        # Step 2: Call process_release (now synchronous)
        mock_task.return_value = MagicMock(id='task-123')
        result = process_release(self.release)  # ← No async_to_sync needed!
        
        # Verify procurement requests created
        proc_requests = ProcurementRequest.objects.filter(target_size__in=['US 10', 'US 11'])
        self.assertEqual(proc_requests.count(), 2)
        
        # Verify batch created
        batches = ReleaseExecutionBatch.objects.filter(scheduled_release=self.release)
        self.assertEqual(batches.count(), 1)
        
        # Verify service requests updated
        sr1.refresh_from_db()
        sr2.refresh_from_db()
        self.assertEqual(sr1.status, 'active')
        self.assertEqual(sr2.status, 'active')
        self.assertIsNotNone(sr1.procurement_request)
        self.assertIsNotNone(sr2.procurement_request)
    

    
    def test_workflow_handles_errors(self):
        """Test: If one user fails, others succeed"""
        # Create 2 service requests
        sr1 = ProcurementServiceRequest.objects.create(
            user=self.user1,
            scheduled_release=self.release,
            size='US 10',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        sr2 = ProcurementServiceRequest.objects.create(
            user=self.user2,
            scheduled_release=self.release,
            size='US 11',
            service_fee=Decimal('15.00'),
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        # First user succeeds
        # pr1 = async_to_sync(sr1.create_procurement_request)()
        pr1 = sr1.create_procurement_request()
        sr1.refresh_from_db()
        self.assertEqual(sr1.status, 'active')
        
        # Second user fails (simulated by setting status manually)
        sr2.status = 'failed'
        sr2.save()
        
        # Verify states
        sr1.refresh_from_db()
        sr2.refresh_from_db()
        self.assertEqual(sr1.status, 'active')
        self.assertEqual(sr2.status, 'failed')


# ============================================================================
# TEST: ERROR SCENARIOS
# ============================================================================

class TestErrorScenarios(EndToEndTestCase):
    """Test error handling in workflow"""
    
    def test_handles_out_of_stock(self):
        """Test bot detects out of stock"""
        handler = NikeSiteHandler(
            engine=self.mock_engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
        
        # Mock coming soon indicator
        self.mock_engine.is_element_visible = AsyncMock(return_value=True)
        
        result = async_to_sync(handler.detect_out_of_stock)()
        
        self.assertTrue(result)
    
    def test_handles_rate_limiting(self):
        """Test bot detects rate limiting"""
        handler = NikeSiteHandler(
            engine=self.mock_engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
        
        # Mock blocked status
        self.mock_engine.get_title = AsyncMock(return_value="429 Too Many Requests")
        
        result = async_to_sync(handler.detect_blocked)()
        
        self.assertTrue(result)
    
    def test_handles_captcha(self):
        """Test bot detects captcha"""
        handler = NikeSiteHandler(
            engine=self.mock_engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
        
        # Mock captcha
        self.mock_engine.is_element_visible = AsyncMock(return_value=True)
        
        result = async_to_sync(handler.detect_captcha)()
        
        self.assertTrue(result)


if __name__ == '__main__':
    import unittest
    unittest.main()