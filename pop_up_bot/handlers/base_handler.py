# pop_up_bot/handlers/base.py

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SiteErrorType(str, Enum):
    """Types of errors that can occur on a site"""
    OUT_OF_STOCK = 'out_of_stock'
    CAPTCHA = 'captcha'
    BLOCKED = 'blocked'
    RATE_LIMITED = 'rate_limited'
    PAYMENT_FAILED = 'payment_failed'
    CHECKOUT_ERROR = 'checkout_error'
    PRODUCT_NOT_FOUND = 'product_not_found'
    NETWORK_ERROR = 'network_error'
    UNKNOWN = 'unknown'


class ExecutionStep(str, Enum):
    """Steps in the procurement flow"""
    INITIALIZED = 'initialized'
    VALIDATING_CONNECTION = 'validating_connection'
    SEARCHING_PRODUCT = 'searching_product'
    PRODUCT_FOUND = 'product_found'
    SELECTING_SIZE = 'selecting_size'
    ADDING_TO_CART = 'adding_to_cart'
    CART_CONFIRMED = 'cart_confirmed'
    PROCEEDING_CHECKOUT = 'proceeding_checkout'
    PAYMENT_PROCESSING = 'payment_processing'
    ORDER_COMPLETE = 'order_complete'
    FAILED = 'failed'


class Product:
    """Represents a product found on a site"""
    
    def __init__(
        self,
        product_id: str,
        name: str,
        price: float,
        available_sizes: list,
        product_url: str,
        in_stock: bool = True,
    ):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.available_sizes = available_sizes
        self.product_url = product_url
        self.in_stock = in_stock
    
    def __str__(self):
        return f"{self.name} (${self.price}) - ID: {self.product_id}"
    
    def __repr__(self):
        return self.__str__()


class CartItem:
    """Represents an item in the cart"""
    
    def __init__(
        self,
        product_id: str,
        product_name: str,
        size: str,
        quantity: int,
        price: float,
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.size = size
        self.quantity = quantity
        self.price = price
        self.total_price = price * quantity
    
    def __str__(self):
        return f"{self.product_name} (Size: {self.size}, Qty: {self.quantity})"


class BaseSiteHandler(ABC):
    """
    Abstract base class for site-specific handlers.
    
    Each site (Nike, Footlocker, etc.) gets its own handler that implements
    site-specific logic. The handler delegates automation to PlaywrightScraperEngine.
    
    Handlers ONLY implement site logic:
    - Product searching
    - Size selection
    - Cart operations
    - Checkout flow
    
    Handlers DO NOT manage:
    - Session/proxy/cookie logic (that's SessionManager/ProxyManager/CookieManager)
    - Low-level Playwright operations (that's PlaywrightScraperEngine)
    - Event logging (that's EventLogger)
    
    Design Pattern:
    1. Handler receives engine, managers, and loggers
    2. Handler implements abstract methods
    3. Handler focuses only on site-specific selectors/flows
    4. Easy to test, easy to add new sites
    
    Usage:
        handler = NikeSiteHandler(
            engine=scraper_engine,
            session_manager=session_manager,
            cookie_manager=cookie_manager,
            event_logger=event_logger,
        )
        
        product = await handler.find_product('Air Jordan 1', 'US 10', 'Red')
        success = await handler.add_to_cart(product.product_id, 'US 10', 1)
        await handler.proceed_to_checkout()
    """
    
    def __init__(
        self,
        engine,  # PlaywrightScraperEngine
        session_manager=None,
        cookie_manager=None,
        event_logger=None,
    ):
        """
        Initialize BaseSiteHandler.
        
        Args:
            engine: PlaywrightScraperEngine instance for automation
            session_manager: SessionManager for browser management
            cookie_manager: CookieManager for cookie persistence
            event_logger: EventLogger for event tracking
        """
        self.engine = engine
        self.session_manager = session_manager
        self.cookie_manager = cookie_manager
        self.event_logger = event_logger
        
        # Handler state
        self.current_step = ExecutionStep.INITIALIZED
        self.product_found = None
        self.cart_item = None
        self.execution_history = []
        self.error_log = []
        self.start_time = datetime.now()
        
        logger.info(f"Handler initialized: {self.site_name}")
    
    # ========================================================================
    # Site Configuration (must be set by subclasses)
    # ========================================================================
    
    @property
    @abstractmethod
    def site_name(self) -> str:
        """Return the name of the site (e.g., 'nike', 'footlocker')"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL of the site (e.g., 'https://nike.com')"""
        pass
    
    # ========================================================================
    # Abstract Methods (must implement in subclasses)
    # ========================================================================
    
    @abstractmethod
    async def validate_site_connection(self) -> bool:
        """
        Validate that we can connect to the site.
        
        Should check:
        - Site loads
        - No blocking/cloudflare
        - Basic page elements present
        
        Returns:
            True if site is accessible
        
        Example:
            async def validate_site_connection(self):
                await self.engine.navigate(self.base_url)
                return await self.engine.is_element_visible('div.site-header')
        """
        pass
    
    @abstractmethod
    async def find_product(
        self,
        product_name: str,
        size: str,
        color: Optional[str] = None,
    ) -> Optional[Product]:
        """
        Search for a product on the site.
        
        Args:
            product_name: Name of product to find
            size: Size to look for
            color: Optional color preference
        
        Returns:
            Product object if found, None if not found/out of stock
        
        Example:
            async def find_product(self, product_name, size, color=None):
                await self.engine.navigate(f'{self.base_url}/search')
                await self.engine.type('input[name="q"]', product_name)
                await self.engine.click('button[name="search"]')
                
                # Wait for results
                await self.engine.wait_for('div.product-results')
                
                # Find matching product
                product_url = await self.engine.extract_attribute(
                    'a.product-link:first-child',
                    'href'
                )
                
                return Product(
                    product_id='123',
                    name=product_name,
                    price=169.99,
                    available_sizes=['8', '9', '10', '11'],
                    product_url=product_url,
                    in_stock=True,
                )
        """
        pass
    
    @abstractmethod
    async def select_size(self, size: str) -> bool:
        """
        Select a size for the current product.
        
        Args:
            size: Size to select (e.g., 'US 10')
        
        Returns:
            True if size was selected successfully
        
        Example:
            async def select_size(self, size):
                await self.engine.click(f'input[value="{size}"]')
                await self.engine.wait_for('button[name="add-to-cart"]:enabled')
                return True
        """
        pass
    
    @abstractmethod
    async def add_to_cart(
        self,
        product_id: str,
        size: str,
        quantity: int = 1,
    ) -> bool:
        """
        Add product to cart.
        
        Args:
            product_id: ID of product
            size: Size to add
            quantity: Quantity to add
        
        Returns:
            True if successfully added to cart
        
        Example:
            async def add_to_cart(self, product_id, size, quantity=1):
                await self.select_size(size)
                await self.engine.click('button[name="add-to-cart"]')
                await self.engine.wait_for('div.cart-confirmation')
                return True
        """
        pass
    
    @abstractmethod
    async def check_cart(self) -> Optional[CartItem]:
        """
        Check what's currently in the cart.
        
        Returns:
            CartItem if item is in cart, None if cart is empty
        
        Example:
            async def check_cart(self):
                await self.engine.navigate(f'{self.base_url}/cart')
                product_name = await self.engine.extract_text('span.product-name')
                if product_name:
                    return CartItem(
                        product_id='123',
                        product_name=product_name,
                        size='US 10',
                        quantity=1,
                        price=169.99,
                    )
                return None
        """
        pass
    
    @abstractmethod
    async def is_item_in_stock(self) -> bool:
        """
        Check if the current item is in stock.
        
        Returns:
            True if in stock
        
        Example:
            async def is_item_in_stock(self):
                in_stock_badge = await self.engine.extract_text('span.in-stock')
                return in_stock_badge is not None
        """
        pass
    
    @abstractmethod
    async def proceed_to_checkout(self) -> bool:
        """
        Navigate to and proceed through checkout.
        
        Returns:
            True if successfully at checkout page
        
        Example:
            async def proceed_to_checkout(self):
                await self.engine.click('button[name="checkout"]')
                await self.engine.wait_for('div.checkout-form')
                return True
        """
        pass
    
    # ========================================================================
    # Common Helper Methods
    # ========================================================================
    
    async def set_step(self, step: ExecutionStep) -> None:
        """
        Set current execution step and log it.
        
        Args:
            step: Current step in the flow
        """
        self.current_step = step
        self.execution_history.append({
            'step': step.value,
            'timestamp': datetime.now().isoformat(),
        })
        logger.info(f"[{self.site_name}] Step: {step.value}")
        
        # Emit event if logger available
        if self.event_logger:
            await self.event_logger.emit_step_change(step.value)
    
    async def log_error(
        self,
        error_type: SiteErrorType,
        message: str,
        details: Optional[Dict] = None,
    ) -> None:
        """
        Log an error that occurred.
        
        Args:
            error_type: Type of error
            message: Error message
            details: Optional additional details
        """
        error_entry = {
            'type': error_type.value,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
        }
        self.error_log.append(error_entry)
        logger.error(f"[{self.site_name}] Error: {message}")
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary with execution info
        """
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'site': self.site_name,
            'duration_seconds': duration,
            'current_step': self.current_step.value,
            'steps_completed': len(self.execution_history),
            'errors': len(self.error_log),
            'product_found': self.product_found is not None,
            'item_in_cart': self.cart_item is not None,
            'execution_history': self.execution_history,
            'error_log': self.error_log,
        }
    
    # ========================================================================
    # Error Detection (can override in subclasses for site-specific logic)
    # ========================================================================
    
    async def detect_out_of_stock(self) -> bool:
        """
        Detect if product is out of stock.
        
        Override in subclass with site-specific detection.
        
        Returns:
            True if out of stock
        """
        # Generic implementation - check for common OOS indicators
        oos_indicators = [
            'out of stock',
            'sold out',
            'coming soon',
            'not available',
        ]
        
        page_text = await self.engine.execute_js(
            'return document.body.innerText.toLowerCase()'
        )
        
        return any(indicator in page_text for indicator in oos_indicators)
    
    async def detect_captcha(self) -> bool:
        """
        Detect if site is showing captcha.
        
        Override in subclass with site-specific detection.
        
        Returns:
            True if captcha detected
        """
        # Generic implementation - check for common captcha elements
        captcha_selectors = [
            'iframe[src*="captcha"]',
            'div[class*="captcha"]',
            'div[id*="recaptcha"]',
        ]
        
        for selector in captcha_selectors:
            if await self.engine.is_element_visible(selector):
                return True
        
        return False
    
    async def detect_blocked(self) -> bool:
        """
        Detect if we're blocked/rate-limited by the site.
        
        Override in subclass with site-specific detection.
        
        Returns:
            True if blocked
        """
        # Generic implementation - check for common block indicators
        title = await self.engine.get_title()
        
        block_indicators = [
            'access denied',
            'blocked',
            'restricted',
            'too many requests',
            '429',
            '403',
        ]
        
        return any(indicator in title.lower() for indicator in block_indicators)
    
    # ========================================================================
    # Lifecycle
    # ========================================================================
    
    async def close(self) -> None:
        """Close handler and cleanup resources"""
        logger.info(f"Handler closing: {self.site_name}")
        # Handlers don't manage pages - that's SessionManager's job
        # But they can cleanup their own state
        self.product_found = None
        self.cart_item = None
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.site_name})"
    
    def __repr__(self):
        return self.__str__()