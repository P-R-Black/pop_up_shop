# pop_up_bot/strategies/implementations.py

import logging
from typing import List, Optional

from .base import ProcurementStrategy

logger = logging.getLogger(__name__)


class SequentialStrategy(ProcurementStrategy):
    """
    Try sites one at a time until success.
    
    Default strategy. Stops on first success.
    
    Order: ['nike', 'footlocker', 'adidas']
    Behavior: nike → fail → footlocker → fail → adidas → success (STOP)
    
    Best for:
    - Conservative approach
    - Avoiding bans from multiple site attempts
    - When you want to avoid waste
    """
    
    def __init__(
        self,
        sites: Optional[List[str]] = None,
        timeout_per_site: int = 30,
    ):
        """
        Initialize SequentialStrategy.
        
        Args:
            sites: List of sites to try in order
            timeout_per_site: Timeout per site in seconds
        """
        super().__init__(timeout_per_site)
        self.sites = sites or ['nike', 'footlocker', 'adidas', 'new_balance']
        logger.info(f"SequentialStrategy: {self.sites}")
    
    def get_site_order(self) -> List[str]:
        """Return sites in order"""
        return self.sites
    
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """
        Continue if last site failed.
        
        Stop if:
        - Last site was successful
        - No more sites remaining
        """
        if last_result.get('success'):
            return False  # Stop on success
        
        remaining = self.get_remaining_sites()
        return len(remaining) > 0


class ParallelStrategy(ProcurementStrategy):
    """
    Try multiple sites simultaneously.
    
    Return when ANY site succeeds.
    
    Order: All sites at once
    Behavior: nike + footlocker + adidas (parallel) → first success WINS
    
    Best for:
    - Time-sensitive drops
    - When speed matters more than stealth
    - Products that sell out quickly
    """
    
    def __init__(
        self,
        sites: Optional[List[str]] = None,
        timeout_per_site: int = 30,
    ):
        """
        Initialize ParallelStrategy.
        
        Args:
            sites: List of sites to try in parallel
            timeout_per_site: Timeout per site in seconds
        """
        super().__init__(timeout_per_site)
        self.sites = sites or ['nike', 'footlocker', 'adidas', 'new_balance']
        logger.info(f"ParallelStrategy: {self.sites}")
    
    def get_site_order(self) -> List[str]:
        """Return all sites to try in parallel"""
        return self.sites
    
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """
        In parallel mode, we don't continue - we wait for first success.
        
        In practice, this is handled by the orchestrator using asyncio.gather
        with return_when=asyncio.FIRST_COMPLETED
        """
        return False  # Stop after first result


class PriorityStrategy(ProcurementStrategy):
    """
    Try highest-priority sites first.
    
    Uses site priority configuration. Can customize priority order.
    
    Order: By priority (1=highest)
    Default: nike (1) → footlocker (2) → adidas (3)
    
    Best for:
    - Preferred retailers
    - When some sites are more reliable
    - Customizable based on product
    """
    
    def __init__(
        self,
        priority_order: Optional[List[str]] = None,
        timeout_per_site: int = 30,
    ):
        """
        Initialize PriorityStrategy.
        
        Args:
            priority_order: Sites in priority order (highest first)
            timeout_per_site: Timeout per site in seconds
        """
        super().__init__(timeout_per_site)
        self.priority_order = priority_order or [
            'nike', 'footlocker', 'adidas', 'new_balance', 'supreme'
        ]
        logger.info(f"PriorityStrategy: {self.priority_order}")
    
    def get_site_order(self) -> List[str]:
        """Return sites sorted by priority"""
        return self.priority_order
    
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """Continue if failed, stop if succeeded"""
        if last_result.get('success'):
            return False
        
        remaining = self.get_remaining_sites()
        return len(remaining) > 0


class FastestStrategy(ProcurementStrategy):
    """
    Parallel execution with fastest response wins.
    
    Similar to ParallelStrategy but explicitly optimized for speed.
    Uses shorter timeouts and aggressive parallelism.
    
    Order: All sites simultaneously
    Behavior: Race to success
    
    Best for:
    - Limited drops
    - When milliseconds matter
    - Hyped releases
    """
    
    def __init__(
        self,
        sites: Optional[List[str]] = None,
        timeout_per_site: int = 15,  # Aggressive timeouts
    ):
        """
        Initialize FastestStrategy.
        
        Args:
            sites: Sites to try
            timeout_per_site: Short timeout for aggressive competition
        """
        super().__init__(timeout_per_site)
        self.sites = sites or ['nike', 'footlocker', 'adidas', 'new_balance']
        logger.info(f"FastestStrategy: {self.sites} (timeout: {timeout_per_site}s)")
    
    def get_site_order(self) -> List[str]:
        """Return all sites"""
        return self.sites
    
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """Stop - we race all sites simultaneously"""
        return False


class CheapestStrategy(ProcurementStrategy):
    """
    Try lower-price retailers first.
    
    Future: Integrate with price tracking system.
    Currently uses fixed price tiers.
    
    Order: retail → boutique → reseller
    
    Best for:
    - Budget-conscious users
    - When price matters
    - Multiple source availability
    """
    
    def __init__(
        self,
        timeout_per_site: int = 30,
    ):
        """Initialize CheapestStrategy"""
        super().__init__(timeout_per_site)
        # Sort by price tier: retail (cheapest) → boutique → reseller
        self.sites = [
            'nike', 'footlocker', 'adidas', 'new_balance', 'supreme',
            'grailed', 'stockx'
        ]
        logger.info(f"CheapestStrategy: Price-optimized order")
    
    def get_site_order(self) -> List[str]:
        """Return sites sorted by price tier (cheapest first)"""
        # Could be enhanced with dynamic price tracking
        return self.sites
    
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """Continue until success or all sites tried"""
        if last_result.get('success'):
            return False
        
        remaining = self.get_remaining_sites()
        return len(remaining) > 0


class RetailOnlyStrategy(ProcurementStrategy):
    """
    Only try official retail sites.
    
    Skip resellers and boutiques.
    Ensures product authenticity.
    
    Order: Official retail only
    Sites: nike, footlocker, adidas, new_balance, supreme
    
    Best for:
    - Verified authenticity required
    - Avoiding counterfeits
    - Official releases only
    """
    
    def __init__(
        self,
        timeout_per_site: int = 30,
    ):
        """Initialize RetailOnlyStrategy"""
        super().__init__(timeout_per_site)
        # Filter to official retail only
        self.sites = [
            'nike', 'footlocker', 'adidas', 'new_balance', 'supreme'
        ]
        logger.info(f"RetailOnlyStrategy: Official retail only")
    
    def get_site_order(self) -> List[str]:
        """Return official retail sites only"""
        return self.sites
    
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """Continue until success or all retail sites tried"""
        if last_result.get('success'):
            return False
        
        remaining = self.get_remaining_sites()
        return len(remaining) > 0