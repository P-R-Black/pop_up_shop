# pop_up_bot/strategies/base.py

import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SiteType(str, Enum):
    """Categorize sites for strategy filtering"""
    OFFICIAL_RETAIL = 'official_retail'
    RESELLER = 'reseller'
    BOUTIQUE = 'boutique'


class Site:
    """Represents a retail site for procurement"""
    
    SITE_REGISTRY = {
        'nike': {
            'type': SiteType.OFFICIAL_RETAIL,
            'priority': 1,
            'price_tier': 'retail',
            'timeout': 30,
        },
        'footlocker': {
            'type': SiteType.OFFICIAL_RETAIL,
            'priority': 2,
            'price_tier': 'retail',
            'timeout': 30,
        },
        'adidas': {
            'type': SiteType.OFFICIAL_RETAIL,
            'priority': 3,
            'price_tier': 'retail',
            'timeout': 30,
        },
        'new_balance': {
            'type': SiteType.OFFICIAL_RETAIL,
            'priority': 4,
            'price_tier': 'retail',
            'timeout': 30,
        },
        'supreme': {
            'type': SiteType.OFFICIAL_RETAIL,
            'priority': 5,
            'price_tier': 'retail',
            'timeout': 30,
        },
        'grailed': {
            'type': SiteType.RESELLER,
            'priority': 6,
            'price_tier': 'premium',
            'timeout': 45,
        },
        'stockx': {
            'type': SiteType.RESELLER,
            'priority': 7,
            'price_tier': 'premium',
            'timeout': 45,
        },
    }
    
    def __init__(self, name: str):
        """Initialize a site"""
        if name not in self.SITE_REGISTRY:
            raise ValueError(f"Unknown site: {name}")
        
        self.name = name
        self.config = self.SITE_REGISTRY[name]
    
    @property
    def type(self) -> SiteType:
        return self.config['type']
    
    @property
    def priority(self) -> int:
        return self.config['priority']
    
    @property
    def price_tier(self) -> str:
        return self.config['price_tier']
    
    @property
    def timeout(self) -> int:
        return self.config['timeout']
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"Site({self.name})"


class ProcurementStrategy(ABC):
    """
    Abstract base class for procurement strategies.
    
    Determines which sites to try, in what order, and fallback behavior.
    
    Subclasses must implement:
    - get_site_order() - Returns list of sites to try
    - should_attempt_next_site() - Whether to continue after failure
    - get_timeout_per_site() - Timeout for each site
    """
    
    def __init__(self, timeout_per_site: int = 30):
        """
        Initialize procurement strategy.
        
        Args:
            timeout_per_site: Default timeout for site attempts (seconds)
        """
        self.timeout_per_site = timeout_per_site
        self.attempted_sites: List[str] = []
        self.failed_sites: List[str] = []
        self.successful_site: Optional[str] = None
        
        logger.info(f"Strategy initialized: {self.__class__.__name__}")
    
    @abstractmethod
    def get_site_order(self) -> List[str]:
        """
        Get the order of sites to attempt.
        
        Returns:
            List of site names in order to try
        
        Example:
            return ['nike', 'footlocker', 'adidas']
        """
        pass
    
    @abstractmethod
    def should_attempt_next_site(self, last_result: dict) -> bool:
        """
        Determine if we should attempt the next site after a failure.
        
        Args:
            last_result: Result dict from previous site attempt with keys:
                - 'success': bool
                - 'site': str
                - 'error': str (if failed)
                - 'reason': str
        
        Returns:
            True if we should continue, False if we should abort
        
        Example:
            # Stop on any failure
            def should_attempt_next_site(self, last_result):
                return not last_result['success']
        """
        pass
    
    def get_timeout_per_site(self, site: str) -> int:
        """
        Get timeout for a specific site.
        
        Args:
            site: Site name
        
        Returns:
            Timeout in seconds
        """
        try:
            site_obj = Site(site)
            return site_obj.timeout
        except ValueError:
            return self.timeout_per_site
    
    def mark_attempted(self, site: str) -> None:
        """Mark a site as attempted"""
        if site not in self.attempted_sites:
            self.attempted_sites.append(site)
    
    def mark_failed(self, site: str) -> None:
        """Mark a site as failed"""
        if site not in self.failed_sites:
            self.failed_sites.append(site)
    
    def mark_successful(self, site: str) -> None:
        """Mark a site as successful"""
        self.successful_site = site
    
    def get_remaining_sites(self) -> List[str]:
        """Get sites that haven't been attempted yet"""
        all_sites = self.get_site_order()
        return [s for s in all_sites if s not in self.attempted_sites]
    
    def get_stats(self) -> dict:
        """Get strategy execution statistics"""
        return {
            'strategy': self.__class__.__name__,
            'attempted': self.attempted_sites,
            'failed': self.failed_sites,
            'successful': self.successful_site,
            'remaining': self.get_remaining_sites(),
        }
    
    def __str__(self):
        return f"{self.__class__.__name__}(timeout={self.timeout_per_site}s)"