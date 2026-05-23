# pop_up_bot/managers/procurement_lock.py

import logging
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class ProcurementLock:
    """
    Redis-based distributed lock to prevent race conditions and double-purchases.
    
    CRITICAL for concurrency safety when multiple executions compete for the same product.
    
    Prevents:
    - Double-charges (same item bought twice)
    - Inventory overselling
    - Payment conflicts
    
    Key Methods:
    - acquire(execution_id, ttl=60) → bool
      * Returns True if this execution won the lock
      * Returns False if another execution already has it
    - release(execution_id) → None
    - is_locked(execution_id) → bool
    
    Usage:
        lock = ProcurementLock()
        
        if await lock.acquire(execution_id, ttl=300):  # 5 minute lock
            # Proceed to checkout - we won the race
            try:
                await process_payment()
                await confirm_order()
            finally:
                await lock.release(execution_id)
        else:
            # Another execution already has the lock
            logger.info("Lost the race - another bot already secured this item")
            return
    
    Lock Behavior:
    - Execution A acquires lock
    - Execution B tries to acquire → fails
    - Execution A releases lock OR TTL expires
    - Lock is now available for next execution
    """
    
    def __init__(self):
        """Initialize ProcurementLock with Redis connection"""
        try:
            # Get Redis connection from Django settings
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            logger.info("ProcurementLock initialized with Redis")
        
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing ProcurementLock: {e}")
            raise
    
    def _lock_key(self, execution_id: int) -> str:
        """
        Generate Redis lock key for an execution.
        
        Format: lock:procurement:{execution_id}
        """
        return f"lock:procurement:{execution_id}"
    
    async def acquire(self, execution_id: int, ttl: int = 60) -> bool:
        """
        Attempt to acquire a lock for this execution.
        
        Uses Redis SET with NX (only if not exists) for atomic lock acquisition.
        Auto-expires after ttl seconds.
        
        Args:
            execution_id: ID of ProcurementExecution
            ttl: Lock time-to-live in seconds (default 60)
        
        Returns:
            True if lock acquired (this execution won the race)
            False if lock already held by another execution
        
        Example:
            if await lock.acquire(execution_id=123, ttl=300):
                print("Won the race! Proceed to checkout")
            else:
                print("Lost the race - another execution got it first")
        """
        lock_key = self._lock_key(execution_id)
        lock_value = str(uuid.uuid4())  # Unique value for this lock holder
        
        try:
            # SET with NX (only if not exists) and EX (expire in ttl seconds)
            # This is atomic and prevents race conditions
            acquired = self.redis_client.set(
                lock_key,
                lock_value,
                nx=True,  # Only set if key doesn't exist
                ex=ttl,   # Expire after ttl seconds
            )
            
            if acquired:
                logger.info(
                    f"Lock acquired for execution {execution_id} "
                    f"(TTL: {ttl}s, value: {lock_value[:8]}...)"
                )
                return True
            else:
                current_holder = self.redis_client.get(lock_key)
                logger.warning(
                    f"Lock already held for execution {execution_id} "
                    f"(held by: {current_holder[:8] if current_holder else 'unknown'}...)"
                )
                return False
        
        except redis.RedisError as e:
            logger.error(f"Redis error acquiring lock: {e}", exc_info=True)
            raise
    
    async def release(self, execution_id: int) -> bool:
        """
        Release the lock for this execution.
        
        Args:
            execution_id: ID of ProcurementExecution
        
        Returns:
            True if lock was released
            False if lock was not found (may have expired)
        
        Example:
            try:
                await process_checkout()
            finally:
                await lock.release(execution_id)
        """
        lock_key = self._lock_key(execution_id)
        
        try:
            deleted = self.redis_client.delete(lock_key)
            
            if deleted:
                logger.info(f"Lock released for execution {execution_id}")
                return True
            else:
                logger.warning(
                    f"Lock not found for execution {execution_id} "
                    f"(may have expired)"
                )
                return False
        
        except redis.RedisError as e:
            logger.error(f"Redis error releasing lock: {e}", exc_info=True)
            raise
    
    async def is_locked(self, execution_id: int) -> bool:
        """
        Check if a lock is currently held for this execution.
        
        Args:
            execution_id: ID of ProcurementExecution
        
        Returns:
            True if lock is held
            False if lock is not held or has expired
        
        Example:
            if await lock.is_locked(execution_id):
                print("Someone is still checking out")
            else:
                print("Lock is available")
        """
        lock_key = self._lock_key(execution_id)
        
        try:
            exists = self.redis_client.exists(lock_key) > 0
            logger.debug(f"Lock check for execution {execution_id}: {exists}")
            return exists
        
        except redis.RedisError as e:
            logger.error(f"Redis error checking lock: {e}", exc_info=True)
            raise
    
    async def get_lock_info(self, execution_id: int) -> Optional[dict]:
        """
        Get information about a lock.
        
        Args:
            execution_id: ID of ProcurementExecution
        
        Returns:
            Dictionary with lock info or None if not locked
        
        Example:
            info = await lock.get_lock_info(execution_id)
            if info:
                print(f"Locked by: {info['holder']}")
                print(f"TTL: {info['ttl']}s")
        """
        lock_key = self._lock_key(execution_id)
        
        try:
            holder = self.redis_client.get(lock_key)
            
            if not holder:
                return None
            
            ttl = self.redis_client.ttl(lock_key)
            
            return {
                'execution_id': execution_id,
                'holder': holder,
                'ttl_seconds': ttl if ttl > 0 else 0,
                'locked': True,
            }
        
        except redis.RedisError as e:
            logger.error(f"Redis error getting lock info: {e}", exc_info=True)
            raise
    
    async def force_release(self, execution_id: int) -> bool:
        """
        Force release a lock (for emergency/timeout scenarios).
        
        Use with caution - should only be used after confirming the
        original execution is no longer using the lock.
        
        Args:
            execution_id: ID of ProcurementExecution
        
        Returns:
            True if lock was released
            False if lock was not found
        
        Example:
            # Force release lock that's been held too long
            if await lock.force_release(execution_id):
                logger.warning(f"Forcefully released stuck lock for {execution_id}")
        """
        logger.warning(f"Force releasing lock for execution {execution_id}")
        return await self.release(execution_id)
    
    async def get_all_locks(self) -> list:
        """
        Get all active procurement locks.
        
        Useful for debugging and monitoring.
        
        Returns:
            List of dicts with info about all active locks
        
        Example:
            locks = await lock.get_all_locks()
            for lock_info in locks:
                print(f"Execution {lock_info['execution_id']} has lock")
        """
        try:
            pattern = self._lock_key('*')
            keys = self.redis_client.keys(pattern)
            
            locks = []
            for key in keys:
                # Extract execution_id from key (format: lock:procurement:{id})
                execution_id = int(key.split(':')[-1])
                
                holder = self.redis_client.get(key)
                ttl = self.redis_client.ttl(key)
                
                locks.append({
                    'execution_id': execution_id,
                    'holder': holder,
                    'ttl_seconds': ttl if ttl > 0 else 0,
                })
            
            logger.debug(f"Found {len(locks)} active locks")
            return locks
        
        except redis.RedisError as e:
            logger.error(f"Redis error getting all locks: {e}", exc_info=True)
            raise
    
    async def clear_all_locks(self) -> int:
        """
        Clear all procurement locks.
        
        Use only for maintenance/testing!
        
        Returns:
            Number of locks cleared
        
        Example:
            # Clear all locks during maintenance
            count = await lock.clear_all_locks()
            logger.info(f"Cleared {count} locks")
        """
        logger.warning("Clearing ALL procurement locks!")
        
        try:
            pattern = self._lock_key('*')
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                return 0
            
            deleted = self.redis_client.delete(*keys)
            logger.warning(f"Cleared {deleted} locks")
            return deleted
        
        except redis.RedisError as e:
            logger.error(f"Redis error clearing locks: {e}", exc_info=True)
            raise
    
    def __str__(self):
        return "ProcurementLock(Redis)"
    
    def __repr__(self):
        return self.__str__()