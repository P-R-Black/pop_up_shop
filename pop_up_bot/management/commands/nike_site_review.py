"""
Nike Selector Inspector

This script navigates Nike.com, searches for a product, and logs all the selectors
you need for the NikeSiteHandler. Run this locally to get current selectors.

Install: pip install playwright
Setup: playwright install chromium

Run: python nike_selector_inspector.py
"""

import asyncio
from playwright.async_api import async_playwright
import json
from django.core.management.base import BaseCommand
from django.utils.timezone import now


class Command(BaseCommand):
    help = "Check for attack patterns in registration and password resets"

    def handle(self, *args, **options):
        print('Handle Test!')
        