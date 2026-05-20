# pop_up_bot/tests/test_cookie_manager.py

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from django.test import TestCase
from django.utils import timezone
from asgiref.sync import sync_to_async
from pop_up_bot.models import CookieModel
from pop_up_bot.managers.cookie_manager import CookieManager, CookieManagerDjango
import uuid


"""
Helper Functions
"""

# Helper functions for async database operations
async def async_create(*args, **kwargs):
    """Async wrapper for model creation"""
    return await sync_to_async(CookieModel.objects.create)(*args, **kwargs)


async def async_count():
    """Async wrapper for count"""
    return await sync_to_async(CookieModel.objects.count)()


async def async_first():
    """Async wrapper for first"""
    return await sync_to_async(CookieModel.objects.first)()


async def async_get(**kwargs):
    """Async wrapper for get"""
    return await sync_to_async(CookieModel.objects.get)(**kwargs)


async def async_filter(**kwargs):
    """Async wrapper for filter - returns queryset"""
    return await sync_to_async(CookieModel.objects.filter)(**kwargs)


async def async_filter_count(**kwargs):
    """Async wrapper for filter().count()"""
    def _filter_count():
        return CookieModel.objects.filter(**kwargs).count()
    return await sync_to_async(_filter_count)()


async def async_all_delete(**kwargs):
    """Async wrapper for delete all matching"""
    def _delete():
        return CookieModel.objects.filter(**kwargs).delete()
    count, _ = await sync_to_async(_delete)()
    return count




class TestCookieModel(TestCase):
    """Test CookieModel database functionality"""
    
    def setUp(self):
        """Create test cookies"""
        # Use unique identifiers per test to avoid conflicts
        import uuid
        self.unique_id = str(uuid.uuid4())[:8]
        
        self.cookie1 = CookieModel.objects.create(
            site_name=f'nike-{self.unique_id}',
            name=f'session_id-{self.unique_id}',
            value='abc123',
            domain=f'.nike-{self.unique_id}.com',
            path='/',
            http_only=True,
            secure=True,
            same_site='Lax',
        )
        
        self.cookie2 = CookieModel.objects.create(
            site_name=f'nike-{self.unique_id}',
            name=f'user_pref-{self.unique_id}',
            value='dark_mode=true',
            domain=f'.nike-{self.unique_id}.com',
            path='/',
            same_site='Strict',
        )
    
    def test_cookie_creation(self):
        """Test cookie model creation"""
        assert CookieModel.objects.count() >= 2  # At least 2 from setUp
        assert self.cookie1.site_name.startswith('nike-')
        assert self.cookie1.name.startswith('session_id-')
    
    def test_cookie_is_expired_false(self):
        """Test is_expired returns False for non-expired cookies"""
        assert self.cookie1.is_expired is False
    
    def test_cookie_is_expired_true(self):
        """Test is_expired returns True for expired cookies"""
        expired_cookie = CookieModel.objects.create(
            site_name=f'nike-{self.unique_id}',
            name=f'old_cookie-{self.unique_id}',
            value='value',
            domain=f'.nike-{self.unique_id}.com',
            expires=timezone.now() - timedelta(hours=1),
        )
        
        assert expired_cookie.is_expired is True
    
    def test_to_playwright_dict(self):
        """Test conversion to Playwright cookie format"""
        cookie_dict = self.cookie1.to_playwright_dict()
        
        assert cookie_dict['name'].startswith('session_id-')
        assert cookie_dict['value'] == 'abc123'
        assert cookie_dict['path'] == '/'
        assert cookie_dict['httpOnly'] is True
        assert cookie_dict['secure'] is True
        assert cookie_dict['sameSite'] == 'Lax'
    
    def test_unique_constraint(self):
        """Test unique constraint on site+domain+name"""
        with pytest.raises(Exception):  # IntegrityError
            CookieModel.objects.create(
                site_name=self.cookie1.site_name,
                name=self.cookie1.name,
                value='different_value',
                domain=self.cookie1.domain,
            )


class TestCookieManagerSave(TestCase):
    """Test CookieManager save functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_save_cookies_creates_new(self):
        """Test saving new cookies"""
        manager = CookieManager()
        
        cookies = [
            {
                'name': 'session_id',
                'value': 'abc123',
                'domain': '.nike.com',
                'path': '/',
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Lax',
            }
        ]
        
        count = await manager.save_cookies('nike', cookies)
        assert count == 1
        
        # Wrap ORM calls in sync_to_async
        cookie_count = await sync_to_async(CookieModel.objects.count)()
        assert cookie_count == 1
        
        first_cookie = await sync_to_async(CookieModel.objects.first)()
        assert first_cookie.name == 'session_id'
    

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_save_cookies_updates_existing(self):
        """Test saving cookies updates existing ones"""
        manager = CookieManager()
        
        # Create initial cookie
        await sync_to_async(CookieModel.objects.create)(
            site_name='nike',
            name='session_id',
            value='old_value',
            domain='.nike.com',
        )
        
        # Save updated cookie
        cookies = [
            {
                'name': 'session_id',
                'value': 'new_value',
                'domain': '.nike.com',
                'path': '/',
            }
        ]
        
        count = await manager.save_cookies('nike', cookies)
        
        assert count == 1
        
        cookie_count = await sync_to_async(CookieModel.objects.count)()
        assert cookie_count == 1
        
        first_cookie = await sync_to_async(CookieModel.objects.first)()
        assert first_cookie.value == 'new_value'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_save_cookies_with_expires(self):
        """Test saving cookies with expiration"""
        manager = CookieManager()
        
        future_time = timezone.now() + timedelta(days=1)
        future_timestamp = future_time.timestamp()
        
        cookies = [
            {
                'name': 'session_id',
                'value': 'abc123',
                'domain': '.nike.com',
                'expires': future_timestamp,
            }
        ]
        
        count = await manager.save_cookies('nike', cookies)
        
        assert count == 1
        
        first_cookie = await sync_to_async(CookieModel.objects.first)()
        assert first_cookie.expires is not None
    

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_save_empty_cookies(self):
        """Test saving empty cookie list"""
        manager = CookieManager()
        
        count = await manager.save_cookies('nike', [])
        
        assert count == 0
        
        cookie_count = await sync_to_async(CookieModel.objects.count)()
        assert cookie_count == 0



class TestCookieManagerLoad(TestCase):
    """Test CookieManager load functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_load_cookies(self):
        """Test loading cookies"""
        manager = CookieManager()
        
        # Create test cookies using async wrapper
        await async_create(
            site_name='nike',
            name='session_id',
            value='abc123',
            domain='.nike.com',
        )
        await async_create(
            site_name='nike',
            name='user_pref',
            value='theme=dark',
            domain='.nike.com',
        )
        
        cookies = await manager.load_cookies('nike')
        
        assert len(cookies) == 2
        assert cookies[0]['name'] in ['session_id', 'user_pref']
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_load_cookies_excludes_expired(self):
        """Test that expired cookies are excluded"""
        manager = CookieManager()
        
        # Create active cookie using async wrapper
        await async_create(
            site_name='nike',
            name='session_id',
            value='abc123',
            domain='.nike.com',
        )
        
        # Create expired cookie using async wrapper
        await async_create(
            site_name='nike',
            name='old_cookie',
            value='xyz',
            domain='.nike.com',
            expires=timezone.now() - timedelta(hours=1),
        )
        
        cookies = await manager.load_cookies('nike')
        
        assert len(cookies) == 1
        assert cookies[0]['name'] == 'session_id'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_load_nonexistent_site(self):
        """Test loading cookies for non-existent site"""
        manager = CookieManager()
        
        cookies = await manager.load_cookies('nonexistent')
        
        assert cookies == []


class TestCookieManagerDelete(TestCase):
    """Test CookieManager delete functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_delete_cookie(self):
        """Test deleting a specific cookie"""
        manager = CookieManager()
        
        await async_create(
            site_name='nike',
            name='session_id',
            value='abc123',
            domain='.nike.com',
        )
        
        deleted = await manager.delete_cookie('nike', 'session_id')
        
        assert deleted is True
       
       # Use async wrapper to check count after deletion
        cookie_count = await sync_to_async(CookieModel.objects.count)()
        assert cookie_count == 0
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_delete_nonexistent_cookie(self):
        """Test deleting non-existent cookie"""
        manager = CookieManager()
        
        deleted = await manager.delete_cookie('nike', 'nonexistent')
        
        assert deleted is False
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_clear_cookies(self):
        """Test clearing all cookies for a site"""
        manager = CookieManager()
        
        await async_create(site_name='nike', name='cookie1', value='val1', domain='.nike.com')
        await async_create(site_name='nike', name='cookie2', value='val2', domain='.nike.com')
        await async_create(site_name='footlocker', name='cookie3', value='val3', domain='.footlocker.com')
        
        count = await manager.clear_cookies('nike')
        assert count == 2
        
        # Use async wrapper to check count after clearing
        total_count = await sync_to_async(CookieModel.objects.count)()
        assert total_count == 1


class TestCookieManagerCleanup(TestCase):
    """Test CookieManager cleanup functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_cleanup_expired_cookies(self):
        """Test cleaning up expired cookies"""
        manager = CookieManager()
        
        # Create active cookie
        await async_create(
            site_name='nike',
            name='active',
            value='val',
            domain='.nike.com',
        )
        
        # Create expired cookie
        await async_create(
            site_name='nike',
            name='expired',
            value='val',
            domain='.nike.com',
            expires=timezone.now() - timedelta(hours=1),
        )
        
        deleted = await manager.cleanup_expired_cookies('nike')
        
        assert deleted == 1

        # Use async wrapper to check count after cleanup
        remaining_count = await sync_to_async(CookieModel.objects.count)()
        assert remaining_count == 1


class TestCookieManagerExport(TestCase):
    """Test CookieManager export/import functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_export_cookies(self):
        """Test exporting cookies as JSON"""
        manager = CookieManager()
        
        await async_create(
            site_name='nike',
            name='session_id',
            value='abc123',
            domain='.nike.com',
        )
        
        json_str = await manager.export_cookies('nike')
        
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'session_id'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_import_cookies(self):
        """Test importing cookies from JSON"""
        manager = CookieManager()
        
        json_str = json.dumps([
            {
                'name': 'session_id',
                'value': 'abc123',
                'domain': '.nike.com',
                'path': '/',
            }
        ])
        
        count = await manager.import_cookies('nike', json_str)
        
        assert count == 1

        # Use async wrapper to check count after import
        cookie_count = await sync_to_async(CookieModel.objects.count)()
        assert cookie_count == 1


class TestCookieManagerStats(TestCase):
    """Test CookieManager statistics"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_cookie_count(self):
        """Test getting cookie count"""
        manager = CookieManager()
        
        await async_create(site_name='nike', name='c1', value='v1', domain='.nike.com')
        await async_create(site_name='nike', name='c2', value='v2', domain='.nike.com')
        
        count = await manager.get_cookie_count('nike')
        
        assert count == 2
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_cookie_info(self):
        """Test getting cookie info"""
        manager = CookieManager()
        
        # Active cookie
        await async_create(site_name='nike', name='active', value='v', domain='.nike.com')
        
        # Expired cookie
        await async_create(
            site_name='nike',
            name='expired',
            value='v',
            domain='.nike.com',
            expires=timezone.now() - timedelta(hours=1),
        )
        
        info = await manager.get_cookie_info('nike')
        
        assert info['total'] == 2
        assert info['active'] == 1
        assert info['expired'] == 1


class TestCookieManagerDuplicate(TestCase):
    """Test CookieManager duplication"""
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_duplicate_cookies(self):
        """Test duplicating cookies between sites"""
        manager = CookieManager()
        
        # Create source cookies
        await async_create(site_name='nike.com', name='session', value='abc', domain='.nike.com')
        await async_create(site_name='nike.com', name='theme', value='dark', domain='.nike.com')
        
        count = await manager.duplicate_cookies('nike.com', 'nike.eu')
        
        assert count == 2
        nike_eu_count = await async_filter_count(site_name='nike.eu')
        assert nike_eu_count == 2

    
    

if __name__ == '__main__':
    pytest.main([__file__, '-v'])