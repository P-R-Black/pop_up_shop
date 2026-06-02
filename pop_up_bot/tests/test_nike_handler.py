# pop_up_bot/tests/test_nike_handler.py

"""
Unit tests for NikeSiteHandler

These tests mock the Playwright engine so we don't make real Nike calls.

Run with:
    python manage.py test pop_up_bot.tests.test_nike_handler
    
Or run specific test:
    python manage.py test pop_up_bot.tests.test_nike_handler.TestValidateSiteConnection.test_valid_connection
"""

from django.test import TestCase
from asgiref.sync import async_to_sync
from unittest.mock import AsyncMock, MagicMock, patch

from pop_up_bot.handlers.nike_handler import NikeSiteHandler
from pop_up_bot.handlers.base_handler import Product


class NikeSiteHandlerTestCase(TestCase):
    """Base test case for NikeSiteHandler tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_engine = self._create_mock_engine()
        self.handler = NikeSiteHandler(
            engine=self.mock_engine,
            session_manager=None,
            cookie_manager=None,
            event_logger=None,
        )
    
    def _create_mock_engine(self):
        """Create a mocked PlaywrightScraperEngine"""
        engine = AsyncMock()
        
        # Default behaviors
        engine.navigate = AsyncMock()
        engine.click = AsyncMock()
        engine.type = AsyncMock()
        engine.wait_for = AsyncMock()
        engine.wait_for_load_state = AsyncMock()
        engine.is_element_visible = AsyncMock(return_value=True)
        engine.query_selector = AsyncMock()
        engine.query_selector_all = AsyncMock(return_value=[])
        engine.extract_text = AsyncMock(return_value="Test")
        engine.extract_attribute = AsyncMock(return_value="http://example.com")
        engine.click_element = AsyncMock()
        engine.evaluate = AsyncMock()
        engine.execute_js = AsyncMock(return_value="")
        engine.wait_for_timeout = AsyncMock()
        engine.get_url = AsyncMock(return_value="https://www.nike.com")
        engine.get_title = AsyncMock(return_value="Nike Product")
        
        return engine


# ============================================================================
# TESTS: SITE VALIDATION
# ============================================================================

class TestValidateSiteConnection(NikeSiteHandlerTestCase):
    """Test Nike site connection validation"""
    
    def test_valid_connection(self):
        """Test successful Nike connection"""
        result = async_to_sync(self.handler.validate_site_connection)()
        
        self.assertTrue(result)
        self.mock_engine.navigate.assert_called_with('https://www.nike.com')
        self.mock_engine.is_element_visible.assert_called()
    
    def test_blocked_connection(self):
        """Test blocked/rate-limited connection"""
        with patch.object(self.handler, 'detect_blocked', return_value=True):
            result = async_to_sync(self.handler.validate_site_connection)()
        
        self.assertFalse(result)
    
    def test_search_not_visible(self):
        """Test when search input is not visible"""
        self.mock_engine.is_element_visible = AsyncMock(return_value=False)
        
        result = async_to_sync(self.handler.validate_site_connection)()
        
        self.assertFalse(result)


# ============================================================================
# TESTS: PRODUCT FINDING
# ============================================================================

class TestFindProduct(NikeSiteHandlerTestCase):
    """Test product search and finding"""
    
    def test_find_product_success(self):
        """Test successfully finding a product"""
        self.mock_engine.extract_text = AsyncMock(return_value="Air Jordan 1 Low")
        self.mock_engine.extract_attribute = AsyncMock(return_value="https://www.nike.com/t/air-jordan-1/553558-404")
        self.mock_engine.query_selector_all = AsyncMock(return_value=[MagicMock(), MagicMock()])
        
        with patch.object(self.handler, '_extract_price', new_callable=AsyncMock, return_value="$150"):
            with patch.object(self.handler, '_get_available_sizes', new_callable=AsyncMock, return_value=["M 10 / W 11.5"]):
                product = async_to_sync(self.handler.find_product)("Air Jordan 1", "10")
        
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Air Jordan 1 Low")
        self.assertEqual(product.price, 150.0)
        self.assertTrue(product.in_stock)
    
    def test_find_product_not_found(self):
        """Test product not found in search"""
        self.mock_engine.query_selector = AsyncMock(return_value=None)
        
        product = async_to_sync(self.handler.find_product)("Nonexistent Shoe", "10")
        
        self.assertIsNone(product)


# ============================================================================
# TESTS: SIZE SELECTION
# ============================================================================

class TestSelectSize(NikeSiteHandlerTestCase):
    """Test size selection logic"""
    
    def test_select_size_exact_match(self):
        """Test selecting size with exact match"""
        radio_mock = MagicMock()
        self.mock_engine.query_selector_all = AsyncMock(return_value=[radio_mock])
        self.mock_engine.evaluate = AsyncMock(side_effect=["10", "grid-selector-input-10", "M 10 / W 11.5"])
        
        label_mock = MagicMock()
        self.mock_engine.query_selector = AsyncMock(return_value=label_mock)
        
        result = async_to_sync(self.handler.select_size)("10")
        print('self.handler', self.handler)
        print('result', result)
        
        self.assertTrue(result)
        self.mock_engine.click_element.assert_called_with(label_mock)
    
    def test_select_size_with_us_prefix(self):
        """Test selecting size with 'US' prefix"""
        radio_mock = MagicMock()
        self.mock_engine.query_selector_all = AsyncMock(return_value=[radio_mock])
        self.mock_engine.evaluate = AsyncMock(side_effect=["10", "grid-selector-input-10", "M 10 / W 11.5"])
        
        label_mock = MagicMock()
        self.mock_engine.query_selector = AsyncMock(return_value=label_mock)
        
        result = async_to_sync(self.handler.select_size)("US 10")
        
        self.assertTrue(result)
    
    def test_select_size_no_sizes_available(self):
        """Test selecting size when no sizes available"""
        self.mock_engine.query_selector_all = AsyncMock(return_value=[])
        
        result = async_to_sync(self.handler.select_size)("10")
        
        self.assertFalse(result)


# ============================================================================
# TESTS: ADD TO CART
# ============================================================================

class TestAddToCart(NikeSiteHandlerTestCase):
    """Test add to cart functionality"""
    
    def test_add_to_cart_success(self):
        """Test successfully adding item to cart"""
        self.handler.product_found = Product(
            product_id="553558-404",
            name="Air Jordan 1 Low",
            price=150.0,
            available_sizes=["M 10 / W 11.5"],
            product_url="https://nike.com",
            in_stock=True,
        )
        
        with patch.object(self.handler, 'select_size', new_callable=AsyncMock, return_value=True):
            with patch.object(self.handler, 'detect_out_of_stock', new_callable=AsyncMock, return_value=False):
                button_mock = MagicMock()
                self.mock_engine.query_selector = AsyncMock(return_value=button_mock)
                self.mock_engine.evaluate = AsyncMock(return_value=False)
                
                result = async_to_sync(self.handler.add_to_cart)("553558-404", "10")
        
        self.assertTrue(result)
        self.assertIsNotNone(self.handler.cart_item)
        self.assertEqual(self.handler.cart_item.product_id, "553558-404")
        self.assertEqual(self.handler.cart_item.size, "10")
    
    def test_add_to_cart_size_selection_fails(self):
        """Test add to cart fails when size selection fails"""
        with patch.object(self.handler, 'select_size', new_callable=AsyncMock, return_value=False):
            result = async_to_sync(self.handler.add_to_cart)("553558-404", "10")
        
        self.assertFalse(result)
    
    def test_add_to_cart_out_of_stock(self):
        """Test add to cart fails when product is out of stock"""
        with patch.object(self.handler, 'select_size', new_callable=AsyncMock, return_value=True):
            with patch.object(self.handler, 'detect_out_of_stock', new_callable=AsyncMock, return_value=True):
                result = async_to_sync(self.handler.add_to_cart)("553558-404", "10")
        
        self.assertFalse(result)


# ============================================================================
# TESTS: STOCK DETECTION
# ============================================================================

class TestStockDetection(NikeSiteHandlerTestCase):
    """Test out of stock detection"""
    
    def test_detect_coming_soon(self):
        """Test detecting 'Coming Soon' products"""
        self.mock_engine.is_element_visible = AsyncMock(return_value=True)
        
        result = async_to_sync(self.handler.detect_out_of_stock)()
        
        self.assertTrue(result)
    
    def test_detect_sold_out(self):
        """Test detecting 'Sold Out' text"""
        self.mock_engine.is_element_visible = AsyncMock(return_value=False)
        self.mock_engine.execute_js = AsyncMock(return_value="SOLD OUT")
        
        result = async_to_sync(self.handler.detect_out_of_stock)()
        
        self.assertTrue(result)
    
    def test_in_stock(self):
        """Test detecting product that's in stock"""
        self.mock_engine.is_element_visible = AsyncMock(return_value=False)
        self.mock_engine.execute_js = AsyncMock(return_value="Available")
        
        button_mock = MagicMock()
        self.mock_engine.query_selector = AsyncMock(return_value=button_mock)
        self.mock_engine.evaluate = AsyncMock(return_value=False)
        
        result = async_to_sync(self.handler.detect_out_of_stock)()
        
        self.assertFalse(result)


# ============================================================================
# TESTS: ERROR DETECTION
# ============================================================================

class TestErrorDetection(NikeSiteHandlerTestCase):
    """Test error detection"""
    
    def test_detect_captcha(self):
        """Test detecting captcha"""
        self.mock_engine.is_element_visible = AsyncMock(return_value=True)
        
        result = async_to_sync(self.handler.detect_captcha)()
        
        self.assertTrue(result)
    
    def test_no_captcha(self):
        """Test when no captcha present"""
        self.mock_engine.is_element_visible = AsyncMock(return_value=False)
        
        result = async_to_sync(self.handler.detect_captcha)()
        
        self.assertFalse(result)
    
    def test_detect_blocked(self):
        """Test detecting rate limiting"""
        self.mock_engine.get_title = AsyncMock(return_value="Access Denied")
        
        result = async_to_sync(self.handler.detect_blocked)()
        
        self.assertTrue(result)


# ============================================================================
# TESTS: HELPER METHODS
# ============================================================================

class TestHelperMethods(NikeSiteHandlerTestCase):
    """Test helper methods"""
    
    def test_extract_price(self):
        """Test price extraction"""
        self.mock_engine.extract_text = AsyncMock(return_value="$150")
        
        price = async_to_sync(self.handler._extract_price)()
        
        self.assertEqual(price, "$150")
    
    def test_extract_sku_from_url(self):
        """Test SKU extraction from URL"""
        url = "https://www.nike.com/t/air-jordan-1-w9HO9jOz/553558-404"
        
        sku = self.handler._extract_sku_from_url(url)
        
        self.assertEqual(sku, "553558-404")


# ============================================================================
# FULL WORKFLOW TEST
# ============================================================================

class TestFullWorkflow(NikeSiteHandlerTestCase):
    """Test complete user workflow"""
    
    def test_find_and_add_to_cart(self):
        """Test: Find product 'Air Jordan 1' in size '10' and add to cart"""
        # Step 1: Find product
        self.mock_engine.extract_text = AsyncMock(return_value="Air Jordan 1 Low")
        self.mock_engine.extract_attribute = AsyncMock(return_value="https://www.nike.com/t/air-jordan-1/553558-404")
        
        with patch.object(self.handler, '_extract_price', new_callable=AsyncMock, return_value="$150"):
            with patch.object(self.handler, '_get_available_sizes', new_callable=AsyncMock, return_value=["M 10 / W 11.5", "M 11 / W 12.5"]):
                product = async_to_sync(self.handler.find_product)("Air Jordan 1", "10")
        
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Air Jordan 1 Low")
        self.assertEqual(product.price, 150.0)
        
        # Step 2: Add to cart
        with patch.object(self.handler, 'select_size', new_callable=AsyncMock, return_value=True):
            with patch.object(self.handler, 'detect_out_of_stock', new_callable=AsyncMock, return_value=False):
                button_mock = MagicMock()
                self.mock_engine.query_selector = AsyncMock(return_value=button_mock)
                self.mock_engine.evaluate = AsyncMock(return_value=False)
                
                success = async_to_sync(self.handler.add_to_cart)("553558-404", "10")
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(self.handler.cart_item.product_name, "Air Jordan 1 Low")
        self.assertEqual(self.handler.cart_item.product_id, "553558-404")
        self.assertEqual(self.handler.cart_item.size, "10")
        self.assertEqual(self.handler.cart_item.price, 150.0)