from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from pathlib import Path
import csv

from requests import options


class Command(BaseCommand):
    help = 'Delete all migration files except __init__.py'

    def handle(self, *args, **kwargs):
        apps = [
            'pop_accounts', 'pop_up_auction', 'pop_up_coupon', 
            'pop_up_home', 'pop_up_order', 'pop_up_payment', 'pop_up_reward', 
            'pop_up_cart', 'pop_up_email', 'pop_up_finance', 'pop_up_shipping'
        ]

        base_dir = settings.BASE_DIR
        deleted_count = 0

        for app in apps:
            migrations_dir = base_dir / app / 'migrations'

            
            if not migrations_dir.exists():
                self.stdout.write(f'⚠️  {app}/migrations/ not found, skipping...')
                continue

            # Get all .py files in migrations/
            for file in migrations_dir.glob('*.py'):
                # Keep __init__.py
                if file.name == '__init__.py':
                    continue
                
                try:
                    file.unlink()
                    print('file', file)
                    self.stdout.write(f'✅ Deleted: {file}')
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(f'❌ Error: {e}')

        self.stdout.write(f'\n🎉 Deleted {deleted_count} migration files!')