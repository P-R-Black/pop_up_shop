# pop_up_bot/management/commands/create_procurement_product.py

from django.core.management.base import BaseCommand
from pop_up_auction.models import PopUpProduct, PopUpProductType, PopUpCategory, PopUpBrand
from decimal import Decimal


class Command(BaseCommand):
    help = 'Creates the Procurement Service Fee product if it does not exist'

    def handle(self, *args, **kwargs):
        product_type, _ = PopUpProductType.objects.get_or_create(
            slug='service',
            defaults={'name': 'Service', 'is_active': True}
        )
        category, _ = PopUpCategory.objects.get_or_create(
            slug='service',
            defaults={'name': 'Service', 'is_active': True}
        )
        brand, _ = PopUpBrand.objects.get_or_create(
            slug='pop-up-shop',
            defaults={'name': 'Pop Up Shop'}
        )

        product, created = PopUpProduct.objects.get_or_create(
            slug='procurement-service-fee',
            defaults={
                'product_type': product_type,
                'category': category,
                'brand': brand,
                'product_title': 'Procurement Service Fee',
                'secondary_product_title': '',
                'retail_price': Decimal('15.00'),
                'buy_now_price': Decimal('15.00'),
                'inventory_status': 'in_inventory',
                'is_active': False,  # hidden from storefront
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created procurement product: {product.id}'))
        else:
            self.stdout.write(f'Procurement product already exists: {product.id}')