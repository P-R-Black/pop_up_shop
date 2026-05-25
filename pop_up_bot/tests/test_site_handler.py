# pop_up_bot/tests/test_site_handler.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from django.test import TestCase

from pop_up_bot.handlers.base_handler import (
    BaseSiteHandler,
    Product,
    CartItem,
    ExecutionStep,
    SiteErrorType,
)


class MockSiteHandler(BaseSiteHandler):
    """Mock site handler for testing"""
    
    @property
    def site_name(self) -> str:
        return 'mock_site'
    
    @property
    def base_url(self) -> str:
        return 'https://mock-site.com'
    
    async def validate_site_connection(self) -> bool:
        return True
    
    async def find_product(self, product_name, size, color=None):
        return Product(
            product_id='123',
            name=product_name,
            price=169.99,
            available_sizes=['8', '9', '10', '11'],
            product_url='https://mock-site.com/product/123',
            in_stock=True,
        )
    
    async def select_size(self, size):
        return True
    
    async def add_to_cart(self, product_id, size, quantity=1):
        self.cart_item = CartItem(
            product_id=product_id,
            product_name='Test Product',
            size=size,
            quantity=quantity,
            price=169.99,
        )
        return True
    
    async def check_cart(self):
        return self.cart_item
    
    async def is_item_in_stock(self):
        return True
    
    async def proceed_to_checkout(self):
        return True


class TestProduct(TestCase):
    """Test Product model"""
    
    def test_product_creation(self):
        """Test creating a product"""
        product = Product(
            product_id='123',
            name='Air Jordan 1',
            price=169.99,
            available_sizes=['8', '9', '10', '11'],
            product_url='https://nike.com/product/123',
        )
        
        assert product.product_id == '123'
        assert product.name == 'Air Jordan 1'
        assert product.price == 169.99
        assert len(product.available_sizes) == 4
    
    def test_product_str(self):
        """Test product string representation"""
        product = Product(
            product_id='123',
            name='Air Jordan 1',
            price=169.99,
            available_sizes=['8', '9', '10'],
            product_url='https://nike.com/product/123',
        )
        
        assert 'Air Jordan 1' in str(product)
        assert '169.99' in str(product)


class TestCartItem(TestCase):
    """Test CartItem model"""
    
    def test_cart_item_creation(self):
        """Test creating a cart item"""
        item = CartItem(
            product_id='123',
            product_name='Air Jordan 1',
            size='US 10',
            quantity=1,
            price=169.99,
        )
        
        assert item.product_id == '123'
        assert item.product_name == 'Air Jordan 1'
        assert item.size == 'US 10'
        assert item.quantity == 1
        assert item.price == 169.99
    
    def test_cart_item_total_price(self):
        """Test cart item total price calculation"""
        item = CartItem(
            product_id='123',
            product_name='Air Jordan 1',
            size='US 10',
            quantity=2,
            price=169.99,
        )
        
        assert item.total_price == 339.98


class TestBaseSiteHandler(TestCase):
    """Test BaseSiteHandler"""
    
    def test_handler_initialization(self):
        """Test handler initialization"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        
        assert handler.site_name == 'mock_site'
        assert handler.base_url == 'https://mock-site.com'
        assert handler.engine == mock_engine
        assert handler.current_step == ExecutionStep.INITIALIZED
    
    @pytest.mark.asyncio
    async def test_find_product(self):
        """Test finding a product"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        product = await handler.find_product('Air Jordan 1', 'US 10')
        
        assert product is not None
        assert product.name == 'Air Jordan 1'
        assert product.price == 169.99
    
    @pytest.mark.asyncio
    async def test_add_to_cart(self):
        """Test adding item to cart"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        success = await handler.add_to_cart('123', 'US 10', 1)
        
        assert success is True
        assert handler.cart_item is not None
        assert handler.cart_item.size == 'US 10'
    
    @pytest.mark.asyncio
    async def test_check_cart(self):
        """Test checking cart"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        
        # Add item first
        await handler.add_to_cart('123', 'US 10', 1)
        
        # Check cart
        item = await handler.check_cart()
        
        assert item is not None
        assert item.product_id == '123'
    
    @pytest.mark.asyncio
    async def test_set_step(self):
        """Test setting execution step"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        
        await handler.set_step(ExecutionStep.SEARCHING_PRODUCT)
        
        assert handler.current_step == ExecutionStep.SEARCHING_PRODUCT
        assert len(handler.execution_history) == 1
        assert handler.execution_history[0]['step'] == 'searching_product'
    
    @pytest.mark.asyncio
    async def test_log_error(self):
        """Test logging an error"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        
        await handler.log_error(
            SiteErrorType.OUT_OF_STOCK,
            'Product is out of stock',
            {'size': 'US 10'},
        )
        
        assert len(handler.error_log) == 1
        assert handler.error_log[0]['type'] == 'out_of_stock'
        assert handler.error_log[0]['message'] == 'Product is out of stock'
    
    @pytest.mark.asyncio
    async def test_get_execution_stats(self):
        """Test getting execution statistics"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        
        await handler.set_step(ExecutionStep.SEARCHING_PRODUCT)
        await handler.set_step(ExecutionStep.PRODUCT_FOUND)
        
        stats = handler.get_execution_stats()
        
        assert stats['site'] == 'mock_site'
        assert stats['current_step'] == 'product_found'
        assert stats['steps_completed'] == 2
        assert 'duration_seconds' in stats
    
    @pytest.mark.asyncio
    async def test_detect_out_of_stock(self):
        """Test out of stock detection"""
        mock_engine = AsyncMock()
        
        # Mock page with "out of stock" text
        mock_engine.execute_js = AsyncMock(
            return_value='product is out of stock'
        )
        
        handler = MockSiteHandler(engine=mock_engine)
        
        is_oos = await handler.detect_out_of_stock()
        
        assert is_oos is True
    
    @pytest.mark.asyncio
    async def test_detect_captcha(self):
        """Test captcha detection"""
        mock_engine = AsyncMock()
        mock_engine.is_element_visible = AsyncMock(return_value=True)
        
        handler = MockSiteHandler(engine=mock_engine)
        
        has_captcha = await handler.detect_captcha()
        
        assert has_captcha is True
    
    @pytest.mark.asyncio
    async def test_detect_blocked(self):
        """Test blocked/rate-limited detection"""
        mock_engine = AsyncMock()
        mock_engine.get_title = AsyncMock(return_value='Access Denied 429')
        
        handler = MockSiteHandler(engine=mock_engine)
        
        is_blocked = await handler.detect_blocked()
        
        assert is_blocked is True
    
    @pytest.mark.asyncio
    async def test_handler_str(self):
        """Test handler string representation"""
        mock_engine = AsyncMock()
        
        handler = MockSiteHandler(engine=mock_engine)
        
        assert 'MockSiteHandler' in str(handler)
        assert 'mock_site' in str(handler)


class TestExecutionStep(TestCase):
    """Test ExecutionStep enum"""
    
    def test_execution_steps_exist(self):
        """Test all execution steps are defined"""
        assert ExecutionStep.INITIALIZED.value == 'initialized'
        assert ExecutionStep.SEARCHING_PRODUCT.value == 'searching_product'
        assert ExecutionStep.PRODUCT_FOUND.value == 'product_found'
        assert ExecutionStep.ORDER_COMPLETE.value == 'order_complete'


class TestSiteErrorType(TestCase):
    """Test SiteErrorType enum"""
    
    def test_error_types_exist(self):
        """Test all error types are defined"""
        assert SiteErrorType.OUT_OF_STOCK.value == 'out_of_stock'
        assert SiteErrorType.CAPTCHA.value == 'captcha'
        assert SiteErrorType.BLOCKED.value == 'blocked'
        assert SiteErrorType.PAYMENT_FAILED.value == 'payment_failed'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])