# pop_up_bot/managers/examples.py

"""
Examples and usage patterns for SessionManager
"""

import asyncio
from session_manager import SessionManager


# ============================================================================
# EXAMPLE 1: Basic Usage
# ============================================================================

async def example_basic_usage():
    """Simple page navigation"""
    session_manager = SessionManager(headless=True, anti_detection=True)
    await session_manager.initialize()
    
    try:
        # Get a page for Nike
        page = await session_manager.get_page('nike')
        
        # Use it
        await page.goto('https://www.nike.com', wait_until='load')
        title = await page.title()
        print(f"Nike page title: {title}")
        
        # Clean up
        await page.close()
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# EXAMPLE 2: Reusing Browser (Efficient)
# ============================================================================

async def example_browser_reuse():
    """Demonstrate browser reuse - efficient for multiple attempts"""
    session_manager = SessionManager(headless=True, anti_detection=True)
    await session_manager.initialize()
    
    try:
        # First request - browser created
        print(f"Active browsers: {session_manager.get_browser_count()}")
        page1 = await session_manager.get_page('nike')
        await page1.goto('https://www.nike.com')
        await page1.close()
        print("First request done, browser still alive")
        
        # Second request - browser reused
        print(f"Active browsers: {session_manager.get_browser_count()}")
        page2 = await session_manager.get_page('nike')
        await page2.goto('https://www.nike.com/search')
        await page2.close()
        print("Second request done, same browser used")
        
        # Contexts created but browser is reused!
        print(f"Contexts created for nike: {session_manager.get_context_count('nike')}")
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# EXAMPLE 3: Parallel Site Attempts
# ============================================================================

async def example_parallel_execution():
    """Attempt to scrape multiple sites simultaneously"""
    session_manager = SessionManager(headless=True, anti_detection=True)
    await session_manager.initialize()
    
    async def scrape_site(site_name: str, url: str):
        """Scrape a single site"""
        try:
            page = await session_manager.get_page(site_name)
            await page.goto(url, wait_until='load', timeout=10000)
            title = await page.title()
            print(f"✓ {site_name}: {title}")
            await page.close()
            return True
        except Exception as e:
            print(f"✗ {site_name}: {e}")
            return False
    
    try:
        # Run all sites in parallel
        results = await asyncio.gather(
            scrape_site('nike', 'https://www.nike.com'),
            scrape_site('footlocker', 'https://www.footlocker.com'),
            scrape_site('adidas', 'https://www.adidas.com'),
            return_exceptions=True
        )
        
        print(f"\nResults: {results}")
        print(f"Total browsers created: {session_manager.get_browser_count()}")
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# EXAMPLE 4: Correlated Actions (Same Context)
# ============================================================================

async def example_correlated_actions():
    """Use same context to maintain session state across multiple pages"""
    session_manager = SessionManager(headless=True, anti_detection=True)
    await session_manager.initialize()
    
    try:
        # Create context (isolated session with shared cookies)
        context = await session_manager.get_context('nike')
        
        # Page 1: Search for product
        page1 = await context.new_page()
        await page1.goto('https://www.nike.com')
        # ... search logic ...
        await page1.close()
        
        # Page 2: Same session, shared cookies
        page2 = await context.new_page()
        # ... page2 has same cookies as page1 (logged in, etc.) ...
        await page2.close()
        
        # All done with context
        await context.close()
        
        print("Correlated actions completed in same session")
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# EXAMPLE 5: Error Handling and Recovery
# ============================================================================

async def example_error_handling():
    """Demonstrate automatic browser recovery"""
    session_manager = SessionManager(headless=True, anti_detection=True)
    await session_manager.initialize()
    
    try:
        # Check if browser is alive
        if await session_manager.is_browser_alive('nike'):
            print("Nike browser is alive")
        else:
            print("Nike browser not created yet")
        
        # Create browser
        page = await session_manager.get_page('nike')
        await page.goto('https://www.nike.com')
        await page.close()
        
        # Check again
        if await session_manager.is_browser_alive('nike'):
            print("Nike browser is still alive after use")
        
        # Close specific browser
        await session_manager.close_browser('nike')
        
        # Check again
        if await session_manager.is_browser_alive('nike'):
            print("Nike browser is alive")
        else:
            print("Nike browser closed successfully")
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# EXAMPLE 6: Using Context Manager (Automatic Cleanup)
# ============================================================================

async def example_context_manager():
    """Use async context manager for automatic cleanup"""
    async with SessionManager(headless=True, anti_detection=True) as session_manager:
        # SessionManager automatically initialized
        page = await session_manager.get_page('nike')
        await page.goto('https://www.nike.com')
        print(f"Title: {await page.title()}")
        await page.close()
        
    # SessionManager automatically shut down here
    print("Cleanup completed automatically")


# ============================================================================
# EXAMPLE 7: Integration with Site Handler
# ============================================================================

class NikeSiteHandler:
    """Example site handler using SessionManager"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    async def find_product(self, product_name: str, size: str):
        """Find a product on Nike"""
        page = await self.session_manager.get_page('nike')
        
        try:
            await page.goto('https://www.nike.com/search')
            await page.fill('[name="q"]', product_name)
            await page.click('[type="submit"]')
            
            # ... search logic ...
            
            return {"found": True, "sku": "DA1971-104"}
        
        finally:
            await page.close()
    
    async def add_to_cart(self, sku: str, size: str):
        """Add product to cart"""
        page = await self.session_manager.get_page('nike')
        
        try:
            await page.goto(f'https://www.nike.com/product/{sku}')
            
            # ... add to cart logic ...
            
            return {"success": True}
        
        finally:
            await page.close()


async def example_with_handler():
    """Use handler with SessionManager"""
    session_manager = SessionManager(headless=True, anti_detection=True)
    await session_manager.initialize()
    
    handler = NikeSiteHandler(session_manager)
    
    try:
        # Handler doesn't manage browsers - SessionManager does!
        result = await handler.find_product('Jordan 1', '10')
        print(f"Product found: {result}")
        
        # Browser is reused automatically
        result = await handler.add_to_cart('DA1971-104', '10')
        print(f"Added to cart: {result}")
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# RUN EXAMPLES
# ============================================================================

async def run_all_examples():
    """Run all examples"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)
    await example_basic_usage()
    
    print("\n" + "="*60)
    print("EXAMPLE 2: Browser Reuse")
    print("="*60)
    await example_browser_reuse()
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Parallel Execution")
    print("="*60)
    await example_parallel_execution()
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Correlated Actions")
    print("="*60)
    await example_correlated_actions()
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Error Handling")
    print("="*60)
    await example_error_handling()
    
    print("\n" + "="*60)
    print("EXAMPLE 6: Context Manager")
    print("="*60)
    await example_context_manager()
    
    print("\n" + "="*60)
    print("EXAMPLE 7: With Handler")
    print("="*60)
    await example_with_handler()


if __name__ == '__main__':
    asyncio.run(run_all_examples())