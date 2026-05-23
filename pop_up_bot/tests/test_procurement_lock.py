# pop_up_bot/tests/test_procurement_lock.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase

from pop_up_bot.managers.procurement_lock import ProcurementLock


class TestProcurementLockBasic(TestCase):
    """Test basic ProcurementLock functionality"""
    
    @pytest.mark.asyncio
    async def test_lock_initialization(self):
        """Test ProcurementLock initializes with Redis"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            
            assert lock.redis_client is not None
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lock_key_generation(self):
        """Test lock key format"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            key = lock._lock_key(execution_id=123)
            
            assert key == 'lock:procurement:123'
    
    @pytest.mark.asyncio
    async def test_acquire_lock_success(self):
        """Test successfully acquiring a lock"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = True  # Lock acquired
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            acquired = await lock.acquire(execution_id=123, ttl=300)
            
            assert acquired is True
            mock_client.set.assert_called_once()
            
            # Verify SET was called with NX and EX
            call_args = mock_client.set.call_args
            assert call_args[1]['nx'] is True
            assert call_args[1]['ex'] == 300
    
    @pytest.mark.asyncio
    async def test_acquire_lock_failure(self):
        """Test lock acquisition fails when already held"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = False  # Lock not acquired
            mock_client.get.return_value = 'holder-uuid'
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            acquired = await lock.acquire(execution_id=123, ttl=300)
            
            assert acquired is False
    
    @pytest.mark.asyncio
    async def test_release_lock_success(self):
        """Test successfully releasing a lock"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.delete.return_value = 1  # Lock deleted
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            released = await lock.release(execution_id=123)
            
            assert released is True
            mock_client.delete.assert_called_once_with('lock:procurement:123')
    
    @pytest.mark.asyncio
    async def test_release_lock_not_found(self):
        """Test releasing lock that doesn't exist"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.delete.return_value = 0  # Lock not found
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            released = await lock.release(execution_id=123)
            
            assert released is False
    
    @pytest.mark.asyncio
    async def test_is_locked_true(self):
        """Test checking if lock is held"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.exists.return_value = 1  # Lock exists
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            is_locked = await lock.is_locked(execution_id=123)
            
            assert is_locked is True
    
    @pytest.mark.asyncio
    async def test_is_locked_false(self):
        """Test checking if lock is not held"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.exists.return_value = 0  # Lock doesn't exist
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            is_locked = await lock.is_locked(execution_id=123)
            
            assert is_locked is False


class TestProcurementLockRaceCondition(TestCase):
    """Test race condition prevention"""
    
    @pytest.mark.asyncio
    async def test_multiple_executions_compete(self):
        """Test multiple executions competing for same lock"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            
            # First SET succeeds, second fails
            mock_client.set.side_effect = [True, False]
            mock_client.get.return_value = 'holder-uuid'
            
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            
            # Execution 1 acquires lock
            acquired1 = await lock.acquire(execution_id=1, ttl=300)
            assert acquired1 is True
            
            # Execution 2 tries to acquire same lock
            acquired2 = await lock.acquire(execution_id=1, ttl=300)
            assert acquired2 is False
    
    @pytest.mark.asyncio
    async def test_lock_ttl_prevents_deadlock(self):
        """Test lock TTL prevents deadlock/stuck locks"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = True
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            
            # Lock with 5 second TTL
            await lock.acquire(execution_id=123, ttl=5)
            
            # Verify TTL was set
            call_args = mock_client.set.call_args
            assert call_args[1]['ex'] == 5


class TestProcurementLockInfo(TestCase):
    """Test lock information retrieval"""
    
    @pytest.mark.asyncio
    async def test_get_lock_info(self):
        """Test getting information about a lock"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.get.return_value = 'holder-uuid-value'
            mock_client.ttl.return_value = 250  # 250 seconds remaining
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            info = await lock.get_lock_info(execution_id=123)
            
            assert info is not None
            assert info['execution_id'] == 123
            assert info['holder'] == 'holder-uuid-value'
            assert info['ttl_seconds'] == 250
            assert info['locked'] is True
    
    @pytest.mark.asyncio
    async def test_get_lock_info_not_locked(self):
        """Test getting lock info when not locked"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.get.return_value = None
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            info = await lock.get_lock_info(execution_id=123)
            
            assert info is None
    
    @pytest.mark.asyncio
    async def test_get_all_locks(self):
        """Test retrieving all active locks"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.keys.return_value = [
                'lock:procurement:1',
                'lock:procurement:2',
                'lock:procurement:3',
            ]
            mock_client.get.side_effect = ['holder1', 'holder2', 'holder3']
            mock_client.ttl.side_effect = [300, 250, 200]
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            all_locks = await lock.get_all_locks()
            
            assert len(all_locks) == 3
            assert all_locks[0]['execution_id'] == 1
            assert all_locks[1]['execution_id'] == 2
            assert all_locks[2]['execution_id'] == 3


class TestProcurementLockMaintenance(TestCase):
    """Test maintenance operations"""
    
    @pytest.mark.asyncio
    async def test_force_release(self):
        """Test force releasing a stuck lock"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.delete.return_value = 1
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            released = await lock.force_release(execution_id=123)
            
            assert released is True
    
    @pytest.mark.asyncio
    async def test_clear_all_locks(self):
        """Test clearing all locks"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.keys.return_value = [
                'lock:procurement:1',
                'lock:procurement:2',
            ]
            mock_client.delete.return_value = 2
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            count = await lock.clear_all_locks()
            
            assert count == 2


class TestProcurementLockWorkflow(TestCase):
    """Test complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_checkout_workflow(self):
        """Test complete acquisition → checkout → release workflow"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = True
            mock_client.delete.return_value = 1
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            
            # Try to acquire lock
            acquired = await lock.acquire(execution_id=123, ttl=300)
            assert acquired is True
            
            # Simulate checkout process
            # (In real code, process payment, confirm order, etc.)
            
            # Release lock
            released = await lock.release(execution_id=123)
            assert released is True
    
    @pytest.mark.asyncio
    async def test_lost_race_scenario(self):
        """Test scenario where execution loses race"""
        with patch('pop_up_bot.managers.procurement_lock.redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.set.return_value = False  # Lost race
            mock_client.get.return_value = 'winner-uuid'
            mock_client.ttl.return_value = 250  # TTL remaining
            mock_redis.return_value = mock_client
            
            lock = ProcurementLock()
            
            # Try to acquire lock - fail
            acquired = await lock.acquire(execution_id=123, ttl=300)
            assert acquired is False
            
            # Check who has the lock
            info = await lock.get_lock_info(execution_id=123)
            assert info is not None
            assert info['holder'] == 'winner-uuid'
            assert info['ttl_seconds'] == 250


if __name__ == '__main__':
    pytest.main([__file__, '-v'])