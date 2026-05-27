# pop_up_bot/tests/test_models.py

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid

from pop_up_bot.models import (
    CookieModel,
    ProcurementRequest,
    ProcurementExecution,
    ExternalProductReference,
    InventoryLock,
    ProcurementEvent,
    BotLog,
    SiteAttempt,
)

from pop_up_auction.models import (
    PopUpProductType,
    PopUpCategory,
    PopUpBrand,)
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_address)


from django.contrib.auth import get_user_model

User = get_user_model()


class TestCookieModel(TestCase):
    """Test CookieModel"""
    
    def setUp(self):
        """Create a test cookie"""
        self.cookie = CookieModel.objects.create(
            site_name='nike',
            name='session_id',
            value='abc123xyz',
            domain='.nike.com',
            path='/',
            http_only=True,
            secure=True,
            same_site='Strict',
        )
    
    def test_cookie_creation(self):
        """Test creating a cookie"""
        assert self.cookie.site_name == 'nike'
        assert self.cookie.name == 'session_id'
        assert self.cookie.value == 'abc123xyz'
    
    def test_cookie_str(self):
        """Test cookie string representation"""
        assert 'nike' in str(self.cookie)
        assert 'session_id' in str(self.cookie)
    
    def test_is_expired_false(self):
        """Test cookie that's not expired"""
        assert self.cookie.is_expired is False
    
    def test_is_expired_true(self):
        """Test cookie that's expired"""
        self.cookie.expires = timezone.now() - timedelta(hours=1)
        self.cookie.save()
        assert self.cookie.is_expired is True
    
    def test_to_playwright_dict(self):
        """Test conversion to Playwright format"""
        cookie_dict = self.cookie.to_playwright_dict()
        
        assert cookie_dict['name'] == 'session_id'
        assert cookie_dict['value'] == 'abc123xyz'
        assert cookie_dict['domain'] == '.nike.com'
        assert cookie_dict['httpOnly'] is True
        assert cookie_dict['secure'] is True
    
    def test_unique_constraint(self):
        """Test unique constraint on site_name, domain, name"""
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            CookieModel.objects.create(
                site_name='nike',
                name='session_id',
                value='different_value',
                domain='.nike.com',
                path='/',
            )


class TestProcurementRequest(TestCase):
    """Test ProcurementRequest model"""
    
    def setUp(self):
        """Create test user and request"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create admin user
        self.admin_user, self.admin_profile = create_test_user(
            "admin@example.com", "adminpass!23", "Admin", "User", "10", "male"
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()

        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Air Jordan 1',
            target_size='US 10',
            target_color='Red',
            max_price=200.00,
            procurement_type='inventory',
            status='pending',
        )
    
    def test_procurement_request_creation(self):
        """Test creating a procurement request"""
        assert self.request.product_name == 'Air Jordan 1'
        assert self.request.target_size == 'US 10'
        assert self.request.max_price == 200.00
    
    def test_procurement_request_str(self):
        """Test string representation"""
        assert 'Air Jordan 1' in str(self.request)
        assert 'pending' in str(self.request)
    
    def test_is_expired_false(self):
        """Test request that's not expired"""
        assert self.request.is_expired is False
    
    def test_is_expired_true(self):
        """Test request that's expired"""
        self.request.expires_at = timezone.now() - timedelta(hours=1)
        self.request.save()
        assert self.request.is_expired is True
    
    def test_execution_count(self):
        """Test counting executions"""
        assert self.request.execution_count == 0
        
        ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='pending',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        
        assert self.request.execution_count == 1
    
    def test_execution_success_count(self):
        """Test counting successful executions"""
        ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='success',
            strategy_used='sequential',
            order_id='ORD-123',
            started_at=timezone.now(),
        )
        
        ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='failed',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        
        assert self.request.execution_success_count == 1


class TestProcurementExecution(TestCase):
    """Test ProcurementExecution model"""
    
    def setUp(self):
        """Create test request and execution"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "testuser", "User", "9", "male"
        )
        
        # Create admin user
        self.admin_user, self.admin_profile = create_test_user(
            "admin@example.com", "adminpass!23", "Admin", "User", "10", "male"
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()

        
        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Nike SB Dunk Low',
            target_size='US 10',
            max_price=150.00,
        )
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='success',
            strategy_used='sequential',
            winning_site='nike',
            order_id='ORD-12345',
            item_price=119.99,
            started_at=timezone.now(),
            completed_at=timezone.now() + timedelta(minutes=5),
        )
    
    def test_execution_creation(self):
        """Test creating an execution"""
        assert self.execution.status == 'success'
        assert self.execution.winning_site == 'nike'
        assert self.execution.order_id == 'ORD-12345'
    
    def test_execution_str(self):
        """Test string representation"""
        assert 'Nike SB Dunk Low' in str(self.execution)
        assert 'success' in str(self.execution)
    
    def test_duration_seconds(self):
        """Test duration calculation"""
        duration = self.execution.duration_seconds
        assert duration is not None
        assert duration > 0
    
    def test_was_successful_true(self):
        """Test successful execution check"""
        assert self.execution.was_successful is True
    
    def test_was_successful_false(self):
        """Test unsuccessful execution check"""
        execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='failed',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        assert execution.was_successful is False
    
    def test_is_running(self):
        """Test running status check"""
        running_execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='running',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        assert running_execution.is_running is True
        assert self.execution.is_running is False


class TestExternalProductReference(TestCase):
    """Test ExternalProductReference model"""

    def setUp(self):
        """Create a test product"""
        from pop_up_auction.models import PopUpProduct
        from decimal import Decimal

        # Create a minimal PopUpProduct for testing
        self.product_type = PopUpProductType.objects.create(
            name="Sneakers",
            slug="sneakers"
        )
        self.category = PopUpCategory.objects.create(
            name="Jordan 3",
            slug="jordan-3"
        )
        self.brand = PopUpBrand.objects.create(
            name="Jordan",
            slug="jordan"
        )

        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Jordan 3 Retro",
            retail_price=Decimal("150.00"),
            is_active=True
        )


    def test_external_reference_creation(self):
        """Test creating an external product reference"""
        # Note: This requires a PopUpProduct, which we mock
        reference = ExternalProductReference.objects.create(
            product=self.product,
            site_name='nike',
            external_sku='DA1971-104',
            external_url='https://nike.com/product/DA1971-104',
        )
        
        assert reference.site_name == 'nike'
        assert reference.external_sku == 'DA1971-104'
        assert reference.product == self.product
    
    def test_external_reference_str(self):
        """Test string representation"""
        reference = ExternalProductReference.objects.create(
            product=self.product,
            site_name='footlocker',
            external_sku='FL-12345',
            external_url='https://footlocker.com/product/12345',
        )
        
        assert 'footlocker' in str(reference)
        assert 'FL-12345' in str(reference)


class TestInventoryLock(TestCase):
    """Test InventoryLock model"""
    
    def setUp(self):
        """Create test execution and lock"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        

        # self.user = User.objects.create_user(username='testuser')
        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Test Product',
            target_size='US 10',
            max_price=200.00,
        )

        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='running',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        self.lock = InventoryLock.objects.create(
            product_identifier='DA1971-104',
            size='US 10',
            execution=self.execution,
            site_name='nike',
            status='acquired',
            locked_until=timezone.now() + timedelta(minutes=10),
        )
    
    def test_lock_creation(self):
        """Test creating a lock"""
        assert self.lock.product_identifier == 'DA1971-104'
        assert self.lock.size == 'US 10'
        assert self.lock.status == 'acquired'
    
    def test_lock_str(self):
        """Test string representation"""
        assert 'DA1971-104' in str(self.lock)
        assert 'acquired' in str(self.lock)
    
    def test_is_active(self):
        """Test active lock check"""
        assert self.lock.is_active is True
    
    def test_is_expired_false(self):
        """Test expired lock check (not expired)"""
        assert self.lock.is_expired is False
    
    def test_is_expired_true(self):
        """Test expired lock check (expired)"""
        self.lock.locked_until = timezone.now() - timedelta(minutes=1)
        self.lock.save()
        assert self.lock.is_expired is True
    
    def test_release_lock(self):
        """Test releasing a lock"""
        self.lock.release()
        
        assert self.lock.status == 'released'
        assert self.lock.released_at is not None
    
    def test_mark_failed(self):
        """Test marking lock as failed"""
        self.lock.mark_failed()
        
        assert self.lock.status == 'failed'
        assert self.lock.released_at is not None
    
    def test_mark_expired(self):
        """Test marking lock as expired"""
        self.lock.mark_expired()
        
        assert self.lock.status == 'expired'
        assert self.lock.released_at is not None
    
    def test_try_acquire_lock_success(self):
        """Test successfully acquiring a lock"""
        lock, acquired = InventoryLock.try_acquire_lock(
            product_identifier='NEW-SKU-123',
            size='US 11',
            site_name='footlocker',
            execution=self.execution,
            ttl_seconds=60,
        )
        
        assert acquired is True
        assert lock is not None
        assert lock.status == 'acquired'
    
    def test_try_acquire_lock_failure(self):
        """Test failing to acquire a lock (already locked)"""
        # First lock succeeds
        lock1, acquired1 = InventoryLock.try_acquire_lock(
            product_identifier='SAME-SKU',
            size='US 10',
            site_name='nike',
            execution=self.execution,
            ttl_seconds=60,
        )
        assert acquired1 is True
        
        # Second lock on same product+size fails
        lock2, acquired2 = InventoryLock.try_acquire_lock(
            product_identifier='SAME-SKU',
            size='US 10',
            site_name='footlocker',
            execution=self.execution,
            ttl_seconds=60,
        )
        assert acquired2 is False
        assert lock2 is None


class TestProcurementEvent(TestCase):
    """Test ProcurementEvent model"""
    
    def setUp(self):
        """Create test execution and event"""

        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Test Product',
            target_size='US 10',
            max_price=200.00,
        )
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='running',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        self.event = ProcurementEvent.objects.create(
            bot_execution=self.execution,
            event_type='INITIALIZED',
            site_name='nike',
            metadata={'product_name': 'Test Product'},
        )
    
    def test_event_creation(self):
        """Test creating an event"""
        assert self.event.event_type == 'INITIALIZED'
        assert self.event.site_name == 'nike'
        assert self.event.metadata['product_name'] == 'Test Product'
    
    def test_event_str(self):
        """Test string representation"""
        assert 'INITIALIZED' in str(self.event)
    
    def test_event_ordering(self):
        """Test events are ordered by timestamp"""
        event2 = ProcurementEvent.objects.create(
            bot_execution=self.execution,
            event_type='STRATEGY_SELECTED',
            metadata={},
        )
        
        events = ProcurementEvent.objects.all()
        assert events[0].event_type == 'INITIALIZED'
        assert events[1].event_type == 'STRATEGY_SELECTED'


class TestBotLog(TestCase):
    """Test BotLog model"""
    
    def setUp(self):
        """Create test execution and log"""        
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Test Product',
            target_size='US 10',
            max_price=200.00,
        )
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='running',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        self.log = BotLog.objects.create(
            bot_execution=self.execution,
            level='info',
            message='Bot started procurement',
            context={'site': 'nike'},
        )
    
    def test_log_creation(self):
        """Test creating a log entry"""
        assert self.log.level == 'info'
        assert self.log.message == 'Bot started procurement'
        assert self.log.context['site'] == 'nike'
    
    def test_log_str(self):
        """Test string representation"""
        assert 'INFO' in str(self.log)
        assert 'Bot started' in str(self.log)
    
    def test_log_ordering(self):
        """Test logs are ordered by timestamp (newest first)"""
        log2 = BotLog.objects.create(
            bot_execution=self.execution,
            level='error',
            message='Bot failed',
            context={},
        )
        
        logs = BotLog.objects.all()
        assert logs[0].level == 'error'
        assert logs[1].level == 'info'


class TestSiteAttempt(TestCase):
    """Test SiteAttempt model"""
    
    def setUp(self):
        """Create test execution and site attempt"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Nike Air Max',
            target_size='US 10',
            max_price=200.00,
        )
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='running',
            strategy_used='sequential',
            started_at=timezone.now(),
        )
        self.attempt = SiteAttempt.objects.create(
            execution=self.execution,
            site_name='nike',
            status='success',
            external_sku='DA1971-104',
            product_url='https://nike.com/product/DA1971-104',
            started_at=timezone.now(),
            completed_at=timezone.now() + timedelta(minutes=3),
        )
    
    def test_site_attempt_creation(self):
        """Test creating a site attempt"""
        assert self.attempt.site_name == 'nike'
        assert self.attempt.status == 'success'
        assert self.attempt.external_sku == 'DA1971-104'
    
    def test_site_attempt_str(self):
        """Test string representation"""
        assert 'nike' in str(self.attempt)
        assert 'success' in str(self.attempt)
    
    def test_duration_seconds(self):
        """Test duration calculation"""
        duration = self.attempt.duration_seconds
        assert duration is not None
        assert duration > 0
    
    def test_was_successful(self):
        """Test success check"""
        assert self.attempt.was_successful is True
        
        failed_attempt = SiteAttempt.objects.create(
            execution=self.execution,
            site_name='footlocker',
            status='failed',
            failure_reason='oos',
            started_at=timezone.now(),
        )
        assert failed_attempt.was_successful is False


class TestModelRelationships(TestCase):
    """Test relationships between models"""
    
    def setUp(self):
        """Create test data"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        self.request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Test Shoe',
            target_size='US 10',
            max_price=200.00,
        )
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.request,
            status='success',
            strategy_used='sequential',
            order_id='ORD-123',
            started_at=timezone.now(),
        )
    
    def test_procurement_request_executions(self):
        """Test accessing executions from request"""
        executions = self.request.executions.all()
        assert executions.count() == 1
        assert executions[0] == self.execution
    
    def test_execution_events(self):
        """Test creating and accessing events"""
        ProcurementEvent.objects.create(
            bot_execution=self.execution,
            event_type='INITIALIZED',
            metadata={},
        )
        ProcurementEvent.objects.create(
            bot_execution=self.execution,
            event_type='ORDER_CONFIRMED',
            metadata={'order_id': 'ORD-123'},
        )
        
        events = self.execution.events.all()
        assert events.count() == 2
    
    def test_execution_logs(self):
        """Test creating and accessing logs"""
        BotLog.objects.create(
            bot_execution=self.execution,
            level='info',
            message='Log message 1',
            context={},
        )
        
        logs = self.execution.logs.all()
        assert logs.count() == 1
    
    def test_execution_site_attempts(self):
        """Test creating and accessing site attempts"""
        SiteAttempt.objects.create(
            execution=self.execution,
            site_name='nike',
            status='success',
            started_at=timezone.now(),
        )
        SiteAttempt.objects.create(
            execution=self.execution,
            site_name='footlocker',
            status='skipped',
            started_at=timezone.now(),
        )
        
        attempts = self.execution.site_attempts.all()
        assert attempts.count() == 2
    
    def test_execution_inventory_locks(self):
        """Test creating and accessing inventory locks"""
        InventoryLock.objects.create(
            execution=self.execution,
            product_identifier='DA1971-104',
            size='US 10',
            site_name='nike',
            status='released',
            locked_until=timezone.now(),
        )
        
        locks = self.execution.inventory_locks.all()
        assert locks.count() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])