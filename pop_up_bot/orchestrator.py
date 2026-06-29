# ============================================================
# UPDATED pop_up_bot/orchestrator.py
# Key change: _attempt_site() now calls NikeSiteHandler
# instead of returning mock data
# ============================================================

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from playwright.async_api import async_playwright

from pop_up_bot.handlers.nike_handler import NikeSiteHandler
from pop_up_bot.engines.scraper_engine import PlaywrightScraperEngine

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    ABANDONED = 'abandoned'


class SearchParameters:
    def __init__(
        self,
        product_name: str,
        size: str,
        sex: Optional[str] = None,
        color: Optional[str] = None,
        price_range: Optional[tuple] = None,
    ):
        self.product_name = product_name
        self.size = size
        self.sex = sex        # "Mens" or "Womens" — for shoes only
        self.color = color
        self.price_range = price_range or (0, float('inf'))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'product_name': self.product_name,
            'size': self.size,
            'sex': self.sex,
            'color': self.color,
            'price_range': self.price_range,
        }

    def __str__(self):
        return (
            f"SearchParameters({self.product_name}, size={self.size}, "
            f"sex={self.sex}, color={self.color}, price={self.price_range})"
        )


class ExecutionResult:
    def __init__(
        self,
        status: ExecutionStatus,
        product_name: Optional[str] = None,
        site: Optional[str] = None,
        order_id: Optional[str] = None,
        item_price: Optional[float] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        duration_seconds: float = 0,
    ):
        self.status = status
        self.product_name = product_name
        self.site = site
        self.order_id = order_id
        self.item_price = item_price
        self.error = error
        self.error_type = error_type   # maps to ProcurementExecution.error_type
        self.duration_seconds = duration_seconds
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'product_name': self.product_name,
            'site': self.site,
            'order_id': self.order_id,
            'item_price': self.item_price,
            'error': self.error,
            'error_type': self.error_type,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat(),
        }

    def __str__(self):
        return (
            f"ExecutionResult({self.status.value}, "
            f"site={self.site}, order_id={self.order_id})"
        )


class BotOrchestrator:
    """
    Orchestrates bot execution across sites.

    Usage:
        orchestrator = BotOrchestrator(
            execution_id='uuid-here',
            strategy_factory=StrategyFactory(),
            session_manager=session_manager,
            procurement_lock=procurement_lock,
            event_logger=event_logger,
        )
        result = await orchestrator.run(
            product_name='Air Jordan 1',
            size='10',
            sex='Mens',
            strategy_name='sequential',
        )
    """

    def __init__(
        self,
        execution_id,
        strategy_factory,
        session_manager,
        procurement_lock,
        event_logger,
        cookie_manager=None,
        proxy_manager=None,
    ):
        self.execution_id = execution_id
        self.strategy_factory = strategy_factory
        self.session_manager = session_manager
        self.procurement_lock = procurement_lock
        self.event_logger = event_logger
        self.cookie_manager = cookie_manager
        self.proxy_manager = proxy_manager

        self.status = ExecutionStatus.PENDING
        self.start_time = datetime.now()
        self.search_params = None
        self.strategy = None
        self.site_results = {}
        self.locked_site = None
        self.event_history = []

        logger.info(f"BotOrchestrator initialized (execution_id={execution_id})")

    async def run(
        self,
        product_name: str,
        size: str,
        sex: Optional[str] = None,
        color: Optional[str] = None,
        strategy_name: str = 'sequential',
        price_range: Optional[tuple] = None,
        site_name: str = 'nike',
        **strategy_kwargs,
    ) -> ExecutionResult:
        """
        Run the procurement execution.

        Args:
            product_name: Product to search for
            size: Size to find (plain number e.g. "10")
            sex: "Mens" or "Womens" for shoes, None otherwise
            color: Optional color preference
            strategy_name: Strategy to use
            price_range: Optional (min, max) price tuple
            site_name: Site to use (currently only 'nike' supported)
        """
        try:
            self.status = ExecutionStatus.RUNNING

            self.search_params = SearchParameters(
                product_name=product_name,
                size=size,
                sex=sex,
                color=color,
                price_range=price_range,
            )

            logger.info(f"Starting procurement: {self.search_params}")

            await self._emit_event(
                'INITIALIZED',
                metadata=self.search_params.to_dict() | {'strategy': strategy_name}
            )

            self.strategy = self.strategy_factory.create(
                strategy_name,
                **strategy_kwargs
            )

            await self._emit_event(
                'STRATEGY_SELECTED',
                metadata={
                    'strategy': strategy_name,
                    'sites': self.strategy.get_site_order(),
                }
            )

            sites = self.strategy.get_site_order()

            if strategy_name in ('parallel', 'fastest'):
                result = await self._run_parallel(sites)
            else:
                result = await self._run_sequential(sites)

            return result

        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            await self._emit_event('FAILED', metadata={'error': str(e)})
            duration = (datetime.now() - self.start_time).total_seconds()
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=str(e),
                error_type='bot_crash',
                duration_seconds=duration,
            )

    # ------------------------------------------------------------------
    # Site attempt — Nike only for now
    # ------------------------------------------------------------------

    async def _attempt_site(self, site: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to procure from a single site.

        Currently supports Nike only. Other sites will return a graceful
        failure so the strategy can move on.
        """
        try:
            logger.info(
                f"Attempting {site} for {self.search_params.product_name} "
                f"(size: {self.search_params.size}, sex: {self.search_params.sex})"
            )

            if site != 'nike':
                logger.warning(f"Handler for '{site}' not yet implemented — skipping")
                return {
                    'success': False,
                    'site': site,
                    'error': f'Handler for {site} not yet implemented',
                    'error_type': 'item_not_found',
                }

            return await self._attempt_nike()

        except Exception as e:
            logger.error(f"Attempt failed for {site}: {e}", exc_info=True)
            await self._emit_event(
                'FAILED',
                site_name=site,
                metadata={'error': str(e)},
            )
            return {
                'success': False,
                'site': site,
                'error': str(e),
                'error_type': 'bot_crash',
            }

    async def _attempt_nike(self) -> Dict[str, Any]:
        """
        Run the full Nike procurement flow using Playwright.

        Flow:
        1. Launch browser
        2. Create PlaywrightScraperEngine
        3. Validate Nike connection
        4. Find product
        5. Add to cart (includes size selection)
        6. Proceed to checkout
        7. Return result
        """
        async with async_playwright() as playwright:
            # Launch browser — headless=False is harder to detect
            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent=(
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
            )

            page = await context.new_page()

            try:
                engine = PlaywrightScraperEngine(page=page)

                handler = NikeSiteHandler(
                    engine=engine,
                    session_manager=self.session_manager,
                    cookie_manager=self.cookie_manager,
                    event_logger=self.event_logger,
                )

                # 1. Validate connection
                await self._emit_event('SITE_SELECTED', site_name='nike')
                connected = await handler.validate_site_connection()
                if not connected:
                    return {
                        'success': False,
                        'site': 'nike',
                        'error': 'Nike site not accessible',
                        'error_type': 'rate_limited',
                    }

                # 2. Find product
                product = await handler.find_product(
                    product_name=self.search_params.product_name,
                    size=self.search_params.size,
                    color=self.search_params.color,
                )

                if not product:
                    return {
                        'success': False,
                        'site': 'nike',
                        'error': 'Product not found',
                        'error_type': 'item_not_found',
                    }

                await self._emit_event('PRODUCT_FOUND', site_name='nike',
                    metadata={'product': product.name, 'price': product.price})

                # 3. Build size string for Nike
                # Nike shows sizes like "M 10 / W 11.5" — we pass the number
                # and let select_size match by value
                size_to_select = self._build_nike_size(
                    self.search_params.size,
                    self.search_params.sex,
                )

                await self._emit_event('SIZE_SELECTED', site_name='nike',
                    metadata={'size': size_to_select})

                # 4. Add to cart (select_size is called inside add_to_cart)
                added = await handler.add_to_cart(
                    product_id=product.product_id,
                    size=size_to_select,
                    quantity=1,
                )

                if not added:
                    # Determine error type from handler's error log
                    error_type = self._classify_handler_error(handler)
                    return {
                        'success': False,
                        'site': 'nike',
                        'error': 'Failed to add to cart',
                        'error_type': error_type,
                    }

                await self._emit_event('CART_SUCCESS', site_name='nike')

                # 5. Proceed to checkout
                at_checkout = await handler.proceed_to_checkout()

                if not at_checkout:
                    return {
                        'success': False,
                        'site': 'nike',
                        'error': 'Failed to reach checkout',
                        'error_type': 'checkout_error',
                    }

                await self._emit_event('CHECKOUT_STARTED', site_name='nike')

                # 6. Return success
                # Note: We stop at checkout — payment is handled separately
                # (Pop Up Shop pays Nike directly, user pays Pop Up Shop)
                logger.info(
                    f"Nike: item in cart and at checkout — "
                    f"{self.search_params.product_name} size {size_to_select}"
                )

                return {
                    'success': True,
                    'site': 'nike',
                    'product_name': product.name,
                    'size': size_to_select,
                    'order_id': None,       # populated after payment
                    'price': product.price,
                    'error_type': 'success',
                }

            except Exception as e:
                logger.error(f"Nike attempt error: {e}", exc_info=True)
                return {
                    'success': False,
                    'site': 'nike',
                    'error': str(e),
                    'error_type': 'bot_crash',
                }

            finally:
                await browser.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_nike_size(self, size: str, sex: Optional[str]) -> str:
        """
        Build a Nike-compatible size string for select_size().

        Nike labels look like "M 10 / W 11.5".
        select_size() matches by checking if our value is contained in
        the radio value or label text, so passing just "10" works for
        men's and "W 8" style matching for women's.

        For men's: pass the bare number ("10")
        For women's: pass "W {size}" so it doesn't accidentally match
                     the men's equivalent
        """
        if not sex:
            return size

        if sex.lower() in ('womens', "women's", 'female', 'w'):
            return f"W {size}"

        # Mens — bare number matches "M 10 / W 11.5" via contains check
        return size

    def _classify_handler_error(self, handler) -> str:
        """
        Map the last handler error to a ProcurementExecution error_type.
        """
        if not handler.error_log:
            return 'unknown_error'

        last_error = handler.error_log[-1]
        error_type_str = last_error.get('type', '')

        mapping = {
            'out_of_stock': 'out_of_stock',
            'blocked': 'rate_limited',
            'rate_limited': 'rate_limited',
            'captcha': 'rate_limited',
            'product_not_found': 'item_not_found',
            'network_error': 'bot_crash',
            'checkout_error': 'bot_crash',
            'payment_failed': 'bot_crash',
            'unknown': 'unknown_error',
        }

        return mapping.get(error_type_str, 'unknown_error')

    async def _emit_event(
        self,
        event_type: str,
        site_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        event_entry = {
            'type': event_type,
            'site': site_name,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
        }
        self.event_history.append(event_entry)
        logger.info(f"Event: {event_type} (site: {site_name})")

        if self.event_logger:
            try:
                await self.event_logger.emit(
                    event_type,
                    site_name=site_name,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(f"Error emitting event: {e}")

    async def _run_sequential(self, sites: List[str]) -> ExecutionResult:
        logger.info(f"Running sequential execution (sites: {sites})")

        for site in sites:
            try:
                await self._emit_event('SITE_SELECTED', site_name=site)
                result = await self._attempt_site(site)

                if result and result.get('success'):
                    lock_acquired = await self._try_acquire_lock(site)

                    if lock_acquired:
                        self.locked_site = site
                        self.status = ExecutionStatus.SUCCESS
                        await self._emit_event(
                            'ORDER_CONFIRMED', site_name=site,
                            metadata={
                                'order_id': result.get('order_id'),
                                'price': result.get('price'),
                            }
                        )
                        duration = (datetime.now() - self.start_time).total_seconds()
                        return ExecutionResult(
                            status=ExecutionStatus.SUCCESS,
                            product_name=self.search_params.product_name,
                            site=site,
                            order_id=result.get('order_id'),
                            item_price=result.get('price'),
                            error_type='success',
                            duration_seconds=duration,
                        )
                    else:
                        logger.info(f"Lost lock race for {site}")
                        await self._emit_event('FAILED', site_name=site,
                            metadata={'reason': 'Lost lock race'})
                        self.status = ExecutionStatus.ABANDONED
                        duration = (datetime.now() - self.start_time).total_seconds()
                        return ExecutionResult(
                            status=ExecutionStatus.ABANDONED,
                            error='Another execution secured the item first',
                            error_type='lost_to_bots',
                            duration_seconds=duration,
                        )

                self.site_results[site] = result
                self.strategy.mark_attempted(site)
                self.strategy.mark_failed(site)

                should_continue = self.strategy.should_attempt_next_site({
                    'success': False,
                    'site': site,
                    'reason': result.get('error') if result else 'Unknown error',
                })

                if not should_continue:
                    break

            except Exception as e:
                logger.error(f"Error attempting {site}: {e}", exc_info=True)
                self.site_results[site] = {'error': str(e)}
                self.strategy.mark_attempted(site)
                self.strategy.mark_failed(site)

        # Determine best error type from site results
        error_type = self._best_error_type_from_results()

        self.status = ExecutionStatus.FAILED
        await self._emit_event('FAILED', metadata={
            'reason': 'All sites failed',
            'attempts': list(self.site_results.keys()),
        })
        duration = (datetime.now() - self.start_time).total_seconds()
        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            error='All sites exhausted',
            error_type=error_type,
            duration_seconds=duration,
        )

    async def _run_parallel(self, sites: List[str]) -> ExecutionResult:
        logger.info(f"Running parallel execution (sites: {sites})")

        tasks = [self._attempt_site_with_lock(site) for site in sites]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

        for task in done:
            try:
                result = task.result()
                if result['success']:
                    self.locked_site = result['site']
                    self.status = ExecutionStatus.SUCCESS
                    await self._emit_event('ORDER_CONFIRMED', site_name=result['site'],
                        metadata={'order_id': result.get('order_id'), 'price': result.get('price')})
                    duration = (datetime.now() - self.start_time).total_seconds()
                    return ExecutionResult(
                        status=ExecutionStatus.SUCCESS,
                        product_name=self.search_params.product_name,
                        site=result['site'],
                        order_id=result.get('order_id'),
                        item_price=result.get('price'),
                        error_type='success',
                        duration_seconds=duration,
                    )
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error in parallel task: {e}")

        self.status = ExecutionStatus.FAILED
        duration = (datetime.now() - self.start_time).total_seconds()
        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            error='All sites failed in parallel',
            error_type=self._best_error_type_from_results(),
            duration_seconds=duration,
        )

    async def _attempt_site_with_lock(self, site: str) -> Dict[str, Any]:
        try:
            result = await self._attempt_site(site)
            if not result or not result.get('success'):
                return {
                    'success': False, 'site': site,
                    'error': result.get('error') if result else 'Unknown error',
                    'error_type': result.get('error_type', 'unknown_error') if result else 'unknown_error',
                }
            lock_acquired = await self._try_acquire_lock(site)
            if lock_acquired:
                return {'success': True, 'site': site,
                        'order_id': result.get('order_id'), 'price': result.get('price')}
            return {'success': False, 'site': site, 'error': 'Lost lock race', 'error_type': 'lost_to_bots'}
        except Exception as e:
            return {'success': False, 'site': site, 'error': str(e), 'error_type': 'bot_crash'}

    async def _try_acquire_lock(self, site: str) -> bool:
        try:
            acquired = await self.procurement_lock.acquire(self.execution_id, ttl=600)
            if acquired:
                logger.info(f"Lock acquired for {site}")
                await self._emit_event('LOCK_ACQUIRED', site_name=site)
                return True
            else:
                logger.warning(f"Lock already held (site: {site})")
                await self._emit_event('LOCK_FAILED', site_name=site)
                return False
        except Exception as e:
            logger.error(f"Lock acquisition error: {e}", exc_info=True)
            return False

    def _best_error_type_from_results(self) -> str:
        """
        Pick the most meaningful error type from site results.
        Prefer non-refundable errors (item_not_found, out_of_stock) over
        refundable ones (bot_crash) since they give the user more info.
        """
        error_types = [
            r.get('error_type', 'unknown_error')
            for r in self.site_results.values()
            if isinstance(r, dict)
        ]
        if 'out_of_stock' in error_types:
            return 'out_of_stock'
        if 'item_not_found' in error_types:
            return 'item_not_found'
        if 'rate_limited' in error_types:
            return 'rate_limited'
        if 'bot_crash' in error_types:
            return 'bot_crash'
        return 'unknown_error'

    def get_stats(self) -> Dict[str, Any]:
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'execution_id': self.execution_id,
            'status': self.status.value,
            'duration_seconds': duration,
            'locked_site': self.locked_site,
            'site_results': self.site_results,
            'strategy': self.strategy.get_stats() if self.strategy else None,
            'event_history': self.event_history,
            'search_parameters': self.search_params.to_dict() if self.search_params else None,
        }

    def __str__(self):
        return (
            f"BotOrchestrator(execution_id={self.execution_id}, "
            f"status={self.status.value}, locked_site={self.locked_site})"
        )