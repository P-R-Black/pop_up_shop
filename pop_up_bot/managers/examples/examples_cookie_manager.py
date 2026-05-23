"""
Examples and usage patterns for CookieManager
"""

import asyncio
from session_manager import SessionManager
from cookie_manager import CookieManager


# ============================================================================
# EXAMPLE 1: Basic Cookie Persistence
# ============================================================================

async def example_basic_persistence():
    """Save and restore cookies across bot executions"""
    session_manager = SessionManager(headless=True)
    cookie_manager = CookieManager()
    
    await session_manager.initialize()
    
    print("\n=== EXAMPLE 1: Basic Cookie Persistence ===\n")
    
    # First execution: Login and save cookies
    print("First execution: Login to Nike")
    page = await session_manager.get_page('nike')
    
    # Simulate login (in real scenario, actual login)
    await page.goto('https://www.nike.com')
    # ... perform login ...
    # ... add to cart ...
    
    # Save cookies for next execution
    cookies = await page.context.cookies()
    saved = await cookie_manager.save_cookies('nike', cookies)
    print(f"✓ Saved {saved} cookies")
    await page.close()
    
    # Simulate bot shutdown
    await session_manager.shutdown()
    
    # Second execution (next day): Login not needed, cookies loaded
    print("\nSecond execution: Load saved cookies (no login needed)")
    session_manager = SessionManager(headless=True)
    await session_manager.initialize()
    
    # Create context
    context = await session_manager.get_context('nike')
    
    # Load cookies from previous execution
    cookies = await cookie_manager.load_cookies('nike')
    print(f"✓ Loaded {len(cookies)} cookies")
    
    # Add cookies to context (maintains session)
    if cookies:
        await context.add_cookies(cookies)
        print("✓ Cookies added to context, session maintained")
    
    # Now bot is already logged in!
    page = await context.new_page()
    await page.goto('https://www.nike.com/account')
    print(f"✓ Accessed account (already logged in thanks to cookies)")
    await page.close()
    await context.close()
    
    await session_manager.shutdown()


# ============================================================================
# EXAMPLE 2: Maintain Shopping Cart State
# ============================================================================

async def example_shopping_cart_state():
    """Maintain shopping cart across multiple attempts"""
    session_manager = SessionManager(headless=True)
    cookie_manager = CookieManager()
    
    await session_manager.initialize()
    
    print("\n=== EXAMPLE 2: Shopping Cart State ===\n")
    
    # First attempt: Add to cart
    print("Attempt 1: Add item to Nike cart")
    context = await session_manager.get_context('nike')
    page = await context.new_page()
    
    await page.goto('https://www.nike.com/product/ABC123')
    # ... add to cart ...
    
    # Save cookies (includes cart state in cookies/session)
    cookies = await context.cookies()
    await cookie_manager.save_cookies('nike', cookies)
    print("✓ Item added to cart, session saved")
    await page.close()
    await context.close()
    
    # Second attempt: Cart still there!
    print("\nAttempt 2: Cart items still there")
    context = await session_manager.get_context('nike')
    
    # Load cookies with cart state
    cookies = await cookie_manager.load_cookies('nike')
    await context.add_cookies(cookies)
    
    page = await context.new_page()
    await page.goto('https://www.nike.com/cart')
    # ... cart still has items!
    print("✓ Cart items persisted from previous attempt")
    await page.close()
    await context.close()
    
    await session_manager.shutdown()


# ============================================================================
# EXAMPLE 3: Cookie Cleanup
# ============================================================================

async def example_cookie_cleanup():
    """Clean up expired cookies"""
    cookie_manager = CookieManager()
    
    print("\n=== EXAMPLE 3: Cookie Cleanup ===\n")
    
    # Get info before cleanup
    info = await cookie_manager.get_cookie_info('nike')
    print(f"Before cleanup: {info}")
    
    # Clean up expired cookies
    deleted = await cookie_manager.cleanup_expired_cookies('nike')
    print(f"✓ Deleted {deleted} expired cookies")
    
    # Get info after cleanup
    info = await cookie_manager.get_cookie_info('nike')
    print(f"After cleanup: {info}")


# ============================================================================
# EXAMPLE 4: Cookie Export/Import (Backup)
# ============================================================================

async def example_backup():
    """Export and import cookies for backup"""
    cookie_manager = CookieManager()
    
    print("\n=== EXAMPLE 4: Cookie Backup ===\n")
    
    # Export cookies
    json_backup = await cookie_manager.export_cookies('nike')
    print(f"✓ Exported Nike cookies to JSON")
    print(f"Backup (first 200 chars): {json_backup[:200]}...")
    
    # Save to file (simulated)
    with open('/tmp/nike_cookies_backup.json', 'w') as f:
        f.write(json_backup)
    print("✓ Saved backup to file")
    
    # Later: Restore from backup
    with open('/tmp/nike_cookies_backup.json', 'r') as f:
        backup_data = f.read()
    
    # Clear current cookies
    deleted = await cookie_manager.clear_cookies('nike')
    print(f"✓ Cleared {deleted} cookies")
    
    # Restore from backup
    imported = await cookie_manager.import_cookies('nike', backup_data)
    print(f"✓ Restored {imported} cookies from backup")


# ============================================================================
# EXAMPLE 5: Multi-Site Cookie Management
# ============================================================================

async def example_multi_site():
    """Manage cookies for multiple sites"""
    session_manager = SessionManager(headless=True)
    cookie_manager = CookieManager()
    
    await session_manager.initialize()
    
    print("\n=== EXAMPLE 5: Multi-Site Cookie Management ===\n")
    
    sites = ['nike', 'footlocker', 'adidas']
    
    # Save cookies for each site
    for site in sites:
        page = await session_manager.get_page(site)
        await page.goto(f'https://www.{site}.com')
        # ... interact with site ...
        
        cookies = await page.context.cookies()
        saved = await cookie_manager.save_cookies(site, cookies)
        print(f"✓ {site.capitalize()}: Saved {saved} cookies")
        await page.close()
    
    # Later: Show cookie stats for all sites
    print("\nCookie statistics:")
    for site in sites:
        count = await cookie_manager.get_cookie_count(site)
        info = await cookie_manager.get_cookie_info(site)
        print(f"  {site}: {info['total']} total, {info['active']} active, {info['expired']} expired")
    
    await session_manager.shutdown()


# ============================================================================
# EXAMPLE 6: Cookie Duplication (Same Auth Domain)
# ============================================================================

async def example_cookie_duplication():
    """Copy cookies between related sites"""
    cookie_manager = CookieManager()
    
    print("\n=== EXAMPLE 6: Cookie Duplication ===\n")
    
    # Nike.com and Nike.eu use same auth
    print("Copying Nike.com cookies to Nike.eu")
    count = await cookie_manager.duplicate_cookies('nike.com', 'nike.eu')
    print(f"✓ Duplicated {count} cookies")
    
    # Now nike.eu also has authenticated session
    print("Nike.eu now has authenticated session without separate login")


# ============================================================================
# EXAMPLE 7: Integration with Site Handler
# ============================================================================

class NikeSiteHandler:
    """Site handler with automatic cookie persistence"""
    
    def __init__(self, session_manager: SessionManager, cookie_manager: CookieManager):
        self.session_manager = session_manager
        self.cookie_manager = cookie_manager
    
    async def find_product(self, product_name: str, size: str):
        """Find product, maintaining session via cookies"""
        # Create context
        context = await self.session_manager.get_context('nike')
        
        # Load previous cookies (maintains login)
        cookies = await self.cookie_manager.load_cookies('nike')
        if cookies:
            await context.add_cookies(cookies)
        
        # Create page
        page = await context.new_page()
        
        try:
            await page.goto('https://www.nike.com/search')
            await page.fill('[name="q"]', product_name)
            await page.click('[type="submit"]')
            
            # ... search logic ...
            
            result = {"found": True, "sku": "DA1971-104"}
            return result
        
        finally:
            # Save updated cookies for next execution
            cookies = await context.cookies()
            await self.cookie_manager.save_cookies('nike', cookies)
            
            await page.close()
            await context.close()


async def example_with_handler():
    """Use handler with automatic cookie persistence"""
    session_manager = SessionManager(headless=True)
    cookie_manager = CookieManager()
    
    await session_manager.initialize()
    
    handler = NikeSiteHandler(session_manager, cookie_manager)
    
    print("\n=== EXAMPLE 7: Handler with Cookie Persistence ===\n")
    
    try:
        # First call: cookies loaded (if any), search performed, cookies saved
        result = await handler.find_product('Jordan 1', '10')
        print(f"First search: {result}")
        
        # Second call: cookies automatically restored from previous search
        result = await handler.find_product('Air Max', '10')
        print(f"Second search: {result}")
        print("✓ Cookies automatically managed between calls")
    
    finally:
        await session_manager.shutdown()


# ============================================================================
# RUN EXAMPLES
# ============================================================================

async def run_all_examples():
    """Run all examples"""
    try:
        await example_basic_persistence()
        await example_shopping_cart_state()
        await example_cookie_cleanup()
        await example_backup()
        await example_multi_site()
        await example_cookie_duplication()
        await example_with_handler()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
    
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(run_all_examples())