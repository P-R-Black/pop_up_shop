# pop_up_bot/tests/test_anti_detection.py

"""
Tests for Anti-Detection Service

Tests all anti-detection features:
- Delays
- User agent rotation
- Rate limiting
- Retry logic
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
import time
import random

from pop_up_bot.services.anti_detection import (
    AntiDetectionService,
    AntiDetectionConfig,
    DelayService,
    UserAgentRotator,
    RateLimiter,
    RetryHandler,
    BrowserType,
    RateLimitConfig,
    RetryConfig,
)


# ============================================================================
# DELAY SERVICE TESTS
# ============================================================================

class TestDelayService(TestCase):
    """Test delay service"""
    
    def setUp(self):
        """Set up test"""
        self.delay_service = DelayService(min_delay=0.1, max_delay=0.5)
    
    def test_initialization(self):
        """Test delay service initialization"""
        self.assertEqual(self.delay_service.min_delay, 0.1)
        self.assertEqual(self.delay_service.max_delay, 0.5)
    
    def test_get_random_delay_in_range(self):
        """Test random delay is within bounds"""
        for _ in range(10):
            delay = self.delay_service.get_random_delay()
            self.assertGreaterEqual(delay, self.delay_service.min_delay)
            self.assertLessEqual(delay, self.delay_service.max_delay)
    
    def test_get_random_delay_distribution(self):
        """Test delay distribution (weighted toward shorter)"""
        delays = [self.delay_service.get_random_delay() for _ in range(100)]
        
        # Most delays should be in lower range
        short_delays = [d for d in delays if d < 0.3]
        self.assertGreater(len(short_delays), 50)  # At least 50%
    
    @patch('time.sleep')
    def test_wait_applies_delay(self, mock_sleep):
        """Test wait method applies delay"""
        self.delay_service.wait()
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        self.assertGreaterEqual(delay, 0.1)
        self.assertLessEqual(delay, 0.5)
    
    @patch('time.sleep')
    def test_wait_for_typing(self, mock_sleep):
        """Test typing delay calculation"""
        text = "This is a test"  # 4 words
        self.delay_service.wait_for_typing(text)
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        self.assertGreater(delay, 0)


# ============================================================================
# USER AGENT ROTATOR TESTS
# ============================================================================

class TestUserAgentRotator(TestCase):
    """Test user agent rotation"""
    
    def setUp(self):
        """Set up test"""
        self.rotator = UserAgentRotator()
    
    def test_initialization(self):
        """Test rotator initialization"""
        self.assertIsNotNone(self.rotator.browser_types)
        self.assertGreater(len(self.rotator.browser_types), 0)
    
    def test_get_random_user_agent(self):
        """Test getting random user agent"""
        ua, browser = self.rotator.get_random_user_agent()
        
        self.assertIsNotNone(ua)
        self.assertIsNotNone(browser)
        self.assertIsInstance(ua, str)
        self.assertIsInstance(browser, BrowserType)
        self.assertGreater(len(ua), 0)
    
    def test_user_agent_from_valid_browser(self):
        """Test user agent comes from valid browser list"""
        for _ in range(10):
            ua, browser = self.rotator.get_random_user_agent()
            self.assertIn(browser, self.rotator.USER_AGENTS)
    
    def test_all_browser_types_have_agents(self):
        """Test all browser types have user agents"""
        for browser in BrowserType:
            self.assertIn(browser, self.rotator.USER_AGENTS)
            self.assertGreater(len(self.rotator.USER_AGENTS[browser]), 0)
    
    def test_browser_type_filtering(self):
        """Test filtering to specific browser types"""
        browsers = [BrowserType.CHROME_DESKTOP, BrowserType.FIREFOX_DESKTOP]
        rotator = UserAgentRotator(browser_types=browsers)
        
        for _ in range(10):
            _, browser = rotator.get_random_user_agent()
            self.assertIn(browser, browsers)
    
    def test_get_browser_headers(self):
        """Test getting browser headers"""
        headers = self.rotator.get_browser_headers()
        
        # Check required headers
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
        self.assertIn('Accept-Language', headers)
        self.assertIn('Connection', headers)
    
    def test_headers_include_user_agent(self):
        """Test headers include the current user agent"""
        ua, _ = self.rotator.get_random_user_agent()
        headers = self.rotator.get_browser_headers()
        self.assertEqual(headers['User-Agent'], ua)
    
    def test_mobile_headers(self):
        """Test mobile-specific headers"""
        # Get mobile user agent
        self.rotator.browser_types = [BrowserType.CHROME_MOBILE]
        self.rotator.get_random_user_agent()
        
        headers = self.rotator.get_browser_headers()
        self.assertEqual(headers['Sec-CH-UA-Mobile'], "?1")
    
    def test_desktop_headers(self):
        """Test desktop-specific headers"""
        # Get desktop user agent
        self.rotator.browser_types = [BrowserType.CHROME_DESKTOP]
        self.rotator.get_random_user_agent()
        
        headers = self.rotator.get_browser_headers()
        self.assertEqual(headers['Sec-CH-UA-Mobile'], "?0")


# ============================================================================
# RATE LIMITER TESTS
# ============================================================================

class TestRateLimiter(TestCase):
    """Test rate limiting"""
    
    def setUp(self):
        """Set up test"""
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=60,
        )
        self.limiter = RateLimiter(config)
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        self.assertEqual(self.limiter.config.requests_per_minute, 5)
        self.assertEqual(self.limiter.config.requests_per_hour, 60)
    
    def test_first_request_allowed(self):
        """Test first request is allowed"""
        can_request, wait = self.limiter.can_make_request("nike")
        self.assertTrue(can_request)
        self.assertIsNone(wait)
    
    def test_multiple_requests_allowed(self):
        """Test multiple requests allowed"""
        for i in range(5):
            can_request, wait = self.limiter.can_make_request("nike")
            self.assertTrue(can_request)
            self.limiter.record_request("nike")
    
    def test_rate_limit_per_minute_enforced(self):
        """Test per-minute rate limit is enforced"""
        # Max 5 requests per minute
        for i in range(5):
            can_request, wait = self.limiter.can_make_request("nike")
            self.assertTrue(can_request)
            self.limiter.record_request("nike")
        
        # 6th request should be denied
        can_request, wait = self.limiter.can_make_request("nike")
        self.assertFalse(can_request)
        self.assertIsNotNone(wait)
    
    def test_record_request(self):
        """Test recording requests"""
        self.limiter.record_request("nike")
        self.limiter.record_request("nike")
        
        self.assertEqual(len(self.limiter.request_times["nike"]), 2)
    
    def test_separate_site_limits(self):
        """Test rate limits are per-site"""
        # Record requests to nike
        for i in range(5):
            self.limiter.record_request("nike")
        
        # nike should be rate limited
        can_nike, _ = self.limiter.can_make_request("nike")
        self.assertFalse(can_nike)
        
        # But footlocker should be fine
        can_footlocker, _ = self.limiter.can_make_request("footlocker")
        self.assertTrue(can_footlocker)
    
    def test_get_stats(self):
        """Test getting rate limit stats"""
        for i in range(3):
            self.limiter.record_request("nike")
        
        stats = self.limiter.get_stats("nike")
        
        self.assertEqual(stats["requests_total"], 3)
        self.assertEqual(stats["requests_last_hour"], 3)
        self.assertEqual(stats["limit_per_hour"], 60)


# ============================================================================
# RETRY HANDLER TESTS
# ============================================================================

class TestRetryHandler(TestCase):
    """Test retry logic"""
    
    def setUp(self):
        """Set up test"""
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.1,
            max_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        self.handler = RetryHandler(config)
    
    def test_initialization(self):
        """Test retry handler initialization"""
        self.assertEqual(self.handler.config.max_retries, 5)
        self.assertEqual(self.handler.config.initial_delay, 0.1)
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff formula"""
        # Retry 0: 0.1 * 2^0 = 0.1
        # Retry 1: 0.1 * 2^1 = 0.2
        # Retry 2: 0.1 * 2^2 = 0.4
        # Retry 3: 0.1 * 2^3 = 0.8
        # Retry 4: 0.1 * 2^4 = 1.6 (capped at 1.0)
        
        self.assertAlmostEqual(self.handler.get_backoff_delay(0), 0.1, places=2)
        self.assertAlmostEqual(self.handler.get_backoff_delay(1), 0.2, places=2)
        self.assertAlmostEqual(self.handler.get_backoff_delay(2), 0.4, places=2)
        self.assertAlmostEqual(self.handler.get_backoff_delay(3), 0.8, places=2)
        self.assertEqual(self.handler.get_backoff_delay(4), 1.0)  # Capped
    
    def test_max_delay_enforced(self):
        """Test max delay is enforced"""
        delay = self.handler.get_backoff_delay(10)
        self.assertLessEqual(delay, 1.0)
    
    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness"""
        handler = RetryHandler(RetryConfig(jitter=True, initial_delay=1.0))
        
        delays = [handler.get_backoff_delay(0) for _ in range(10)]
        unique_delays = len(set(delays))
        
        # With jitter, we should get different values
        self.assertGreater(unique_delays, 1)
    
    @patch('time.sleep')
    def test_wait_before_retry(self, mock_sleep):
        """Test wait before retry"""
        self.handler.wait_before_retry(0)
        mock_sleep.assert_called_once()


# ============================================================================
# ANTI-DETECTION SERVICE TESTS
# ============================================================================

class TestAntiDetectionService(TestCase):
    """Test master anti-detection service"""
    
    def setUp(self):
        """Set up test"""
        self.config = AntiDetectionConfig(
            use_delays=True,
            min_delay=0.1,
            max_delay=0.3,
            rotate_user_agents=True,
        )
        self.service = AntiDetectionService(self.config)
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service.delay_service)
        self.assertIsNotNone(self.service.user_agent_rotator)
        self.assertIsNotNone(self.service.rate_limiter)
        self.assertIsNotNone(self.service.retry_handler)
    
    @patch('time.sleep')
    def test_apply_action_delay(self, mock_sleep):
        """Test applying action delay"""
        self.service.apply_action_delay()
        mock_sleep.assert_called_once()
    
    def test_apply_action_delay_disabled(self):
        """Test delays can be disabled"""
        config = AntiDetectionConfig(use_delays=False)
        service = AntiDetectionService(config)
        
        with patch('time.sleep') as mock_sleep:
            service.apply_action_delay()
            mock_sleep.assert_not_called()
    
    def test_get_headers(self):
        """Test getting headers"""
        headers = self.service.get_headers()
        
        self.assertIsInstance(headers, dict)
        self.assertIn('User-Agent', headers)
    
    def test_get_user_agent(self):
        """Test getting user agent"""
        ua = self.service.get_user_agent()
        
        self.assertIsNotNone(ua)
        self.assertIsInstance(ua, str)
        self.assertGreater(len(ua), 0)
    

    def test_check_rate_limit_allowed(self):
        """Test when request is allowed"""
        result = self.service.check_rate_limit("nike")
        self.assertTrue(result)

    # def test_check_rate_limit_denied(self):
    #     """Test when request is denied"""
    #     # Mock rate limiter to return: (can_request=False, wait_time=10.0)
    #     with patch.object(self.service.rate_limiter, 'can_make_request') as mock_check:
    #         mock_check.return_value = (False, 10.0)
            
    #         result = self.service.check_rate_limit("nike")
    #         self.assertFalse(result)  # ✅ Should return False

    def test_check_rate_limit_disabled(self):
        """Test when rate limiting is disabled"""
        config = AntiDetectionConfig(enforce_rate_limits=False)
        service = AntiDetectionService(config)
        
        # Even if rate limiter says no, enforcement disabled = always True
        with patch.object(service.rate_limiter, 'can_make_request') as mock_check:
            mock_check.return_value = (False, 10.0)
            
            result = service.check_rate_limit("nike")
            self.assertTrue(result)  # ✅ Should return True
        
    def test_record_request(self):
        """Test recording requests"""
        self.service.record_request("nike")
        stats = self.service.get_rate_limit_stats("nike")
        
        self.assertEqual(stats["requests_total"], 1)
    
    def test_get_rate_limit_stats(self):
        """Test getting rate limit stats"""
        self.service.record_request("nike")
        self.service.record_request("nike")
        
        stats = self.service.get_rate_limit_stats("nike")
        
        self.assertEqual(stats["requests_total"], 2)
        self.assertIn("requests_last_hour", stats)
        self.assertIn("limit_per_hour", stats)
    
    def test_should_retry(self):
        """Test should retry logic"""
        self.assertTrue(self.service.should_retry(0))
        self.assertTrue(self.service.should_retry(4))
        self.assertFalse(self.service.should_retry(5))  # Max is 5
    
    def test_get_retry_delay(self):
        """Test getting retry delay"""
        delay = self.service.get_retry_delay(0)
        self.assertGreater(delay, 0)
    
    @patch('time.sleep')
    def test_wait_before_retry(self, mock_sleep):
        """Test waiting before retry"""
        self.service.wait_before_retry(0)
        mock_sleep.assert_called_once()
    
    def test_get_summary(self):
        """Test getting summary"""
        summary = self.service.get_summary()
        
        self.assertEqual(summary["delays_enabled"], True)
        self.assertEqual(summary["user_agent_rotation"], True)
        self.assertIn("rate_limiting", summary)
        self.assertIn("max_retries", summary)


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestAntiDetectionConfig(TestCase):
    """Test configuration"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = AntiDetectionConfig()
        
        self.assertEqual(config.min_delay, 0.5)
        self.assertEqual(config.max_delay, 5.0)
        self.assertTrue(config.use_delays)
        self.assertTrue(config.rotate_user_agents)
        self.assertIsNotNone(config.rate_limit)
        self.assertIsNotNone(config.retry_config)
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = AntiDetectionConfig(
            min_delay=1.0,
            max_delay=2.0,
            use_delays=False,
        )
        
        self.assertEqual(config.min_delay, 1.0)
        self.assertEqual(config.max_delay, 2.0)
        self.assertFalse(config.use_delays)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAntiDetectionIntegration(TestCase):
    """Integration tests"""
    
    def test_full_anti_detection_workflow(self):
        """Test complete anti-detection workflow"""
        service = AntiDetectionService()
        
        # Get headers
        headers = service.get_headers()
        self.assertIn('User-Agent', headers)
        
        # Check rate limit
        can_request = service.check_rate_limit("nike")
        self.assertTrue(can_request)
        
        # Record request
        service.record_request("nike")
        
        # Get retry delay
        delay = service.get_retry_delay(0)
        self.assertGreater(delay, 0)
        
        # Get summary
        summary = service.get_summary()
        self.assertIn('delays_enabled', summary)
    
    def test_multiple_sites(self):
        """Test handling multiple sites"""
        service = AntiDetectionService()
        
        # Make requests to different sites
        service.record_request("nike")
        service.record_request("footlocker")
        service.record_request("adidas")
        
        # Each should have separate stats
        nike_stats = service.get_rate_limit_stats("nike")
        footlocker_stats = service.get_rate_limit_stats("footlocker")
        
        self.assertEqual(nike_stats["requests_total"], 1)
        self.assertEqual(footlocker_stats["requests_total"], 1)
    
    def test_disabled_features(self):
        """Test disabling individual features"""
        config = AntiDetectionConfig(
            use_delays=False,
            rotate_user_agents=False,
            enforce_rate_limits=False,
        )
        service = AntiDetectionService(config)
        
        with patch('time.sleep') as mock_sleep:
            service.apply_action_delay()
            mock_sleep.assert_not_called()