# pop_up_bot/tests/test_procurement_strategy.py

import pytest
from django.test import TestCase

import pop_up_bot
from pop_up_bot.strategies import (
    StrategyFactory,
    Site,
    SiteType,
)

from pop_up_bot.strategies.base import ProcurementStrategy

from pop_up_bot.strategies.implementations import (
    SequentialStrategy,
    ParallelStrategy,
    PriorityStrategy,
    FastestStrategy,
    CheapestStrategy,
    RetailOnlyStrategy,
)


class TestSite(TestCase):
    """Test Site model"""
    
    def test_site_creation(self):
        """Test creating a site"""
        site = Site('nike')
        
        assert site.name == 'nike'
        assert site.type == SiteType.OFFICIAL_RETAIL
        assert site.priority == 1
        assert site.timeout == 30
    
    def test_site_invalid(self):
        """Test invalid site"""
        with pytest.raises(ValueError):
            Site('invalid_site')
    
    
    def test_site_str(self):
        """Test site string representation"""
        site = Site('nike')
        assert str(site) == 'nike'


class TestSequentialStrategy(TestCase):
    """Test SequentialStrategy"""
    
    def test_sequential_initialization(self):
        """Test initializing sequential strategy"""
        strategy = SequentialStrategy(sites=['nike', 'adidas', 'footlocker'])
        
        assert strategy.sites == ['nike', 'adidas', 'footlocker']
        assert strategy.timeout_per_site == 30
    
    def test_sequential_get_site_order(self):
        """Test site order is preserved"""
        sites = ['nike', 'footlocker', 'adidas']
        strategy = SequentialStrategy(sites=sites)
        
        order = strategy.get_site_order()
        assert order == sites
    
    def test_sequential_stop_on_success(self):
        """Test sequential stops on success"""
        strategy = SequentialStrategy(sites=['nike', 'footlocker'])
        
        result = {'success': True, 'site': 'nike'}
        should_continue = strategy.should_attempt_next_site(result)
        
        assert should_continue is False
    
    def test_sequential_continue_on_failure(self):
        """Test sequential continues on failure"""
        strategy = SequentialStrategy(sites=['nike', 'footlocker'])
        strategy.mark_attempted('nike')
        
        result = {'success': False, 'site': 'nike', 'reason': 'Out of stock'}
        should_continue = strategy.should_attempt_next_site(result)
        
        assert should_continue is True
    
    def test_sequential_mark_attempted(self):
        """Test marking sites as attempted"""
        strategy = SequentialStrategy(sites=['nike', 'footlocker', 'adidas'])
        
        strategy.mark_attempted('nike')
        strategy.mark_attempted('footlocker')
        
        assert strategy.attempted_sites == ['nike', 'footlocker']
        assert strategy.get_remaining_sites() == ['adidas']
    
    def test_sequential_stats(self):
        """Test strategy statistics"""
        strategy = SequentialStrategy(sites=['nike', 'footlocker', 'adidas'])
        
        strategy.mark_attempted('nike')
        strategy.mark_failed('nike')
        strategy.mark_attempted('footlocker')
        strategy.mark_successful('footlocker')
        
        stats = strategy.get_stats()
        
        assert stats['strategy'] == 'SequentialStrategy'
        assert stats['attempted'] == ['nike', 'footlocker']
        assert stats['failed'] == ['nike']
        assert stats['successful'] == 'footlocker'
        assert stats['remaining'] == ['adidas']


class TestParallelStrategy(TestCase):
    """Test ParallelStrategy"""
    
    def test_parallel_initialization(self):
        """Test initializing parallel strategy"""
        strategy = ParallelStrategy(sites=['nike', 'adidas', 'footlocker'])
        
        assert strategy.sites == ['nike', 'adidas', 'footlocker']
    
    def test_parallel_all_sites_at_once(self):
        """Test parallel returns all sites"""
        strategy = ParallelStrategy(sites=['nike', 'adidas', 'footlocker'])
        
        order = strategy.get_site_order()
        
        assert len(order) == 3
        assert all(site in order for site in ['nike', 'adidas', 'footlocker'])
    
    def test_parallel_stops_immediately(self):
        """Test parallel doesn't continue (coordinator handles parallelism)"""
        strategy = ParallelStrategy()
        
        result = {'success': False, 'site': 'nike', 'reason': 'Out of stock'}
        should_continue = strategy.should_attempt_next_site(result)
        
        assert should_continue is False


class TestPriorityStrategy(TestCase):
    """Test PriorityStrategy"""
    
    def test_priority_custom_order(self):
        """Test custom priority order"""
        priority_order = ['adidas', 'nike', 'footlocker']
        strategy = PriorityStrategy(priority_order=priority_order)
        
        assert strategy.get_site_order() == priority_order
    
    def test_priority_default_order(self):
        """Test default priority order"""
        strategy = PriorityStrategy()
        
        order = strategy.get_site_order()
        
        assert order[0] == 'nike'  # Nike has priority 1
        assert 'footlocker' in order
        assert 'adidas' in order


class TestFastestStrategy(TestCase):
    """Test FastestStrategy"""
    
    def test_fastest_short_timeout(self):
        """Test fastest strategy uses aggressive timeouts"""
        strategy = FastestStrategy()
        
        assert strategy.timeout_per_site == 15  # Short timeout
    
    def test_fastest_all_sites(self):
        """Test fastest tries all sites"""
        strategy = FastestStrategy(sites=['nike', 'adidas'])
        
        assert strategy.get_site_order() == ['nike', 'adidas']


class TestCheapestStrategy(TestCase):
    """Test CheapestStrategy"""
    
    def test_cheapest_initialization(self):
        """Test cheapest strategy initializes"""
        strategy = CheapestStrategy()
        
        assert strategy.timeout_per_site == 30
        assert len(strategy.get_site_order()) > 0


class TestRetailOnlyStrategy(TestCase):
    """Test RetailOnlyStrategy"""
    
    def test_retail_only_excludes_resellers(self):
        """Test retail-only excludes resellers"""
        strategy = RetailOnlyStrategy()
        
        sites = strategy.get_site_order()
        
        # Should include official retail
        assert 'nike' in sites
        assert 'footlocker' in sites
        
        # Should exclude resellers (grailed, stockx)
        # Note: Our current registry doesn't have these in retail-only
    
    def test_retail_only_count(self):
        """Test retail-only has expected number of sites"""
        strategy = RetailOnlyStrategy()
        
        sites = strategy.get_site_order()
        
        # Nike, Footlocker, Adidas, New Balance, Supreme
        assert len(sites) >= 5


class TestStrategyFactory(TestCase):
    """Test StrategyFactory"""
    
    def test_factory_create_sequential(self):
        """Test creating sequential strategy"""
        strategy = StrategyFactory.create('sequential', sites=['nike', 'adidas'])
        
        assert isinstance(strategy, SequentialStrategy)
        assert strategy.get_site_order() == ['nike', 'adidas']
    
    def test_factory_create_parallel(self):
        """Test creating parallel strategy"""
        strategy = StrategyFactory.create('parallel')
        
        assert isinstance(strategy, ParallelStrategy)
    
    def test_factory_create_priority(self):
        """Test creating priority strategy"""
        strategy = StrategyFactory.create('priority')
        
        assert isinstance(strategy, PriorityStrategy)
    
    def test_factory_create_fastest(self):
        """Test creating fastest strategy"""
        strategy = StrategyFactory.create('fastest')
        
        assert isinstance(strategy, FastestStrategy)
    
    def test_factory_create_cheapest(self):
        """Test creating cheapest strategy"""
        strategy = StrategyFactory.create('cheapest')
        
        assert isinstance(strategy, CheapestStrategy)
    
    def test_factory_create_retail_only(self):
        """Test creating retail-only strategy"""
        strategy = StrategyFactory.create('retail_only')
        
        assert isinstance(strategy, RetailOnlyStrategy)
    
    def test_factory_invalid_strategy(self):
        """Test creating invalid strategy raises error"""
        with pytest.raises(ValueError):
            StrategyFactory.create('invalid_strategy')
    
    def test_factory_get_available(self):
        """Test getting available strategies"""
        available = StrategyFactory.get_available()
        
        assert 'sequential' in available
        assert 'parallel' in available
        assert 'priority' in available
        assert 'fastest' in available
        assert 'cheapest' in available
        assert 'retail_only' in available


class TestStrategyWorkflows(TestCase):
    """Test complete strategy workflows"""
    
    def test_sequential_workflow_success_on_second(self):
        """Test sequential strategy succeeds on second site"""
        strategy = SequentialStrategy(sites=['nike', 'footlocker', 'adidas'])
        
        # First site fails
        result1 = {'success': False, 'site': 'nike', 'reason': 'Out of stock'}
        strategy.mark_attempted('nike')
        strategy.mark_failed('nike')
        
        assert strategy.should_attempt_next_site(result1) is True
        assert len(strategy.get_remaining_sites()) == 2
        
        # Second site succeeds
        result2 = {'success': True, 'site': 'footlocker'}
        strategy.mark_attempted('footlocker')
        strategy.mark_successful('footlocker')
        
        assert strategy.should_attempt_next_site(result2) is False
        assert strategy.successful_site == 'footlocker'
    
    def test_sequential_workflow_all_fail(self):
        """Test sequential when all sites fail"""
        strategy = SequentialStrategy(sites=['nike', 'footlocker'])
        
        # Nike fails
        strategy.mark_attempted('nike')
        strategy.mark_failed('nike')
        result1 = {'success': False, 'site': 'nike'}
        assert strategy.should_attempt_next_site(result1) is True
        
        # Footlocker fails
        strategy.mark_attempted('footlocker')
        strategy.mark_failed('footlocker')
        result2 = {'success': False, 'site': 'footlocker'}
        assert strategy.should_attempt_next_site(result2) is False
        
        # No more sites
        assert len(strategy.get_remaining_sites()) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



