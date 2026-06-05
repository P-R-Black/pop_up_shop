# pop_up_bot/handlers/nike_handler.py

"""
Nike Site Handler

Implements Nike.com automation for the Pop Up Bot.
Handles product search, size selection, cart operations, and checkout.

Key Nike behaviors:
- Uses data-testid attributes heavily
- Size selection is button-based
- "Add to Bag" is the add-to-cart action
- Coming Soon products are common (need to detect)
- Uses dynamic pricing
"""

import logging
from typing import Optional
from datetime import datetime

from pop_up_bot.handlers.base_handler import BaseSiteHandler, Product, CartItem, SiteErrorType, ExecutionStep

logger = logging.getLogger(__name__)


# ============================================================================
# NIKE SELECTORS - Update these if Nike changes their site structure
# ============================================================================

NIKE_SELECTORS = {
    # Search & Navigation
    'search_input': "input[type='search']",
    'product_link': "a[href*='/t/']",
    'cart_link': "a[href*='/cart']",
    
    # Product Info
    'product_title': 'h1',
    'product_price': "span[data-testid='currentPrice-container']",
    'product_price_fallback': "span[data-lu-target='price']",
    
    # Size Selection - Uses radio inputs with labels (verified by manual inspection)
    'size_selector_container': "div[data-testid='pdp-grid-selector-grid']",
    'size_radio_input': "input[name='grid-selector-input']",
    'size_item_wrapper': "div[data-testid='pdp-grid-selector-item']",
    'size_label': "label[class*='u-full-width']",
    
    # Cart Actions
    'add_to_bag_button': "button:has-text('Add to Bag')",
    'add_to_bag_fallback': "button[class*='AddToCart']",
    
    # Stock Status
    'coming_soon_indicator': "div[data-testid='coming-soon']",
    'out_of_stock_indicator': "button:has-text('Add to Bag')[disabled]",
    
    # Checkout
    'checkout_button': "button:has-text('Checkout')",
}


class NikeSiteHandler(BaseSiteHandler):
    """
    Handler for Nike.com
    
    Automation flow:
    1. Navigate to Nike.com
    2. Search for product by name
    3. Click first result
    4. Check if in stock / coming soon
    5. Select size
    6. Add to bag
    7. Proceed to checkout
    """
    
    @property
    def site_name(self) -> str:
        return 'nike'
    
    @property
    def base_url(self) -> str:
        return 'https://www.nike.com'
    
    # ========================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================
    
    async def validate_site_connection(self) -> bool:
        """
        Validate that Nike site is accessible and not blocked.
        
        Returns:
            True if site is accessible
        """
        await self.set_step(ExecutionStep.VALIDATING_CONNECTION)
        
        try:
            # Navigate to home page
            await self.engine.navigate(self.base_url)
            
            # Check for common blocking indicators
            if await self.detect_blocked():
                await self.log_error(
                    SiteErrorType.BLOCKED,
                    "Nike site blocked - likely rate limited or IP banned"
                )
                return False
            
            # Check that search is present
            if not await self.engine.is_element_visible(NIKE_SELECTORS['search_input']):
                await self.log_error(
                    SiteErrorType.PRODUCT_NOT_FOUND,
                    "Search input not found on Nike homepage"
                )
                return False
            
            logger.info("Nike site is accessible")
            return True
        
        except Exception as e:
            await self.log_error(
                SiteErrorType.NETWORK_ERROR,
                f"Failed to validate Nike connection: {str(e)}"
            )
            return False
    
    async def find_product(
        self,
        product_name: str,
        size: str,
        color: Optional[str] = None,
    ) -> Optional[Product]:
        """
        Search for a product on Nike.com
        
        Args:
            product_name: Product name to search (e.g., "Air Jordan 1")
            size: Size to find (e.g., "US 10")
            color: Optional color preference
        
        Returns:
            Product object if found, None if not found
        """
        await self.set_step(ExecutionStep.SEARCHING_PRODUCT)
        
        try:
            # Navigate to Nike home if not already there
            await self.engine.navigate(self.base_url)
            
            # Click search input
            await self.engine.click(NIKE_SELECTORS['search_input'])
            
            # Type product name
            await self.engine.type(NIKE_SELECTORS['search_input'], product_name)
            
            # Wait for search results
            logger.info(f"Searching for: {product_name}")
            await self.engine.wait_for('a[href*="/t/"]', timeout=10000)
            
            # Click first product result
            first_product = await self.engine.query_selector(NIKE_SELECTORS['product_link'])
            if not first_product:
                await self.log_error(
                    SiteErrorType.PRODUCT_NOT_FOUND,
                    f"Product '{product_name}' not found in search results"
                )
                return None
            
            # Get product URL and click
            product_url = await self.engine.extract_attribute(
                NIKE_SELECTORS['product_link'],
                'href'
            )
            
            await self.engine.click(NIKE_SELECTORS['product_link'])
            
            # Wait for product page to load
            await self.engine.wait_for_load_state('networkidle')
            
            # Extract product info
            product_title = await self.engine.extract_text(NIKE_SELECTORS['product_title'])
            
            # Extract price
            price_text = await self._extract_price()
            
            # Parse price (e.g., "$150" -> 150.0)
            try:
                price = float(price_text.replace('$', '').replace(',', ''))
            except:
                price = 0.0
            
            # Get available sizes
            available_sizes = await self._get_available_sizes()
            
            # Create product object
            product = Product(
                product_id=self._extract_sku_from_url(product_url),
                name=product_title,
                price=price,
                available_sizes=available_sizes,
                product_url=product_url,
                in_stock=len(available_sizes) > 0,
            )
            
            self.product_found = product
            await self.set_step(ExecutionStep.PRODUCT_FOUND)
            logger.info(f"Product found: {product}")
            
            return product
        
        except Exception as e:
            await self.log_error(
                SiteErrorType.PRODUCT_NOT_FOUND,
                f"Error finding product: {str(e)}"
            )
            return None
    
    async def select_size(self, size: str) -> bool:
        """
        Select a size for the current product.
        
        Nike uses radio inputs with associated labels:
        - Hidden radio: <input type="radio" name="grid-selector-input" value="3.5">
        - Visible label: <label for="grid-selector-input-3.5">M 3.5 / W 5</label>
        
        We click the label to select the size.
        
        Args:
            size: Size to select (e.g., "US 10", "10", "3.5", "M 3.5 / W 5")
        
        Returns:
            True if size was selected
        """
        await self.set_step(ExecutionStep.SELECTING_SIZE)
        
        try:
            # Normalize size - remove "US " prefix if present
            size_normalized = size.replace('US ', '').strip()
            print('size_normalized', size_normalized)
            
            logger.info(f"Selecting size: {size_normalized}")
            
            # Get all size radio inputs
            size_radios = await self.engine.query_selector_all(
                NIKE_SELECTORS['size_radio_input']
            )
            print('size_radios', size_radios)
            if not size_radios:
                await self.log_error(
                    SiteErrorType.UNKNOWN,
                    "No size radio inputs found on product page"
                )
                return False
            
            logger.info(f"Found {len(size_radios)} available sizes")
            
            # Try to find matching size by value or label text
            for radio in size_radios:
                # Get the radio's value (e.g., "3.5", "10.5")
                radio_value = await self.engine.evaluate(
                    '(el) => el.value',
                    radio
                )
                # Get the radio's value (e
                
                # Get the associated label text (e.g., "M 3.5 / W 5", "US 10")
                radio_id = await self.engine.evaluate(
                    '(el) => el.id',
                    radio
                )
                
                label_text = ""
                if radio_id:
                    label = await self.engine.query_selector(f"label[for='{radio_id}']")
                    if label:
                        label_text = await self.engine.evaluate(
                            '(el) => el.innerText',
                            label
                        )
                
                # Check if this size matches the requested size
                if (size_normalized in str(radio_value) or 
                    size_normalized in str(label_text) or 
                    str(radio_value).strip() == size_normalized):
                    
                    # Click the associated label
                    if radio_id:
                        label = await self.engine.query_selector(f"label[for='{radio_id}']")
                        if label:
                            await self.engine.click_element(label)
                            logger.info(f"✓ Clicked size: {label_text} (value: {radio_value})")
                            await self.engine.wait_for_timeout(500)
                            return True
            
            # If no exact match found, click first available size
            logger.warning(f"Exact size '{size_normalized}' not found, clicking first available")
            first_radio_id = await self.engine.evaluate('(el) => el.id', size_radios[0])
            if first_radio_id:
                label = await self.engine.query_selector(f"label[for='{first_radio_id}']")
                if label:
                    await self.engine.click_element(label)
                    return True
            
            # Fallback: click the radio directly
            await self.engine.click_element(size_radios[0])
            return True
        
        except Exception as e:
            await self.log_error(
                SiteErrorType.UNKNOWN,
                f"Error selecting size: {str(e)}"
            )
            return False
    
    async def add_to_cart(
        self,
        product_id: str,
        size: str,
        quantity: int = 1,
    ) -> bool:
        """
        Add product to cart.
        
        Args:
            product_id: Product ID
            size: Size to add
            quantity: Quantity (usually 1 for sneakers)
        
        Returns:
            True if successfully added to cart
        """
        await self.set_step(ExecutionStep.ADDING_TO_CART)
        
        try:
            # Select size first
            size_selected = await self.select_size(size)
            if not size_selected:
                await self.log_error(
                    SiteErrorType.UNKNOWN,
                    "Could not select size before adding to cart"
                )
                return False
            
            # Check for out of stock
            if await self.detect_out_of_stock():
                await self.log_error(
                    SiteErrorType.OUT_OF_STOCK,
                    "Product is out of stock"
                )
                return False
            
            # Click "Add to Bag" button
            add_to_bag = await self.engine.query_selector(NIKE_SELECTORS['add_to_bag_button'])
            
            if not add_to_bag:
                # Try fallback selector
                add_to_bag = await self.engine.query_selector(NIKE_SELECTORS['add_to_bag_fallback'])
            
            if not add_to_bag:
                await self.log_error(
                    SiteErrorType.UNKNOWN,
                    "Add to Bag button not found"
                )
                return False
            
            # Check if button is disabled (out of stock)
            is_disabled = await self.engine.evaluate(
                '(el) => el.hasAttribute("disabled") || el.getAttribute("aria-disabled") === "true"',
                add_to_bag
            )
            
            if is_disabled:
                await self.log_error(
                    SiteErrorType.OUT_OF_STOCK,
                    "Add to Bag button is disabled - product out of stock"
                )
                return False
            
            # Click the button
            await self.engine.click_element(add_to_bag)
            logger.info("Clicked Add to Bag")
            
            # Wait for confirmation
            await self.engine.wait_for_timeout(2000)
            
            # Store cart item
            self.cart_item = CartItem(
                product_id=product_id,
                product_name=self.product_found.name if self.product_found else "Unknown",
                size=size,
                quantity=quantity,
                price=self.product_found.price if self.product_found else 0.0,
            )
            
            await self.set_step(ExecutionStep.CART_CONFIRMED)
            logger.info("Item added to cart successfully")
            
            return True
        
        except Exception as e:
            await self.log_error(
                SiteErrorType.UNKNOWN,
                f"Error adding to cart: {str(e)}"
            )
            return False
    
    async def check_cart(self) -> Optional[CartItem]:
        """
        Check what's in the cart.
        
        Returns:
            CartItem if something is in cart, None otherwise
        """
        try:
            # Navigate to cart
            await self.engine.click(NIKE_SELECTORS['cart_link'])
            await self.engine.wait_for_load_state('networkidle')
            
            # Check if cart is empty
            page_text = await self.engine.execute_js(
                'return document.body.innerText'
            )
            
            if 'empty' in page_text.lower():
                return None
            
            # Return the cart item we stored
            return self.cart_item
        
        except Exception as e:
            logger.error(f"Error checking cart: {str(e)}")
            return None
    
    async def is_item_in_stock(self) -> bool:
        """
        Check if item is in stock.
        
        Returns:
            True if in stock
        """
        try:
            # Check for out of stock indicators
            if await self.detect_out_of_stock():
                return False
            
            # Check if Add to Bag button is enabled
            add_to_bag = await self.engine.query_selector(NIKE_SELECTORS['add_to_bag_button'])
            
            if not add_to_bag:
                return False
            
            # Check if disabled
            is_disabled = await self.engine.evaluate(
                '(el) => el.hasAttribute("disabled")',
                add_to_bag
            )
            
            return not is_disabled
        
        except Exception:
            return False
    
    async def proceed_to_checkout(self) -> bool:
        """
        Proceed to checkout.
        
        Returns:
            True if successfully at checkout
        """
        await self.set_step(ExecutionStep.PROCEEDING_CHECKOUT)
        
        try:
            # Navigate to cart
            await self.engine.click(NIKE_SELECTORS['cart_link'])
            await self.engine.wait_for_load_state('networkidle')
            
            # Look for checkout button
            checkout_btn = await self.engine.query_selector(NIKE_SELECTORS['checkout_button'])
            
            if checkout_btn:
                await self.engine.click_element(checkout_btn)
                await self.engine.wait_for_load_state('networkidle')
            
            # Verify we're at checkout
            current_url = await self.engine.get_url()
            
            if '/checkout' in current_url or '/cart' in current_url:
                logger.info("Successfully navigated to checkout")
                return True
            
            return False
        
        except Exception as e:
            await self.log_error(
                SiteErrorType.CHECKOUT_ERROR,
                f"Error proceeding to checkout: {str(e)}"
            )
            return False
    
    # ========================================================================
    # NIKE-SPECIFIC ERROR DETECTION
    # ========================================================================
    
    async def detect_out_of_stock(self) -> bool:
        """
        Detect if product is out of stock on Nike.
        
        Nike indicators:
        - "Coming Soon" message
        - "Sold Out" text
        - "Add to Bag" button is disabled
        
        Returns:
            True if out of stock
        """
        try:
            # Check for Coming Soon
            coming_soon = await self.engine.is_element_visible(
                NIKE_SELECTORS['coming_soon_indicator']
            )
            
            if coming_soon:
                logger.warning("Product is Coming Soon - not yet available")
                return True
            
            # Check for Sold Out in page text
            page_text = await self.engine.execute_js(
                'return document.body.innerText.toUpperCase()'
            )
            
            if 'SOLD OUT' in page_text:
                logger.warning("Product is Sold Out")
                return True
            
            # Check if Add to Bag button is disabled
            add_to_bag = await self.engine.query_selector(NIKE_SELECTORS['add_to_bag_button'])
            
            if add_to_bag:
                is_disabled = await self.engine.evaluate(
                    '(el) => el.hasAttribute("disabled") || el.getAttribute("aria-disabled") === "true"',
                    add_to_bag
                )
                
                if is_disabled:
                    logger.warning("Add to Bag button is disabled")
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error detecting out of stock: {str(e)}")
            return False
    
    async def detect_captcha(self) -> bool:
        """
        Detect if Nike is showing captcha challenge.
        
        Returns:
            True if captcha detected
        """
        try:
            # Check for common captcha elements
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'div[class*="captcha"]',
                'div[id*="recaptcha"]',
            ]
            
            for selector in captcha_selectors:
                if await self.engine.is_element_visible(selector):
                    logger.warning(f"Captcha detected: {selector}")
                    return True
            
            return False
        
        except Exception:
            return False
    
    async def detect_blocked(self) -> bool:
        """
        Detect if we're blocked/rate-limited by Nike.
        
        Returns:
            True if blocked
        """
        try:
            title = await self.engine.get_title()
            page_text = await self.engine.execute_js(
                'return document.body.innerText.toUpperCase()'
            )
            
            blocked_indicators = [
                'ACCESS DENIED',
                'BLOCKED',
                'TOO MANY REQUESTS',
                '429',
                '403',
            ]
            
            for indicator in blocked_indicators:
                if indicator in title.upper() or indicator in page_text:
                    logger.warning(f"Nike blocked us: {indicator}")
                    return True
            
            return False
        
        except Exception:
            return False
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _extract_price(self) -> str:
        """Extract price from product page"""
        try:
            price = await self.engine.extract_text(NIKE_SELECTORS['product_price'])
            if not price:
                # Try fallback
                price = await self.engine.extract_text(NIKE_SELECTORS['product_price_fallback'])
            return price or "$0"
        except Exception:
            return "$0"
    
    async def _get_available_sizes(self) -> list:
        """
        Get list of available sizes from product page.
        
        Nike uses hidden radio inputs with associated labels.
        We extract the label text for each radio input.
        
        Returns:
            List of available sizes (e.g., ["M 3.5 / W 5", "M 4 / W 5.5", ...])
        """
        try:
            sizes = []
            
            # Get all size radio inputs
            size_radios = await self.engine.query_selector_all(
                NIKE_SELECTORS['size_radio_input']
            )
            
            if not size_radios:
                logger.warning("No size radio inputs found")
                return []
            
            logger.info(f"Found {len(size_radios)} available sizes")
            
            # Extract size text from associated labels
            for radio in size_radios:
                radio_id = await self.engine.evaluate(
                    '(el) => el.id',
                    radio
                )
                
                if radio_id:
                    label = await self.engine.query_selector(f"label[for='{radio_id}']")
                    if label:
                        size_text = await self.engine.evaluate(
                            '(el) => el.innerText',
                            label
                        )
                        if size_text:
                            sizes.append(size_text.strip())
            
            logger.info(f"Available sizes: {sizes}")
            return sizes
        
        except Exception as e:
            logger.error(f"Error getting available sizes: {str(e)}")
            return []
    
    def _extract_sku_from_url(self, url: str) -> str:
        """
        Extract SKU from Nike product URL.
        
        Nike URL format: https://www.nike.com/t/product-name-XXXXX/SKU
        Example: https://www.nike.com/t/air-jordan-1-low-w9HO9jOz/553558-404
        
        Args:
            url: Product URL
        
        Returns:
            SKU (e.g., "553558-404")
        """
        try:
            # Extract SKU (last part after /)
            sku = url.split('/')[-1]
            return sku
        except Exception:
            return "UNKNOWN"