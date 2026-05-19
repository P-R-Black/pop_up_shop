# pop_up_bot/tests/test_session_manager.py

import pytest
from unittest import skip
from django.test import Client, TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pop_up_bot.managers.session_manager import SessionManager
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

class TestSessionManagerInitialization(TestCase):
    """Test SessionManager initialization"""
    
    def test_init_default_values(self):
        """Test default initialization values"""
        sm = SessionManager()
        
        assert sm.headless is True
        assert sm.anti_detection is True
        assert sm.viewport == {'width': 1920, 'height': 1080}
        assert sm.user_agent_rotation is False
        assert sm.timeout_ms == 30000
        assert sm.browsers == {}
        assert sm.context_count == {}
    
    def test_init_custom_values(self):
        """Test initialization with custom values"""
        custom_viewport = {'width': 1280, 'height': 720}
        sm = SessionManager(
            headless=False,
            anti_detection=False,
            viewport=custom_viewport,
            user_agent_rotation=True,
            timeout_ms=60000
        )
        
        assert sm.headless is False
        assert sm.anti_detection is False
        assert sm.viewport == custom_viewport
        assert sm.user_agent_rotation is True
        assert sm.timeout_ms == 60000


class TestBrowserManagement(TestCase):
    """Test browser creation and management"""
    
    @pytest.mark.asyncio
    async def test_get_browser_creates_new(self):
        """Test that get_browser creates a new browser on first call"""
        sm = SessionManager()
        
        with patch.object(sm, '_create_browser', new_callable=AsyncMock) as mock_create:
            with patch.object(sm, '_is_browser_alive', new_callable=AsyncMock, return_value=True):
                mock_browser = AsyncMock()
                mock_create.return_value = mock_browser
                
                browser = await sm.get_browser('nike')
                
                assert browser == mock_browser
                mock_create.assert_called_once_with('chromium')
                assert 'nike' in sm.browsers
    
    @pytest.mark.asyncio
    async def test_get_browser_reuses_existing(self):
        """Test that get_browser reuses cached browser"""
        sm = SessionManager()
        mock_browser = AsyncMock()
        sm.browsers['nike'] = mock_browser
        
        with patch.object(sm, '_is_browser_alive', new_callable=AsyncMock, return_value=True):
            browser = await sm.get_browser('nike')
            
            assert browser == mock_browser
            # Should not create new browser
    
    @pytest.mark.asyncio
    async def test_get_browser_recreates_dead_browser(self):
        """Test that dead browsers are recreated"""
        sm = SessionManager()
        dead_browser = AsyncMock()
        sm.browsers['nike'] = dead_browser
        
        with patch.object(sm, '_is_browser_alive', new_callable=AsyncMock, return_value=False):
            with patch.object(sm, '_create_browser', new_callable=AsyncMock) as mock_create:
                with patch.object(sm, '_close_browser_instance', new_callable=AsyncMock):
                    new_browser = AsyncMock()
                    mock_create.return_value = new_browser
                    
                    browser = await sm.get_browser('nike')
                    
                    assert browser == new_browser
                    mock_create.assert_called_once()


class TestPageManagement(TestCase):
    """Test page creation and management"""
    
    @pytest.mark.asyncio
    async def test_get_page_creates_context_and_page(self):
        """Test that get_page creates context and page"""
        sm = SessionManager()
        
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        
        with patch.object(sm, 'get_context', new_callable=AsyncMock, return_value=mock_context):
            page = await sm.get_page('nike')
            
            assert page == mock_page
            mock_context.new_page.assert_called_once()


class TestContextManagement(TestCase):
    """Test browser context creation"""
    
    @pytest.mark.asyncio
    async def test_get_context_creates_new_context(self):
        """Test that get_context creates a new context"""
        sm = SessionManager()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        with patch.object(sm, 'get_browser', new_callable=AsyncMock, return_value=mock_browser):
            with patch.object(sm, '_apply_stealth_mode', new_callable=AsyncMock):
                context = await sm.get_context('nike')
                
                assert context == mock_context
                mock_browser.new_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_context_with_user_agent_rotation(self):
        """Test that user agent rotation is applied"""
        sm = SessionManager(user_agent_rotation=True)
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        with patch.object(sm, 'get_browser', new_callable=AsyncMock, return_value=mock_browser):
            with patch.object(sm, '_apply_stealth_mode', new_callable=AsyncMock):
                await sm.get_context('nike')
                
                # Verify new_context was called
                assert mock_browser.new_context.called
                # User agent should be in the call arguments
                call_args = mock_browser.new_context.call_args
                assert 'user_agent' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_context_count_increments(self):
        """Test that context count is tracked"""
        sm = SessionManager()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        with patch.object(sm, 'get_browser', new_callable=AsyncMock, return_value=mock_browser):
            with patch.object(sm, '_apply_stealth_mode', new_callable=AsyncMock):
                await sm.get_context('nike')
                assert sm.get_context_count('nike') == 1
                
                await sm.get_context('nike')
                assert sm.get_context_count('nike') == 2


class TestBrowserHealth(TestCase):
    """Test browser health checks"""
    
    @pytest.mark.asyncio
    async def test_is_browser_alive_true(self):
        """Test is_browser_alive returns True for alive browser"""
        sm = SessionManager()
        mock_browser = AsyncMock()
        mock_browser.version = "100.0"
        sm.browsers['nike'] = mock_browser
        
        alive = await sm.is_browser_alive('nike')
        
        assert alive is True
    
    @pytest.mark.asyncio
    async def test_is_browser_alive_false_not_exists(self):
        """Test is_browser_alive returns False for non-existent browser"""
        sm = SessionManager()
        
        alive = await sm.is_browser_alive('nike')
        
        assert alive is False
    
    @pytest.mark.asyncio
    async def test_is_browser_alive_handles_exception(self):
        """Test is_browser_alive handles exceptions"""
        sm = SessionManager()
        mock_browser = AsyncMock()
        mock_browser.version = None
        sm.browsers['nike'] = mock_browser
        
        with patch.object(sm, '_is_browser_alive', new_callable=AsyncMock, return_value=False):
            alive = await sm.is_browser_alive('nike')
            
            assert alive is False


class TestCleanup(TestCase):
    """Test resource cleanup"""
    
    @pytest.mark.asyncio
    async def test_close_browser_removes_from_cache(self):
        """Test that close_browser removes browser from cache"""
        sm = SessionManager()
        mock_browser = AsyncMock()
        sm.browsers['nike'] = mock_browser
        sm.context_count['nike'] = 5
        
        with patch.object(sm, '_close_browser_instance', new_callable=AsyncMock) as mock_close:
            await sm.close_browser('nike')
            
            mock_close.assert_called_once_with('nike')
    
    @pytest.mark.asyncio
    async def test_close_all_closes_all_browsers(self):
        """Test that close_all closes all browsers"""
        sm = SessionManager()
        mock_browser1 = AsyncMock()
        mock_browser2 = AsyncMock()
        sm.browsers['nike'] = mock_browser1
        sm.browsers['footlocker'] = mock_browser2
        
        with patch.object(sm, '_close_browser_instance', new_callable=AsyncMock) as mock_close:
            await sm.close_all()
            
            assert mock_close.call_count == 2
            assert len(sm.browsers) == 0


class TestUserAgentRotation(TestCase):
    """Test user agent rotation"""
    
    def test_get_next_user_agent_cycles(self):
        """Test that user agent cycles through list"""
        sm = SessionManager()
        ua_count = len(sm.user_agents)
        
        # Call it ua_count times to complete one full cycle
        for _ in range(ua_count):
            ua = sm._get_next_user_agent()
        
        # After cycling through all, should be back at start
        assert sm.ua_index == 0
    
    def test_get_next_user_agent_returns_different_values(self):
        """Test that consecutive calls return different values"""
        sm = SessionManager()
        
        ua1 = sm._get_next_user_agent()
        ua2 = sm._get_next_user_agent()
        ua3 = sm._get_next_user_agent()
        
        # First three should be different (assuming 5 agents)
        assert ua1 != ua2
        assert ua2 != ua3


class TestContextManager(TestCase):
    """Test async context manager support"""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test that SessionManager works as async context manager"""
        with patch.object(SessionManager, 'initialize', new_callable=AsyncMock):
            with patch.object(SessionManager, 'shutdown', new_callable=AsyncMock):
                async with SessionManager() as sm:
                    assert sm is not None


class TestStats(TestCase):
    """Test statistics and metrics"""
    
    def test_get_browser_count(self):
        """Test browser count"""
        sm = SessionManager()
        assert sm.get_browser_count() == 0
        
        sm.browsers['nike'] = AsyncMock()
        sm.browsers['footlocker'] = AsyncMock()
        
        assert sm.get_browser_count() == 2
    
    def test_get_context_count(self):
        """Test context count tracking"""
        sm = SessionManager()
        assert sm.get_context_count('nike') == 0
        
        sm.context_count['nike'] = 5
        assert sm.get_context_count('nike') == 5


    # ============================================================================
    # Integration Tests
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_full_workflow(self):
        """Integration test: full workflow"""
        sm = SessionManager()
        
        with patch.object(sm, '_create_browser', new_callable=AsyncMock) as mock_create:
            with patch.object(sm, '_is_browser_alive', new_callable=AsyncMock, return_value=True):
                # Don't mock _close_browser_instance - let it work
                mock_browser = AsyncMock()
                mock_context = AsyncMock()
                mock_page = AsyncMock()
                
                mock_create.return_value = mock_browser
                mock_browser.new_context.return_value = mock_context
                mock_context.new_page.return_value = mock_page
                
                # Mock playwright
                sm.playwright = AsyncMock()
                
                # Get page (creates browser)
                page1 = await sm.get_page('nike')
                assert page1 == mock_page
                assert sm.get_browser_count() == 1
                
                # Get another page (reuses browser)
                page2 = await sm.get_page('nike')
                assert sm.get_browser_count() == 1
                assert sm.get_context_count('nike') == 2
                
                # Close browser
                await sm.close_browser('nike')
                assert sm.get_browser_count() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


# """
# Run Test
# python3 manage.py test pop_accounts/tests
# python3 manage.py test pop_accounts.tests.test_views.PersonalInfoViewIntegrationTests
# Run Test with Coverage
# coverage run --omit='*/venv/*' manage.py test pop_accounts/tests 
# coverage report | to get overview 
# coverage html | to get hml overview
# """