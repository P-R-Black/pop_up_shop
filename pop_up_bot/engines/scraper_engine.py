# pop_up_bot/engines/scraper_engine.py

import logging
import asyncio
import random
from typing import Optional, Dict, Any, List
from datetime import datetime

from playwright.async_api import Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class PlaywrightScraperEngine:
    """
    Low-level Playwright operations engine.
    
    Provides site-agnostic automation for:
    - Navigation and page interaction
    - Element waiting and extraction
    - Anti-detection measures
    - Error handling and retries
    - Screenshot capture for debugging
    
    Site-specific logic (selectors, flows) goes in SiteHandlers.
    
    Features:
    - Async/await support (for Celery integration)
    - Human-like delays and behavior
    - Comprehensive error handling
    - Screenshot capture on errors
    - Network monitoring
    
    Usage:
        engine = PlaywrightScraperEngine(page, event_logger)
        
        await engine.navigate('https://nike.com/product/123')
        await engine.wait_for('input[name="size"]')
        await engine.click('input[value="US 10"]')
        await engine.click('button[name="add-to-cart"]')
        
        # Extract data
        title = await engine.extract_text('h1.product-name')
        price = await engine.extract_text('span.price')
    """
    
    def __init__(
        self,
        page: Page,
        event_logger=None,
        default_timeout: int = 30,
        default_delay_ms: int = 500,
        max_retries: int = 3,
    ):
        """
        Initialize PlaywrightScraperEngine.
        
        Args:
            page: Playwright Page object
            event_logger: Optional EventLogger for event tracking
            default_timeout: Default timeout for operations (seconds)
            default_delay_ms: Default delay between actions (milliseconds)
            max_retries: Max retries for failed operations
        """
        self.page = page
        self.event_logger = event_logger
        self.default_timeout = default_timeout
        self.default_delay_ms = default_delay_ms
        self.max_retries = max_retries
        
        self.action_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        
        logger.info(
            f"PlaywrightScraperEngine initialized "
            f"(timeout={default_timeout}s, retries={max_retries})"
        )
    
    # ========================================================================
    # Navigation
    # ========================================================================
    
    async def navigate(
        self,
        url: str,
        wait_until: str = 'load',
        timeout: Optional[int] = None,
    ) -> None:
        """
        Navigate to a URL with anti-detection measures.
        
        Args:
            url: URL to navigate to
            wait_until: 'load', 'domcontentloaded', or 'networkidle'
            timeout: Timeout in seconds (uses default if None)
        
        Raises:
            TimeoutError: If navigation times out
        
        Example:
            await engine.navigate('https://nike.com/product/123')
        """
        timeout_ms = (timeout or self.default_timeout) * 1000
        
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            self.action_count += 1
            logger.info(f"Navigated to: {url}")
            
            # Emit event
            if self.event_logger:
                await self.event_logger.emit_navigation(url)
        
        except PlaywrightTimeoutError as e:
            self.error_count += 1
            logger.error(f"Navigation timeout to {url}: {e}")
            await self._capture_screenshot(f"navigation_error_{self.error_count}")
            raise
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Navigation error to {url}: {e}", exc_info=True)
            await self._capture_screenshot(f"navigation_error_{self.error_count}")
            raise
    
    # ========================================================================
    # Waiting
    # ========================================================================
    
    async def wait_for(
        self,
        selector: str,
        timeout: Optional[int] = None,
        visible: bool = False,
    ) -> None:
        """
        Wait for an element to appear in DOM.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in seconds
            visible: If True, wait for element to be visible
        
        Raises:
            TimeoutError: If element doesn't appear
        
        Example:
            await engine.wait_for('input[name="size"]', visible=True)
        """
        timeout_ms = (timeout or self.default_timeout) * 1000
        
        try:
            if visible:
                await self.page.locator(selector).wait_for(
                    state='visible',
                    timeout=timeout_ms,
                )
            else:
                await self.page.locator(selector).wait_for(
                    state='attached',
                    timeout=timeout_ms,
                )
            
            logger.debug(f"Found element: {selector}")
        
        except PlaywrightTimeoutError as e:
            self.error_count += 1
            logger.error(f"Wait timeout for {selector}: {e}")
            await self._capture_screenshot(f"wait_error_{self.error_count}")
            raise
    
    async def wait_for_navigation(
        self,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Wait for page navigation to complete.
        
        Args:
            timeout: Timeout in seconds
        
        Example:
            # Click button that causes navigation
            await engine.click('a.checkout-link')
            await engine.wait_for_navigation()
        """
        timeout_ms = (timeout or self.default_timeout) * 1000
        
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout_ms)
            logger.debug("Navigation completed")
        
        except PlaywrightTimeoutError as e:
            self.error_count += 1
            logger.error(f"Navigation wait timeout: {e}")
            raise
    
    # ========================================================================
    # Clicking
    # ========================================================================
    
    async def click(
        self,
        selector: str,
        retry: bool = True,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Click an element with retry logic.
        
        Args:
            selector: CSS selector of element to click
            retry: If True, retry on failure
            timeout: Timeout in seconds
        
        Raises:
            Exception: If click fails after retries
        
        Example:
            await engine.click('button[name="add-to-cart"]')
        """
        timeout_ms = (timeout or self.default_timeout) * 1000
        
        for attempt in range(self.max_retries if retry else 1):
            try:
                # Add human-like delay before clicking
                await self._human_delay()
                
                # Scroll element into view
                await self.page.locator(selector).scroll_into_view_if_needed()
                
                # Click with human-like behavior
                await self.page.locator(selector).click(
                    timeout=timeout_ms,
                    force=False,  # Don't force - wait for element to be clickable
                )
                
                self.action_count += 1
                logger.info(f"Clicked: {selector}")
                return
            
            except Exception as e:
                self.error_count += 1
                
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Click failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Click failed after {self.max_retries} attempts: {e}")
                    await self._capture_screenshot(f"click_error_{self.error_count}")
                    raise
    
    # ========================================================================
    # Typing
    # ========================================================================
    
    async def type(
        self,
        selector: str,
        text: str,
        delay: int = 50,
        clear_first: bool = True,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Type text into an input field with human-like typing speed.
        
        Args:
            selector: CSS selector of input field
            text: Text to type
            delay: Delay between keystrokes in milliseconds (human-like)
            clear_first: If True, clear field before typing
            timeout: Timeout in seconds
        
        Example:
            await engine.type('input[name="search"]', 'Air Jordan 1', delay=50)
        """
        timeout_ms = (timeout or self.default_timeout) * 1000
        
        try:
            locator = self.page.locator(selector)
            
            # Scroll into view
            await locator.scroll_into_view_if_needed()
            
            # Clear field if requested
            if clear_first:
                await locator.clear()
            
            # Add human-like delay before typing
            await self._human_delay()
            
            # Type with realistic delays between keystrokes
            await locator.type(text, delay=delay, timeout=timeout_ms)
            
            self.action_count += 1
            logger.info(f"Typed into {selector}: {text[:20]}...")
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Type error on {selector}: {e}", exc_info=True)
            await self._capture_screenshot(f"type_error_{self.error_count}")
            raise
    
    # ========================================================================
    # Extraction
    # ========================================================================
    
    async def extract_text(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Extract text content from an element.
        
        Args:
            selector: CSS selector
            timeout: Timeout in seconds
        
        Returns:
            Text content or None if element not found
        
        Example:
            title = await engine.extract_text('h1.product-name')
        """
        try:
            text = await self.page.locator(selector).text_content(
                timeout=(timeout or self.default_timeout) * 1000
            )
            logger.debug(f"Extracted text from {selector}: {text[:50] if text else 'None'}...")
            return text
        
        except PlaywrightTimeoutError:
            logger.warning(f"Element not found: {selector}")
            return None
        
        except Exception as e:
            logger.error(f"Extract error on {selector}: {e}")
            return None
    
    async def extract_attribute(
        self,
        selector: str,
        attribute: str,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Extract attribute value from an element.
        
        Args:
            selector: CSS selector
            attribute: Attribute name (e.g., 'href', 'data-id')
            timeout: Timeout in seconds
        
        Returns:
            Attribute value or None if not found
        
        Example:
            price = await engine.extract_attribute('span.price', 'data-value')
        """
        try:
            value = await self.page.locator(selector).get_attribute(
                attribute,
                timeout=(timeout or self.default_timeout) * 1000
            )
            logger.debug(f"Extracted {attribute} from {selector}: {value}")
            return value
        
        except PlaywrightTimeoutError:
            logger.warning(f"Element not found: {selector}")
            return None
        
        except Exception as e:
            logger.error(f"Attribute extract error on {selector}: {e}")
            return None
    
    async def extract_all_text(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> List[str]:
        """
        Extract text from multiple matching elements.
        
        Args:
            selector: CSS selector
            timeout: Timeout in seconds
        
        Returns:
            List of text contents
        
        Example:
            sizes = await engine.extract_all_text('div.size-option')
        """
        try:
            elements = await self.page.locator(selector).all()
            texts = []
            
            for element in elements:
                text = await element.text_content()
                if text:
                    texts.append(text.strip())
            
            logger.debug(f"Extracted {len(texts)} texts from {selector}")
            return texts
        
        except Exception as e:
            logger.error(f"Extract all error on {selector}: {e}")
            return []
    
    async def get_inner_html(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Get inner HTML of an element.
        
        Args:
            selector: CSS selector
            timeout: Timeout in seconds
        
        Returns:
            Inner HTML or None
        
        Example:
            html = await engine.get_inner_html('div.product-info')
        """
        try:
            html = await self.page.locator(selector).inner_html(
                timeout=(timeout or self.default_timeout) * 1000
            )
            return html
        
        except Exception as e:
            logger.error(f"Get HTML error on {selector}: {e}")
            return None
    
    # ========================================================================
    # Page State
    # ========================================================================
    
    async def get_url(self) -> str:
        """Get current page URL"""
        return self.page.url
    
    async def get_title(self) -> str:
        """Get current page title"""
        return await self.page.title()
    
    async def is_element_visible(self, selector: str) -> bool:
        """Check if element is visible"""
        try:
            return await self.page.locator(selector).is_visible()
        except Exception:
            return False
    
    async def is_element_enabled(self, selector: str) -> bool:
        """Check if element is enabled (for buttons, inputs)"""
        try:
            return await self.page.locator(selector).is_enabled()
        except Exception:
            return False
    
    async def element_count(self, selector: str) -> int:
        """Count matching elements"""
        try:
            return await self.page.locator(selector).count()
        except Exception:
            return 0
    
    # ========================================================================
    # JavaScript Execution
    # ========================================================================
    
    async def execute_js(
        self,
        script: str,
        args: Optional[List[Any]] = None,
    ) -> Any:
        """
        Execute JavaScript on the page.
        
        Args:
            script: JavaScript code
            args: Arguments to pass to script
        
        Returns:
            Return value from script
        
        Example:
            result = await engine.execute_js(
                'return document.querySelector(".price").innerText'
            )
        """
        try:
            result = await self.page.evaluate(script, args or [])
            logger.debug(f"JavaScript executed: {script[:50]}...")
            return result
        
        except Exception as e:
            logger.error(f"JavaScript error: {e}")
            raise
    
    # ========================================================================
    # Anti-Detection
    # ========================================================================
    
    async def _human_delay(self) -> None:
        """Add human-like delay before action"""
        # Random delay between 200-1000ms with distribution skew
        delay = random.gauss(self.default_delay_ms, 200)
        delay = max(100, min(2000, delay))  # Clamp between 100-2000ms
        await asyncio.sleep(delay / 1000)
    
    async def scroll_to_element(self, selector: str) -> None:
        """Scroll naturally to element (not instant)"""
        await self.page.locator(selector).scroll_into_view_if_needed()
        await self._human_delay()
    
    async def random_scroll(self, amount: int = 500) -> None:
        """
        Scroll page randomly (simulate human browsing).
        
        Args:
            amount: Pixels to scroll
        """
        await self.page.evaluate(f"window.scrollBy(0, {amount})")
        await self._human_delay()
    
    async def hover(self, selector: str) -> None:
        """Hover over element (human-like behavior)"""
        await self.page.locator(selector).hover()
        await self._human_delay()
    
    # ========================================================================
    # Debugging
    # ========================================================================
    
    async def _capture_screenshot(self, name: str) -> None:
        """
        Capture screenshot for debugging.
        
        Args:
            name: Screenshot name (will be timestamped)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"debug_{name}_{timestamp}.png"
            
            await self.page.screenshot(path=f"/tmp/{filename}")
            logger.info(f"Screenshot saved: {filename}")
        
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
    
    async def print_page_content(self, selector: Optional[str] = None) -> None:
        """
        Print page content for debugging.
        
        Args:
            selector: Optional selector to print specific element
        """
        try:
            if selector:
                content = await self.get_inner_html(selector)
            else:
                content = await self.page.content()
            
            logger.debug(f"Page content:\n{content[:500]}...")
        
        except Exception as e:
            logger.error(f"Print content error: {e}")
    
    # ========================================================================
    # Lifecycle
    # ========================================================================
    
    async def close(self) -> None:
        """Close page"""
        try:
            await self.page.close()
            logger.info(f"Page closed (actions: {self.action_count}, errors: {self.error_count})")
        except Exception as e:
            logger.error(f"Close error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'actions': self.action_count,
            'errors': self.error_count,
            'duration_seconds': duration,
            'actions_per_second': self.action_count / duration if duration > 0 else 0,
        }
    
    def __str__(self):
        stats = self.get_stats()
        return (
            f"PlaywrightScraperEngine("
            f"actions={stats['actions']}, "
            f"errors={stats['errors']}, "
            f"duration={stats['duration_seconds']:.1f}s"
            f")"
        )