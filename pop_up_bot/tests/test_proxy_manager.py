# pop_up_bot/tests/test_proxy_manager.py

import pytest
from django.test import TestCase
from pop_up_bot.managers.proxy_manager import ProxyManager, Proxy, ProxyProtocol


class TestProxy(TestCase):
    """Test Proxy model"""
    
    def test_proxy_creation(self):
        """Test creating a proxy"""
        proxy = Proxy(
            host='proxy.com',
            port=8080,
            protocol=ProxyProtocol.HTTP,
        )
        
        assert proxy.host == 'proxy.com'
        assert proxy.port == 8080
        assert proxy.protocol == ProxyProtocol.HTTP
        assert proxy.is_alive is True
    
    def test_proxy_url_without_auth(self):
        """Test proxy URL without authentication"""
        proxy = Proxy(
            host='proxy.com',
            port=8080,
            protocol=ProxyProtocol.HTTP,
        )
        
        assert proxy.url == 'http://proxy.com:8080'
        assert proxy.server == 'http://proxy.com:8080'
    
    def test_proxy_url_with_auth(self):
        """Test proxy URL with authentication"""
        proxy = Proxy(
            host='proxy.com',
            port=8080,
            protocol=ProxyProtocol.HTTP,
            username='user',
            password='pass',
        )
        
        assert proxy.url == 'http://user:pass@proxy.com:8080'
        assert proxy.server == 'http://proxy.com:8080'
    
    def test_proxy_from_string_basic(self):
        """Test parsing basic proxy string"""
        proxy = Proxy.from_string('http://proxy.com:8080')
        
        assert proxy.host == 'proxy.com'
        assert proxy.port == 8080
        assert proxy.protocol == ProxyProtocol.HTTP
        assert proxy.username is None
        assert proxy.password is None
    
    def test_proxy_from_string_with_auth(self):
        """Test parsing proxy with auth"""
        proxy = Proxy.from_string('http://user:pass@proxy.com:8080')
        
        assert proxy.host == 'proxy.com'
        assert proxy.port == 8080
        assert proxy.username == 'user'
        assert proxy.password == 'pass'
    
    def test_proxy_from_string_socks5(self):
        """Test parsing SOCKS5 proxy"""
        proxy = Proxy.from_string('socks5://proxy.com:1080')
        
        assert proxy.protocol == ProxyProtocol.SOCKS5
        assert proxy.url == 'socks5://proxy.com:1080'
    
    def test_proxy_from_string_invalid(self):
        """Test parsing invalid proxy string"""
        with pytest.raises(ValueError):
            Proxy.from_string('invalid-proxy')
    
    def test_proxy_from_string_missing_port(self):
        """Test parsing proxy without port"""
        with pytest.raises(ValueError):
            Proxy.from_string('http://proxy.com')


class TestProxyManager(TestCase):
    """Test ProxyManager"""
    
    def test_initialization_empty(self):
        """Test initializing with no proxies"""
        manager = ProxyManager()
        
        assert manager.get_total_count() == 0
        assert manager.get_alive_count() == 0
    
    def test_initialization_with_proxies(self):
        """Test initializing with proxies"""
        proxies = [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
        ]
        
        manager = ProxyManager(proxies)
        
        assert manager.get_total_count() == 2
        assert manager.get_alive_count() == 2
    
    def test_add_proxy(self):
        """Test adding a proxy"""
        manager = ProxyManager()
        
        success = manager.add_proxy('http://proxy.com:8080')
        
        assert success is True
        assert manager.get_total_count() == 1
    
    def test_add_invalid_proxy(self):
        """Test adding invalid proxy"""
        manager = ProxyManager()
        
        success = manager.add_proxy('invalid')
        
        assert success is False
        assert manager.get_total_count() == 0
    
    def test_get_next_proxy_round_robin(self):
        """Test round-robin proxy selection"""
        proxies = [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
            'http://proxy3.com:8080',
        ]
        
        manager = ProxyManager(proxies, strategy='round_robin')
        
        # Should cycle through proxies
        proxy1 = manager.get_next_proxy()
        proxy2 = manager.get_next_proxy()
        proxy3 = manager.get_next_proxy()
        proxy1_again = manager.get_next_proxy()
        
        assert proxy1.server == 'http://proxy1.com:8080'
        assert proxy2.server == 'http://proxy2.com:8080'
        assert proxy3.server == 'http://proxy3.com:8080'
        assert proxy1_again.server == proxy1.server
    
    def test_get_next_proxy_empty(self):
        """Test getting proxy when none available"""
        manager = ProxyManager()
        
        proxy = manager.get_next_proxy()
        
        assert proxy is None
    
    def test_mark_proxy_failed(self):
        """Test marking proxy as failed"""
        proxies = ['http://proxy1.com:8080']
        manager = ProxyManager(proxies, max_failures=3)
        
        proxy = manager.proxy_list[0]
        
        # Mark as failed 3 times
        for i in range(3):
            manager.mark_proxy_failed(proxy)
            assert proxy.fail_count == i + 1
    
    def test_proxy_removal_on_max_failures(self):
        """Test proxy is removed after max failures"""
        proxies = ['http://proxy1.com:8080']
        manager = ProxyManager(proxies, max_failures=2)
        
        proxy = manager.proxy_list[0]
        
        manager.mark_proxy_failed(proxy)
        assert manager.get_total_count() == 1
        
        manager.mark_proxy_failed(proxy)
        assert manager.get_total_count() == 0
    
    def test_mark_proxy_success(self):
        """Test marking proxy as successful"""
        proxies = ['http://proxy1.com:8080']
        manager = ProxyManager(proxies)
        
        proxy = manager.proxy_list[0]
        proxy.fail_count = 5
        
        manager.mark_proxy_success(proxy)
        
        assert proxy.fail_count == 0
    
    def test_remove_proxy(self):
        """Test removing a proxy"""
        proxies = [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
        ]
        
        manager = ProxyManager(proxies)
        proxy_to_remove = manager.proxy_list[0]
        
        success = manager.remove_proxy(proxy_to_remove)
        
        assert success is True
        assert manager.get_total_count() == 1
    
    def test_remove_nonexistent_proxy(self):
        """Test removing proxy not in pool"""
        proxies = ['http://proxy1.com:8080']
        manager = ProxyManager(proxies)
        
        fake_proxy = Proxy(host='fake.com', port=8080)
        success = manager.remove_proxy(fake_proxy)
        
        assert success is False
    
    def test_get_proxy_stats(self):
        """Test getting proxy statistics"""
        proxies = [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
        ]
        
        manager = ProxyManager(proxies)
        
        stats = manager.get_proxy_stats()
        
        assert stats['total'] == 2
        assert stats['alive'] == 2
        assert stats['dead'] == 0
        assert stats['strategy'] == 'round_robin'
    
    def test_reset_all_proxies(self):
        """Test resetting all proxies"""
        proxies = ['http://proxy1.com:8080']
        manager = ProxyManager(proxies)
        
        proxy = manager.proxy_list[0]
        proxy.is_alive = False
        proxy.fail_count = 5
        
        manager.reset_all()
        
        assert proxy.is_alive is True
        assert proxy.fail_count == 0
    
    def test_skip_dead_proxies(self):
        """Test that dead proxies are skipped"""
        proxies = [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
        ]
        
        manager = ProxyManager(proxies)
        
        # Mark first proxy as dead
        proxy1 = manager.proxy_list[0]
        proxy1.is_alive = False
        
        # Next proxy should be the second one
        proxy = manager.get_next_proxy()
        assert proxy.server == 'http://proxy2.com:8080'


class TestProxyManagerRandom(TestCase):
    """Test ProxyManager with random strategy"""
    
    def test_random_strategy(self):
        """Test random strategy returns proxies"""
        proxies = [
            'http://proxy1.com:8080',
            'http://proxy2.com:8080',
            'http://proxy3.com:8080',
        ]
        
        manager = ProxyManager(proxies, strategy='random')
        
        # Get several proxies - should get at least 2 different ones
        selected = set()
        for _ in range(10):
            proxy = manager.get_next_proxy()
            selected.add(proxy.server)
        
        # With random strategy on 3 proxies, we should get variety
        assert len(selected) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])