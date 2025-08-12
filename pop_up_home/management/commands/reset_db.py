from django.core.management.base import BaseCommand

import csv


class Command(BaseCommand):
    help = 'import booms'

    print('help', help)

    def handle(self, *args, **kwargs):
        # rm -rf quotes_api/migrations/  # Remove migration files
        apps = ['pop_up_auction', 'pop_up_coupon', 'pop_up_home', 
                'pop_up_order', 'pop_up_payment', 'pop_accounts', 
                'pop_up_reward', 'pop_up_cart', 'pop_up_email', 'pop_up_finance',
                'pop_up_home', 'pop_up_shipping']


        for app in apps:
            if app + '/' + 'migrations/0001_initial.py' in app + '/' + 'migrations':
                print('yes', app)