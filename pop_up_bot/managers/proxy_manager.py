# pop_up_bot/managers/proxy_manager.py
"""
ProxyManager
├── Load proxies from config/database
├── Rotate through them round-robin
├── Track proxy health (detect dead proxies)
├── Apply proxy to Playwright context
└── Remove dead proxies automatically
"""

import logging
import random
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProxyProtocol(str, Enum):
    """Supported proxy protocols"""
    HTTP = 'http'
    HTTPS = 'https'
    SOCKS5 = 'socks5'


@dataclass
class Proxy:
    """
    Represents a single proxy.
    
    Supports formats:
    - http://proxy.com:8080
    - http://user:pass@proxy.com:8080
    - socks5://proxy.com:1080
    """
    
    host: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    is_alive: bool = True
    fail_count: int = 0
    
    @property
    def url(self) -> str:
        """Get full proxy URL"""
        if self.username and self.password:
            return f"{self.protocol.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol.value}://{self.host}:{self.port}"
    
    @property
    def server(self) -> str:
        """Get server address for Playwright (without credentials)"""
        return f"{self.protocol.value}://{self.host}:{self.port}"
    
    @classmethod
    def from_string(cls, proxy_string: str) -> 'Proxy':
        """
        Parse proxy from string format.
        
        Formats supported:
        - http://proxy.com:8080
        - http://user:pass@proxy.com:8080
        - socks5://proxy.com:1080
        
        Example:
            proxy = Proxy.from_string('http://user:pass@proxy.com:8080')
        """
        try:
            # Parse protocol
            if '://' not in proxy_string:
                raise ValueError(f"Invalid proxy format: {proxy_string}")
            
            protocol_str, rest = proxy_string.split('://', 1)
            protocol = ProxyProtocol(protocol_str)
            
            # Parse credentials if present
            username = None
            password = None
            
            if '@' in rest:
                creds, rest = rest.rsplit('@', 1)
                if ':' in creds:
                    username, password = creds.split(':', 1)
                else:
                    username = creds
            
            # Parse host and port
            if ':' in rest:
                host, port_str = rest.rsplit(':', 1)
                port = int(port_str)
            else:
                raise ValueError(f"Invalid proxy format - missing port: {proxy_string}")
            
            return cls(
                host=host,
                port=port,
                protocol=protocol,
                username=username,
                password=password,
            )
        
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse proxy {proxy_string}: {e}")
            raise
    
    def __str__(self):
        status = "✓" if self.is_alive else "✗"
        return f"{status} {self.server} (fails: {self.fail_count})"


class ProxyManager:
    """
    Manages proxy rotation for bot executions.
    
    Features:
    - Round-robin proxy rotation
    - Proxy health tracking
    - Automatic dead proxy removal
    - Multiple proxy sources (config, env, database)
    - Per-user/execution proxy assignment
    
    Usage:
        proxy_manager = ProxyManager([
            'http://proxy1.com:8080',
            'http://user:pass@proxy2.com:8080',
            'socks5://proxy3.com:1080',
        ])
        
        # Get next proxy
        proxy = proxy_manager.get_next_proxy()
        
        # Use with Playwright
        context = await browser.new_context(
            proxy={
                'server': proxy.server,
                'username': proxy.username,
                'password': proxy.password,
            }
        )
        
        # Mark proxy as failed
        proxy_manager.mark_proxy_failed(proxy)
    """
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        max_failures: int = 3,
        strategy: str = 'round_robin'
    ):
        """
        Initialize ProxyManager.
        
        Args:
            proxies: List of proxy strings to use
            max_failures: Remove proxy after this many failures
            strategy: 'round_robin' or 'random'
        """
        self.max_failures = max_failures
        self.strategy = strategy
        self.current_index = 0
        self.proxy_list: List[Proxy] = []
        
        if proxies:
            for proxy_string in proxies:
                try:
                    proxy = Proxy.from_string(proxy_string)
                    self.proxy_list.append(proxy)
                except ValueError as e:
                    logger.warning(f"Skipping invalid proxy: {e}")
        
        logger.info(f"ProxyManager initialized with {len(self.proxy_list)} proxies (strategy: {strategy})")
    
    def add_proxy(self, proxy_string: str) -> bool:
        """
        Add a proxy to the pool.
        
        Args:
            proxy_string: Proxy URL string
        
        Returns:
            True if added successfully, False otherwise
        
        Example:
            success = proxy_manager.add_proxy('http://proxy.com:8080')
        """
        try:
            proxy = Proxy.from_string(proxy_string)
            self.proxy_list.append(proxy)
            logger.info(f"Added proxy: {proxy}")
            return True
        except ValueError as e:
            logger.error(f"Failed to add proxy: {e}")
            return False
    
    def get_next_proxy(self) -> Optional[Proxy]:
        """
        Get the next proxy to use.
        
        Uses round-robin or random strategy based on configuration.
        Only returns alive proxies.
        
        Returns:
            Proxy object or None if no proxies available
        
        Example:
            proxy = proxy_manager.get_next_proxy()
            if proxy:
                print(f"Using proxy: {proxy.url}")
        """
        if not self.proxy_list:
            logger.warning("No proxies available")
            return None
        
        # Get alive proxies only
        alive_proxies = [p for p in self.proxy_list if p.is_alive]
        
        if not alive_proxies:
            logger.warning("No alive proxies available")
            return None
        
        # Select proxy based on strategy
        if self.strategy == 'random':
            proxy = random.choice(alive_proxies)
        else:  # round_robin
            proxy = alive_proxies[self.current_index % len(alive_proxies)]
            self.current_index += 1
        
        logger.debug(f"Selected proxy: {proxy}")
        return proxy
    
    def mark_proxy_failed(self, proxy: Proxy) -> None:
        """
        Mark a proxy as failed.
        
        Removes proxy if it exceeds max_failures threshold.
        
        Args:
            proxy: Proxy object that failed
        
        Example:
            try:
                await page.goto(url, proxy=proxy.server)
            except Exception as e:
                proxy_manager.mark_proxy_failed(proxy)
        """
        proxy.fail_count += 1
        logger.warning(f"Proxy failed: {proxy} (failures: {proxy.fail_count}/{self.max_failures})")
        
        if proxy.fail_count >= self.max_failures:
            self.remove_proxy(proxy)
    
    def mark_proxy_success(self, proxy: Proxy) -> None:
        """
        Mark a proxy as successful.
        
        Resets failure count on successful use.
        
        Args:
            proxy: Proxy object that succeeded
        """
        if proxy.fail_count > 0:
            proxy.fail_count = 0
            logger.debug(f"Proxy success, failure count reset: {proxy}")
    
    def remove_proxy(self, proxy: Proxy) -> bool:
        """
        Remove a proxy from the pool.
        
        Args:
            proxy: Proxy object to remove
        
        Returns:
            True if removed, False if not found
        """
        try:
            self.proxy_list.remove(proxy)
            logger.info(f"Removed proxy: {proxy}")
            return True
        except ValueError:
            logger.warning(f"Proxy not found in pool: {proxy}")
            return False
    
    def get_alive_count(self) -> int:
        """Get count of alive proxies"""
        return sum(1 for p in self.proxy_list if p.is_alive)
    
    def get_total_count(self) -> int:
        """Get total proxy count"""
        return len(self.proxy_list)
    
    def get_proxy_stats(self) -> Dict:
        """
        Get statistics about proxy pool.
        
        Returns:
            Dictionary with proxy statistics
        
        Example:
            stats = proxy_manager.get_proxy_stats()
            print(f"Alive: {stats['alive']}, Dead: {stats['dead']}")
        """
        return {
            'total': self.get_total_count(),
            'alive': self.get_alive_count(),
            'dead': self.get_total_count() - self.get_alive_count(),
            'strategy': self.strategy,
            'details': [
                {
                    'proxy': p.server,
                    'alive': p.is_alive,
                    'failures': p.fail_count,
                }
                for p in self.proxy_list
            ]
        }
    
    def reset_all(self) -> None:
        """Reset all proxies to alive state"""
        for proxy in self.proxy_list:
            proxy.is_alive = True
            proxy.fail_count = 0
        logger.info("All proxies reset to alive state")
    
    def __str__(self):
        alive = self.get_alive_count()
        total = self.get_total_count()
        return f"ProxyManager({alive}/{total} alive, strategy={self.strategy})"
    
    def __repr__(self):
        return self.__str__()