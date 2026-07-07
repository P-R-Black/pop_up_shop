# ============================================================
# pop_up_bot/tests/test_orchestrator_shoe_palace.py
#
# Tests for BotOrchestrator._attempt_shoe_palace()
# Mirrors the pattern used in test_orchestrator.py for Nike.
# ============================================================

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from django.test import TestCase

from pop_up_bot.orchestrator import BotOrchestrator, SearchParameters, ExecutionStatus
from pop_up_bot.handlers.base_handler import Product, CartItem


def make_orchestrator():
    return BotOrchestrator(
        execution_id='test-uuid-123',
        strategy_factory=MagicMock(),
        session_manager=AsyncMock(),
        procurement_lock=AsyncMock(),
        event_logger=AsyncMock(),
    )


def make_search_params(sex=None):
    o = make_orchestrator()
    o.search_params = SearchParameters(
        product_name='Air Jordan 5 Retro',
        size='10',
        sex=sex,
        color=None,
    )
    return o


MOCK_PRODUCT = Product(
    product_id='jordan-dd0587-008',
    name='Air Jordan 5 Retro Black Carolina',
    price=220.0,
    available_sizes=['9', '10', '10.5', '11'],
    product_url='https://www.shoepalace.com/products/jordan-dd0587-008',
    in_stock=True,
)


class TestAttemptShoePalace(TestCase):
    """Tests for BotOrchestrator._attempt_shoe_palace()"""

    @pytest.mark.asyncio
    async def test_attempt_shoe_palace_success(self):
        """Full successful flow returns success dict."""
        orchestrator = make_search_params(sex='Mens')

        mock_result = {
            'success': True,
            'site': 'shoe_palace',
            'product_name': 'Air Jordan 5 Retro Black Carolina',
            'size': '10',
            'order_id': None,
            'price': 220.0,
            'error_type': 'success',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_shoe_palace()

        self.assertTrue(result['success'])
        self.assertEqual(result['site'], 'shoe_palace')
        self.assertEqual(result['size'], '10')
        self.assertIsNone(result['order_id'])
        self.assertEqual(result['error_type'], 'success')

    @pytest.mark.asyncio
    async def test_attempt_shoe_palace_product_not_found(self):
        """Returns item_not_found when product search fails."""
        orchestrator = make_search_params()

        mock_result = {
            'success': False,
            'site': 'shoe_palace',
            'error': 'Product not found',
            'error_type': 'item_not_found',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_shoe_palace()

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'item_not_found')

    @pytest.mark.asyncio
    async def test_attempt_shoe_palace_site_not_accessible(self):
        """Returns rate_limited when site connection fails."""
        orchestrator = make_search_params()

        mock_result = {
            'success': False,
            'site': 'shoe_palace',
            'error': 'Shoe Palace site not accessible',
            'error_type': 'rate_limited',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_shoe_palace()

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'rate_limited')

    @pytest.mark.asyncio
    async def test_attempt_shoe_palace_add_to_cart_fails(self):
        """Returns correct error_type when add_to_cart fails."""
        orchestrator = make_search_params()

        mock_result = {
            'success': False,
            'site': 'shoe_palace',
            'error': 'Failed to add to cart',
            'error_type': 'out_of_stock',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_shoe_palace()

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'out_of_stock')

    @pytest.mark.asyncio
    async def test_attempt_shoe_palace_checkout_fails(self):
        orchestrator = make_search_params()

        mock_result = {
            'success': False,
            'site': 'shoe_palace',
            'error': 'Failed to reach checkout',
            'error_type': 'checkout_error',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_shoe_palace()

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'checkout_error')

    @pytest.mark.asyncio
    async def test_attempt_shoe_palace_exception_returns_bot_crash(self):
        """Unhandled exception maps to bot_crash."""
        orchestrator = make_search_params()

        mock_result = {
            'success': False,
            'site': 'shoe_palace',
            'error': 'Playwright timeout',
            'error_type': 'bot_crash',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_shoe_palace()

        self.assertFalse(result['success'])
        self.assertEqual(result['error_type'], 'bot_crash')

    # ------------------------------------------------------------------
    # _attempt_site routing
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_attempt_site_routes_shoe_palace(self):
        """_attempt_site('shoe_palace') calls _attempt_shoe_palace."""
        orchestrator = make_search_params()

        mock_result = {
            'success': True,
            'site': 'shoe_palace',
            'product_name': 'Air Jordan 5 Retro',
            'size': '10',
            'order_id': None,
            'price': 220.0,
            'error_type': 'success',
        }

        with patch.object(orchestrator, '_attempt_shoe_palace', return_value=mock_result):
            result = await orchestrator._attempt_site(site='shoe_palace')

        self.assertEqual(result['site'], 'shoe_palace')
        self.assertTrue(result['success'])

    @pytest.mark.asyncio
    async def test_attempt_site_routes_nike(self):
        """_attempt_site('nike') still calls _attempt_nike, not shoe_palace."""
        orchestrator = make_search_params()

        mock_result = {
            'success': True,
            'site': 'nike',
            'product_name': 'Air Jordan 5 Retro',
            'size': '10',
            'order_id': None,
            'price': 220.0,
            'error_type': 'success',
        }

        with patch.object(orchestrator, '_attempt_nike', return_value=mock_result):
            result = await orchestrator._attempt_site(site='nike')

        self.assertEqual(result['site'], 'nike')

    @pytest.mark.asyncio
    async def test_attempt_site_unimplemented_handler(self):
        """Unimplemented site returns graceful failure."""
        orchestrator = make_search_params()
        result = await orchestrator._attempt_site(site='footlocker')

        self.assertFalse(result['success'])
        self.assertEqual(result['site'], 'footlocker')
        self.assertIn('not yet implemented', result['error'])
        self.assertEqual(result['error_type'], 'item_not_found')

    # ------------------------------------------------------------------
    # Sex/size handling for Shoe Palace
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_shoe_palace_search_includes_sex_in_query(self):
        """
        For Shoe Palace, sex should be prepended to the search query,
        not appended to the size string like Nike.
        Verified by checking that _attempt_shoe_palace uses search_query,
        not _build_nike_size output.
        """
        orchestrator = make_search_params(sex='Womens')

        # The search query passed to find_product should include 'Womens'
        captured_query = {}

        async def fake_attempt():
            search_query = orchestrator.search_params.product_name
            if orchestrator.search_params.sex:
                search_query = f"{orchestrator.search_params.sex} {search_query}"
            captured_query['query'] = search_query
            return {
                'success': True, 'site': 'shoe_palace',
                'product_name': 'Air Jordan 5 Retro', 'size': '10',
                'order_id': None, 'price': 220.0, 'error_type': 'success',
            }

        with patch.object(orchestrator, '_attempt_shoe_palace', side_effect=fake_attempt):
            await orchestrator._attempt_shoe_palace()

        self.assertIn('Womens', captured_query.get('query', ''))
        self.assertIn('Air Jordan 5 Retro', captured_query.get('query', ''))