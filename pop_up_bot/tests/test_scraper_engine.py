# pop_up_bot/tests/test_scraper_engine.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from django.test import TestCase
from pop_up_bot.engines.scraper_engine import PlaywrightScraperEngine


class TestPlaywrightScraperEngine(TestCase):
    """Test PlaywrightScraperEngine"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test engine initialization"""
        mock_page = AsyncMock()
        
        engine = PlaywrightScraperEngine(
            page=mock_page,
            default_timeout=30,
            max_retries=3,
        )
        
        assert engine.page == mock_page
        assert engine.default_timeout == 30
        assert engine.max_retries == 3
        assert engine.action_count == 0
        assert engine.error_count == 0
    
    @pytest.mark.asyncio
    async def test_navigate_success(self):
        """Test successful navigation"""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        await engine.navigate('https://example.com')
        
        mock_page.goto.assert_called_once()
        assert engine.action_count == 1
    
    @pytest.mark.asyncio
    async def test_navigate_timeout(self):
        """Test navigation timeout"""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Navigation timed out"))
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        with pytest.raises(PlaywrightTimeoutError):
            await engine.navigate('https://example.com')
        
        assert engine.error_count == 1
    
    @pytest.mark.asyncio
    async def test_wait_for_element(self):
        """Test waiting for element"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        await engine.wait_for('input[name="size"]')
        
        mock_page.locator.assert_called_with('input[name="size"]')
        mock_locator.wait_for.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_click_element(self):
        """Test clicking element"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.scroll_into_view_if_needed = AsyncMock()
        mock_locator.click = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        await engine.click('button[name="add-to-cart"]')
        
        mock_locator.scroll_into_view_if_needed.assert_called_once()
        mock_locator.click.assert_called_once()
        assert engine.action_count == 1
    
    @pytest.mark.asyncio
    async def test_click_with_retry(self):
        """Test click with retry on failure"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.scroll_into_view_if_needed = AsyncMock()
        
        # Fail twice, then succeed
        mock_locator.click = AsyncMock(
            side_effect=[Exception("Click failed"), Exception("Click failed"), None]
        )
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page, max_retries=3)
        
        await engine.click('button', retry=True)
        
        # Should have retried 3 times
        assert mock_locator.click.call_count == 3
    
    @pytest.mark.asyncio
    async def test_type_text(self):
        """Test typing into input"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.scroll_into_view_if_needed = AsyncMock()
        mock_locator.clear = AsyncMock()
        mock_locator.type = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        await engine.type('input[name="search"]', 'Air Jordan 1')
        
        mock_locator.clear.assert_called_once()
        mock_locator.type.assert_called_once()
        assert engine.action_count == 1
    
    @pytest.mark.asyncio
    async def test_extract_text(self):
        """Test extracting text"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.text_content = AsyncMock(return_value='Product Name')
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        text = await engine.extract_text('h1.product-name')
        
        assert text == 'Product Name'
        mock_locator.text_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_not_found(self):
        """Test extracting text when element not found"""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.text_content = AsyncMock(side_effect=PlaywrightTimeoutError("Element not found"))
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        text = await engine.extract_text('h1.nonexistent')
        
        assert text is None
    
    @pytest.mark.asyncio
    async def test_extract_attribute(self):
        """Test extracting attribute"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.get_attribute = AsyncMock(return_value='https://example.com')
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        href = await engine.extract_attribute('a.link', 'href')
        
        assert href == 'https://example.com'
    
    @pytest.mark.asyncio
    async def test_extract_all_text(self):
        """Test extracting text from multiple elements"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        
        # Mock multiple elements
        mock_elem1 = AsyncMock()
        mock_elem1.text_content = AsyncMock(return_value='Size 10')
        
        mock_elem2 = AsyncMock()
        mock_elem2.text_content = AsyncMock(return_value='Size 11')
        
        mock_locator.all = AsyncMock(return_value=[mock_elem1, mock_elem2])
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        texts = await engine.extract_all_text('div.size-option')
        
        assert len(texts) == 2
        assert 'Size 10' in texts
        assert 'Size 11' in texts
    
    @pytest.mark.asyncio
    async def test_get_url(self):
        """Test getting current URL"""
        mock_page = AsyncMock()
        mock_page.url = 'https://example.com/product'
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        url = await engine.get_url()
        
        assert url == 'https://example.com/product'
    
    @pytest.mark.asyncio
    async def test_get_title(self):
        """Test getting page title"""
        mock_page = AsyncMock()
        mock_page.title = AsyncMock(return_value='Product Page')
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        title = await engine.get_title()
        
        assert title == 'Product Page'
    
    @pytest.mark.asyncio
    async def test_is_element_visible(self):
        """Test checking element visibility"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.is_visible = AsyncMock(return_value=True)
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        visible = await engine.is_element_visible('button.submit')
        
        assert visible is True
    
    @pytest.mark.asyncio
    async def test_execute_js(self):
        """Test executing JavaScript"""
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value='$99.99')
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        result = await engine.execute_js(
            'return document.querySelector(".price").innerText'
        )
        
        assert result == '$99.99'
    
    @pytest.mark.asyncio
    async def test_scroll_to_element(self):
        """Test scrolling to element"""
        mock_page = AsyncMock()
        mock_locator = AsyncMock()
        mock_locator.scroll_into_view_if_needed = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        engine = PlaywrightScraperEngine(page=mock_page)
        
        await engine.scroll_to_element('input[name="email"]')
        
        mock_locator.scroll_into_view_if_needed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting engine statistics"""
        mock_page = AsyncMock()
        
        engine = PlaywrightScraperEngine(page=mock_page)
        engine.action_count = 10
        engine.error_count = 2
        
        stats = engine.get_stats()
        
        assert stats['actions'] == 10
        assert stats['errors'] == 2
        assert 'duration_seconds' in stats
        assert 'actions_per_second' in stats
    
    @pytest.mark.asyncio
    async def test_close_page(self):
        """Test closing page"""
        mock_page = AsyncMock()
        mock_page.close = AsyncMock()
        
        engine = PlaywrightScraperEngine(page=mock_page)
        engine.action_count = 5
        
        await engine.close()
        
        mock_page.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])