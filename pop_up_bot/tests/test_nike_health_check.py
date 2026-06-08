# pop_up_bot/tests/test_nike_health_check.py

"""
Tests for Nike Health Check System

Tests daily synthetic monitoring of Nike bot functionality.
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta
from decimal import Decimal

from pop_up_bot.models import DailyHealthCheck, HealthCheckStep
from pop_up_bot.health.nike_health_check import NikeHealthCheckHandler
from pop_up_bot.handlers.base_handler import Product

User = None  # Not needed for these tests


class HealthCheckModelTestCase(TestCase):
    """Test DailyHealthCheck and HealthCheckStep models"""
    
    def setUp(self):
        """Set up test data"""
        self.health_check = DailyHealthCheck.objects.create(
            site='nike',
            status='pending',
            product_sku='DJ0646-610',
            product_name='Air Jordan 1 Low',
        )
    
    def test_create_health_check(self):
        """Test creating a health check record"""
        self.assertIsNotNone(self.health_check.id)
        self.assertEqual(self.health_check.site, 'nike')
        self.assertEqual(self.health_check.status, 'pending')
        self.assertEqual(self.health_check.product_sku, 'DJ0646-610')
    
    def test_mark_running(self):
        """Test marking health check as running"""
        self.health_check.mark_running()
        
        self.health_check.refresh_from_db()
        self.assertEqual(self.health_check.status, 'running')
        self.assertIsNotNone(self.health_check.started_at)
    
    def test_mark_success(self):
        """Test marking health check as successful"""
        self.health_check.mark_running()
        self.health_check.add_step('navigate')
        self.health_check.add_step('search')
        self.health_check.add_step('add_to_cart')
        self.health_check.add_step('remove_from_cart')
        
        self.health_check.mark_success()
        
        self.health_check.refresh_from_db()
        self.assertEqual(self.health_check.status, 'success')
        self.assertIsNotNone(self.health_check.completed_at)
        self.assertIsNotNone(self.health_check.duration_seconds)
        self.assertTrue(self.health_check.all_steps_completed)
    
    def test_mark_failed(self):
        """Test marking health check as failed"""
        self.health_check.mark_running()
        self.health_check.add_step('navigate')
        
        error_msg = 'Selector not found'
        self.health_check.mark_failed('search', error_msg)
        
        self.health_check.refresh_from_db()
        self.assertEqual(self.health_check.status, 'failed')
        self.assertEqual(self.health_check.error_step, 'search')
        self.assertEqual(self.health_check.error_message, error_msg)
    
    def test_mark_admin_notified(self):
        """Test marking that admin was notified"""
        self.health_check.mark_failed('navigate', 'Connection error')
        self.health_check.mark_admin_notified()
        
        self.health_check.refresh_from_db()
        self.assertTrue(self.health_check.admin_notified)
        self.assertIsNotNone(self.health_check.admin_notification_sent_at)
    
    def test_is_success_property(self):
        """Test is_success property"""
        self.health_check.status = 'success'
        self.assertTrue(self.health_check.is_success)
        
        self.health_check.status = 'failed'
        self.assertFalse(self.health_check.is_success)
    
    def test_is_failed_property(self):
        """Test is_failed property"""
        self.health_check.status = 'failed'
        self.assertTrue(self.health_check.is_failed)
        
        self.health_check.status = 'success'
        self.assertFalse(self.health_check.is_failed)
    
    def test_add_step(self):
        """Test adding steps"""
        self.health_check.add_step('navigate')
        self.health_check.add_step('search')
        
        self.health_check.refresh_from_db()
        self.assertIn('navigate', self.health_check.steps_completed)
        self.assertIn('search', self.health_check.steps_completed)
    
    def test_all_steps_completed(self):
        """Test all_steps_completed property"""
        # No steps yet
        self.assertFalse(self.health_check.all_steps_completed)
        
        # Add all steps
        for step in ['navigate', 'search', 'add_to_cart', 'remove_from_cart']:
            self.health_check.add_step(step)
        
        self.health_check.refresh_from_db()
        self.assertTrue(self.health_check.all_steps_completed)


class HealthCheckStepTestCase(TestCase):
    """Test HealthCheckStep model"""
    
    def setUp(self):
        """Set up test data"""
        self.health_check = DailyHealthCheck.objects.create(
            site='nike',
            status='running',
            product_sku='DJ0646-610',
            product_name='Air Jordan 1 Low',
        )
        
        self.step = HealthCheckStep.objects.create(
            health_check=self.health_check,
            step_number=1,
            step_name='navigate',
            description='Navigate to Nike.com',
            status='pending',
        )
    
    def test_create_step(self):
        """Test creating a health check step"""
        self.assertIsNotNone(self.step.id)
        self.assertEqual(self.step.step_name, 'navigate')
        self.assertEqual(self.step.status, 'pending')
    
    def test_mark_running(self):
        """Test marking step as running"""
        self.step.mark_running()
        
        self.step.refresh_from_db()
        self.assertEqual(self.step.status, 'running')
        self.assertIsNotNone(self.step.started_at)
    
    def test_mark_success(self):
        """Test marking step as successful"""
        self.step.mark_running()
        self.step.mark_success(duration_ms=1500)
        
        self.step.refresh_from_db()
        self.assertEqual(self.step.status, 'success')
        self.assertEqual(self.step.duration_ms, 1500)
        self.assertIsNotNone(self.step.completed_at)
    
    def test_mark_failed(self):
        """Test marking step as failed"""
        self.step.mark_running()
        
        error = 'Element not found'
        self.step.mark_failed(error, duration_ms=2000)
        
        self.step.refresh_from_db()
        self.assertEqual(self.step.status, 'failed')
        self.assertEqual(self.step.error_message, error)
        self.assertEqual(self.step.duration_ms, 2000)


class NikeHealthCheckHandlerTestCase(TestCase):
    """Test NikeHealthCheckHandler"""
    
    def setUp(self):
        """Set up test data"""
        self.handler = NikeHealthCheckHandler()
    
    def test_handler_initialization(self):
        """Test handler initializes correctly"""
        self.assertIsNone(self.handler.health_check)
        self.assertIsNone(self.handler.engine)
        self.assertIsNone(self.handler.site_handler)
    
    def test_test_product_constants(self):
        """Test handler has correct test product constants"""
        self.assertEqual(self.handler.TEST_PRODUCT_SKU, 'DJ0646-610')
        self.assertEqual(self.handler.TEST_PRODUCT_NAME, 'Air Jordan 1 Low')
        self.assertIn('nike', self.handler.TEST_PRODUCT_URL.lower())
    
    def test_steps_defined(self):
        """Test all required steps are defined"""
        required_steps = ['navigate', 'search', 'add_to_cart', 'remove_from_cart']
        for step in required_steps:
            self.assertIn(step, self.handler.STEPS)
    
    @patch('pop_up_bot.health.nike_health_check.PlaywrightScraperEngine')
    @patch('pop_up_bot.health.nike_health_check.NikeSiteHandler')
    def test_initialize_handlers(self, mock_site_handler, mock_engine):
        """Test handler initialization"""
        self.handler._initialize_handlers()
        
        # Verify handlers were created
        self.assertIsNotNone(self.handler.engine)
        self.assertIsNotNone(self.handler.site_handler)
    
    @patch('pop_up_bot.health.nike_health_check.PlaywrightScraperEngine')
    @patch('pop_up_bot.health.nike_health_check.NikeSiteHandler')
    def test_run_health_check_success(self, mock_site_handler_class, mock_engine_class):
        """Test successful health check"""
        # Mock engine and site handler
        mock_engine = AsyncMock()
        mock_engine.navigate = AsyncMock()
        mock_engine.get_title = AsyncMock(return_value='Nike')
        mock_engine.close = AsyncMock()
        mock_engine_class.return_value = mock_engine
        
        mock_site_handler = AsyncMock()
        mock_site_handler.engine = mock_engine
        mock_site_handler.find_product = AsyncMock(
            return_value=Product(
                product_id='553558-404',
                name='Air Jordan 1 Low',
                price=170.0,
                available_sizes=['US 10'],
                product_url='https://nike.com',
                in_stock=True,
            )
        )
        mock_site_handler.add_to_cart = AsyncMock(return_value=True)
        mock_site_handler.cart_item = MagicMock(product_name='Air Jordan 1 Low')
        mock_site_handler_class.return_value = mock_site_handler
        
        # Run health check
        self.handler._initialize_handlers = MagicMock()
        self.handler.site_handler = mock_site_handler
        self.handler.engine = mock_engine
        
        # Manually run through steps
        self.handler.health_check = DailyHealthCheck.objects.create(
            site='nike',
            product_sku='DJ0646-610',
            product_name='Air Jordan 1 Low',
        )
        self.handler.health_check.mark_running()
        
        # Run navigate step
        result = self.handler._step_navigate()
        self.assertTrue(result)
        
        # Verify health check was created
        self.assertIsNotNone(self.handler.health_check.id)
    
    def test_check_step_failed(self):
        """Test checking if step failed"""
        health_check = DailyHealthCheck.objects.create(
            site='nike',
            product_sku='DJ0646-610',
        )
        self.handler.health_check = health_check
        
        # No error yet
        self.assertFalse(self.handler._check_step_failed())
        
        # Mark as failed
        health_check.mark_failed('navigate', 'Connection error')
        self.assertTrue(self.handler._check_step_failed())
    
    def test_get_health_check_summary(self):
        """Test getting health check summary"""
        health_check = DailyHealthCheck.objects.create(
            site='nike',
            status='success',
            product_sku='DJ0646-610',
            product_name='Air Jordan 1 Low',
        )
        health_check.mark_running()
        health_check.add_step('navigate')
        health_check.add_step('search')
        health_check.mark_success()
        
        self.handler.health_check = health_check
        summary = self.handler.get_health_check_summary()
        
        self.assertEqual(summary['site'], 'nike')
        self.assertEqual(summary['status'], 'success')
        self.assertTrue(summary['is_success'])
        self.assertIn('navigate', summary['steps_completed'])
        self.assertIn('search', summary['steps_completed'])


class HealthCheckQueryTestCase(TestCase):
    """Test health check queries and filtering"""
    
    def setUp(self):
        """Create multiple health checks"""
        # Create successful checks
        for i in range(3):
            DailyHealthCheck.objects.create(
                site='nike',
                status='success',
                product_sku='DJ0646-610',
                product_name='Air Jordan 1 Low',
            )
        
        # Create failed checks
        for i in range(2):
            DailyHealthCheck.objects.create(
                site='nike',
                status='failed',
                product_sku='DJ0646-610',
                error_step='search',
                error_message='Selector not found',
            )
    
    def test_filter_by_status(self):
        """Test filtering by status"""
        successful = DailyHealthCheck.objects.filter(status='success')
        failed = DailyHealthCheck.objects.filter(status='failed')
        
        self.assertEqual(successful.count(), 3)
        self.assertEqual(failed.count(), 2)
    
    def test_filter_by_site(self):
        """Test filtering by site"""
        nike_checks = DailyHealthCheck.objects.filter(site='nike')
        self.assertEqual(nike_checks.count(), 5)
    
    def test_latest_health_check(self):
        """Test getting latest health check"""
        latest = DailyHealthCheck.objects.latest('created_at')
        self.assertIsNotNone(latest)
        self.assertEqual(latest.site, 'nike')
    
    def test_today_health_checks(self):
        """Test getting today's health checks"""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_checks = DailyHealthCheck.objects.filter(
            created_at__gte=today_start,
            created_at__lt=today_end,
        )
        
        self.assertEqual(today_checks.count(), 5)