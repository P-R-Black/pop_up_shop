# pop_up_bot/tests/test_event_logger.py

import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from asgiref.sync import sync_to_async

from pop_up_bot.models import ProcurementExecution, ProcurementEvent
from pop_up_bot.managers.event_logger import EventLogger, EventType


# ============================================================================
# Helper Functions for Async ORM Operations
# ============================================================================

async def async_create_execution(**kwargs):
    """Async wrapper for creating ProcurementExecution"""
    from django.utils import timezone
    from pop_up_bot.models import ProcurementRequest
    
    # Create procurement request first (required FK)
    request = await sync_to_async(ProcurementRequest.objects.create)(
        status='pending',
        procurement_type='inventory',
        max_price=200.00,  # Required field
    )
    
    defaults = {
        'procurement_request': request,
        'status': 'pending',
        'strategy_used': 'sequential',
        'started_at': timezone.now(),
    }
    defaults.update(kwargs)
    return await sync_to_async(ProcurementExecution.objects.create)(**defaults)


async def async_get_event_count(execution_id: int):
    """Async wrapper to count events"""
    def _count():
        return ProcurementEvent.objects.filter(
            bot_execution_id=execution_id
        ).count()
    return await sync_to_async(_count)()


async def async_get_events(execution_id: int):
    """Async wrapper to get all events"""
    def _get():
        return list(
            ProcurementEvent.objects.filter(
                bot_execution_id=execution_id
            ).order_by('timestamp').values()
        )
    return await sync_to_async(_get)()


# ============================================================================
# Tests
# ============================================================================

class TestEventLogger(TestCase):
    """Test EventLogger functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_event_logger_initialization(self):
        """Test EventLogger initializes correctly"""
        execution = await async_create_execution()
        
        logger = EventLogger(execution.id)
        
        assert logger.execution_id == execution.id
        assert logger.start_time is not None
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_emit_simple_event(self):
        """Test emitting a simple event"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        await logger.emit(EventType.INITIALIZED)
        
        count = await async_get_event_count(execution.id)
        assert count == 1
        
        events = await async_get_events(execution.id)
        assert events[0]['event_type'] == EventType.INITIALIZED.value
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_emit_event_with_site(self):
        """Test emitting event with site name"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        
        events = await async_get_events(execution.id)
        assert events[0]['site_name'] == 'nike'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_emit_event_with_metadata(self):
        """Test emitting event with metadata"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        metadata = {
            'product_name': 'Air Jordan 1',
            'price': 170.00,
            'url': 'https://nike.com/product/123',
        }
        
        await logger.emit(
            EventType.PRODUCT_FOUND,
            site_name='nike',
            metadata=metadata,
        )
        
        events = await async_get_events(execution.id)
        assert events[0]['metadata']['product_name'] == 'Air Jordan 1'
        assert events[0]['metadata']['price'] == 170.00
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_timeline(self):
        """Test retrieving event timeline"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit multiple events
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.STRATEGY_SELECTED, metadata={'strategy': 'sequential'})
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        
        timeline = await logger.get_timeline()
        
        assert len(timeline) == 3
        assert timeline[0]['event_type'] == EventType.INITIALIZED.value
        assert timeline[1]['event_type'] == EventType.STRATEGY_SELECTED.value
        assert timeline[2]['event_type'] == EventType.SITE_SELECTED.value
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_events_by_type(self):
        """Test filtering events by type"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit mixed events
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.PRODUCT_FOUND, site_name='nike')
        await logger.emit(EventType.SITE_SELECTED, site_name='footlocker')
        
        site_selected = await logger.get_events_by_type(EventType.SITE_SELECTED)
        
        assert len(site_selected) == 2
        assert all(e['event_type'] == EventType.SITE_SELECTED.value for e in site_selected)
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_events_by_site(self):
        """Test filtering events by site"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit events for different sites
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.PRODUCT_FOUND, site_name='nike')
        await logger.emit(EventType.SITE_SELECTED, site_name='footlocker')
        
        nike_events = await logger.get_events_by_site('nike')
        
        assert len(nike_events) == 2
        assert all(e['site_name'] == 'nike' for e in nike_events)
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_failure_point_with_failure(self):
        """Test finding failure event"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit sequence with failure
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(
            EventType.FAILED,
            site_name='nike',
            metadata={'reason': 'Out of stock'},
        )
        
        failure = await logger.get_failure_point()
        
        assert failure is not None
        assert failure['event_type'] == EventType.FAILED.value
        assert failure['metadata']['reason'] == 'Out of stock'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_failure_point_no_failure(self):
        """Test failure point when execution is successful"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit successful sequence
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.ORDER_CONFIRMED, site_name='nike')
        
        failure = await logger.get_failure_point()
        
        assert failure is None
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_execution_summary_successful(self):
        """Test getting summary for successful execution"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit successful sequence
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.STRATEGY_SELECTED)
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.PRODUCT_FOUND)
        await logger.emit(EventType.ORDER_CONFIRMED)
        
        summary = await logger.get_execution_summary()
        
        assert summary['status'] == 'success'
        assert summary['total_events'] == 5
        assert 'duration_seconds' in summary
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_execution_summary_failed(self):
        """Test getting summary for failed execution"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit failed sequence
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.FAILED, metadata={'reason': 'Captcha'})
        
        summary = await logger.get_execution_summary()
        
        assert summary['status'] == 'failed'
        assert summary['total_events'] == 3
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_execution_summary_abandoned(self):
        """Test getting summary for abandoned execution"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit abandoned sequence
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.SITE_SELECTED, site_name='nike')
        await logger.emit(EventType.ABANDONED, metadata={'reason': 'Timeout'})
        
        summary = await logger.get_execution_summary()
        
        assert summary['status'] == 'abandoned'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_event_timestamp_ordering(self):
        """Test events are ordered by timestamp"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit events
        await logger.emit(EventType.INITIALIZED)
        await logger.emit(EventType.SITE_SELECTED)
        await logger.emit(EventType.PRODUCT_FOUND)
        
        timeline = await logger.get_timeline()
        
        # Check timestamps are in order
        for i in range(len(timeline) - 1):
            assert timeline[i]['timestamp'] <= timeline[i + 1]['timestamp']
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_multiple_executions_isolated(self):
        """Test events are isolated per execution"""
        execution1 = await async_create_execution()
        execution2 = await async_create_execution()
        
        logger1 = EventLogger(execution1.id)
        logger2 = EventLogger(execution2.id)
        
        # Emit events to different executions
        await logger1.emit(EventType.INITIALIZED)
        await logger1.emit(EventType.SITE_SELECTED, site_name='nike')
        
        await logger2.emit(EventType.INITIALIZED)
        await logger2.emit(EventType.SITE_SELECTED, site_name='footlocker')
        
        timeline1 = await logger1.get_timeline()
        timeline2 = await logger2.get_timeline()
        
        assert len(timeline1) == 2
        assert len(timeline2) == 2
        assert timeline1[1]['site_name'] == 'nike'
        assert timeline2[1]['site_name'] == 'footlocker'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_empty_timeline(self):
        """Test getting timeline with no events"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        timeline = await logger.get_timeline()
        
        assert timeline == []
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_event_types_enum(self):
        """Test all EventType values are valid"""
        execution = await async_create_execution()
        logger = EventLogger(execution.id)
        
        # Emit one of each event type
        for event_type in EventType:
            await logger.emit(event_type)
        
        count = await async_get_event_count(execution.id)
        
        assert count == len(EventType)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])