# pop_up_bot/orchestrator.py

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Overall execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    ABANDONED = 'abandoned'


class SearchParameters:
    """Search parameters for procurement execution"""
    
    def __init__(
        self,
        product_name: str,
        size: str,
        color: Optional[str] = None,
        price_range: Optional[tuple] = None,  # (min, max)
    ):
        """
        Initialize search parameters.
        
        Args:
            product_name: Name of product to find
            size: Size to find
            color: Optional color preference
            price_range: Optional (min_price, max_price) tuple
        """
        self.product_name = product_name
        self.size = size
        self.color = color
        self.price_range = price_range or (0, float('inf'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'product_name': self.product_name,
            'size': self.size,
            'color': self.color,
            'price_range': self.price_range,
        }
    
    def __str__(self):
        return (
            f"SearchParameters({self.product_name}, size={self.size}, "
            f"color={self.color}, price={self.price_range})"
        )


class ExecutionResult:
    """Result of a procurement execution"""
    
    def __init__(
        self,
        status: ExecutionStatus,
        product_name: Optional[str] = None,
        site: Optional[str] = None,
        order_id: Optional[str] = None,
        item_price: Optional[float] = None,
        error: Optional[str] = None,
        duration_seconds: float = 0,
    ):
        self.status = status
        self.product_name = product_name
        self.site = site
        self.order_id = order_id
        self.item_price = item_price
        self.error = error
        self.duration_seconds = duration_seconds
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'status': self.status.value,
            'product_name': self.product_name,
            'site': self.site,
            'order_id': self.order_id,
            'item_price': self.item_price,
            'error': self.error,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def __str__(self):
        return f"ExecutionResult({self.status.value}, site={self.site}, order_id={self.order_id})"


class BotOrchestrator:
    """
    Bot Orchestrator - Manages bot execution, strategy selection, locking, and event emission.
    
    Responsibilities:
    - Initialize search parameters (product name, size, price range)
    - Apply ProcurementStrategy to determine site order
    - Create ProcurementLock to prevent double-purchases
    - Run scraper tasks for each site
    - Emit ProcurementEvent for each state transition
    - Handle race conditions (first site to cart + lock wins)
    - Log all attempts and results
    - Return success/failure with purchased item details
    
    Design:
    - Orchestrator coordinates but doesn't automate
    - SessionManager handles browser lifecycle
    - PlaywrightScraperEngine handles Playwright operations
    - SiteHandlers handle site-specific logic
    - ProcurementLock ensures only one wins
    - EventLogger tracks all events
    
    Usage:
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=strategy_factory,
            session_manager=session_manager,
            procurement_lock=procurement_lock,
            event_logger=event_logger,
        )
        
        result = await orchestrator.run(
            product_name='Air Jordan 1',
            size='US 10',
            color='Red',
            strategy_name='sequential',
            price_range=(100, 200),
        )
        
        print(f"Status: {result.status}")
        print(f"Order ID: {result.order_id}")
        print(f"Price: {result.item_price}")
    """
    
    def __init__(
        self,
        execution_id: int,
        strategy_factory,  # StrategyFactory
        session_manager,  # SessionManager
        procurement_lock,  # ProcurementLock
        event_logger,  # EventLogger
        cookie_manager=None,  # CookieManager
        proxy_manager=None,  # ProxyManager
    ):
        """
        Initialize BotOrchestrator.
        
        Args:
            execution_id: ID of ProcurementExecution
            strategy_factory: StrategyFactory for creating strategies
            session_manager: SessionManager for browser management
            procurement_lock: ProcurementLock for race condition prevention
            event_logger: EventLogger for event tracking
            cookie_manager: Optional CookieManager
            proxy_manager: Optional ProxyManager
        """
        self.execution_id = execution_id
        self.strategy_factory = strategy_factory
        self.session_manager = session_manager
        self.procurement_lock = procurement_lock
        self.event_logger = event_logger
        self.cookie_manager = cookie_manager
        self.proxy_manager = proxy_manager
        
        # Execution state
        self.status = ExecutionStatus.PENDING
        self.start_time = datetime.now()
        self.search_params = None  # Will be set in run()
        self.strategy = None
        self.site_results = {}  # site -> result
        self.locked_site = None  # Which site won the lock
        self.event_history = []  # Track all events
        
        logger.info(f"BotOrchestrator initialized (execution_id={execution_id})")
    
    async def run(
        self,
        product_name: str,
        size: str,
        color: Optional[str] = None,
        strategy_name: str = 'sequential',
        price_range: Optional[tuple] = None,
        **strategy_kwargs,
    ) -> ExecutionResult:
        """
        Run the procurement execution.
        
        Orchestrates the entire procurement flow:
        1. Initialize search parameters
        2. Create strategy based on parameters
        3. Execute sites based on strategy
        4. Handle race conditions with locking
        5. Emit events for state transitions
        6. Return success/failure result
        
        Args:
            product_name: Product to search for
            size: Size to find
            color: Optional color preference
            strategy_name: Strategy to use ('sequential', 'parallel', etc.)
            price_range: Optional (min_price, max_price) tuple
            **strategy_kwargs: Additional strategy parameters
        
        Returns:
            ExecutionResult with status and details
        
        Example:
            result = await orchestrator.run(
                product_name='Air Jordan 1',
                size='US 10',
                color='Red',
                strategy_name='sequential',
                price_range=(100, 200),
            )
        """
        try:
            self.status = ExecutionStatus.RUNNING
            
            # Initialize search parameters
            self.search_params = SearchParameters(
                product_name=product_name,
                size=size,
                color=color,
                price_range=price_range,
            )
            
            logger.info(f"Starting procurement: {self.search_params}")
            
            # Emit initialization event
            await self._emit_event(
                'INITIALIZED',
                metadata=self.search_params.to_dict() | {'strategy': strategy_name}
            )
            
            # Create strategy based on search parameters
            self.strategy = self.strategy_factory.create(
                strategy_name,
                **strategy_kwargs
            )
            
            logger.info(f"Strategy created: {self.strategy}")
            
            # Emit strategy selection event
            await self._emit_event(
                'STRATEGY_SELECTED',
                metadata={
                    'strategy': strategy_name,
                    'sites': self.strategy.get_site_order(),
                }
            )
            
            # Get site order from strategy
            sites = self.strategy.get_site_order()
            
            logger.info(f"Site order: {sites}")
            
            # Execute based on strategy type
            if strategy_name == 'parallel' or strategy_name == 'fastest':
                result = await self._run_parallel(sites)
            else:
                # Sequential or priority
                result = await self._run_sequential(sites)
            
            return result
        
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            
            await self._emit_event(
                'FAILED',
                metadata={'error': str(e)}
            )
            
            duration = (datetime.now() - self.start_time).total_seconds()
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=str(e),
                duration_seconds=duration,
            )
    
    async def _emit_event(
        self,
        event_type: str,
        site_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit an event for state transitions.
        
        Logs event locally and delegates to EventLogger if available.
        
        Args:
            event_type: Type of event (e.g., 'INITIALIZED', 'STRATEGY_SELECTED')
            site_name: Optional site name if event is site-specific
            metadata: Optional additional metadata
        
        Example:
            await orchestrator._emit_event(
                'ORDER_CONFIRMED',
                site_name='nike',
                metadata={'order_id': 'ORD-123', 'price': 169.99}
            )
        """
        event_entry = {
            'type': event_type,
            'site': site_name,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
        }
        
        self.event_history.append(event_entry)
        logger.info(f"Event emitted: {event_type} (site: {site_name})")
        
        # Emit to event logger if available
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
        """
        Run sites sequentially (try one, if fail try next).
        
        First site to add to cart AND acquire lock wins.
        """
        logger.info(f"Running sequential execution (sites: {sites})")
        
        for site in sites:
            logger.info(f"Attempting site: {site}")
            
            try:
                # Emit site selection
                await self._emit_event('SITE_SELECTED', site_name=site)
                
                # Try to procure from this site
                result = await self._attempt_site(site)
                
                # If successful, try to acquire lock
                if result and result.get('success'):
                    lock_acquired = await self._try_acquire_lock(site)
                    
                    if lock_acquired:
                        # We won! Return success
                        self.locked_site = site
                        self.status = ExecutionStatus.SUCCESS
                        
                        await self._emit_event(
                            'ORDER_CONFIRMED',
                            site_name=site,
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
                            duration_seconds=duration,
                        )
                    else:
                        # Another execution beat us to the lock
                        logger.info(f"Lost lock race for {site}")
                        await self._emit_event(
                            'FAILED',
                            site_name=site,
                            metadata={'reason': 'Lost lock race'},
                        )
                        self.status = ExecutionStatus.ABANDONED
                        
                        duration = (datetime.now() - self.start_time).total_seconds()
                        return ExecutionResult(
                            status=ExecutionStatus.ABANDONED,
                            error='Another execution secured the item first',
                            duration_seconds=duration,
                        )
                
                # Site attempt failed, log it and continue
                self.site_results[site] = result
                self.strategy.mark_attempted(site)
                self.strategy.mark_failed(site)
                
                # Check if we should continue
                should_continue = self.strategy.should_attempt_next_site({
                    'success': False,
                    'site': site,
                    'reason': result.get('error') if result else 'Unknown error',
                })
                
                if not should_continue:
                    logger.info("Strategy says stop - aborting")
                    break
            
            except Exception as e:
                logger.error(f"Error attempting {site}: {e}", exc_info=True)
                self.site_results[site] = {'error': str(e)}
                self.strategy.mark_attempted(site)
                self.strategy.mark_failed(site)
        
        # All sites failed
        logger.warning("All sites exhausted")
        self.status = ExecutionStatus.FAILED
        
        await self._emit_event(
            'FAILED',
            metadata={
                'reason': 'All sites failed',
                'attempts': list(self.site_results.keys()),
            }
        )
        
        duration = (datetime.now() - self.start_time).total_seconds()
        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            error='All sites exhausted',
            duration_seconds=duration,
        )
    
    async def _run_parallel(self, sites: List[str]) -> ExecutionResult:
        """
        Run sites in parallel (all at once, first to success wins).
        """
        logger.info(f"Running parallel execution (sites: {sites})")
        
        # Create tasks for all sites
        tasks = [
            self._attempt_site_with_lock(site)
            for site in sites
        ]
        
        # Return when first succeeds
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
        
        # Get result from first completed task
        for task in done:
            try:
                result = task.result()
                
                if result['success']:
                    self.locked_site = result['site']
                    self.status = ExecutionStatus.SUCCESS
                    
                    await self._emit_event(
                        'ORDER_CONFIRMED',
                        site_name=result['site'],
                        metadata={
                            'order_id': result.get('order_id'),
                            'price': result.get('price'),
                        }
                    )
                    
                    duration = (datetime.now() - self.start_time).total_seconds()
                    return ExecutionResult(
                        status=ExecutionStatus.SUCCESS,
                        product_name=self.search_params.product_name,
                        site=result['site'],
                        order_id=result.get('order_id'),
                        item_price=result.get('price'),
                        duration_seconds=duration,
                    )
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error in parallel task: {e}")
        
        # No site succeeded
        logger.warning("All parallel attempts failed")
        self.status = ExecutionStatus.FAILED
        
        duration = (datetime.now() - self.start_time).total_seconds()
        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            error='All sites failed in parallel',
            duration_seconds=duration,
        )
    
    async def _attempt_site(self, site: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to procure from a single site.
        
        Returns dict with success status and details, or None if failed.
        
        TODO:
        - Instantiate SiteHandler for this site
        - Call site_handler.find_product()
        - Call site_handler.select_size()
        - Call site_handler.add_to_cart()
        - Call site_handler.proceed_to_checkout()
        """
        try:
            logger.info(
                f"Attempting {site} for {self.search_params.product_name} "
                f"(size: {self.search_params.size})"
            )
            
            # For now, return mock success
            # TODO: Replace with actual site handler logic
            return {
                'success': True,
                'site': site,
                'product_name': self.search_params.product_name,
                'size': self.search_params.size,
                'order_id': f'ORD-{site.upper()}-12345',
                'price': 169.99,
            }
        
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
            }
    
    async def _attempt_site_with_lock(self, site: str) -> Dict[str, Any]:
        """
        Attempt site AND acquire lock (for parallel execution).
        
        Returns dict with success and lock status.
        """
        try:
            # Attempt the site
            result = await self._attempt_site(site)
            
            if not result or not result.get('success'):
                return {
                    'success': False,
                    'site': site,
                    'error': result.get('error') if result else 'Unknown error',
                }
            
            # Try to acquire lock
            lock_acquired = await self._try_acquire_lock(site)
            
            if lock_acquired:
                return {
                    'success': True,
                    'site': site,
                    'order_id': result.get('order_id'),
                    'price': result.get('price'),
                }
            else:
                return {
                    'success': False,
                    'site': site,
                    'error': 'Lost lock race',
                }
        
        except Exception as e:
            logger.error(f"Error in parallel attempt {site}: {e}")
            return {
                'success': False,
                'site': site,
                'error': str(e),
            }
    
    async def _try_acquire_lock(self, site: str) -> bool:
        """
        Try to acquire the lock for this execution.
        
        First execution to add to cart + acquire lock wins.
        
        Args:
            site: Site name (for logging)
        
        Returns:
            True if lock acquired, False if another execution has it
        """
        try:
            acquired = await self.procurement_lock.acquire(
                self.execution_id,
                ttl=600,  # 10 minute lock
            )
            
            if acquired:
                logger.info(f"Lock acquired for {site}")
                
                await self._emit_event(
                    'LOCK_ACQUIRED',
                    site_name=site,
                )
                
                return True
            else:
                logger.warning(f"Lock already held (site: {site})")
                
                await self._emit_event(
                    'LOCK_FAILED',
                    site_name=site,
                )
                
                return False
        
        except Exception as e:
            logger.error(f"Lock acquisition error: {e}", exc_info=True)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
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