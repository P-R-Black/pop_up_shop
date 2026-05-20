# pop_up_bot/managers/examples_proxy_manager.py

"""
Examples and usage patterns for ProxyManager
"""

from proxy_manager import ProxyManager, Proxy


# ============================================================================
# EXAMPLE 1: Basic Proxy Rotation
# ============================================================================

def example_basic_rotation():
    """Simple round-robin proxy rotation"""
    
    print("\n=== EXAMPLE 1: Basic Proxy Rotation ===\n")
    
    proxies = [
        'http://proxy1.com:8080',
        'http://proxy2.com:8080',
        'http://proxy3.com:8080',
    ]
    
    manager = ProxyManager(proxies, strategy='round_robin')
    
    # Get proxies in sequence
    for i in range(6):
        proxy = manager.get_next_proxy()
        print(f"Request {i+1}: Using {proxy.server}")


# ============================================================================
# EXAMPLE 2: Proxy with Authentication
# ============================================================================

def example_authenticated_proxy():
    """Use proxy with username/password"""
    
    print("\n=== EXAMPLE 2: Authenticated Proxy ===\n")
    
    proxies = [
        'http://user:pass@proxy1.com:8080',
        'socks5://user:pass@proxy2.com:1080',
    ]
    
    manager = ProxyManager(proxies)
    
    for proxy in manager.proxy_list:
        print(f"Proxy: {proxy.server}")
        print(f"  Username: {proxy.username}")
        print(f"  Password: {proxy.password}")
        print(f"  Full URL: {proxy.url}")


# ============================================================================
# EXAMPLE 3: Tracking Failures
# ============================================================================

def example_failure_tracking():
    """Track proxy failures and remove dead proxies"""
    
    print("\n=== EXAMPLE 3: Failure Tracking ===\n")
    
    proxies = [
        'http://proxy1.com:8080',
        'http://proxy2.com:8080',
        'http://proxy3.com:8080',
    ]
    
    manager = ProxyManager(proxies, max_failures=3)
    
    print(f"Initial: {manager.get_proxy_stats()}\n")
    
    # Simulate proxy failures
    proxy1 = manager.proxy_list[0]
    proxy2 = manager.proxy_list[1]
    
    # Proxy 1 fails 3 times
    for i in range(3):
        manager.mark_proxy_failed(proxy1)
        print(f"Proxy1 failed (attempt {i+1})")
    
    print(f"\nAfter failures: {manager.get_proxy_stats()}\n")
    
    # Proxy 2 succeeds
    manager.mark_proxy_success(proxy2)
    print(f"Proxy2 succeeded, reset")
    
    print(f"\nFinal stats: {manager.get_proxy_stats()}")


# ============================================================================
# EXAMPLE 4: Random Strategy
# ============================================================================

def example_random_strategy():
    """Use random proxy selection instead of round-robin"""
    
    print("\n=== EXAMPLE 4: Random Strategy ===\n")
    
    proxies = [
        'http://proxy1.com:8080',
        'http://proxy2.com:8080',
        'http://proxy3.com:8080',
    ]
    
    manager = ProxyManager(proxies, strategy='random')
    
    # Get random proxies
    for i in range(5):
        proxy = manager.get_next_proxy()
        print(f"Request {i+1}: Using {proxy.server}")


# ============================================================================
# EXAMPLE 5: Integration with Playwright
# ============================================================================

async def example_with_playwright():
    """Use proxy with Playwright context"""
    
    print("\n=== EXAMPLE 5: Playwright Integration ===\n")
    
    # This is pseudo-code showing how to use with Playwright
    
    proxies = [
        'http://proxy1.com:8080',
        'http://proxy2.com:8080',
    ]
    
    manager = ProxyManager(proxies)
    
    print("Pseudo-code for Playwright integration:\n")
    
    for site in ['nike', 'footlocker']:
        proxy = manager.get_next_proxy()
        
        print(f"Site: {site}")
        print(f"Proxy: {proxy.server}")
        print(f"""
        # Create context with proxy
        context = await browser.new_context(
            proxy={{
                'server': '{proxy.server}',
        """)
        
        if proxy.username and proxy.password:
            print(f"        'username': '{proxy.username}',")
            print(f"        'password': '{proxy.password}',")
        
        print("""        }
        )
        
        # Use context
        page = await context.new_page()
        try:
            await page.goto('https://...')
            # Success
            manager.mark_proxy_success(proxy)
        except Exception as e:
            # Failed
            manager.mark_proxy_failed(proxy)
        finally:
            await context.close()
        """)
        print()


# ============================================================================
# EXAMPLE 6: Dynamic Proxy Addition
# ============================================================================

def example_dynamic_addition():
    """Add proxies dynamically"""
    
    print("\n=== EXAMPLE 6: Dynamic Proxy Addition ===\n")
    
    manager = ProxyManager()
    print(f"Initial: {manager}")
    
    # Add proxies one by one
    proxies = [
        'http://proxy1.com:8080',
        'http://proxy2.com:8080',
        'http://proxy3.com:8080',
    ]
    
    for proxy_str in proxies:
        success = manager.add_proxy(proxy_str)
        print(f"Added {proxy_str}: {success}")
    
    print(f"\nFinal: {manager}")
    print(f"Stats: {manager.get_proxy_stats()}")


# ============================================================================
# EXAMPLE 7: Proxy Parsing
# ============================================================================

def example_proxy_parsing():
    """Parse various proxy formats"""
    
    print("\n=== EXAMPLE 7: Proxy Format Parsing ===\n")
    
    formats = [
        'http://proxy.com:8080',
        'https://proxy.com:443',
        'socks5://proxy.com:1080',
        'http://user:pass@proxy.com:8080',
        'socks5://user:pass@proxy.com:1080',
    ]
    
    for format_str in formats:
        try:
            proxy = Proxy.from_string(format_str)
            print(f"✓ {format_str}")
            print(f"  → {proxy.server} (protocol: {proxy.protocol.value})")
            if proxy.username:
                print(f"  → Auth: {proxy.username}:***")
        except ValueError as e:
            print(f"✗ {format_str}: {e}")
        print()


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == '__main__':
    example_basic_rotation()
    example_authenticated_proxy()
    example_failure_tracking()
    example_random_strategy()
    example_dynamic_addition()
    example_proxy_parsing()
    
    # Async example (requires asyncio)
    import asyncio
    asyncio.run(example_with_playwright())