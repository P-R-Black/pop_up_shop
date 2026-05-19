# pop_up_bot/managers/session_manager.py

import asyncio
import logging
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages Playwright browser instances and page lifecycles.
    
    Responsibilities:
    - Create and cache browser instances per site
    - Manage browser contexts (isolated sessions)
    - Handle browser failures and recovery
    - Provide anti-detection features
    - Clean up resources
    
    Usage:
        session_manager = SessionManager()
        page = await session_manager.get_page('nike')
        await page.goto('https://nike.com')
        await page.close()
    """
    
    def __init__(
        self,
        headless: bool = True,
        anti_detection: bool = True,
        viewport: Optional[Dict] = None,
        user_agent_rotation: bool = False,
        timeout_ms: int = 30000,
    ):
        """
        Initialize SessionManager.
        
        Args:
            headless: Run browser in headless mode (no GUI)
            anti_detection: Enable stealth mode to hide automation
            viewport: Custom viewport size {'width': 1920, 'height': 1080}
            user_agent_rotation: Rotate user agents between requests
            timeout_ms: Default timeout for all operations
        """
        self.headless = headless
        self.anti_detection = anti_detection
        self.viewport = viewport or {'width': 1920, 'height': 1080}
        self.user_agent_rotation = user_agent_rotation
        self.timeout_ms = timeout_ms
        
        # Browser instances cache
        self.browsers: Dict[str, Browser] = {}
        
        # Track context count per browser
        self.context_count: Dict[str, int] = {}
        
        # Playwright instance
        self.playwright = None
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
        ]
        self.ua_index = 0
        
        logger.info(f"SessionManager initialized: headless={headless}, anti_detection={anti_detection}")
    
    async def initialize(self):
        """
        Initialize Playwright. Must be called before using SessionManager.
        
        Usage:
            session_manager = SessionManager()
            await session_manager.initialize()
        """
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            logger.info("Playwright initialized")
    
    async def shutdown(self):
        """
        Clean up all browsers and Playwright instance.
        
        Usage:
            await session_manager.shutdown()
        """
        await self.close_all()
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            logger.info("Playwright shutdown")
    
    async def get_browser(
        self,
        site_name: str,
        browser_type: str = 'chromium'
    ) -> Browser:
        """
        Get or create a browser for a site.
        
        Args:
            site_name: Site identifier (e.g., 'nike', 'footlocker')
            browser_type: 'chromium', 'firefox', or 'webkit'
        
        Returns:
            Playwright Browser instance
        
        Behavior:
            - First call: Creates new browser, caches it
            - Subsequent calls: Returns cached browser
            - Dead browsers: Auto-detects and recreates
        
        Example:
            browser = await session_manager.get_browser('nike')
        """
        if self.playwright is None:
            await self.initialize()
        
        # Check if browser exists and is alive
        if site_name in self.browsers:
            if await self._is_browser_alive(self.browsers[site_name]):
                logger.debug(f"Reusing existing {site_name} browser")
                return self.browsers[site_name]
            else:
                logger.warning(f"Browser for {site_name} is dead, recreating")
                await self._close_browser_instance(site_name)
        
        # Create new browser
        logger.info(f"Creating new {browser_type} browser for {site_name}")
        browser = await self._create_browser(browser_type)
        self.browsers[site_name] = browser
        self.context_count[site_name] = 0
        
        logger.info(f"Browser created for {site_name}")
        return browser
    
    async def get_page(self, site_name: str) -> Page:
        """
        Get a fresh page for a site.
        
        Creates a new context (isolated session with fresh cookies/cache)
        and returns a page in that context.
        
        Args:
            site_name: Site identifier
        
        Returns:
            Playwright Page instance
        
        Example:
            page = await session_manager.get_page('nike')
            await page.goto('https://nike.com')
            # ... use page ...
            await page.close()
        """
        context = await self.get_context(site_name)
        page = await context.new_page()
        
        logger.debug(f"Page created for {site_name}")
        return page
    
    async def get_context(
        self,
        site_name: str,
        user_data_dir: Optional[str] = None
    ) -> BrowserContext:
        """
        Get a fresh browser context for a site.
        
        A context is an isolated session with:
        - Separate cookies
        - Separate cache
        - Separate local storage
        
        Useful for:
        - Running multiple correlated actions (search → add to cart → checkout)
        - Simulating multiple user sessions
        - Isolating failed attempts
        
        Args:
            site_name: Site identifier
            user_data_dir: Optional persistent user data directory
        
        Returns:
            Playwright BrowserContext instance
        
        Example:
            # Scenario: Search, add to cart, checkout in same session
            context = await session_manager.get_context('nike')
            
            page1 = await context.new_page()
            await page1.goto('https://nike.com/search')
            # ... search for product ...
            
            page2 = await context.new_page()
            await page2.goto('https://nike.com/cart')
            # ... add to cart (uses same cookies as page1) ...
            
            await context.close()
        """
        browser = await self.get_browser(site_name)
        
        context_args = {
            'viewport': self.viewport,
            'ignore_https_errors': True,
        }
        
        # Add user agent
        if self.user_agent_rotation:
            user_agent = self._get_next_user_agent()
            context_args['user_agent'] = user_agent
            logger.debug(f"Using user agent for {site_name}: {user_agent[:50]}...")
        
        # Add persistent data dir if provided
        if user_data_dir:
            context_args['storage_state'] = user_data_dir
        
        context = await browser.new_context(**context_args)
        
        # Add stealth scripts if anti_detection enabled
        if self.anti_detection:
            await self._apply_stealth_mode(context)
        
        # Increment context counter
        self.context_count[site_name] = self.context_count.get(site_name, 0) + 1
        
        logger.debug(f"Context created for {site_name} (count: {self.context_count[site_name]})")
        
        return context
    
    async def close_browser(self, site_name: str) -> None:
        """
        Close a specific browser and clean up.
        
        Args:
            site_name: Site identifier
        
        Example:
            await session_manager.close_browser('nike')
        """
        await self._close_browser_instance(site_name)
    
    async def close_all(self) -> None:
        """
        Close all browsers and clean up all resources.
        
        Example:
            await session_manager.close_all()
        """
        logger.info(f"Closing {len(self.browsers)} browsers")
        
        for site_name in list(self.browsers.keys()):
            await self._close_browser_instance(site_name)
        
        self.browsers.clear()
        self.context_count.clear()
        logger.info("All browsers closed")
    
    async def is_browser_alive(self, site_name: str) -> bool:
        """
        Check if a browser is still alive and responsive.
        
        Args:
            site_name: Site identifier
        
        Returns:
            bool - True if browser is alive, False otherwise
        
        Example:
            if await session_manager.is_browser_alive('nike'):
                print("Browser is working")
            else:
                print("Browser crashed, will be recreated")
        """
        if site_name not in self.browsers:
            return False
        
        return await self._is_browser_alive(self.browsers[site_name])
    
    def get_browser_count(self) -> int:
        """Get number of active browsers"""
        return len(self.browsers)
    
    def get_context_count(self, site_name: str) -> int:
        """Get number of contexts created for a site"""
        return self.context_count.get(site_name, 0)
    
    # ========================================================================
    # Private Methods
    # ========================================================================
    
    async def _create_browser(self, browser_type: str = 'chromium') -> Browser:
        """
        Create a new browser with anti-detection and anti-bot measures.
        
        Args:
            browser_type: 'chromium', 'firefox', or 'webkit'
        
        Returns:
            Playwright Browser instance
        """
        if self.playwright is None:
            await self.initialize()
        
        # Base launch arguments
        args = [
            '--disable-blink-features=AutomationControlled',  # Hide automation
            '--start-maximized',
            '--disable-dev-shm-usage',  # Prevent memory issues
            '--disable-gpu',
            '--no-first-run',
            '--no-default-browser-check',
        ]
        
        # Additional stealth args
        if self.anti_detection:
            args.extend([
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Don't load images (faster)
            ])
        
        # Get appropriate browser launcher
        if browser_type == 'chromium':
            launcher = self.playwright.chromium
        elif browser_type == 'firefox':
            launcher = self.playwright.firefox
        elif browser_type == 'webkit':
            launcher = self.playwright.webkit
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")
        
        # Launch browser
        browser = await launcher.launch(
            headless=self.headless,
            args=args,
        )
        
        logger.info(f"Browser created: {browser_type}")
        
        return browser
    
    async def _apply_stealth_mode(self, context: BrowserContext) -> None:
        """
        Apply stealth scripts to hide that we're using Playwright.
        
        This is critical to avoid detection by anti-bot services.
        """
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
    
    def _get_next_user_agent(self) -> str:
        """Get next user agent in rotation"""
        ua = self.user_agents[self.ua_index]
        self.ua_index = (self.ua_index + 1) % len(self.user_agents)
        return ua
    
    async def _is_browser_alive(self, browser: Browser) -> bool:
        """
        Check if browser is still responsive.
        
        Returns True if browser can execute a simple command.
        """
        try:
            # Try to get browser version (simple operation)
            version = browser.version
            return version is not None
        except Exception as e:
            logger.warning(f"Browser health check failed: {e}")
            return False
    
    async def _close_browser_instance(self, site_name: str) -> None:
        """Close a specific browser instance"""
        if site_name not in self.browsers:
            return
        
        try:
            browser = self.browsers[site_name]
            await browser.close()
            logger.info(f"Browser closed for {site_name}")
        except Exception as e:
            logger.error(f"Error closing browser for {site_name}: {e}")
        finally:
            del self.browsers[site_name]
            if site_name in self.context_count:
                del self.context_count[site_name]
    
    async def __aenter__(self):
        """Async context manager support"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager cleanup"""
        await self.shutdown()