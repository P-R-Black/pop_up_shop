from django.core.management.base import BaseCommand

import csv


class Command(BaseCommand):
    help = 'import booms'

    print('help', help)

    def handle(self, *args, **kwargs):
        # rm -rf quotes_api/migrations/  # Remove migration files
        apps = ['auction', 'coupon', 'home', 'orders', 'payment', 'pop_accounts', 'reward']

        for app in apps:
            if app + '/' + 'migrations/0001_initial.py' in app + '/' + 'migrations':
                print('yes', app)