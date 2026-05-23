# pop_up_bot/managers/examples_event_logger.py

"""
Examples and usage patterns for EventLogger
"""

import asyncio
from event_logger import EventLogger, EventType


# ============================================================================
# EXAMPLE 1: Basic Event Emission
# ============================================================================

async def example_basic_emission():
    """Simple event emission"""
    
    print("\n=== EXAMPLE 1: Basic Event Emission ===\n")
    
    execution_id = 1
    logger = EventLogger(execution_id)
    
    # Emit events during procurement workflow
    await logger.emit(EventType.INITIALIZED)
    await logger.emit(EventType.STRATEGY_SELECTED, metadata={'strategy': 'sequential'})
    await logger.emit(EventType.SITE_SELECTED, site_name='nike')
    await logger.emit(EventType.PRODUCT_FOUND, metadata={
        'product_name': 'Air Jordan 1',
        'price': 170.00,
    })
    await logger.emit(EventType.SIZE_SELECTED, metadata={'size': 'US 10'})
    await logger.emit(EventType.CART_SUCCESS)
    await logger.emit(EventType.ORDER_CONFIRMED)
    
    # Get timeline
    timeline = await logger.get_timeline()
    print(f"Total events: {len(timeline)}")
    for event in timeline:
        print(f"  - {event['event_type']} (site: {event['site_name']})")


# ============================================================================
# EXAMPLE 2: Tracking Failures
# ============================================================================

async def example_failure_tracking():
    """Track and analyze failures"""
    
    print("\n=== EXAMPLE 2: Failure Tracking ===\n")
    
    execution_id = 2
    logger = EventLogger(execution_id)
    
    # Emit successful start
    await logger.emit(EventType.INITIALIZED)
    await logger.emit(EventType.STRATEGY_SELECTED, metadata={'strategy': 'sequential'})
    await logger.emit(EventType.SITE_SELECTED, site_name='nike')
    await logger.emit(EventType.PRODUCT_FOUND)
    
    # Emit failure
    await logger.emit(
        EventType.FAILED,
        site_name='nike',
        metadata={
            'reason': 'Captcha detected',
            'error_code': 'CAPTCHA_CHALLENGE',
        }
    )
    
    # Analyze failure
    failure = await logger.get_failure_point()
    if failure:
        print(f"Execution failed at: {failure['event_type']}")
        print(f"Site: {failure['site_name']}")
        print(f"Reason: {failure['metadata']['reason']}")
    
    summary = await logger.get_execution_summary()
    print(f"\nExecution Summary:")
    print(f"  Status: {summary['status']}")
    print(f"  Total Events: {summary['total_events']}")


# ============================================================================
# EXAMPLE 3: Multi-Site Attempt Tracking
# ============================================================================

async def example_multi_site():
    """Track multiple site attempts"""
    
    print("\n=== EXAMPLE 3: Multi-Site Tracking ===\n")
    
    execution_id = 3
    logger = EventLogger(execution_id)
    
    sites = ['nike', 'footlocker', 'adidas']
    
    await logger.emit(EventType.INITIALIZED)
    await logger.emit(EventType.STRATEGY_SELECTED, metadata={'strategy': 'parallel'})
    
    for site in sites:
        print(f"\nAttempting {site}...")
        
        await logger.emit(EventType.SITE_SELECTED, site_name=site)
        await logger.emit(EventType.PRODUCT_FOUND, site_name=site, metadata={
            'url': f'https://{site}.com/product/123',
        })
        
        # Alternate success/failure
        if site == 'nike':
            await logger.emit(EventType.CART_SUCCESS, site_name=site)
            await logger.emit(EventType.ORDER_CONFIRMED, site_name=site)
            print(f"  ✓ Success on {site}")
        else:
            await logger.emit(EventType.FAILED, site_name=site, metadata={
                'reason': 'Out of stock',
            })
            print(f"  ✗ Failed on {site}")
    
    # Analyze by site
    print("\nPer-site summary:")
    for site in sites:
        events = await logger.get_events_by_site(site)
        print(f"  {site}: {len(events)} events")


# ============================================================================
# EXAMPLE 4: Event Replay for Debugging
# ============================================================================

async def example_replay():
    """Use replay for debugging"""
    
    print("\n=== EXAMPLE 4: Event Replay ===\n")
    
    execution_id = 4
    logger = EventLogger(execution_id)
    
    # Simulate procurement workflow
    await logger.emit(EventType.INITIALIZED)
    await logger.emit(EventType.STRATEGY_SELECTED, metadata={'strategy': 'sequential'})
    await logger.emit(EventType.SITE_SELECTED, site_name='nike')
    await logger.emit(EventType.PRODUCT_FOUND)
    await logger.emit(EventType.SIZE_SELECTED, metadata={'size': 'US 10'})
    await logger.emit(EventType.CART_SUCCESS)
    await logger.emit(EventType.CHECKOUT_STARTED)
    await logger.emit(EventType.PAYMENT_SUBMITTED)
    await logger.emit(EventType.ORDER_CONFIRMED)
    
    # Use replay to see full timeline
    print("Replaying execution for debugging:")
    await logger.replay()


# ============================================================================
# EXAMPLE 5: Getting Execution Summary
# ============================================================================

async def example_summary():
    """Get execution summary"""
    
    print("\n=== EXAMPLE 5: Execution Summary ===\n")
    
    execution_id = 5
    logger = EventLogger(execution_id)
    
    # Emit various events
    await logger.emit(EventType.INITIALIZED)
    await logger.emit(EventType.STRATEGY_SELECTED)
    await logger.emit(EventType.SITE_SELECTED, site_name='nike')
    await logger.emit(EventType.SITE_SELECTED, site_name='footlocker')
    await logger.emit(EventType.PRODUCT_FOUND)
    await logger.emit(EventType.CART_SUCCESS)
    await logger.emit(EventType.ORDER_CONFIRMED)
    
    summary = await logger.get_execution_summary()
    
    print(f"Execution ID: {summary['execution_id']}")
    print(f"Status: {summary['status']}")
    print(f"Total Events: {summary['total_events']}")
    print(f"Duration: {summary['duration_seconds']:.2f}s")
    print(f"\nEvent Breakdown:")
    for event_type, count in summary['events_by_type'].items():
        print(f"  {event_type}: {count}")


# ============================================================================
# EXAMPLE 6: Event Filtering
# ============================================================================

async def example_filtering():
    """Filter and analyze events"""
    
    print("\n=== EXAMPLE 6: Event Filtering ===\n")
    
    execution_id = 6
    logger = EventLogger(execution_id)
    
    # Emit mixed events
    await logger.emit(EventType.INITIALIZED)
    await logger.emit(EventType.SITE_SELECTED, site_name='nike')
    await logger.emit(EventType.PRODUCT_FOUND, site_name='nike')
    await logger.emit(EventType.SITE_SELECTED, site_name='footlocker')
    await logger.emit(EventType.PRODUCT_FOUND, site_name='footlocker')
    await logger.emit(EventType.LOCK_ACQUIRED, site_name='nike')
    await logger.emit(EventType.LOCK_FAILED, site_name='footlocker')
    
    # Filter by type
    site_selections = await logger.get_events_by_type(EventType.SITE_SELECTED)
    print(f"Site selections: {len(site_selections)}")
    
    # Filter by site
    nike_events = await logger.get_events_by_site('nike')
    print(f"Nike events: {len(nike_events)}")
    
    # Get full timeline
    timeline = await logger.get_timeline()
    print(f"Total timeline events: {len(timeline)}")


# ============================================================================
# EXAMPLE 7: Async Workflow Integration
# ============================================================================

async def example_workflow_integration():
    """Integrate logging into procurement workflow"""
    
    print("\n=== EXAMPLE 7: Workflow Integration ===\n")
    
    execution_id = 7
    logger = EventLogger(execution_id)
    
    async def procurement_workflow():
        """Simulated procurement workflow with logging"""
        
        try:
            # Initialize
            await logger.emit(EventType.INITIALIZED)
            print("✓ Initialized")
            
            # Select strategy
            await logger.emit(EventType.STRATEGY_SELECTED, metadata={
                'strategy': 'sequential',
                'max_retries': 3,
            })
            print("✓ Strategy selected: sequential")
            
            # Try multiple sites
            sites = ['nike', 'adidas']
            for site in sites:
                await logger.emit(EventType.SITE_SELECTED, site_name=site)
                print(f"✓ Trying {site}")
                
                await logger.emit(EventType.PRODUCT_FOUND, site_name=site)
                print(f"✓ Found product on {site}")
                
                # Simulate success on first site
                if site == 'nike':
                    await logger.emit(EventType.CART_SUCCESS, site_name=site)
                    await logger.emit(EventType.ORDER_CONFIRMED, site_name=site)
                    print(f"✓ Order confirmed on {site}")
                    return
            
        except Exception as e:
            await logger.emit(EventType.FAILED, metadata={
                'error': str(e),
            })
            print(f"✗ Workflow failed: {e}")
    
    # Run workflow
    await procurement_workflow()
    
    # Show summary
    summary = await logger.get_execution_summary()
    print(f"\nFinal Status: {summary['status']}")


# ============================================================================
# Run All Examples
# ============================================================================

async def run_all_examples():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("EVENTLOGGER EXAMPLES")
    print("="*80)
    
    await example_basic_emission()
    # Note: Remaining examples require database setup
    # await example_failure_tracking()
    # await example_multi_site()
    # await example_replay()
    # await example_summary()
    # await example_filtering()
    # await example_workflow_integration()


if __name__ == '__main__':
    asyncio.run(run_all_examples())