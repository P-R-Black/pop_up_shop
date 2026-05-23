# pop_up_bot/managers/examples_procurement_lock.py

"""
Examples and usage patterns for ProcurementLock
"""

import asyncio
from procurement_lock import ProcurementLock


# ============================================================================
# EXAMPLE 1: Basic Lock Workflow
# ============================================================================

async def example_basic_workflow():
    """Basic lock acquire → use → release pattern"""
    
    print("\n=== EXAMPLE 1: Basic Lock Workflow ===\n")
    
    lock = ProcurementLock()
    execution_id = 123
    
    # Try to acquire lock
    if await lock.acquire(execution_id, ttl=300):  # 5 minute lock
        print(f"✓ Lock acquired for execution {execution_id}")
        
        try:
            # Do critical work (checkout, payment, etc.)
            print("  → Processing checkout...")
            print("  → Processing payment...")
            print("  → Confirming order...")
        
        finally:
            # Always release
            await lock.release(execution_id)
            print(f"✓ Lock released")
    
    else:
        print(f"✗ Failed to acquire lock - another bot got it first")


# ============================================================================
# EXAMPLE 2: Race Condition Prevention
# ============================================================================

async def example_race_condition():
    """Demonstrate race condition prevention"""
    
    print("\n=== EXAMPLE 2: Race Condition Prevention ===\n")
    
    lock = ProcurementLock()
    
    async def execution_workflow(execution_id: int, site: str):
        """Simulate an execution competing for the same item"""
        
        print(f"[{site}] Starting procurement...")
        
        if await lock.acquire(execution_id, ttl=300):
            print(f"[{site}] ✓ Won the race! Proceeding to checkout")
            
            try:
                # Simulate checkout
                print(f"[{site}]   → Processing payment...")
                await asyncio.sleep(0.5)
                print(f"[{site}]   → Order confirmed!")
            
            finally:
                await lock.release(execution_id)
                print(f"[{site}] ✓ Finished")
        
        else:
            print(f"[{site}] ✗ Lost the race - aborting")
    
    # Multiple executions competing for same item
    execution_id = 999  # Same item/size
    
    # Run in parallel (simulating concurrent requests)
    print("Simulating 3 concurrent executions buying the same item:\n")
    
    await asyncio.gather(
        execution_workflow(execution_id, 'Nike Bot'),
        execution_workflow(execution_id, 'Footlocker Bot'),
        execution_workflow(execution_id, 'Adidas Bot'),
    )
    
    print("\nResult: Only ONE succeeded (other TWO aborted)")


# ============================================================================
# EXAMPLE 3: Lock Info & Monitoring
# ============================================================================

async def example_lock_monitoring():
    """Monitor active locks"""
    
    print("\n=== EXAMPLE 3: Lock Monitoring ===\n")
    
    lock = ProcurementLock()
    
    # Simulate multiple active locks
    execution_ids = [1, 2, 3, 4, 5]
    
    print("Acquiring locks for 5 executions:\n")
    for eid in execution_ids:
        acquired = await lock.acquire(eid, ttl=300)
        if acquired:
            print(f"  ✓ Execution {eid}: Lock acquired")
    
    # Monitor all active locks
    print("\nMonitoring active locks:\n")
    all_locks = await lock.get_all_locks()
    
    for lock_info in all_locks:
        eid = lock_info['execution_id']
        holder = lock_info['holder'][:8]
        ttl = lock_info['ttl_seconds']
        
        print(f"  Execution {eid}: held by {holder}... (TTL: {ttl}s)")
    
    # Check specific lock
    print("\nChecking lock for execution 3:\n")
    info = await lock.get_lock_info(3)
    if info:
        print(f"  Status: Locked")
        print(f"  Holder: {info['holder'][:16]}...")
        print(f"  Time Remaining: {info['ttl_seconds']}s")
    
    # Release all
    print("\nReleasing all locks:\n")
    for eid in execution_ids:
        await lock.release(eid)
        print(f"  ✓ Released execution {eid}")


# ============================================================================
# EXAMPLE 4: Lock TTL for Deadlock Prevention
# ============================================================================

async def example_ttl_deadlock():
    """Demonstrate TTL preventing deadlock"""
    
    print("\n=== EXAMPLE 4: TTL for Deadlock Prevention ===\n")
    
    lock = ProcurementLock()
    
    print("Scenario: Process crashes during checkout")
    print("Lock acquired with 5s TTL:\n")
    
    execution_id = 777
    
    # Acquire lock
    if await lock.acquire(execution_id, ttl=5):
        print(f"✓ Lock acquired (expires in 5s)")
        print(f"✗ Simulating process crash...")
        print(f"✗ Lock NOT released manually\n")
        
        # Check if locked
        print(f"Immediately after crash:")
        is_locked = await lock.is_locked(execution_id)
        print(f"  Lock held: {is_locked}\n")
        
        # Wait for TTL to expire
        print(f"After 6 seconds (TTL expired):")
        print(f"  Lock would auto-expire")
        print(f"  Next execution can acquire it")
        print(f"\nThis prevents deadlock from crashed processes!")


# ============================================================================
# EXAMPLE 5: Force Release (Emergency)
# ============================================================================

async def example_force_release():
    """Emergency force release of stuck locks"""
    
    print("\n=== EXAMPLE 5: Force Release (Emergency) ===\n")
    
    lock = ProcurementLock()
    
    execution_id = 888
    
    # Acquire lock
    await lock.acquire(execution_id, ttl=3600)  # 1 hour lock
    print(f"✓ Lock acquired for execution {execution_id} (1 hour TTL)\n")
    
    # Check it
    print(f"Lock status:")
    info = await lock.get_lock_info(execution_id)
    print(f"  Locked: {info['locked']}")
    print(f"  Time Remaining: {info['ttl_seconds']}s\n")
    
    # Force release (emergency)
    print(f"Force releasing stuck lock...\n")
    await lock.force_release(execution_id)
    
    # Verify
    print(f"After force release:")
    is_locked = await lock.is_locked(execution_id)
    print(f"  Locked: {is_locked}")


# ============================================================================
# EXAMPLE 6: Clear All Locks (Maintenance)
# ============================================================================

async def example_maintenance():
    """Clear all locks during maintenance"""
    
    print("\n=== EXAMPLE 6: Maintenance - Clear All Locks ===\n")
    
    lock = ProcurementLock()
    
    # Simulate multiple active locks
    for i in range(1, 6):
        await lock.acquire(i, ttl=300)
    
    # Check count
    all_locks = await lock.get_all_locks()
    print(f"Active locks before cleanup: {len(all_locks)}\n")
    
    for l in all_locks:
        print(f"  - Execution {l['execution_id']}")
    
    # Maintenance: clear all
    print(f"\nPerforming maintenance cleanup...\n")
    count = await lock.clear_all_locks()
    print(f"✓ Cleared {count} locks\n")
    
    # Verify
    all_locks = await lock.get_all_locks()
    print(f"Active locks after cleanup: {len(all_locks)}")


# ============================================================================
# EXAMPLE 7: Real Procurement Workflow
# ============================================================================

async def example_real_workflow():
    """Complete real-world procurement workflow"""
    
    print("\n=== EXAMPLE 7: Complete Procurement Workflow ===\n")
    
    lock = ProcurementLock()
    execution_id = 12345
    
    async def full_procurement():
        """Full procurement with locking"""
        
        print("Starting procurement for Air Jordan 1 (Size 10)\n")
        
        # Try to secure the item
        if await lock.acquire(execution_id, ttl=600):  # 10 min lock
            print("✓ Secured item - no one else can buy this\n")
            
            try:
                # Step 1: Navigate to site
                print("1. Navigating to Nike...")
                await asyncio.sleep(0.5)
                
                # Step 2: Find product
                print("2. Finding Air Jordan 1...")
                await asyncio.sleep(0.5)
                
                # Step 3: Select size
                print("3. Selecting size US 10...")
                await asyncio.sleep(0.5)
                
                # Step 4: Add to cart
                print("4. Adding to cart...")
                await asyncio.sleep(0.5)
                
                # Step 5: Checkout (critical - others can't interfere)
                print("5. Processing checkout (protected by lock)...")
                await asyncio.sleep(1.0)
                
                # Step 6: Payment
                print("6. Processing payment...")
                await asyncio.sleep(0.5)
                
                # Step 7: Confirm order
                print("7. Confirming order...")
                await asyncio.sleep(0.5)
                
                print("\n✓ Order confirmed! Item secured!\n")
            
            except Exception as e:
                print(f"\n✗ Error during checkout: {e}\n")
            
            finally:
                # Always release lock
                await lock.release(execution_id)
                print("✓ Lock released (transaction complete)")
        
        else:
            print("✗ Failed to secure lock")
            print("✗ Another bot already bought this item")
            print("✗ Aborting procurement")
    
    await full_procurement()


# ============================================================================
# Run Examples
# ============================================================================

async def run_all_examples():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("PROCUREMENTLOCK EXAMPLES")
    print("="*80)
    
    try:
        await example_basic_workflow()
        # await example_race_condition()  # Requires actual Redis
        # await example_lock_monitoring()
        # await example_ttl_deadlock()
        # await example_force_release()
        # await example_maintenance()
        await example_real_workflow()
    except Exception as e:
        print(f"\nNote: Examples require Redis connection")
        print(f"Error: {e}\n")


if __name__ == '__main__':
    asyncio.run(run_all_examples())