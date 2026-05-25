# pop_up_bot/tests/test_orchestrator.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from django.test import TestCase

from pop_up_bot.orchestrator import (
    BotOrchestrator,
    ExecutionResult,
    ExecutionStatus,
    SearchParameters
)


class TestExecutionResult(TestCase):
    """Test ExecutionResult model"""
    
    def test_result_creation_success(self):
        """Test creating a successful result"""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            product_name='Air Jordan 1',
            site='nike',
            order_id='ORD-123',
            item_price=169.99,
            duration_seconds=45.2,
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.product_name == 'Air Jordan 1'
        assert result.site == 'nike'
        assert result.order_id == 'ORD-123'
        assert result.item_price == 169.99
    
    def test_result_creation_failure(self):
        """Test creating a failed result"""
        result = ExecutionResult(
            status=ExecutionStatus.FAILED,
            error='Product out of stock',
            duration_seconds=30.0,
        )
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error == 'Product out of stock'
        assert result.product_name is None
    
    def test_result_to_dict(self):
        """Test converting result to dictionary"""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            product_name='Air Jordan 1',
            site='nike',
            order_id='ORD-123',
            item_price=169.99,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'success'
        assert result_dict['product_name'] == 'Air Jordan 1'
        assert result_dict['site'] == 'nike'
        assert result_dict['order_id'] == 'ORD-123'
    
    def test_result_str(self):
        """Test result string representation"""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            site='nike',
            order_id='ORD-123',
        )
        
        assert 'success' in str(result)
        assert 'nike' in str(result)

class TestBotOrchestrator(TestCase):
    """Test BotOrchestrator"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        mock_strategy_factory = MagicMock()
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_event_logger = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        assert orchestrator.execution_id == 123
        assert orchestrator.status == ExecutionStatus.PENDING
        assert orchestrator.strategy is None
    
    @pytest.mark.asyncio
    async def test_run_sequential_success(self):
        """Test sequential strategy with success"""
        # Mock strategy
        mock_strategy = AsyncMock()
        mock_strategy.get_site_order = MagicMock(
            return_value=['nike', 'footlocker']
        )
        mock_strategy.should_attempt_next_site = MagicMock(return_value=False)
        mock_strategy.mark_attempted = MagicMock()
        mock_strategy.mark_failed = MagicMock()
        
        # Mock factory
        mock_strategy_factory = MagicMock()
        mock_strategy_factory.create = MagicMock(return_value=mock_strategy)
        
        # Mock managers
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_procurement_lock.acquire = AsyncMock(return_value=True)
        mock_event_logger = AsyncMock()
        mock_event_logger.emit = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        # Mock _attempt_site to return success
        orchestrator._attempt_site = AsyncMock(
            return_value={
                'success': True,
                'order_id': 'ORD-123',
                'price': 169.99,
            }
        )
        
        result = await orchestrator.run(
            product_name='Air Jordan 1',
            size='US 10',
            strategy_name='sequential',
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert result.order_id == 'ORD-123'
        assert result.item_price == 169.99
        assert orchestrator.locked_site == 'nike'
    
    @pytest.mark.asyncio
    async def test_run_sequential_all_failed(self):
        """Test sequential strategy with all sites failing"""
        # Mock strategy
        mock_strategy = AsyncMock()
        mock_strategy.get_site_order = MagicMock(
            return_value=['nike', 'footlocker']
        )
        mock_strategy.should_attempt_next_site = MagicMock(return_value=True)
        mock_strategy.mark_attempted = MagicMock()
        mock_strategy.mark_failed = MagicMock()
        
        # Mock factory
        mock_strategy_factory = MagicMock()
        mock_strategy_factory.create = MagicMock(return_value=mock_strategy)
        
        # Mock managers
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_event_logger = AsyncMock()
        mock_event_logger.emit = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        # Mock _attempt_site to always fail
        orchestrator._attempt_site = AsyncMock(
            return_value={'success': False, 'error': 'Out of stock'}
        )
        
        result = await orchestrator.run(
            product_name='Air Jordan 1',
            size='US 10',
            strategy_name='sequential',
        )
        
        assert result.status == ExecutionStatus.FAILED
        assert orchestrator.locked_site is None
    
    @pytest.mark.asyncio
    async def test_run_lost_lock_race(self):
        """Test losing the lock race to another execution"""
        # Mock strategy
        mock_strategy = AsyncMock()
        mock_strategy.get_site_order = MagicMock(return_value=['nike'])
        
        # Mock factory
        mock_strategy_factory = MagicMock()
        mock_strategy_factory.create = MagicMock(return_value=mock_strategy)
        
        # Mock managers
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_procurement_lock.acquire = AsyncMock(return_value=False)  # Lost race
        mock_event_logger = AsyncMock()
        mock_event_logger.emit = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        # Mock _attempt_site to succeed
        orchestrator._attempt_site = AsyncMock(
            return_value={
                'success': True,
                'order_id': 'ORD-123',
                'price': 169.99,
            }
        )
        
        result = await orchestrator.run(
            product_name='Air Jordan 1',
            size='US 10',
            strategy_name='sequential',
        )
        
        assert result.status == ExecutionStatus.ABANDONED
        assert result.error == 'Another execution secured the item first'
    
    @pytest.mark.asyncio
    async def test_attempt_site(self):
        """Test attempting a single site"""
        mock_strategy_factory = MagicMock()
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_event_logger = AsyncMock()
        mock_event_logger.emit = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        # Set search parameters first
        orchestrator.search_params = SearchParameters(
            product_name='Air Jordan 1',
            size='US 10',
            color='Red',
        )
        
        result = await orchestrator._attempt_site(site='nike')
        
        assert result is not None
        assert result['site'] == 'nike'
        assert result['product_name'] == 'Air Jordan 1'
        assert result['size'] == 'US 10'
    
    @pytest.mark.asyncio
    async def test_try_acquire_lock_success(self):
        """Test successfully acquiring lock"""
        mock_strategy_factory = MagicMock()
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_procurement_lock.acquire = AsyncMock(return_value=True)
        mock_event_logger = AsyncMock()
        mock_event_logger.emit = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        acquired = await orchestrator._try_acquire_lock('nike')
        
        assert acquired is True
        mock_procurement_lock.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_try_acquire_lock_failure(self):
        """Test failing to acquire lock"""
        mock_strategy_factory = MagicMock()
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_procurement_lock.acquire = AsyncMock(return_value=False)
        mock_event_logger = AsyncMock()
        mock_event_logger.emit = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        acquired = await orchestrator._try_acquire_lock('nike')
        
        assert acquired is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting orchestrator statistics"""
        mock_strategy_factory = MagicMock()
        mock_strategy = AsyncMock()
        mock_strategy.get_stats = MagicMock(return_value={'sites': ['nike']})
        mock_strategy_factory.create = MagicMock(return_value=mock_strategy)
        
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_event_logger = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        orchestrator.strategy = mock_strategy
        orchestrator.locked_site = 'nike'
        
        stats = orchestrator.get_stats()
        
        assert stats['execution_id'] == 123
        assert stats['locked_site'] == 'nike'
        assert 'duration_seconds' in stats
    
    @pytest.mark.asyncio
    async def test_orchestrator_str(self):
        """Test orchestrator string representation"""
        mock_strategy_factory = MagicMock()
        mock_session_manager = AsyncMock()
        mock_procurement_lock = AsyncMock()
        mock_event_logger = AsyncMock()
        
        orchestrator = BotOrchestrator(
            execution_id=123,
            strategy_factory=mock_strategy_factory,
            session_manager=mock_session_manager,
            procurement_lock=mock_procurement_lock,
            event_logger=mock_event_logger,
        )
        
        assert 'BotOrchestrator' in str(orchestrator)
        assert '123' in str(orchestrator)
 
 
class TestExecutionStatus(TestCase):
    """Test ExecutionStatus enum"""
    
    def test_all_statuses_exist(self):
        """Test all execution statuses are defined"""
        assert ExecutionStatus.PENDING.value == 'pending'
        assert ExecutionStatus.RUNNING.value == 'running'
        assert ExecutionStatus.SUCCESS.value == 'success'
        assert ExecutionStatus.FAILED.value == 'failed'
        assert ExecutionStatus.ABANDONED.value == 'abandoned'




if __name__ == '__main__':
    pytest.main([__file__, '-v'])