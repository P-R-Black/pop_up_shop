# pop_up_bot/tests/test_models.py

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone as django_timezone
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
    ScheduledRelease,
    ProcurementServiceRequest,
    ReleaseExecutionBatch,
)


from pop_up_auction.models import (
    PopUpProductType,
    PopUpCategory,
    PopUpBrand,)


from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory

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



class TestScheduledRelease(TestCase):
    """Test ScheduledRelease model"""
    
    def setUp(self):
        """Create test data"""
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
            product_title="LeBron NXXT Gen By JuJu",
            secondary_product_title="Silver Lining",
            retail_price=Decimal("140.00"),
            is_active=True
        )

        
        self.release_date = timezone.now() + timedelta(days=7)
        
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='IQ8495-002',
            release_date=self.release_date,
            search_method='direct_url',
            product_url='https://www.nike.com/t/lebron-nxxt-gen-by-juju.../IQ8495-002',
            retail_price=140.00,
        )
    
    def test_scheduled_release_creation(self):
        """Test creating a scheduled release"""
        assert self.release.product == self.product
        assert self.release.sku == 'IQ8495-002'
        assert self.release.status == 'scheduled'

    def test_scheduled_release_str(self):
        """Test string representation"""
        str_repr = str(self.release)
        assert 'LeBron NXXT' in str_repr
        assert 'IQ8495-002' in str_repr
    
    def test_is_upcoming_true(self):
        """Test is_upcoming property when release is in future"""
        assert self.release.is_upcoming is True
    
    def test_is_upcoming_false(self):
        """Test is_upcoming property when release is in past"""
        past_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='IQ8495-003',
            release_date=timezone.now() - timedelta(days=1),
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
        )
        assert past_release.is_upcoming is False
    
    def test_is_active_false_before_release(self):
        """Test is_active when before release time"""
        assert self.release.is_active is False
    
    def test_is_active_true_at_release(self):
        """Test is_active when within procurement window"""
        # Create release that's happening now
        now_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='IQ8495-004',
            release_date=timezone.now() - timedelta(seconds=10),
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
        )
        assert now_release.is_active is True
    
    def test_is_active_false_after_window(self):
        """Test is_active when after procurement window"""
        expired_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='IQ8495-005',
            release_date=timezone.now() - timedelta(hours=1),
            procurement_window_minutes=30,
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
        )
        assert expired_release.is_active is False
    
    def test_minutes_until_release(self):
        """Test minutes_until_release calculation"""
        minutes = self.release.minutes_until_release
        assert minutes > 0
        assert minutes < (7 * 24 * 60) + 1  # Less than 7 days
    
    def test_interested_user_count(self):
        """Test interested_user_count property"""
        from pop_accounts.models import PopUpCustomerProfile
        # Create test user
        user1, user_profile1 = create_test_user(
            "user1@test.com", "testpass!23", "Test", "User", "9", "male"
        )

        user2, user_profile2 = create_test_user(
            "user2@test.com", "testpass!23", "Test2", "User2", "8", "male"
        )
        
        # Add to interested users
        self.product.interested_users.add(user_profile1, user_profile2)
        
        assert self.release.interested_user_count == 2
    
    def test_paid_user_count(self):
        """Test paid_user_count property"""

        user, user_profile = create_test_user(
            "user1@test.com", "testpass!23", "Test", "User", "9", "male"
        )
        # Create service requests
        ProcurementServiceRequest.objects.create(
            user=user,
            scheduled_release=self.release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=timezone.now(),
            status='pending',
        )
        
        assert self.release.paid_user_count == 1
    
    def test_paid_user_count_excludes_abandoned(self):
        """Test paid_user_count excludes abandoned requests"""
        user, user_profile = create_test_user(
            "user1@test.com", "testpass!23", "Test", "User", "9", "male"
        )

        ProcurementServiceRequest.objects.create(
            user=user,
            scheduled_release=self.release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=timezone.now(),
            status='abandoned',
        )
        
        assert self.release.paid_user_count == 0
    
    def test_get_search_params_direct_url(self):
        """Test get_search_params with direct_url method"""
        params = self.release.get_search_params()
        assert params['method'] == 'direct_url'
        assert params['sku'] == 'IQ8495-002'
        assert 'nike.com' in params['query']
    
    def test_get_search_params_sku_search(self):
        """Test get_search_params with sku_search method"""
        sku_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='IQ8495-006',
            release_date=self.release_date,
            search_method='sku_search',
            product_url=None,
        )
        params = sku_release.get_search_params()
        assert params['method'] == 'sku_search'
        assert params['sku'] == 'IQ8495-006'
    
    def test_get_search_params_product_name(self):
        """Test get_search_params with product_name method"""
        name_release = ScheduledRelease.objects.create(
            product=self.product,
            sku='IQ8495-007',
            release_date=self.release_date,
            search_method='product_name',
            search_query='LeBron NXXT Gen By JuJu',
        )
        params = name_release.get_search_params()
        assert params['method'] == 'product_name'
        assert 'LeBron' in params['query']


class TestProcurementServiceRequest(TestCase):
    """Test ProcurementServiceRequest model"""
    
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
            product_title="Air Jordan 1",
            secondary_product_title="Chicago",
            retail_price=Decimal("170.00"),
            is_active=True
        )
        
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='DJ0646-610',
            release_date=timezone.now() + timedelta(days=1),
            search_method='direct_url',
            product_url='https://www.nike.com/t/air-jordan-1-chicago',
            retail_price=170.00,
        )
        
        self.user, self.user_profile = create_test_user(
            "test@test.com", "testpass!23", "Test", "User", "10", "male"
        )

        self.request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 10',
            sex='Mens',
            color='Chicago Red',
            max_price=180.00,
            service_fee=15.00,
            fee_paid_at=timezone.now(),
            status='pending',
        )
    
    def test_procurement_service_request_creation(self):
        """Test creating a service request"""
        assert self.request.user == self.user
        assert self.request.scheduled_release == self.release
        assert self.request.size == 'US 10'
        assert self.request.status == 'pending'
    
    def test_procurement_service_request_str(self):
        """Test string representation"""
        str_repr = str(self.request)
        assert 'test@test.com' in str_repr
        assert 'Air Jordan' in str_repr
        assert 'US 10' in str_repr
    

    def test_was_successful_true(self):
        """Test was_successful when success"""
        # Create execution
        proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Air Jordan 1',
            target_size='US 10',
            max_price=180.00,
            procurement_type='inventory',
        )
        
        execution = ProcurementExecution.objects.create(
            procurement_request=proc_request,
            status='success',
            strategy_used='fastest',
            winning_site='nike',
            order_id='ORD-123',
            started_at=django_timezone.now(),
        )
        
        # Link to service request
        self.request.procurement_request = proc_request
        self.request.procurement_execution = execution
        self.request.status = 'success'
        self.request.save()
        
        assert self.request.was_successful is True
    
    def test_was_successful_false(self):
        """Test was_successful when not successful"""
        assert self.request.was_successful is False
    
    def test_time_until_release(self):
        """Test time_until_release property"""
        time_delta = self.request.time_until_release
        assert isinstance(time_delta, timedelta)
        assert time_delta.total_seconds() > 0
    
    def test_unique_constraint_user_release_size(self):
        """Test unique constraint on user, release, size"""
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            ProcurementServiceRequest.objects.create(
                user=self.user,
                scheduled_release=self.release,
                size='US 10',  # Same as existing
                sex='Mens',
                service_fee=15.00,
                fee_paid_at=timezone.now(),
            )
    
    def test_different_sex_same_size_allowed(self):
        """Mens 10 and Womens 10 are distinct procurement requests."""
        # self.request already has sex='Mens', size='US 10'
        # A Womens 10 should be allowed
        womens_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 10',
            sex='Womens',     # different sex — should NOT raise
            service_fee=15.00,
            fee_paid_at=timezone.now(),
        )
        self.assertIsNotNone(womens_request.pk)

        
    def test_unique_allows_different_sizes(self):
        """Test unique constraint allows different sizes for same user/release"""
        request2 = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 11',  # Different size
            service_fee=15.00,
            fee_paid_at=timezone.now(),
        )
        
        assert request2.size == 'US 11'
        assert request2.user == self.user
        assert request2.scheduled_release == self.release
    
    def test_create_procurement_request(self):
        """Test create_procurement_request method"""
        proc_request = self.request.create_procurement_request()
        
        assert proc_request.user == self.user
        assert proc_request.product == self.product
        assert proc_request.target_size == 'US 10'
        assert proc_request.target_color == 'Chicago Red'
        assert proc_request.status == 'pending'
        
        # Check links are set
        self.request.refresh_from_db()
        assert self.request.procurement_request == proc_request
        assert self.request.procurement_request_created_at is not None
        assert self.request.status == 'active'
    
    def test_create_procurement_request_uses_max_price(self):
        """Test create_procurement_request uses provided max_price"""
        proc_request = self.request.create_procurement_request()
        assert proc_request.max_price == 180.00
    
    def test_create_procurement_request_falls_back_to_retail(self):
        """Test create_procurement_request falls back to retail price"""
        request_no_max = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 12',
            max_price=None,  # No max price
            service_fee=15.00,
            fee_paid_at=timezone.now(),
        )
        
        proc_request = request_no_max.create_procurement_request()
        assert proc_request.max_price == 170.00  # Retail price


class TestReleaseExecutionBatch(TestCase):
    """Test ReleaseExecutionBatch model"""
    
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
            product_title="Dunk Low",
            secondary_product_title="Tarheel",
            retail_price=Decimal("170.00"),
            is_active=True
        )
        
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='CW1590-100',
            release_date=timezone.now(),
            search_method='direct_url',
            product_url='https://www.nike.com/t/dunk-low',
        )
        
        self.user, self.user_profile = create_test_user(
            "test@test.com", "testpass!23", "Test", "User", "10", "male"
        )

        self.proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product_name='Dunk Low',
            target_size='US 10',
            max_price=120.00,
            procurement_type='inventory',
            # started_at=timezone.now(),
        )
        
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='success',
            strategy_used='fastest',
            winning_site='nike',
            order_id='ORD-456',
            started_at=django_timezone.now(),
            completed_at=django_timezone.now() + timedelta(minutes=5),
        )
        
        self.batch = ReleaseExecutionBatch.objects.create(
            scheduled_release=self.release,
            total_attempts=5,
            successful_count=3,
            failed_count=2,
            started_at=django_timezone.now(),
            completed_at=django_timezone.now() + timedelta(minutes=10),
        )
    
    def test_release_execution_batch_creation(self):
        """Test creating a batch"""
        assert self.batch.scheduled_release == self.release
        assert self.batch.total_attempts == 5
        assert self.batch.successful_count == 3
        assert self.batch.failed_count == 2
    
    def test_release_execution_batch_str(self):
        """Test string representation"""
        str_repr = str(self.batch)
        assert 'Dunk Low' in str_repr
        assert '3/5' in str_repr
    
    def test_success_rate(self):
        """Test success_rate calculation"""
        rate = self.batch.success_rate
        assert rate == 60.0  # 3/5 = 60%
    
    def test_success_rate_zero_attempts(self):
        """Test success_rate with zero attempts"""
        batch = ReleaseExecutionBatch.objects.create(
            scheduled_release=self.release,
            total_attempts=0,
            successful_count=0,
            failed_count=0,
            started_at=timezone.now(),
        )
        assert batch.success_rate == 0
    
    def test_duration_seconds(self):
        """Test duration_seconds calculation"""
        duration = self.batch.duration_seconds
        assert duration >= 10 * 60  # At least 10 minutes
    
    def test_duration_seconds_not_completed(self):
        """Test duration_seconds when batch not completed"""
        batch = ReleaseExecutionBatch.objects.create(
            scheduled_release=self.release,
            total_attempts=2,
            successful_count=1,
            failed_count=1,
            started_at=timezone.now(),
            completed_at=None,
        )
        assert batch.duration_seconds == 0
    
    def test_add_executions_to_batch(self):
        """Test adding executions to batch"""
        self.batch.executions.add(self.execution)
        
        assert self.batch.executions.count() == 1
        assert self.execution in self.batch.executions.all()


class TestScheduledModelsRelationships(TestCase):
    """Test relationships between scheduled models"""
    
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
            release_date=timezone.now() + timedelta(days=1),
            search_method='direct_url',
            product_url='https://www.nike.com/t/test',
        )
        
        self.user, self.user_profile = create_test_user(
            "test@test.com", "testpass!23", "Test", "User", "10", "male"
        )

    def test_service_request_linked_to_release(self):
        """Test service request is linked to release"""
        service_req = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=timezone.now(),
        )
        
        assert service_req.scheduled_release == self.release
        assert service_req in self.release.procurement_service_requests.all()
    
    def test_batch_linked_to_release(self):
        """Test batch is linked to release"""
        batch = ReleaseExecutionBatch.objects.create(
            scheduled_release=self.release,
            total_attempts=1,
            successful_count=1,
            failed_count=0,
            started_at=timezone.now(),
        )
        
        assert batch.scheduled_release == self.release
        assert batch in self.release.execution_batches.all()
    
    def test_cascade_delete_release_deletes_service_requests(self):
        """Test that deleting release deletes service requests"""
        service_req = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='US 10',
            service_fee=15.00,
            fee_paid_at=timezone.now(),
        )
        
        release_id = self.release.id
        self.release.delete()
        
        # Service request should be deleted
        assert not ProcurementServiceRequest.objects.filter(
            scheduled_release_id=release_id
        ).exists()



if __name__ == '__main__':
    pytest.main([__file__, '-v'])