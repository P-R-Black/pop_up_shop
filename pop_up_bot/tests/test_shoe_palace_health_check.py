# ============================================================
# pop_up_bot/tests/test_shoe_palace_health_check.py
# ============================================================

from django.test import TestCase
from django.utils import timezone
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from pop_up_bot.models import DailyHealthCheck, HealthCheckStep
from pop_up_bot.health.shoe_palace_health_check import ShoePalaceHealthCheckHandler
from pop_up_bot.handlers.base_handler import Product


class ShoePalaceHealthCheckHandlerInitTestCase(TestCase):
    """Test ShoePalaceHealthCheckHandler initialization and constants"""

    def setUp(self):
        self.handler = ShoePalaceHealthCheckHandler()

    def test_handler_initialization(self):
        self.assertIsNone(self.handler.health_check)
        self.assertIsNone(self.handler.engine)
        self.assertIsNone(self.handler.site_handler)

    def test_test_product_constants(self):
        self.assertEqual(self.handler.TEST_PRODUCT_SKU, 'DD0587-008')
        self.assertEqual(self.handler.TEST_PRODUCT_NAME, 'Air Jordan 5 Retro')
        self.assertIn('shoepalace.com', self.handler.TEST_PRODUCT_URL)
        self.assertEqual(self.handler.TEST_SIZE, '10')

    def test_steps_defined(self):
        for step in ['navigate', 'search', 'add_to_cart', 'remove_from_cart']:
            self.assertIn(step, self.handler.STEPS)

    def test_site_is_shoe_palace(self):
        """Health check records should use 'shoe_palace' as site."""
        self.handler._initialize_handlers = MagicMock()
        self.handler.site_handler = MagicMock()
        self.handler.engine = MagicMock()

        # Patch all steps to succeed immediately
        self.handler._run_step = MagicMock(return_value=True)
        self.handler._check_step_failed = MagicMock(return_value=False)

        result = self.handler.run_health_check()
        self.assertEqual(result.site, 'shoe_palace')


class ShoePalaceHealthCheckStepsTestCase(TestCase):
    """Test individual health check steps"""

    def setUp(self):
        self.handler = ShoePalaceHealthCheckHandler()

        # Create a real health check record
        self.handler.health_check = DailyHealthCheck.objects.create(
            site='shoe_palace',
            status='running',
            product_sku='DD0587-008',
            product_name='Air Jordan 5 Retro',
        )
        self.handler.health_check.mark_running()

        # Mock engine and site handler
        self.mock_engine = AsyncMock()
        self.mock_site_handler = AsyncMock()
        self.mock_site_handler.engine = self.mock_engine
        self.handler.engine = self.mock_engine
        self.handler.site_handler = self.mock_site_handler

    # ------------------------------------------------------------------
    # Step: navigate
    # ------------------------------------------------------------------

    def test_step_navigate_success(self):
        self.mock_engine.navigate = AsyncMock()
        self.mock_engine.get_title = AsyncMock(
            return_value='Shoe Palace | Sneakers & More'
        )
        result = self.handler._step_navigate()
        self.assertTrue(result)

    def test_step_navigate_success_shoepalace_in_title(self):
        self.mock_engine.navigate = AsyncMock()
        self.mock_engine.get_title = AsyncMock(
            return_value='shoepalace.com — Sneakers'
        )
        result = self.handler._step_navigate()
        self.assertTrue(result)

    def test_step_navigate_wrong_site_raises(self):
        self.mock_engine.navigate = AsyncMock()
        self.mock_engine.get_title = AsyncMock(return_value='Google')
        with self.assertRaises(Exception) as ctx:
            self.handler._step_navigate()
        self.assertIn('Unexpected page title', str(ctx.exception))

    # ------------------------------------------------------------------
    # Step: search
    # ------------------------------------------------------------------

    def test_step_search_success(self):
        self.mock_site_handler.find_product = AsyncMock(
            return_value=Product(
                product_id='jordan-dd0587-008',
                name='Air Jordan 5 Retro',
                price=220.0,
                available_sizes=['9', '10', '11'],
                product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
                in_stock=True,
            )
        )
        result = self.handler._step_search()
        self.assertTrue(result)

    def test_step_search_product_not_found_raises(self):
        self.mock_site_handler.find_product = AsyncMock(return_value=None)
        with self.assertRaises(Exception) as ctx:
            self.handler._step_search()
        self.assertIn('Could not find product', str(ctx.exception))

    def test_step_search_out_of_stock_raises(self):
        self.mock_site_handler.find_product = AsyncMock(
            return_value=Product(
                product_id='jordan-dd0587-008',
                name='Air Jordan 5 Retro',
                price=220.0,
                available_sizes=[],
                product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
                in_stock=False,
            )
        )
        with self.assertRaises(Exception) as ctx:
            self.handler._step_search()
        self.assertIn('no available sizes', str(ctx.exception))

    # ------------------------------------------------------------------
    # Step: add_to_cart
    # ------------------------------------------------------------------

    def test_step_add_to_cart_success(self):
        self.mock_site_handler.product_found = Product(
            product_id='jordan-dd0587-008',
            name='Air Jordan 5 Retro',
            price=220.0,
            available_sizes=['10'],
            product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
            in_stock=True,
        )
        self.mock_site_handler.add_to_cart = AsyncMock(return_value=True)
        self.mock_site_handler.cart_item = MagicMock(
            product_name='Air Jordan 5 Retro'
        )
        result = self.handler._step_add_to_cart()
        self.assertTrue(result)

    def test_step_add_to_cart_no_product_raises(self):
        self.mock_site_handler.product_found = None
        with self.assertRaises(Exception) as ctx:
            self.handler._step_add_to_cart()
        self.assertIn('No product found', str(ctx.exception))

    def test_step_add_to_cart_failure_raises(self):
        self.mock_site_handler.product_found = Product(
            product_id='jordan-dd0587-008',
            name='Air Jordan 5 Retro',
            price=220.0,
            available_sizes=['10'],
            product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
            in_stock=True,
        )
        self.mock_site_handler.add_to_cart = AsyncMock(return_value=False)
        self.mock_site_handler.cart_item = None
        with self.assertRaises(Exception) as ctx:
            self.handler._step_add_to_cart()
        self.assertIn('Failed to add', str(ctx.exception))

    def test_step_add_to_cart_no_cart_item_raises(self):
        self.mock_site_handler.product_found = Product(
            product_id='jordan-dd0587-008',
            name='Air Jordan 5 Retro',
            price=220.0,
            available_sizes=['10'],
            product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
            in_stock=True,
        )
        self.mock_site_handler.add_to_cart = AsyncMock(return_value=True)
        self.mock_site_handler.cart_item = None
        with self.assertRaises(Exception) as ctx:
            self.handler._step_add_to_cart()
        self.assertIn('Cart item not set', str(ctx.exception))

    # ------------------------------------------------------------------
    # Step: remove_from_cart
    # ------------------------------------------------------------------

    def test_step_remove_from_cart_success(self):
        self.mock_site_handler.cart_item = MagicMock()
        self.mock_engine.navigate = AsyncMock()
        self.mock_engine.get_url = AsyncMock(
            return_value='https://www.shoepalace.com/cart'
        )
        result = self.handler._step_remove_from_cart()
        self.assertTrue(result)

    def test_step_remove_from_cart_wrong_url_raises(self):
        self.mock_site_handler.cart_item = MagicMock()
        self.mock_engine.navigate = AsyncMock()
        self.mock_engine.get_url = AsyncMock(
            return_value='https://www.shoepalace.com/collections/all'
        )
        with self.assertRaises(Exception) as ctx:
            self.handler._step_remove_from_cart()
        self.assertIn('Could not navigate to cart', str(ctx.exception))


class ShoePalaceHealthCheckRunTestCase(TestCase):
    """Test full run_health_check flow"""

    def setUp(self):
        self.handler = ShoePalaceHealthCheckHandler()

    @patch('pop_up_bot.health.shoe_palace_health_check.PlaywrightScraperEngine')
    @patch('pop_up_bot.health.shoe_palace_health_check.ShoePalaceSiteHandler')
    def test_run_health_check_success(
        self, mock_handler_class, mock_engine_class
    ):
        mock_engine = AsyncMock()
        mock_engine.navigate = AsyncMock()
        mock_engine.get_title = AsyncMock(return_value='Shoe Palace')
        mock_engine.get_url = AsyncMock(
            return_value='https://www.shoepalace.com/cart'
        )
        mock_engine.close = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_site_handler = AsyncMock()
        mock_site_handler.engine = mock_engine
        mock_site_handler.find_product = AsyncMock(
            return_value=Product(
                product_id='jordan-dd0587-008',
                name='Air Jordan 5 Retro',
                price=220.0,
                available_sizes=['10'],
                product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
                in_stock=True,
            )
        )
        mock_site_handler.add_to_cart = AsyncMock(return_value=True)
        mock_site_handler.cart_item = MagicMock(product_name='Air Jordan 5 Retro')
        mock_site_handler.product_found = Product(
            product_id='jordan-dd0587-008',
            name='Air Jordan 5 Retro',
            price=220.0,
            available_sizes=['10'],
            product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
            in_stock=True,
        )
        mock_handler_class.return_value = mock_site_handler

        result = self.handler.run_health_check()

        self.assertEqual(result.site, 'shoe_palace')
        self.assertEqual(result.status, 'success')
        self.assertTrue(result.is_success)
        self.assertIn('navigate', result.steps_completed)
        self.assertIn('search', result.steps_completed)
        self.assertIn('add_to_cart', result.steps_completed)
        self.assertIn('remove_from_cart', result.steps_completed)

    @patch('pop_up_bot.health.shoe_palace_health_check.PlaywrightScraperEngine')
    @patch('pop_up_bot.health.shoe_palace_health_check.ShoePalaceSiteHandler')
    def test_run_health_check_fails_at_search(
        self, mock_handler_class, mock_engine_class
    ):
        mock_engine = AsyncMock()
        mock_engine.navigate = AsyncMock()
        mock_engine.get_title = AsyncMock(return_value='Shoe Palace')
        mock_engine.close = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_site_handler = AsyncMock()
        mock_site_handler.engine = mock_engine
        mock_site_handler.find_product = AsyncMock(return_value=None)
        mock_handler_class.return_value = mock_site_handler

        result = self.handler.run_health_check()

        self.assertEqual(result.status, 'failed')
        self.assertEqual(result.error_step, 'search')
        self.assertIn('navigate', result.steps_completed)
        self.assertNotIn('add_to_cart', result.steps_completed)

    @patch('pop_up_bot.health.shoe_palace_health_check.PlaywrightScraperEngine')
    @patch('pop_up_bot.health.shoe_palace_health_check.ShoePalaceSiteHandler')
    def test_run_health_check_fails_at_navigate(
        self, mock_handler_class, mock_engine_class
    ):
        mock_engine = AsyncMock()
        mock_engine.navigate = AsyncMock()
        mock_engine.get_title = AsyncMock(return_value='Error 403 Forbidden')
        mock_engine.close = AsyncMock()
        mock_engine_class.return_value = mock_engine

        mock_site_handler = AsyncMock()
        mock_site_handler.engine = mock_engine
        mock_handler_class.return_value = mock_site_handler

        result = self.handler.run_health_check()

        self.assertEqual(result.status, 'failed')
        self.assertEqual(result.error_step, 'navigate')
        self.assertEqual(result.steps_completed, [])

    def test_get_health_check_summary(self):
        hc = DailyHealthCheck.objects.create(
            site='shoe_palace',
            status='success',
            product_sku='DD0587-008',
            product_name='Air Jordan 5 Retro',
        )
        hc.mark_running()
        hc.add_step('navigate')
        hc.add_step('search')
        hc.mark_success()

        self.handler.health_check = hc
        summary = self.handler.get_health_check_summary()

        self.assertEqual(summary['site'], 'shoe_palace')
        self.assertEqual(summary['status'], 'success')
        self.assertTrue(summary['is_success'])
        self.assertIn('navigate', summary['steps_completed'])
        self.assertIn('search', summary['steps_completed'])
        self.assertIsNotNone(summary['started_at'])
        self.assertIsNotNone(summary['completed_at'])

    def test_check_step_failed_false_when_no_error(self):
        self.handler.health_check = DailyHealthCheck.objects.create(
            site='shoe_palace',
            product_sku='DD0587-008',
        )
        self.assertFalse(self.handler._check_step_failed())

    def test_check_step_failed_true_after_failure(self):
        self.handler.health_check = DailyHealthCheck.objects.create(
            site='shoe_palace',
            product_sku='DD0587-008',
        )
        self.handler.health_check.mark_failed('search', 'Selector changed')
        self.assertTrue(self.handler._check_step_failed())

    def test_notify_admin_no_op_on_success(self):
        self.handler.health_check = DailyHealthCheck.objects.create(
            site='shoe_palace',
            product_sku='DD0587-008',
            status='success',
        )
        result = self.handler.notify_admin_if_failed()
        self.assertTrue(result)
        # Admin should NOT be marked notified on success
        self.assertFalse(self.handler.health_check.admin_notified)