# pop_up_bot/engines/__init__.py

"""
Engines Package

Core automation engines for bot operations.

Engines:
- PlaywrightScraperEngine: Low-level Playwright automation

Usage:
    from pop_up_bot.engines import PlaywrightScraperEngine
    
    engine = PlaywrightScraperEngine(page, event_logger)
    await engine.navigate('https://nike.com')
    await engine.click('button.add-to-cart')
"""

from .scraper_engine import PlaywrightScraperEngine

__all__ = [
    'PlaywrightScraperEngine',
]