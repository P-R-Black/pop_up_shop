# pop_up_bot/managers/examples_procurement_strategy.py

"""
Examples and usage patterns for procurement strategies
"""

from implementations import (
    SequentialStrategy,
    ParallelStrategy,
    PriorityStrategy,
    FastestStrategy,
    CheapestStrategy,
    RetailOnlyStrategy,
    StrategyFactory,
)


# ============================================================================
# EXAMPLE 1: Sequential Strategy (Default)
# ============================================================================

def example_sequential():
    """
    Sequential strategy: Try sites one-by-one until success
    
    Use case: Conservative approach, avoid bans
    Order: nike → footlocker → adidas
    Result: Stop on first success
    """
    
    print("\n=== EXAMPLE 1: Sequential Strategy ===\n")
    
    strategy = SequentialStrategy(
        sites=['nike', 'footlocker', 'adidas', 'new_balance'],
        timeout_per_site=30,
    )
    
    print(f"Strategy: {strategy}")
    print(f"Sites to try: {strategy.get_site_order()}\n")
    
    # Simulate execution flow
    sites_attempted = ['nike', 'footlocker', 'adidas']
    
    for i, site in enumerate(sites_attempted, 1):
        strategy.mark_attempted(site)
        
        if i < 3:
            # Sites 1 and 2 fail
            strategy.mark_failed(site)
            result = {'success': False, 'site': site, 'reason': 'Out of stock'}
            
            print(f"Attempt {i}: {site.upper()}")
            print(f"  Result: FAILED ({result['reason']})")
            
            if not strategy.should_attempt_next_site(result):
                print(f"  Action: STOP")
                break
            else:
                print(f"  Action: Try next site")
        else:
            # Site 3 succeeds
            strategy.mark_successful(site)
            result = {'success': True, 'site': site}
            
            print(f"Attempt {i}: {site.upper()}")
            print(f"  Result: SUCCESS")
            print(f"  Action: STOP (success)")
            break
    
    print(f"\nFinal Stats:")
    stats = strategy.get_stats()
    print(f"  Successful site: {stats['successful']}")
    print(f"  Attempted: {stats['attempted']}")
    print(f"  Failed: {stats['failed']}")


# ============================================================================
# EXAMPLE 2: Parallel Strategy (Fast)
# ============================================================================

def example_parallel():
    """
    Parallel strategy: Try multiple sites simultaneously
    
    Use case: Time-sensitive drops, speed critical
    Order: All sites at once
    Result: First success wins
    
    Note: In real implementation, this uses asyncio.gather()
    """
    
    print("\n=== EXAMPLE 2: Parallel Strategy ===\n")
    
    strategy = ParallelStrategy(
        sites=['nike', 'footlocker', 'adidas', 'new_balance'],
        timeout_per_site=30,
    )
    
    print(f"Strategy: {strategy}")
    print(f"Sites to try: {strategy.get_site_order()}\n")
    
    print("Simulating parallel execution:\n")
    print("Timeline:")
    print("  T=0s:  ├─ Nike request")
    print("         ├─ Footlocker request")
    print("         ├─ Adidas request")
    print("         └─ New Balance request")
    print()
    print("  T=2s:  └─ Adidas: SUCCESS ✓ (WINNER)")
    print("         ├─ Nike: Still processing...")
    print("         ├─ Footlocker: Out of stock ✗")
    print("         └─ New Balance: Still processing...")
    print()
    print("Result: ADIDAS wins the race")
    print("\nAdvantage: Much faster than sequential")
    print("Risk: Higher chance of detection by sites")


# ============================================================================
# EXAMPLE 3: Priority Strategy
# ============================================================================

def example_priority():
    """
    Priority strategy: Try preferred sites first
    
    Use case: Some retailers are more reliable
    Order: Custom priority
    """
    
    print("\n=== EXAMPLE 3: Priority Strategy ===\n")
    
    # Custom priority: prefer boutiques over big sites
    strategy = PriorityStrategy(
        priority_order=[
            'supreme',           # 1st choice - exclusive drops
            'nike',              # 2nd choice - high stock
            'footlocker',        # 3rd choice - backup
            'adidas',            # 4th choice
        ],
        timeout_per_site=30,
    )
    
    print(f"Priority Order:")
    for i, site in enumerate(strategy.get_site_order(), 1):
        print(f"  {i}. {site.upper()}")
    
    print(f"\nRationale:")
    print(f"  - Supreme: Exclusive products, highest priority")
    print(f"  - Nike: Official source, reliable")
    print(f"  - Footlocker: Backup option")
    print(f"  - Adidas: Last resort")


# ============================================================================
# EXAMPLE 4: Fastest Strategy (Aggressive)
# ============================================================================

def example_fastest():
    """
    Fastest strategy: Aggressive parallel with short timeouts
    
    Use case: Limited drops, hyped releases
    Speed: Maximum
    Risk: Maximum
    """
    
    print("\n=== EXAMPLE 4: Fastest Strategy ===\n")
    
    strategy = FastestStrategy(
        sites=['nike', 'footlocker', 'adidas', 'new_balance'],
        timeout_per_site=15,  # Aggressive - fail fast
    )
    
    print(f"Strategy: {strategy}")
    print(f"Timeout per site: {strategy.timeout_per_site}s (aggressive)")
    print(f"Behavior: Parallel with short timeouts\n")
    
    print("Execution Profile:")
    print("  ├─ All 4 sites start simultaneously")
    print("  ├─ 15 second timeout per site")
    print("  ├─ First success returns immediately")
    print("  └─ Slow sites are abandoned\n")
    
    print("Best for:")
    print("  - Limited quantity drops (e.g., 50 units available)")
    print("  - Hyped releases (e.g., new Jordan release)")
    print("  - Time-sensitive products")


# ============================================================================
# EXAMPLE 5: Cheapest Strategy (Budget)
# ============================================================================

def example_cheapest():
    """
    Cheapest strategy: Lower-price retailers first
    
    Use case: Budget-conscious, multiple sources available
    """
    
    print("\n=== EXAMPLE 5: Cheapest Strategy ===\n")
    
    strategy = CheapestStrategy()
    
    print(f"Strategy: {strategy}")
    print(f"Goal: Find lowest price\n")
    
    print("Site Priority (by price tier):")
    print("  1. Official Retail (cheapest) - Nike, Footlocker, Adidas")
    print("  2. Boutiques - Supreme, New Balance")
    print("  3. Resellers (premium) - Grailed, StockX\n")
    
    print("Execution Flow:")
    print("  Try retail sites first (better prices)")
    print("  ↓")
    print("  If all fail, try boutiques")
    print("  ↓")
    print("  Last resort: Premium resellers")


# ============================================================================
# EXAMPLE 6: Retail-Only Strategy (Authenticity)
# ============================================================================

def example_retail_only():
    """
    Retail-only strategy: Official sources only
    
    Use case: Authenticity required, no counterfeits
    """
    
    print("\n=== EXAMPLE 6: Retail-Only Strategy ===\n")
    
    strategy = RetailOnlyStrategy()
    
    print(f"Strategy: {strategy}")
    print(f"Allowed sites: Official retail only\n")
    
    print("Includes:")
    for site in strategy.get_site_order():
        print(f"  ✓ {site.upper()} (official)")
    
    print("\nExcludes:")
    print("  ✗ Grailed (reseller)")
    print("  ✗ StockX (reseller)")
    print("  ✗ Other secondhand markets\n")
    
    print("Use case:")
    print("  - Guarantee authenticity")
    print("  - Avoid counterfeits")
    print("  - Official releases only")


# ============================================================================
# EXAMPLE 7: Strategy Factory
# ============================================================================

def example_factory():
    """
    Use factory to create strategies dynamically
    
    Useful for configuration-based strategy selection
    """
    
    print("\n=== EXAMPLE 7: Strategy Factory ===\n")
    
    print("Creating strategies dynamically:\n")
    
    # Create different strategies
    strategies = [
        ('sequential', {'sites': ['nike', 'adidas']}),
        ('parallel', {}),
        ('fastest', {}),
        ('retail_only', {}),
    ]
    
    for strategy_name, kwargs in strategies:
        strategy = StrategyFactory.create(strategy_name, **kwargs)
        print(f"✓ Created: {strategy}")
    
    print(f"\nAvailable strategies:")
    for name in StrategyFactory.get_available():
        print(f"  - {name}")


# ============================================================================
# EXAMPLE 8: Real-World Scenario
# ============================================================================

def example_real_world():
    """
    Real-world procurement scenario:
    User drops a product with specific requirements
    """
    
    print("\n=== EXAMPLE 8: Real-World Scenario ===\n")
    
    print("Scenario: New Air Jordan release")
    print("Budget: $200")
    print("Requirements: Official product, fast delivery\n")
    
    print("Strategy Selection:")
    print("  1. Time-sensitive? YES")
    print("     → Use FastestStrategy (parallel with short timeouts)")
    print()
    print("  2. Authenticity required? YES")
    print("     → Use RetailOnlyStrategy (official sources only)")
    print()
    print("  3. Budget-conscious? NO")
    print("     → Price not a priority\n")
    
    print("Decision: Combine RetailOnly + Parallel execution")
    print("\nImplementation:")
    
    strategy = StrategyFactory.create(
        'retail_only',  # Official sources only
    )
    
    print(f"  Strategy: {strategy}")
    print(f"  Sites: {strategy.get_site_order()}")
    print(f"  Execution: Parallel")
    print(f"  Timeout: {strategy.timeout_per_site}s per site")


# ============================================================================
# Run All Examples
# ============================================================================

def run_all_examples():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("PROCUREMENT STRATEGY EXAMPLES")
    print("="*80)
    
    example_sequential()
    example_parallel()
    example_priority()
    example_fastest()
    example_cheapest()
    example_retail_only()
    example_factory()
    example_real_world()
    
    print("\n" + "="*80)


if __name__ == '__main__':
    run_all_examples()