# pop_up_bot/engines/examples_scraper_engine.py

"""
Examples and usage patterns for PlaywrightScraperEngine

The scraper engine provides low-level Playwright automation.
Site-specific logic (selectors, flows) goes in SiteHandlers.
"""

import asyncio


async def example_basic_workflow():
    """
    Basic workflow: Navigate → Find product → Extract info
    
    (Pseudocode - requires actual Playwright setup)
    """
    
    print("\n=== EXAMPLE 1: Basic Workflow ===\n")
    
    print("""
    from playwright.async_api import async_playwright
    from pop_up_bot.engines.scraper_engine import PlaywrightScraperEngine
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create engine
        engine = PlaywrightScraperEngine(page)
        
        # Navigate to site
        await engine.navigate('https://nike.com/product/123')
        
        # Wait for product to load
        await engine.wait_for('h1.product-name', visible=True)
        
        # Extract product information
        title = await engine.extract_text('h1.product-name')
        price = await engine.extract_text('span.price')
        
        print(f"Product: {title}")
        print(f"Price: {price}")
        
        await engine.close()
    """)


async def example_add_to_cart():
    """
    Common pattern: Add product to cart
    
    (Pseudocode - site selectors are examples)
    """
    
    print("\n=== EXAMPLE 2: Add to Cart ===\n")
    
    print("""
    # Select size
    await engine.click('input[value="US 10"]')
    
    # Wait for cart button to be enabled
    await engine.wait_for('button[name="add-to-cart"]', visible=True)
    
    # Check if item is in stock
    in_stock = await engine.is_element_visible('span.in-stock')
    
    if in_stock:
        # Add to cart
        await engine.click('button[name="add-to-cart"]')
        
        # Wait for confirmation
        await engine.wait_for('div.cart-notification')
        
        # Extract cart count
        cart_count = await engine.extract_text('span.cart-count')
        print(f"Item added! Cart count: {cart_count}")
    else:
        print("Out of stock")
    """)


async def example_checkout_flow():
    """
    Complete checkout flow with error handling
    
    (Pseudocode - real implementation in SiteHandler)
    """
    
    print("\n=== EXAMPLE 3: Checkout Flow ===\n")
    
    print("""
    async def checkout(engine):
        # Go to cart
        await engine.navigate('https://nike.com/cart')
        
        # Review items
        items = await engine.extract_all_text('div.cart-item-name')
        print(f"Items in cart: {items}")
        
        # Proceed to checkout
        await engine.click('button[name="proceed-to-checkout"]')
        
        # Fill shipping info
        await engine.type('input[name="email"]', 'user@example.com')
        await engine.type('input[name="address"]', '123 Main St')
        await engine.type('input[name="zipcode"]', '12345')
        
        # Wait for form validation
        await engine.wait_for('button[name="continue"]:enabled')
        
        # Continue
        await engine.click('button[name="continue"]')
        
        # Wait for payment page
        await engine.wait_for('div.payment-section', visible=True)
        
        return True
    
    success = await checkout(engine)
    """)


async def example_error_handling():
    """
    Error handling with retries
    
    (Pseudocode - built-in to engine methods)
    """
    
    print("\n=== EXAMPLE 4: Error Handling ===\n")
    
    print("""
    # Click with automatic retry (3 attempts by default)
    try:
        await engine.click('button[name="add-to-cart"]', retry=True)
    except Exception as e:
        print(f"Failed to click after retries: {e}")
    
    # Wait with custom timeout
    try:
        await engine.wait_for('input[name="size"]', timeout=10)
    except TimeoutError:
        print("Size selector not found - might be out of stock")
    
    # Extract with fallback
    price = await engine.extract_text('span.price')
    if price is None:
        # Try alternative selector
        price = await engine.extract_attribute('div.product-info', 'data-price')
    
    print(f"Price: {price}")
    """)


async def example_anti_detection():
    """
    Anti-detection measures built-in
    
    (Pseudocode - automatic in engine)
    """
    
    print("\n=== EXAMPLE 5: Anti-Detection ===\n")
    
    print("""
    # Human-like delays are automatic
    await engine.click('button.submit')  # Auto delay before click
    await engine.type('input[name="name"]', 'John')  # Auto delay, realistic typing
    
    # Manual anti-detection measures
    
    # Random scroll (simulate browsing)
    await engine.random_scroll(amount=500)
    
    # Hover over element (human behavior)
    await engine.hover('a.product-link')
    
    # Scroll naturally to element
    await engine.scroll_to_element('button.checkout')
    
    # These are all Playwright actions that don't trigger bot detection
    # compared to fast, mechanical Selenium clicks
    """)


async def example_debugging():
    """
    Debugging and monitoring
    
    (Pseudocode - real implementation)
    """
    
    print("\n=== EXAMPLE 6: Debugging ===\n")
    
    print("""
    # Get engine statistics
    stats = engine.get_stats()
    print(f"Actions: {stats['actions']}")
    print(f"Errors: {stats['errors']}")
    print(f"Duration: {stats['duration_seconds']}s")
    
    # Print page content for debugging
    await engine.print_page_content('div.product-info')
    
    # Screenshots are captured automatically on errors
    # Stored as debug_[error_type]_[timestamp].png
    
    # Execute JavaScript for debugging
    page_state = await engine.execute_js('''
        return {
            title: document.title,
            url: window.location.href,
            readyState: document.readyState
        }
    ''')
    print(f"Page state: {page_state}")
    """)


async def example_site_agnostic_design():
    """
    Why scraper engine is site-agnostic
    
    Different sites = different selectors and flows
    """
    
    print("\n=== EXAMPLE 7: Site-Agnostic Design ===\n")
    
    print("""
    # PlaywrightScraperEngine is just the low-level automation
    # It doesn't know about specific site structure
    
    # Nike selector: input[value="US 10"]
    # Footlocker selector: div[data-size="10"]
    # Adidas selector: span[class*="size-10"]
    
    # SiteHandler handles site-specific logic
    # SiteHandler uses PlaywrightScraperEngine for automation
    
    class NikeSiteHandler:
        def __init__(self, engine: PlaywrightScraperEngine):
            self.engine = engine  # Uses engine for all Playwright operations
        
        async def select_size(self, size: str):
            # Nike-specific selector
            await self.engine.click(f'input[value="{size}"]')
        
        async def add_to_cart(self):
            # Nike-specific flow
            await self.engine.click('button[name="add-to-cart"]')
            await self.engine.wait_for('div.cart-notification')
    
    class FootlockerSiteHandler:
        def __init__(self, engine: PlaywrightScraperEngine):
            self.engine = engine
        
        async def select_size(self, size: str):
            # Footlocker-specific selector
            await self.engine.click(f'div[data-size="{size}"]')
        
        async def add_to_cart(self):
            # Footlocker-specific flow
            await self.engine.click('button[class*="add-cart"]')
            await self.engine.wait_for('span.added-to-cart')
    
    # Usage
    engine = PlaywrightScraperEngine(page)
    
    nike_handler = NikeSiteHandler(engine)
    await nike_handler.select_size("US 10")
    await nike_handler.add_to_cart()
    """)


async def run_all_examples():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("PLAYRIGHTSCRAPER ENGINE EXAMPLES")
    print("="*80)
    
    await example_basic_workflow()
    await example_add_to_cart()
    await example_checkout_flow()
    await example_error_handling()
    await example_anti_detection()
    await example_debugging()
    await example_site_agnostic_design()
    
    print("\n" + "="*80)
    print("Key Takeaway:")
    print("- PlaywrightScraperEngine = Low-level automation (site-agnostic)")
    print("- SiteHandlers = Site-specific logic (uses engine)")
    print("- Separation of concerns = Easy to add new sites")
    print("="*80 + "\n")


if __name__ == '__main__':
    asyncio.run(run_all_examples())