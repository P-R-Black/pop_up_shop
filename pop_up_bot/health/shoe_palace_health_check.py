# ============================================================
# pop_up_bot/health/shoe_palace_health_check.py
#
# Daily synthetic monitoring of Shoe Palace bot functionality.
# Mirrors NikeHealthCheckHandler structure exactly.
# ============================================================

import logging
import time
from django.utils import timezone
from asgiref.sync import async_to_sync

from pop_up_bot.models import DailyHealthCheck, HealthCheckStep
from pop_up_bot.handlers.shoe_palace_handler import ShoePalaceSiteHandler
from pop_up_bot.engines.scraper_engine import PlaywrightScraperEngine
from pop_up_bot.handlers.base_handler import Product

logger = logging.getLogger(__name__)


class ShoePalaceHealthCheckHandler:
    """
    Execute daily health checks on shoepalace.com

    Verifies bot can:
    1. Navigate to Shoe Palace
    2. Search for product
    3. Add to cart
    4. Remove from cart (verify cart access)

    Logs each step and alerts on failure.
    """

    # Test product — Jordan 5 Retro is a stable evergreen product
    TEST_PRODUCT_SKU    = 'DD0587-008'
    TEST_PRODUCT_NAME   = 'Air Jordan 5 Retro'
    TEST_PRODUCT_URL    = 'https://www.shoepalace.com/products/jordan-dd0587-008-air-jordan-5-retro-black-carolina-mens-lifestyle-shoes-black-university-blue-white'
    TEST_SEARCH_TERM    = 'Air Jordan 5 Retro'
    TEST_SIZE           = '10'

    STEPS = {
        'navigate':        'Navigate to Shoe Palace',
        'search':          'Search for product',
        'add_to_cart':     'Add product to cart',
        'remove_from_cart': 'Remove product from cart',
    }

    def __init__(self):
        self.health_check = None
        self.steps_log    = {}
        self.engine       = None
        self.site_handler = None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run_health_check(self) -> DailyHealthCheck:
        """
        Execute full Shoe Palace health check.

        Returns:
            DailyHealthCheck instance with results
        """
        logger.info("=" * 60)
        logger.info("Starting Shoe Palace Daily Health Check")
        logger.info("=" * 60)

        try:
            self.health_check = DailyHealthCheck.objects.create(
                site='shoe_palace',
                status='pending',
                product_sku=self.TEST_PRODUCT_SKU,
                product_name=self.TEST_PRODUCT_NAME,
            )

            self.health_check.mark_running()
            logger.info(f"Health check {self.health_check.id} started")

            self._initialize_handlers()

            self._run_step('navigate',        self._step_navigate)
            if not self._check_step_failed():
                self._run_step('search',      self._step_search)
            if not self._check_step_failed():
                self._run_step('add_to_cart', self._step_add_to_cart)
            if not self._check_step_failed():
                self._run_step('remove_from_cart', self._step_remove_from_cart)

            if self._check_step_failed():
                logger.error(f"Health check FAILED at: {self.health_check.error_step}")
                self.health_check.mark_failed(
                    self.health_check.error_step,
                    self.health_check.error_message
                )
            else:
                logger.info("Health check SUCCEEDED — all steps completed")
                self.health_check.mark_success()

            return self.health_check

        except Exception as e:
            logger.error(f"Health check crashed: {str(e)}", exc_info=True)
            if self.health_check:
                self.health_check.mark_failed(
                    'health_check_crash',
                    f"Unexpected error: {str(e)}"
                )
            return self.health_check

        finally:
            if self.engine:
                try:
                    async_to_sync(self.engine.close)()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Step runner
    # ------------------------------------------------------------------

    def _run_step(self, step_key: str, step_func) -> bool:
        step_name   = self.STEPS.get(step_key, step_key)
        step_number = len(self.health_check.steps_completed) + 1

        logger.info(f"\n--- Step: {step_name} ---")

        step_record = HealthCheckStep.objects.create(
            health_check=self.health_check,
            step_number=step_number,
            step_name=step_key,
            description=step_name,
            status='running',
        )

        start_time = time.time()

        try:
            step_record.mark_running()
            result = step_func()

            if not result:
                raise Exception(f"Step {step_key} returned False")

            duration_ms = int((time.time() - start_time) * 1000)
            step_record.mark_success(duration_ms)
            self.health_check.add_step(step_key)

            logger.info(f"✓ {step_name} — SUCCESS ({duration_ms}ms)")
            return True

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            step_record.mark_failed(str(e), duration_ms)
            self.health_check.mark_failed(step_key, str(e))
            logger.error(f"✗ {step_name} — FAILED: {str(e)}")
            return False

    # ------------------------------------------------------------------
    # Individual steps
    # ------------------------------------------------------------------

    def _step_navigate(self) -> bool:
        """Step 1: Navigate to shoepalace.com"""
        async_to_sync(self.site_handler.engine.navigate)(
            'https://www.shoepalace.com'
        )
        title = async_to_sync(self.site_handler.engine.get_title)()
        logger.info(f"Page title: {title}")

        if 'shoe palace' not in title.lower() and 'shoepalace' not in title.lower():
            raise Exception(f"Unexpected page title: {title}")

        return True

    def _step_search(self) -> bool:
        """Step 2: Search for test product"""
        product = async_to_sync(self.site_handler.find_product)(
            self.TEST_SEARCH_TERM,
            self.TEST_SIZE,
        )

        if not product:
            raise Exception(f"Could not find product: {self.TEST_SEARCH_TERM}")

        if not product.in_stock:
            raise Exception("Test product has no available sizes")

        logger.info(f"Found: {product.name} — ${product.price}")
        return True

    def _step_add_to_cart(self) -> bool:
        """Step 3: Add product to cart"""
        if not self.site_handler.product_found:
            raise Exception("No product found from previous step")

        success = async_to_sync(self.site_handler.add_to_cart)(
            self.site_handler.product_found.product_id,
            self.TEST_SIZE,
            quantity=1,
        )

        if not success:
            raise Exception("Failed to add product to cart")

        if not self.site_handler.cart_item:
            raise Exception("Cart item not set after add_to_cart")

        logger.info(f"Added to cart: {self.site_handler.cart_item.product_name}")
        return True

    def _step_remove_from_cart(self) -> bool:
        """Step 4: Verify cart access (Shopify /cart)"""
        async_to_sync(self.site_handler.engine.navigate)(
            'https://www.shoepalace.com/cart'
        )
        current_url = async_to_sync(self.site_handler.engine.get_url)()
        logger.info(f"Cart URL: {current_url}")

        if 'cart' not in current_url.lower():
            raise Exception("Could not navigate to cart page")

        logger.info("Verified cart page access")
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _initialize_handlers(self):
        logger.info("Initializing browser engine...")
        self.engine = PlaywrightScraperEngine()
        self.site_handler = ShoePalaceSiteHandler(
            engine=self.engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
        logger.info("✓ Handlers initialized")

    def _check_step_failed(self) -> bool:
        return self.health_check.error_step is not None

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def notify_admin_if_failed(self) -> bool:
        if self.health_check.is_success:
            return True
        if self.health_check.admin_notified:
            return True
        try:
            self._send_admin_notification()
            self.health_check.mark_admin_notified()
            logger.info("✓ Admin notification sent")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False

    def _send_admin_notification(self):
        subject = (
            f"⚠️ Shoe Palace Health Check FAILED — "
            f"{self.health_check.error_step}"
        )
        message = f"""
        Shoe Palace Daily Health Check FAILED

        Site: shoepalace.com
        Test Product: {self.health_check.product_name} ({self.health_check.product_sku})
        Status: {self.health_check.status}
        Failed At: {self.health_check.error_step}
        Error: {self.health_check.error_message}

        Time: {self.health_check.completed_at}
        Duration: {self.health_check.duration_seconds}s
        Completed Steps: {', '.join(self.health_check.steps_completed)}

        IMMEDIATE ACTION REQUIRED:
        - Check if Shoe Palace site structure changed
        - Verify selectors in ShoePalaceSiteHandler
        - Update code if needed
        - Re-run health check to verify fix
        """
        logger.warning(f"\n{subject}\n{message}")
        # TODO: Send email/Slack notification

    def get_health_check_summary(self) -> dict:
        if not self.health_check:
            return {}
        return {
            'id':               str(self.health_check.id),
            'site':             self.health_check.site,
            'status':           self.health_check.status,
            'is_success':       self.health_check.is_success,
            'product_sku':      self.health_check.product_sku,
            'product_name':     self.health_check.product_name,
            'steps_completed':  self.health_check.steps_completed,
            'error_step':       self.health_check.error_step,
            'error_message':    self.health_check.error_message,
            'duration_seconds': self.health_check.duration_seconds,
            'started_at':       self.health_check.started_at.isoformat() if self.health_check.started_at else None,
            'completed_at':     self.health_check.completed_at.isoformat() if self.health_check.completed_at else None,
        }