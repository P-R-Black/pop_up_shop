# pop_up_bot/handlers/__init__.py

"""
Handlers Package

Site-specific handler implementations.

Base Handler:
- BaseSiteHandler: Abstract base for all site handlers

Site Handlers (to be implemented):
- NikeSiteHandler
- FootlockerSiteHandler
- AdidasSiteHandler
- NewBalanceSiteHandler
- SupremeSiteHandler

Usage:
    from pop_up_bot.handlers import BaseSiteHandler
    from pop_up_bot.handlers.nike import NikeSiteHandler
    
    handler = NikeSiteHandler(engine, session_manager, cookie_manager)
    product = await handler.find_product('Air Jordan 1', 'US 10')
    await handler.add_to_cart(product.product_id, 'US 10')
"""

from .base_handler import (
    BaseSiteHandler,
    Product,
    CartItem,
    ExecutionStep,
    SiteErrorType,
)

__all__ = [
    'BaseSiteHandler',
    'Product',
    'CartItem',
    'ExecutionStep',
    'SiteErrorType',
]