# pop_up_bot/services/anti_detection.py

"""
Anti-Detection Service

Coordinates all bot detection evasion features:
- Random delays
- User agent rotation
- Proxy rotation
- Rate limiting
- Browser fingerprinting
- Smart retries
"""

import logging
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class BrowserType(Enum):
    """Browser types to rotate through"""
    CHROME_DESKTOP = "chrome_desktop"
    CHROME_MOBILE = "chrome_mobile"
    FIREFOX_DESKTOP = "firefox_desktop"
    FIREFOX_MOBILE = "firefox_mobile"
    SAFARI_DESKTOP = "safari_desktop"
    SAFARI_MOBILE = "safari_mobile"
    EDGE_DESKTOP = "edge_desktop"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 12  # 1 request every 5 seconds max
    requests_per_hour: int = 360   # Max 360 per hour
    requests_per_day: int = 5000   # Max 5000 per day
    burst_size: int = 3            # Allow brief bursts


@dataclass
class RetryConfig:
    """Retry configuration with exponential backoff"""
    max_retries: int = 5
    initial_delay: float = 1.0      # 1 second
    max_delay: float = 60.0         # Max 60 seconds
    exponential_base: float = 2.0   # Double each time
    jitter: bool = True             # Add randomness


@dataclass
class AntiDetectionConfig:
    """Master anti-detection configuration"""
    # Delays
    min_delay: float = 0.5          # Min 500ms between actions
    max_delay: float = 5.0          # Max 5 seconds between actions
    use_delays: bool = True
    
    # User agents
    rotate_user_agents: bool = True
    browser_types: List[BrowserType] = None
    
    # Proxies
    use_proxies: bool = False
    rotate_proxies: bool = True
    proxy_list: List[str] = None
    
    # Rate limiting
    rate_limit: RateLimitConfig = None
    enforce_rate_limits: bool = True
    
    # Retries
    retry_config: RetryConfig = None
    
    # Logging
    verbose_logging: bool = True
    
    def __post_init__(self):
        """Set defaults for nested configs"""
        if self.browser_types is None:
            self.browser_types = [
                BrowserType.CHROME_DESKTOP,
                BrowserType.CHROME_MOBILE,
                BrowserType.FIREFOX_DESKTOP,
                BrowserType.SAFARI_DESKTOP,
            ]
        
        if self.rate_limit is None:
            self.rate_limit = RateLimitConfig()
        
        if self.retry_config is None:
            self.retry_config = RetryConfig()
        
        if self.proxy_list is None:
            self.proxy_list = []


class DelayService:
    """Handles random delays to appear human-like"""
    
    def __init__(self, min_delay: float = 0.5, max_delay: float = 5.0):
        """
        Initialize delay service
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
    
    def get_random_delay(self) -> float:
        """
        Get a random delay with realistic distribution.
        
        Uses a weighted distribution favoring shorter delays
        but occasionally including longer pauses (like humans).
        
        Returns:
            Delay in seconds
        """
        delay_range = self.max_delay - self.min_delay
        
        # 70% of time: short delays (min to min+20% of range)
        if random.random() < 0.7:
            return random.uniform(self.min_delay, self.min_delay + delay_range * 0.2)
        
        # 20% of time: medium delays (min+20% to min+60% of range)
        elif random.random() < 0.9:
            return random.uniform(self.min_delay + delay_range * 0.2, self.min_delay + delay_range * 0.6)
        
        # 10% of time: longer delays (min+60% to max)
        else:
            return random.uniform(self.min_delay + delay_range * 0.6, self.max_delay)
    
    def wait(self):
        """Apply random delay"""
        delay = self.get_random_delay()
        logger.debug(f"Applying delay: {delay:.2f}s")
        time.sleep(delay)
    
    def wait_for_typing(self, text: str):
        """Simulate human typing speed (30-100 WPM)"""
        # Average typing speed: ~60 WPM = 5 chars per second
        words = len(text.split())
        # 100-200ms per word
        delay = (words / 60.0) * 60 + random.uniform(0, 0.5)
        logger.debug(f"Simulating typing {len(text)} chars: {delay:.2f}s")
        time.sleep(delay)


class UserAgentRotator:
    """Rotates user agents to avoid detection"""
    
    USER_AGENTS = {
        BrowserType.CHROME_DESKTOP: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        BrowserType.CHROME_MOBILE: [
            "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        ],
        BrowserType.FIREFOX_DESKTOP: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        ],
        BrowserType.FIREFOX_MOBILE: [
            "Mozilla/5.0 (Android; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
        ],
        BrowserType.SAFARI_DESKTOP: [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ],
        BrowserType.SAFARI_MOBILE: [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        ],
        BrowserType.EDGE_DESKTOP: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ],
    }
    
    def __init__(self, browser_types: List[BrowserType] = None):
        """
        Initialize user agent rotator
        
        Args:
            browser_types: List of browsers to rotate through
        """
        self.browser_types = browser_types or list(self.USER_AGENTS.keys())
        self.current_browser = None
        self.current_user_agent = None
    
    def get_random_user_agent(self) -> Tuple[str, BrowserType]:
        """
        Get a random user agent
        
        Returns:
            Tuple of (user_agent_string, browser_type)
        """
        browser = random.choice(self.browser_types)
        user_agent = random.choice(self.USER_AGENTS[browser])
        
        self.current_browser = browser
        self.current_user_agent = user_agent
        
        logger.debug(f"Selected user agent: {browser.value}")
        
        return user_agent, browser
    
    def get_browser_headers(self) -> Dict[str, str]:
        """
        Get headers that match current browser
        
        Returns:
            Dictionary of headers
        """
        if not self.current_user_agent:
            self.get_random_user_agent()
        
        headers = {
            "User-Agent": self.current_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        
        # Mobile-specific headers
        if "Mobile" in self.current_user_agent or "Android" in self.current_user_agent:
            headers["Sec-CH-UA-Mobile"] = "?1"
        else:
            headers["Sec-CH-UA-Mobile"] = "?0"
        
        return headers


class RateLimiter:
    """Enforces rate limits to avoid overwhelming servers"""
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Initialize rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self.request_times: Dict[str, List[datetime]] = {}  # site -> list of request times
        self.last_request_time: Dict[str, datetime] = {}
    
    def can_make_request(self, site: str) -> Tuple[bool, Optional[float]]:
        """
        Check if request can be made to site
        
        Args:
            site: Site identifier (e.g., 'nike')
        
        Returns:
            Tuple of (can_request, wait_seconds_if_not)
        """
        now = datetime.now()
        
        if site not in self.request_times:
            self.request_times[site] = []
            return True, None
        
        # Clean old requests (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.request_times[site] = [
            t for t in self.request_times[site] if t > cutoff
        ]
        
        # Check per-minute limit
        last_minute = now - timedelta(minutes=1)
        requests_this_minute = len([
            t for t in self.request_times[site] if t > last_minute
        ])
        
        if requests_this_minute >= self.config.requests_per_minute:
            wait_time = 60.0 / self.config.requests_per_minute
            logger.warning(f"Rate limit (per-minute) hit for {site}. Waiting {wait_time:.1f}s")
            return False, wait_time
        
        # Check per-hour limit
        requests_this_hour = len([
            t for t in self.request_times[site] if t > cutoff
        ])
        
        if requests_this_hour >= self.config.requests_per_hour:
            wait_time = 300.0  # Wait 5 minutes
            logger.warning(f"Rate limit (per-hour) hit for {site}. Waiting {wait_time:.1f}s")
            return False, wait_time
        
        return True, None
    
    def record_request(self, site: str):
        """Record that a request was made"""
        if site not in self.request_times:
            self.request_times[site] = []
        
        self.request_times[site].append(datetime.now())
        self.last_request_time[site] = datetime.now()
        
        logger.debug(f"Recorded request for {site}")
    
    def get_stats(self, site: str) -> Dict:
        """Get rate limiting stats for a site"""
        if site not in self.request_times:
            return {"requests_total": 0}
        
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        requests_hour = len([t for t in self.request_times[site] if t > last_hour])
        requests_day = len([t for t in self.request_times[site] if t > last_day])
        
        return {
            "requests_total": len(self.request_times[site]),
            "requests_last_hour": requests_hour,
            "requests_last_day": requests_day,
            "limit_per_hour": self.config.requests_per_hour,
            "limit_per_day": self.config.requests_per_day,
        }


class RetryHandler:
    """Handles exponential backoff retries"""
    
    def __init__(self, config: RetryConfig = None):
        """
        Initialize retry handler
        
        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()
    
    def get_backoff_delay(self, retry_count: int) -> float:
        """
        Calculate exponential backoff delay with jitter
        
        Args:
            retry_count: Number of retries so far (0-indexed)
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff: initial_delay * (base ^ retry_count)
        delay = self.config.initial_delay * (
            self.config.exponential_base ** retry_count
        )
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter (±10%)
        if self.config.jitter:
            jitter = delay * 0.1 * random.uniform(-1, 1)
            delay += jitter
        
        return max(0, delay)  # Ensure non-negative
    
    def wait_before_retry(self, retry_count: int):
        """
        Wait with exponential backoff before retry
        
        Args:
            retry_count: Number of retries so far (0-indexed)
        """
        delay = self.get_backoff_delay(retry_count)
        logger.warning(f"Retry {retry_count + 1}/{self.config.max_retries}. Waiting {delay:.2f}s")
        time.sleep(delay)


class AntiDetectionService:
    """
    Master anti-detection service
    
    Coordinates all detection evasion features.
    """
    
    def __init__(self, config: AntiDetectionConfig = None):
        """
        Initialize anti-detection service
        
        Args:
            config: Anti-detection configuration
        """
        self.config = config or AntiDetectionConfig()
        
        # Initialize sub-services
        self.delay_service = DelayService(
            self.config.min_delay,
            self.config.max_delay
        )
        
        self.user_agent_rotator = UserAgentRotator(
            self.config.browser_types
        )
        
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        
        self.retry_handler = RetryHandler(self.config.retry_config)
        
        logger.info("Anti-detection service initialized")
        if self.config.verbose_logging:
            logger.info(f"Config: delays={self.config.use_delays}, "
                       f"user_agents={self.config.rotate_user_agents}, "
                       f"rate_limiting={self.config.enforce_rate_limits}")
    
    # =====================================================================
    # DELAY OPERATIONS
    # =====================================================================
    
    def apply_action_delay(self):
        """Apply delay between actions"""
        if self.config.use_delays:
            self.delay_service.wait()
    
    def apply_typing_delay(self, text: str):
        """Apply human-like typing speed"""
        if self.config.use_delays:
            self.delay_service.wait_for_typing(text)
    
    # =====================================================================
    # USER AGENT OPERATIONS
    # =====================================================================
    
    def get_headers(self) -> Dict[str, str]:
        """Get browser headers for next request"""
        if self.config.rotate_user_agents:
            self.user_agent_rotator.get_random_user_agent()
        
        return self.user_agent_rotator.get_browser_headers()
    
    def get_user_agent(self) -> str:
        """Get user agent string"""
        if self.config.rotate_user_agents:
            ua, _ = self.user_agent_rotator.get_random_user_agent()
            return ua
        
        if not self.user_agent_rotator.current_user_agent:
            ua, _ = self.user_agent_rotator.get_random_user_agent()
            return ua
        
        return self.user_agent_rotator.current_user_agent
    
    # =====================================================================
    # RATE LIMITING
    # =====================================================================
    
    def check_rate_limit(self, site: str) -> bool:
        """
        Check if we can make a request to site
        
        Args:
            site: Site identifier
        
        Returns:
            True if ok, False if rate limited
        """
        if not self.config.enforce_rate_limits:
            return True
        
        can_request, wait_time = self.rate_limiter.can_make_request(site)
        
        if not can_request and wait_time:
            logger.warning(f"Rate limit for {site}. Waiting {wait_time:.1f}s")
            time.sleep(wait_time)
            return self.check_rate_limit(site)  # Check again
        
        return True
    
    def record_request(self, site: str):
        """Record a request was made"""
        self.rate_limiter.record_request(site)
    
    def get_rate_limit_stats(self, site: str) -> Dict:
        """Get rate limiting stats"""
        return self.rate_limiter.get_stats(site)
    
    # =====================================================================
    # RETRY OPERATIONS
    # =====================================================================
    
    def get_retry_delay(self, retry_count: int) -> float:
        """Get delay before next retry"""
        return self.retry_handler.get_backoff_delay(retry_count)
    
    def wait_before_retry(self, retry_count: int):
        """Wait before retrying"""
        self.retry_handler.wait_before_retry(retry_count)
    
    def should_retry(self, retry_count: int) -> bool:
        """Check if we should retry"""
        return retry_count < self.retry_handler.config.max_retries
    
    # =====================================================================
    # SUMMARY
    # =====================================================================
    
    def get_summary(self) -> Dict:
        """Get summary of anti-detection configuration"""
        return {
            "delays_enabled": self.config.use_delays,
            "delay_range": f"{self.config.min_delay}-{self.config.max_delay}s",
            "user_agent_rotation": self.config.rotate_user_agents,
            "rate_limiting": self.config.enforce_rate_limits,
            "rate_limit_per_minute": self.config.rate_limit.requests_per_minute,
            "max_retries": self.retry_handler.config.max_retries,
            "current_browser": (
                self.user_agent_rotator.current_browser.value
                if self.user_agent_rotator.current_browser
                else "not_set"
            ),
        }