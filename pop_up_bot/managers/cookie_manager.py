# pop_up_bot/managers/cookie_manager.py

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from django.conf import settings
from asgiref.sync import sync_to_async
from pop_up_bot.models import CookieModel

logger = logging.getLogger(__name__)


class CookieManager:
    """
    Manages browser cookies - persists and restores them across executions.
    
    Benefits:
    - Maintain logged-in state (avoid re-login each run)
    - Preserve shopping cart state
    - Keep session cookies
    - Reduce bot detection (natural login pattern)
    
    Usage:
        cookie_manager = CookieManager()
        
        # When context is created, load cookies
        context = await session_manager.get_context('nike')
        cookies = await cookie_manager.load_cookies('nike')
        await context.add_cookies(cookies)
        
        # When done, save cookies for next run
        new_cookies = await context.cookies()
        await cookie_manager.save_cookies('nike', new_cookies)
    """
    
    def __init__(self):
        """Initialize CookieManager"""
        logger.info("CookieManager initialized")
    
    async def save_cookies(
        self,
        site_name: str,
        cookies: List[Dict],
        auto_cleanup_expired: bool = True
    ) -> int:
        """
        Save cookies from a browser context to database.
        
        Args:
            site_name: Site identifier (e.g., 'nike')
            cookies: List of cookies from context.cookies()
            auto_cleanup_expired: Delete expired cookies
        
        Returns:
            Number of cookies saved
        
        Example:
            cookies = await context.cookies()
            count = await cookie_manager.save_cookies('nike', cookies)
            print(f"Saved {count} cookies")
        """
        if not cookies:
            logger.warning(f"No cookies to save for {site_name}")
            return 0
        
        saved_count = 0
        
        for cookie in cookies:
            try:
                saved_count += await self._save_single_cookie(site_name, cookie)
            except Exception as e:
                logger.error(f"Error saving cookie {cookie.get('name')}: {e}")
                continue
        
        if auto_cleanup_expired:
            await self.cleanup_expired_cookies(site_name)
        
        logger.info(f"Saved {saved_count} cookies for {site_name}")
        return saved_count
    
    @sync_to_async
    def _save_single_cookie(self, site_name: str, cookie: Dict) -> int:
        """
        Save a single cookie (synchronous wrapper).
        
        Uses sync_to_async to handle Django ORM in async context.
        """
        try:
            # Convert Playwright cookie to Django model
            expires = None
            if 'expires' in cookie and cookie['expires']:
                from django.utils import timezone
                # ✅ FIX: Make datetime timezone-aware
                expires = timezone.make_aware(
                    timezone.datetime.fromtimestamp(cookie['expires'])
                )
            
            # Save or update cookie in database
            cookie_obj, created = CookieModel.objects.update_or_create(
                site_name=site_name,
                domain=cookie.get('domain', ''),
                name=cookie.get('name', ''),
                defaults={
                    'value': cookie.get('value', ''),
                    'path': cookie.get('path', '/'),
                    'expires': expires,
                    'http_only': cookie.get('httpOnly', False),
                    'secure': cookie.get('secure', False),
                    'same_site': cookie.get('sameSite', 'Lax'),
                }
            )
            
            action = "created" if created else "updated"
            logger.debug(f"Cookie {action}: {site_name}/{cookie.get('name')}")
            return 1
        
        except Exception as e:
            logger.error(f"Error saving cookie {cookie.get('name')}: {e}")
            return 0
    
    async def load_cookies(self, site_name: str) -> List[Dict]:
        """
        Load cookies from database for a site.
        
        Only loads non-expired cookies.
        
        Args:
            site_name: Site identifier
        
        Returns:
            List of cookies in Playwright format, ready to add to context
        
        Example:
            cookies = await cookie_manager.load_cookies('nike')
            await context.add_cookies(cookies)
        """
        return await self._load_cookies_async(site_name)
    
    @sync_to_async
    def _load_cookies_async(self, site_name: str) -> List[Dict]:
        """Load cookies (synchronous wrapper)"""
        try:
            # Get non-expired cookies for site
            cookie_objects = CookieModel.objects.filter(
                site_name=site_name
            )
            
            cookies = []
            for cookie_obj in cookie_objects:
                if not cookie_obj.is_expired:
                    cookies.append(cookie_obj.to_playwright_dict())
            
            logger.info(f"Loaded {len(cookies)} cookies for {site_name}")
            return cookies
        
        except Exception as e:
            logger.error(f"Error loading cookies for {site_name}: {e}")
            return []
    
    async def clear_cookies(self, site_name: str) -> int:
        """
        Delete all cookies for a site.
        
        Args:
            site_name: Site identifier
        
        Returns:
            Number of cookies deleted
        
        Example:
            deleted = await cookie_manager.clear_cookies('nike')
            print(f"Deleted {deleted} cookies")
        """
        return await self._clear_cookies_async(site_name)
    
    @sync_to_async
    def _clear_cookies_async(self, site_name: str) -> int:
        """Clear cookies (synchronous wrapper)"""
        try:
            count, _ = CookieModel.objects.filter(
                site_name=site_name
            ).delete()
            
            logger.info(f"Cleared {count} cookies for {site_name}")
            return count
        
        except Exception as e:
            logger.error(f"Error clearing cookies for {site_name}: {e}")
            return 0
    
    async def delete_cookie(
        self,
        site_name: str,
        name: str,
        domain: Optional[str] = None
    ) -> bool:
        """
        Delete a specific cookie.
        
        Args:
            site_name: Site identifier
            name: Cookie name
            domain: Cookie domain (if multiple domains)
        
        Returns:
            True if deleted, False otherwise
        
        Example:
            deleted = await cookie_manager.delete_cookie('nike', 'session_id')
        """
        return await self._delete_cookie_async(site_name, name, domain)
    
    @sync_to_async
    def _delete_cookie_async(self, site_name: str, name: str, domain: Optional[str]) -> bool:
        """Delete cookie (synchronous wrapper)"""
        try:
            filters = {
                'site_name': site_name,
                'name': name,
            }
            
            if domain:
                filters['domain'] = domain
            
            count, _ = CookieModel.objects.filter(**filters).delete()
            
            if count > 0:
                logger.info(f"Deleted cookie: {site_name}/{name}")
                return True
            else:
                logger.warning(f"Cookie not found: {site_name}/{name}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting cookie {name}: {e}")
            return False
    
    async def cleanup_expired_cookies(self, site_name: Optional[str] = None) -> int:
        """
        Delete all expired cookies.
        
        Args:
            site_name: If provided, only cleanup this site's cookies
        
        Returns:
            Number of cookies deleted
        
        Example:
            deleted = await cookie_manager.cleanup_expired_cookies()
            print(f"Deleted {deleted} expired cookies")
        """
        return await self._cleanup_expired_async(site_name)
    
    @sync_to_async
    def _cleanup_expired_async(self, site_name: Optional[str]) -> int:
        """Cleanup expired cookies (synchronous wrapper)"""
        try:
            from django.utils import timezone
            from django.db.models import Q
            
            filters = Q(expires__lt=timezone.now()) & Q(expires__isnull=False)
            
            if site_name:
                filters = filters & Q(site_name=site_name)
            
            count, _ = CookieModel.objects.filter(filters).delete()
            
            logger.info(f"Cleaned up {count} expired cookies")
            return count
        
        except Exception as e:
            logger.error(f"Error cleaning up expired cookies: {e}")
            return 0
    
    async def get_cookie_count(self, site_name: str) -> int:
        """
        Get number of cookies for a site.
        
        Args:
            site_name: Site identifier
        
        Returns:
            Number of cookies
        
        Example:
            count = await cookie_manager.get_cookie_count('nike')
            print(f"Nike has {count} cookies")
        """
        return await self._get_cookie_count_async(site_name)
    
    @sync_to_async
    def _get_cookie_count_async(self, site_name: str) -> int:
        """Get cookie count (synchronous wrapper)"""
        try:
            return CookieModel.objects.filter(site_name=site_name).count()
        except Exception as e:
            logger.error(f"Error getting cookie count: {e}")
            return 0
    
    async def export_cookies(self, site_name: str) -> str:
        """
        Export cookies as JSON string.
        
        Useful for debugging, sharing, or backup.
        
        Args:
            site_name: Site identifier
        
        Returns:
            JSON string of cookies
        
        Example:
            json_cookies = await cookie_manager.export_cookies('nike')
            print(json_cookies)
        """
        try:
            cookies = await self.load_cookies(site_name)
            return json.dumps(cookies, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error exporting cookies: {e}")
            return "{}"
    
    async def import_cookies(self, site_name: str, json_string: str) -> int:
        """
        Import cookies from JSON string.
        
        Useful for restoring from backup.
        
        Args:
            site_name: Site identifier
            json_string: JSON string of cookies
        
        Returns:
            Number of cookies imported
        
        Example:
            count = await cookie_manager.import_cookies('nike', json_string)
            print(f"Imported {count} cookies")
        """
        try:
            cookies = json.loads(json_string)
            return await self.save_cookies(site_name, cookies)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error importing cookies: {e}")
            return 0
    
    async def duplicate_cookies(
        self,
        from_site: str,
        to_site: str,
        overwrite: bool = False
    ) -> int:
        """
        Copy cookies from one site to another.
        
        Useful for sites with same authentication.
        
        Args:
            from_site: Source site identifier
            to_site: Destination site identifier
            overwrite: If True, overwrite existing cookies
        
        Returns:
            Number of cookies duplicated
        
        Example:
            count = await cookie_manager.duplicate_cookies('nike.com', 'nike.eu')
        """
        try:
            cookies = await self.load_cookies(from_site)
            
            if not overwrite:
                # Get existing cookies to avoid duplicates
                existing = await self.load_cookies(to_site)
                existing_names = {c['name'] for c in existing}
                cookies = [c for c in cookies if c['name'] not in existing_names]
            
            return await self.save_cookies(to_site, cookies)
        
        except Exception as e:
            logger.error(f"Error duplicating cookies: {e}")
            return 0
    
    async def get_cookie_info(self, site_name: str) -> Dict:
        """
        Get detailed info about cookies for a site.
        
        Args:
            site_name: Site identifier
        
        Returns:
            Dictionary with cookie statistics
        
        Example:
            info = await cookie_manager.get_cookie_info('nike')
            print(f"Total: {info['total']}, Expired: {info['expired']}")
        """
        return await self._get_cookie_info_async(site_name)
    
    @sync_to_async
    def _get_cookie_info_async(self, site_name: str) -> Dict:
        """Get cookie info (synchronous wrapper)"""
        try:
            from django.utils import timezone
            
            all_cookies = CookieModel.objects.filter(site_name=site_name)
            total = all_cookies.count()
            
            expired_count = 0
            for cookie in all_cookies:
                if cookie.is_expired:
                    expired_count += 1
            
            active_count = total - expired_count
            
            return {
                'site_name': site_name,
                'total': total,
                'active': active_count,
                'expired': expired_count,
                'domains': list(all_cookies.values_list('domain', flat=True).distinct()),
            }
        
        except Exception as e:
            logger.error(f"Error getting cookie info: {e}")
            return {'error': str(e)}


class CookieManagerDjango:
    """
    Synchronous wrapper for CookieManager to use with Django ORM.
    
    Use this when you need synchronous cookie operations.
    """
    
    def __init__(self):
        self.manager = CookieManager()
    
    def save_cookies(self, site_name: str, cookies: List[Dict]) -> int:
        """Synchronous version of save_cookies"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.manager.save_cookies(site_name, cookies)
        )
    
    def load_cookies(self, site_name: str) -> List[Dict]:
        """Synchronous version of load_cookies"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.manager.load_cookies(site_name)
        )
    
    def clear_cookies(self, site_name: str) -> int:
        """Synchronous version of clear_cookies"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.manager.clear_cookies(site_name)
        )