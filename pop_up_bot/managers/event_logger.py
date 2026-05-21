# pop_up_bot/managers/event_logger.py

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """All possible procurement event types"""
    
    # Initialization
    INITIALIZED = 'INITIALIZED'
    
    # Strategy & Planning
    STRATEGY_SELECTED = 'STRATEGY_SELECTED'
    
    # Site Selection & Navigation
    SITE_SELECTED = 'SITE_SELECTED'
    
    # Product Discovery
    PRODUCT_FOUND = 'PRODUCT_FOUND'
    SIZE_SELECTED = 'SIZE_SELECTED'
    
    # Cart Operations
    CART_SUCCESS = 'CART_SUCCESS'
    
    # Locking
    LOCK_ACQUIRED = 'LOCK_ACQUIRED'
    LOCK_FAILED = 'LOCK_FAILED'
    
    # Checkout Flow
    CHECKOUT_STARTED = 'CHECKOUT_STARTED'
    PAYMENT_SUBMITTED = 'PAYMENT_SUBMITTED'
    
    # Order Confirmation
    ORDER_CONFIRMED = 'ORDER_CONFIRMED'
    
    # Terminal States
    FAILED = 'FAILED'
    ABANDONED = 'ABANDONED'


class EventLogger:
    """
    Logs procurement events for audit trail and debugging.
    
    Emits structured events at each major state transition,
    persisted to database for full replay capability.
    
    Features:
    - Async-safe event emission
    - Structured metadata capture
    - Chronological event history
    - Failure analysis tools
    
    Usage:
        logger = EventLogger(execution_id=execution.id)
        
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.STRATEGY_SELECTED, strategy='sequential')
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.PRODUCT_FOUND, product_url='https://...')
        
        timeline = await logger.get_timeline()
    """
    
    def __init__(self, execution_id: int):
        """
        Initialize EventLogger for an execution.
        
        Args:
            execution_id: ID of ProcurementExecution to log events for
        """
        self.execution_id = execution_id
        self.start_time = datetime.now()
        logger.info(f"EventLogger initialized for execution {execution_id}")
    
    async def emit(
        self,
        event_type: EventType,
        site_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit an event to the database.
        
        Args:
            event_type: Type of event
            site_name: Which site (nike, footlocker, etc)
            metadata: Additional event data (JSON-serializable)
        
        Example:
            await logger.emit(
                EventType.PRODUCT_FOUND,
                site_name='nike',
                metadata={
                    'product_url': 'https://nike.com/product/123',
                    'product_name': 'Air Jordan 1',
                    'price': 170.00,
                }
            )
        """
        from pop_up_bot.models import ProcurementEvent, ProcurementExecution
        
        try:
            # Ensure metadata is a dict
            if metadata is None:
                metadata = {}
            
            # Create event in database using async wrapper
            await sync_to_async(ProcurementEvent.objects.create)(
                bot_execution_id=self.execution_id,
                event_type=event_type.value,
                timestamp=datetime.now(),
                site_name=site_name,
                metadata=metadata,
            )
            
            logger.info(
                f"Event emitted: {event_type.value} "
                f"(execution: {self.execution_id}, site: {site_name})"
            )
        
        except Exception as e:
            logger.error(f"Failed to emit event: {e}", exc_info=True)
            raise
    
    async def get_timeline(self) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of all events for this execution.
        
        Returns:
            List of events with timestamps, ordered chronologically
        
        Example:
            timeline = await logger.get_timeline()
            for event in timeline:
                print(f"{event['timestamp']}: {event['event_type']}")
        """
        from pop_up_bot.models import ProcurementEvent
        
        try:
            def _get_events():
                return list(
                    ProcurementEvent.objects.filter(
                        bot_execution_id=self.execution_id
                    ).order_by('timestamp').values()
                )
            
            events = await sync_to_async(_get_events)()
            logger.debug(f"Retrieved {len(events)} events for execution {self.execution_id}")
            return events
        
        except Exception as e:
            logger.error(f"Failed to retrieve timeline: {e}", exc_info=True)
            return []
    
    async def get_failure_point(self) -> Optional[Dict[str, Any]]:
        """
        Find where execution failed.
        
        Returns the first FAILED or ABANDONED event, or None if successful.
        
        Returns:
            Event that caused failure, or None if no failure
        
        Example:
            failure = await logger.get_failure_point()
            if failure:
                print(f"Failed at: {failure['event_type']}")
                print(f"Details: {failure['metadata']}")
        """
        from pop_up_bot.models import ProcurementEvent
        
        try:
            def _find_failure():
                failure_events = ProcurementEvent.objects.filter(
                    bot_execution_id=self.execution_id,
                    event_type__in=[EventType.FAILED.value, EventType.ABANDONED.value]
                ).order_by('timestamp').values().first()
                return failure_events
            
            failure = await sync_to_async(_find_failure)()
            
            if failure:
                logger.warning(f"Found failure event: {failure['event_type']}")
            
            return failure
        
        except Exception as e:
            logger.error(f"Failed to find failure point: {e}", exc_info=True)
            return None
    
    async def get_events_by_type(self, event_type: EventType) -> List[Dict[str, Any]]:
        """
        Get all events of a specific type for this execution.
        
        Args:
            event_type: EventType to filter by
        
        Returns:
            List of events matching the type
        
        Example:
            site_selections = await logger.get_events_by_type(EventType.SITE_SELECTED)
            for event in site_selections:
                print(f"Tried site: {event['site_name']}")
        """
        from pop_up_bot.models import ProcurementEvent
        
        try:
            def _get_typed_events():
                return list(
                    ProcurementEvent.objects.filter(
                        bot_execution_id=self.execution_id,
                        event_type=event_type.value,
                    ).order_by('timestamp').values()
                )
            
            events = await sync_to_async(_get_typed_events)()
            logger.debug(f"Retrieved {len(events)} {event_type.value} events")
            return events
        
        except Exception as e:
            logger.error(f"Failed to retrieve events by type: {e}", exc_info=True)
            return []
    
    async def get_events_by_site(self, site_name: str) -> List[Dict[str, Any]]:
        """
        Get all events for a specific site.
        
        Args:
            site_name: Site to filter by (nike, footlocker, etc)
        
        Returns:
            List of events for that site
        
        Example:
            nike_events = await logger.get_events_by_site('nike')
            for event in nike_events:
                print(f"{event['timestamp']}: {event['event_type']}")
        """
        from pop_up_bot.models import ProcurementEvent
        
        try:
            def _get_site_events():
                return list(
                    ProcurementEvent.objects.filter(
                        bot_execution_id=self.execution_id,
                        site_name=site_name,
                    ).order_by('timestamp').values()
                )
            
            events = await sync_to_async(_get_site_events)()
            logger.debug(f"Retrieved {len(events)} events for site {site_name}")
            return events
        
        except Exception as e:
            logger.error(f"Failed to retrieve site events: {e}", exc_info=True)
            return []
    
    async def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for this execution.
        
        Returns:
            Dictionary with event counts and timeline
        
        Example:
            summary = await logger.get_execution_summary()
            print(f"Total events: {summary['total_events']}")
            print(f"Duration: {summary['duration_seconds']}s")
            print(f"Status: {summary['status']}")
        """
        from pop_up_bot.models import ProcurementEvent
        
        try:
            def _get_stats():
                all_events = ProcurementEvent.objects.filter(
                    bot_execution_id=self.execution_id
                ).order_by('timestamp')
                
                total = all_events.count()
                events_by_type = {}
                
                for event_type in EventType:
                    count = all_events.filter(
                        event_type=event_type.value
                    ).count()
                    if count > 0:
                        events_by_type[event_type.value] = count
                
                # Determine status
                status = 'pending'
                if all_events.filter(event_type=EventType.ORDER_CONFIRMED.value).exists():
                    status = 'success'
                elif all_events.filter(event_type=EventType.FAILED.value).exists():
                    status = 'failed'
                elif all_events.filter(event_type=EventType.ABANDONED.value).exists():
                    status = 'abandoned'
                
                # Calculate duration
                first_event = all_events.first()
                last_event = all_events.last()
                
                duration_seconds = 0
                if first_event and last_event:
                    duration_seconds = (
                        last_event.timestamp - first_event.timestamp
                    ).total_seconds()
                
                return {
                    'execution_id': self.execution_id,
                    'total_events': total,
                    'status': status,
                    'duration_seconds': duration_seconds,
                    'events_by_type': events_by_type,
                }
            
            summary = await sync_to_async(_get_stats)()
            logger.info(f"Execution summary: {summary}")
            return summary
        
        except Exception as e:
            logger.error(f"Failed to get execution summary: {e}", exc_info=True)
            return {
                'execution_id': self.execution_id,
                'error': str(e),
            }
    
    async def replay(self) -> None:
        """
        Print full event timeline for debugging/replay.
        
        Useful for understanding exactly what happened during execution.
        
        Example:
            await logger.replay()
            # Output:
            # 2026-05-20 10:30:00: INITIALIZED
            # 2026-05-20 10:30:01: STRATEGY_SELECTED (sequential)
            # 2026-05-20 10:30:02: SITE_SELECTED (nike)
            # ...
        """
        timeline = await self.get_timeline()
        
        if not timeline:
            logger.info("No events recorded for this execution")
            return
        
        logger.info(f"\n{'='*80}")
        logger.info(f"EXECUTION REPLAY: {self.execution_id}")
        logger.info(f"{'='*80}\n")
        
        for i, event in enumerate(timeline, 1):
            timestamp = event.get('timestamp', 'N/A')
            event_type = event.get('event_type', 'UNKNOWN')
            site = event.get('site_name', '-')
            metadata = event.get('metadata', {})
            
            logger.info(f"{i}. [{timestamp}] {event_type} (site: {site})")
            
            if metadata:
                for key, value in metadata.items():
                    logger.info(f"   → {key}: {value}")
        
        logger.info(f"\n{'='*80}\n")