# ============================================================
# pop_up_bot/handlers/shoe_palace_handler.py
#
# Handler for shoepalace.com (Shopify + FastSimon search)
#
# Key site characteristics:
# - Shopify storefront — consistent, stable structure
# - FastSimon search overlay (class="fast-simon-form")
# - Size selection via radio inputs (.SizeSwatch_Radio)
# - Available/soldout indicated by .swatch-element class
# - Product URLs follow /products/<slug> pattern
# - Price stored in data-price attribute (in cents: 22000 = $220)
# ============================================================

import logging
from typing import Optional
from datetime import datetime

from pop_up_bot.handlers.base_handler import (
    BaseSiteHandler,
    Product,
    CartItem,
    SiteErrorType,
    ExecutionStep,
)

logger = logging.getLogger(__name__)


SHOE_PALACE_SELECTORS = {
    # Search
    'search_input':         'input#search-field',
    'search_input_alt':     'input.nav-search-input',
    'search_form':          'form.search-form',

    # Search results — FastSimon product cards
    'product_card_link':    'a[href*="/products/"]',
    'product_card_wrapper': 'div.product-card-items-wrapper',

    # Product page — title & price
    'product_title':        'h1.product-title',
    'product_price':        'div#spProductPrice',
    'product_price_data':   'div[data-price]',      # data-price is in cents

    # Size selection
    # Available sizes only — soldout elements have class "soldout"
    'size_swatch_available': 'div.swatch-element.available',
    'size_radio_input':      'input.SizeSwatch_Radio',
    'size_label':            'label.SizeSwatch',

    # Add to cart
    'add_to_cart_button':   'button.productForm-submit',
    'add_to_cart_alt':      'button.js-productForm-submit',

    # Stock status
    # Sold-out size swatches have class "soldout"
    'soldout_swatch':       'div.swatch-element.soldout',

    # Cart & checkout
    'cart_link':            'a[href="/cart"]',
    'checkout_button':      'button[name="checkout"]',
    'checkout_button_alt':  'input[name="checkout"]',
}


class ShoePalaceSiteHandler(BaseSiteHandler):
    """
    Handler for shoepalace.com

    Shopify-based storefront with FastSimon search.
    Lighter bot protection than Footlocker — generally more
    bot-friendly due to Shopify's standard infrastructure.

    Automation flow:
    1. Navigate to shoepalace.com
    2. Enter search term in FastSimon search overlay
    3. Click first matching product card
    4. Select size via radio input (.SizeSwatch_Radio)
    5. Click "Add to Cart"
    6. Navigate to /cart and proceed to checkout
    """

    @property
    def site_name(self) -> str:
        return 'shoe_palace'

    @property
    def base_url(self) -> str:
        return 'https://www.shoepalace.com'

    # ------------------------------------------------------------------
    # Connection validation
    # ------------------------------------------------------------------

    async def validate_site_connection(self) -> bool:
        await self.set_step(ExecutionStep.VALIDATING_CONNECTION)

        try:
            await self.engine.navigate(self.base_url)

            if await self.detect_blocked():
                await self.log_error(
                    SiteErrorType.BLOCKED,
                    'Shoe Palace site blocked or inaccessible'
                )
                return False

            # Verify search input is present
            if not await self.engine.is_element_visible(SHOE_PALACE_SELECTORS['search_input']):
                # Try alt selector
                if not await self.engine.is_element_visible(SHOE_PALACE_SELECTORS['search_input_alt']):
                    await self.log_error(
                        SiteErrorType.PRODUCT_NOT_FOUND,
                        'Search input not found on Shoe Palace homepage'
                    )
                    return False

            logger.info('Shoe Palace site is accessible')
            return True

        except Exception as e:
            await self.log_error(
                SiteErrorType.NETWORK_ERROR,
                f'Failed to validate Shoe Palace connection: {str(e)}'
            )
            return False

    # ------------------------------------------------------------------
    # Product search
    # ------------------------------------------------------------------

    async def find_product(
        self,
        product_name: str,
        size: str,
        color: Optional[str] = None,
    ) -> Optional[Product]:
        await self.set_step(ExecutionStep.SEARCHING_PRODUCT)

        try:
            await self.engine.navigate(self.base_url)

            # FastSimon search opens as an overlay — click/focus the input
            search_sel = SHOE_PALACE_SELECTORS['search_input']
            if not await self.engine.is_element_visible(search_sel):
                search_sel = SHOE_PALACE_SELECTORS['search_input_alt']

            await self.engine.click(search_sel)
            await self.engine.type(search_sel, product_name)

            # Submit the search form
            await self.engine.execute_js(
                "document.querySelector('form.search-form').submit()"
            )

            await self.engine.wait_for_load_state('networkidle')
            await self.engine.wait_for_timeout(2000)

            logger.info(f'Searching Shoe Palace for: {product_name}')

            # Wait for product cards to render (FastSimon loads async)
            try:
                await self.engine.wait_for(
                    SHOE_PALACE_SELECTORS['product_card_link'],
                    timeout=10,
                    visible=True
                )
            except Exception:
                await self.log_error(
                    SiteErrorType.PRODUCT_NOT_FOUND,
                    f'No product results found for "{product_name}"'
                )
                return None

            # Get all product links and click the first one
            # Filter out non-product links (navigation etc.)
            product_links = await self.engine.query_selector_all(
                SHOE_PALACE_SELECTORS['product_card_link']
            )

            if not product_links:
                await self.log_error(
                    SiteErrorType.PRODUCT_NOT_FOUND,
                    f'Product "{product_name}" not found on Shoe Palace'
                )
                return None

            # Get the href and navigate directly (more reliable than clicking)
            product_url = await self.engine.extract_attribute(
                SHOE_PALACE_SELECTORS['product_card_link'],
                'href'
            )

            if not product_url:
                await self.log_error(
                    SiteErrorType.PRODUCT_NOT_FOUND,
                    'Could not extract product URL from search results'
                )
                return None

            # Build full URL if relative
            if product_url.startswith('/'):
                product_url = f'{self.base_url}{product_url}'

            await self.engine.navigate(product_url)
            await self.engine.wait_for_load_state('networkidle')
            await self.engine.wait_for_timeout(1000)

            # Extract product title
            product_title = await self.engine.extract_text(
                SHOE_PALACE_SELECTORS['product_title']
            )
            product_title = (product_title or '').strip()

            # Extract price from data-price attribute (value is in cents)
            price = await self._extract_price()

            # Get available sizes
            available_sizes = await self._get_available_sizes()

            product = Product(
                product_id=self._extract_handle_from_url(product_url),
                name=product_title,
                price=price,
                available_sizes=available_sizes,
                product_url=product_url,
                in_stock=len(available_sizes) > 0,
            )

            self.product_found = product
            await self.set_step(ExecutionStep.PRODUCT_FOUND)
            logger.info(f'Product found on Shoe Palace: {product}')

            return product

        except Exception as e:
            await self.log_error(
                SiteErrorType.PRODUCT_NOT_FOUND,
                f'Error finding product on Shoe Palace: {str(e)}'
            )
            return None

    # ------------------------------------------------------------------
    # Size selection
    # ------------------------------------------------------------------

    async def select_size(self, size: str) -> bool:
        """
        Select a size by clicking the radio input label.

        Shoe Palace size structure:
            <div class="swatch-element available" data-value="10">
                <input id="swatch-0-10" class="SizeSwatch_Radio"
                       name="option-0" type="radio" value="10">
                <label class="SizeSwatch" for="swatch-0-10"></label>
            </div>

        We click the <label> associated with the matching radio input,
        or click the radio directly via JavaScript if label click fails.
        """
        await self.set_step(ExecutionStep.SELECTING_SIZE)

        try:
            # Normalize size — strip "US ", "Men's ", "Women's " prefixes
            size_normalized = (
                size.replace("Men's ", '')
                    .replace("Womens ", '')
                    .replace("Women's ", '')
                    .replace('US ', '')
                    .strip()
            )
            logger.info(f'Selecting size on Shoe Palace: {size_normalized}')

            # Find all available swatch elements
            available_swatches = await self.engine.query_selector_all(
                SHOE_PALACE_SELECTORS['size_swatch_available']
            )

            if not available_swatches:
                await self.log_error(
                    SiteErrorType.OUT_OF_STOCK,
                    'No available sizes found on product page'
                )
                return False

            for swatch in available_swatches:
                # Get the data-value attribute on the swatch div
                data_value = await self.engine.evaluate(
                    '(el) => el.getAttribute("data-value")',
                    swatch
                )

                if not data_value:
                    continue

                if data_value.strip() == size_normalized:
                    # Find the radio input inside this swatch
                    radio = await self.engine.evaluate(
                        '(el) => el.querySelector("input.SizeSwatch_Radio")',
                        swatch
                    )

                    # Find the label and click it
                    label = await self.engine.evaluate(
                        '(el) => el.querySelector("label.SizeSwatch")',
                        swatch
                    )

                    if label:
                        await self.engine.click_element(label)
                        logger.info(f'✓ Clicked size label for {size_normalized}')
                    else:
                        # Fallback: click the swatch div directly
                        await self.engine.click_element(swatch)
                        logger.info(f'✓ Clicked swatch div for {size_normalized}')

                    await self.engine.wait_for_timeout(500)
                    return True

            # Size not found in available swatches
            await self.log_error(
                SiteErrorType.OUT_OF_STOCK,
                f'Size {size_normalized} not available on Shoe Palace'
            )
            return False

        except Exception as e:
            await self.log_error(
                SiteErrorType.UNKNOWN,
                f'Error selecting size on Shoe Palace: {str(e)}'
            )
            return False

    # ------------------------------------------------------------------
    # Add to cart
    # ------------------------------------------------------------------

    async def add_to_cart(
        self,
        product_id: str,
        size: str,
        quantity: int = 1,
    ) -> bool:
        await self.set_step(ExecutionStep.ADDING_TO_CART)

        try:
            # Select size first
            size_selected = await self.select_size(size)
            if not size_selected:
                await self.log_error(
                    SiteErrorType.UNKNOWN,
                    'Could not select size before adding to cart'
                )
                return False

            # Find the add to cart button
            atc_button = await self.engine.query_selector(
                SHOE_PALACE_SELECTORS['add_to_cart_button']
            )
            if not atc_button:
                atc_button = await self.engine.query_selector(
                    SHOE_PALACE_SELECTORS['add_to_cart_alt']
                )

            if not atc_button:
                await self.log_error(
                    SiteErrorType.UNKNOWN,
                    'Add to Cart button not found'
                )
                return False

            # Check if disabled
            is_disabled = await self.engine.evaluate(
                '(el) => el.disabled || el.getAttribute("aria-disabled") === "true"',
                atc_button
            )
            if is_disabled:
                await self.log_error(
                    SiteErrorType.OUT_OF_STOCK,
                    'Add to Cart button is disabled'
                )
                return False

            await self.engine.click_element(atc_button)
            logger.info('Clicked Add to Cart on Shoe Palace')

            # Wait for cart to update — Shopify AJAX cart
            await self.engine.wait_for_timeout(2500)

            self.cart_item = CartItem(
                product_id=product_id,
                product_name=self.product_found.name if self.product_found else 'Unknown',
                size=size,
                quantity=quantity,
                price=self.product_found.price if self.product_found else 0.0,
            )

            await self.set_step(ExecutionStep.CART_CONFIRMED)
            logger.info('Item added to cart on Shoe Palace')
            return True

        except Exception as e:
            await self.log_error(
                SiteErrorType.UNKNOWN,
                f'Error adding to cart on Shoe Palace: {str(e)}'
            )
            return False

    # ------------------------------------------------------------------
    # Cart check
    # ------------------------------------------------------------------

    async def check_cart(self) -> Optional[CartItem]:
        try:
            await self.engine.navigate(f'{self.base_url}/cart')
            await self.engine.wait_for_load_state('networkidle')

            page_text = await self.engine.execute_js(
                'return document.body.innerText'
            )
            if 'empty' in page_text.lower():
                return None

            return self.cart_item
        except Exception as e:
            logger.error(f'Error checking Shoe Palace cart: {str(e)}')
            return None

    # ------------------------------------------------------------------
    # Stock check
    # ------------------------------------------------------------------

    async def is_item_in_stock(self) -> bool:
        try:
            available = await self.engine.query_selector_all(
                SHOE_PALACE_SELECTORS['size_swatch_available']
            )
            return len(available) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------

    async def proceed_to_checkout(self) -> bool:
        await self.set_step(ExecutionStep.PROCEEDING_CHECKOUT)

        try:
            await self.engine.navigate(f'{self.base_url}/cart')
            await self.engine.wait_for_load_state('networkidle')
            await self.engine.wait_for_timeout(1000)

            # Shopify checkout button
            checkout_btn = await self.engine.query_selector(
                SHOE_PALACE_SELECTORS['checkout_button']
            )
            if not checkout_btn:
                checkout_btn = await self.engine.query_selector(
                    SHOE_PALACE_SELECTORS['checkout_button_alt']
                )

            if checkout_btn:
                await self.engine.click_element(checkout_btn)
                await self.engine.wait_for_load_state('networkidle')

            current_url = await self.engine.get_url()

            if 'checkout' in current_url or 'cart' in current_url:
                logger.info(f'Shoe Palace: at checkout — {current_url}')
                return True

            return False

        except Exception as e:
            await self.log_error(
                SiteErrorType.CHECKOUT_ERROR,
                f'Error proceeding to checkout on Shoe Palace: {str(e)}'
            )
            return False

    # ------------------------------------------------------------------
    # Shoe Palace-specific detection
    # ------------------------------------------------------------------

    async def detect_out_of_stock(self) -> bool:
        try:
            available = await self.engine.query_selector_all(
                SHOE_PALACE_SELECTORS['size_swatch_available']
            )
            if not available:
                logger.warning('Shoe Palace: no available sizes')
                return True

            page_text = await self.engine.execute_js(
                'return document.body.innerText.toUpperCase()'
            )
            if 'SOLD OUT' in page_text:
                logger.warning('Shoe Palace: page shows Sold Out')
                return True

            return False
        except Exception:
            return False

    async def detect_blocked(self) -> bool:
        try:
            title = await self.engine.get_title()
            page_text = await self.engine.execute_js(
                'return document.body.innerText.toUpperCase()'
            )
            indicators = ['ACCESS DENIED', 'BLOCKED', 'TOO MANY REQUESTS', '429', '403']
            return any(i in title.upper() or i in page_text for i in indicators)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _extract_price(self) -> float:
        """
        Extract price from data-price attribute (stored in cents).
        e.g. data-price="22000" → 220.00
        """
        try:
            price_cents = await self.engine.extract_attribute(
                SHOE_PALACE_SELECTORS['product_price_data'],
                'data-price'
            )
            if price_cents:
                return float(price_cents) / 100
        except Exception:
            pass

        # Fallback: parse visible price text
        try:
            price_text = await self.engine.extract_text(
                SHOE_PALACE_SELECTORS['product_price']
            )
            if price_text:
                cleaned = price_text.replace('$', '').replace(',', '').strip()
                # Take first number found
                import re
                match = re.search(r'[\d.]+', cleaned)
                if match:
                    return float(match.group())
        except Exception:
            pass

        return 0.0

    async def _get_available_sizes(self) -> list:
        """
        Return list of available size values from .swatch-element.available divs.
        Ignores .swatch-element.soldout elements automatically.
        """
        try:
            available_swatches = await self.engine.query_selector_all(
                SHOE_PALACE_SELECTORS['size_swatch_available']
            )
            sizes = []
            for swatch in available_swatches:
                value = await self.engine.evaluate(
                    '(el) => el.getAttribute("data-value")',
                    swatch
                )
                if value:
                    sizes.append(value.strip())
            logger.info(f'Shoe Palace available sizes: {sizes}')
            return sizes
        except Exception as e:
            logger.error(f'Error getting Shoe Palace sizes: {str(e)}')
            return []

    def _extract_handle_from_url(self, url: str) -> str:
        """
        Extract Shopify product handle from URL.
        e.g. /products/jordan-dd0587-008-air-jordan-5-retro → jordan-dd0587-008-air-jordan-5-retro
        """
        try:
            parts = url.rstrip('/').split('/products/')
            if len(parts) > 1:
                return parts[-1].split('?')[0]
        except Exception:
            pass
        return 'unknown'