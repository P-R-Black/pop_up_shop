# pop_up_bot/strategies/__init__.py

"""
Procurement Strategies Package

Strategies determine which sites to try, in what order, and fallback behavior.

Available Strategies:
- SequentialStrategy: Try sites one-by-one (default, safe)
- ParallelStrategy: Try all sites simultaneously (fast)
- PriorityStrategy: Custom priority order (flexible)
- FastestStrategy: Aggressive parallel (risky, fastest)
- CheapestStrategy: Lower-price retailers first (budget)
- RetailOnlyStrategy: Official sources only (authentic)

Usage:
    from pop_up_bot.strategies import StrategyFactory, SequentialStrategy
    
    # Create by name
    strategy = StrategyFactory.create('sequential', sites=['nike', 'adidas'])
    
    # Or directly
    strategy = SequentialStrategy(sites=['nike', 'adidas'])
    
    # Get execution order
    sites = strategy.get_site_order()
    
    # Track execution
    strategy.mark_attempted('nike')
    strategy.mark_failed('nike')
    strategy.mark_successful('footlocker')
"""

from .base import ProcurementStrategy, Site, SiteType
from .implementations import (
    SequentialStrategy,
    ParallelStrategy,
    PriorityStrategy,
    FastestStrategy,
    CheapestStrategy,
    RetailOnlyStrategy,
)
from .factory import StrategyFactory

__all__ = [
    'ProcurementStrategy',
    'Site',
    'SiteType',
    'SequentialStrategy',
    'ParallelStrategy',
    'PriorityStrategy',
    'FastestStrategy',
    'CheapestStrategy',
    'RetailOnlyStrategy',
    'StrategyFactory',
]