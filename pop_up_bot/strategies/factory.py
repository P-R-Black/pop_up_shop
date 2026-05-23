# pop_up_bot/strategies/factory.py

import logging
from typing import List

from .base import ProcurementStrategy
from .implementations import (
    SequentialStrategy,
    ParallelStrategy,
    PriorityStrategy,
    FastestStrategy,
    CheapestStrategy,
    RetailOnlyStrategy,
)

logger = logging.getLogger(__name__)


class StrategyFactory:
    """
    Factory for creating procurement strategies.
    
    Usage:
        strategy = StrategyFactory.create('sequential', sites=['nike', 'adidas'])
        strategy = StrategyFactory.create('parallel')
        strategy = StrategyFactory.create('fastest')
    """
    
    STRATEGIES = {
        'sequential': SequentialStrategy,
        'parallel': ParallelStrategy,
        'priority': PriorityStrategy,
        'fastest': FastestStrategy,
        'cheapest': CheapestStrategy,
        'retail_only': RetailOnlyStrategy,
    }
    
    @classmethod
    def create(cls, strategy_name: str, **kwargs) -> ProcurementStrategy:
        """
        Create a strategy by name.
        
        Args:
            strategy_name: Name of strategy ('sequential', 'parallel', etc.)
            **kwargs: Strategy-specific arguments
        
        Returns:
            Strategy instance
        
        Raises:
            ValueError: If strategy name is unknown
        
        Example:
            strategy = StrategyFactory.create(
                'sequential',
                sites=['nike', 'footlocker'],
                timeout_per_site=45,
            )
        """
        if strategy_name not in cls.STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {', '.join(cls.STRATEGIES.keys())}"
            )
        
        strategy_class = cls.STRATEGIES[strategy_name]
        logger.info(f"Creating strategy: {strategy_name}")
        return strategy_class(**kwargs)
    
    @classmethod
    def get_available(cls) -> List[str]:
        """Get list of available strategy names"""
        return list(cls.STRATEGIES.keys())