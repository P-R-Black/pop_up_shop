from django.core.management.base import BaseCommand
from auction.models import (PopUpBrand, PopUpCategory, PopUpProductType, PopUpProductSpecification, 
                            PopUpProduct, PopUpProductSpecificationValue, PopUpProductImage)
from auction.auction_dummy_data import test_account_data
from django.utils.text import slugify
from datetime import datetime
from decimal import Decimal, InvalidOperation


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print('test')

        for tad in test_account_data:
            
            # BRAND
            brand, created = PopUpBrand.objects.get_or_create(
                name = tad['brand'],
                defaults = {'slug': slugify(tad['brand'])}

            )
            if not created:
                self.stdout.write(self.style.WARNING(f"Brand {brand.name} already exists, skipping name..."))

            # CATEGORY 
            category, created = PopUpCategory.objects.get_or_create(
                name = tad['category'],
                defaults = {'slug': slugify(tad['category']), 'is_active': True}
            )
            if not created:
                self.stdout.write(self.style.WARNING(f"Category {category.name} already exists, skipping name..."))

            # PRODUCT TYPE
            product_type, created = PopUpProductType.objects.get_or_create(
                name = tad['product_type'],
                defaults = {'slug': slugify(tad['product_type']), 'is_active': True}
            )
            if not created:
                self.stdout.write(self.style.WARNING(f"Product Type {product_type.name} already exists, skipping name..."))

            # PRODUCT            
            if PopUpProduct.objects.filter(slug=slugify(tad['product_title'] + tad['secondary_product_title'])).exists():
                self.stdout.write(self.style.WARNING(f"Product {tad['product_title']} already exists, skipping name..."))
            
            if tad['product_title'] != "" and tad['secondary_product_title'] != "":
                product_slug = slugify(tad['product_title'] + '-'+ tad['secondary_product_title'])
            else:
                product_slug = slugify(tad['product_title'])
            try:
                product = PopUpProduct.objects.create(
                    product_type = product_type,
                    category = category, 
                    product_title = tad['product_title'],
                    secondary_product_title = tad['secondary_product_title'],
                    description = tad['description'],
                    slug = product_slug,
                    buy_now_price = self.safe_decimal(tad['buy_now_price']),
                    current_highest_bid = self.safe_decimal(0.00),
                    retail_price = self.safe_decimal(tad['retail_price']),
                    brand = brand,
                    auction_start_date = self.parse_date(tad['auction_start_date']),
                    auction_end_date = self.parse_date(tad['auction_end_date']),
                    inventory_status = tad['inventory_status'],
                    bid_count = int(tad['bid_count']),
                    reserve_price = self.safe_decimal(tad['reserve_price']),
                    is_active = tad['is_active'],

                )

                product.save()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to create product {tad['product_title']}: {e}"))
                continue
            
    
            spec_fields = {
                "style_number": tad.get('style_number'),
                "colorway": tad.get('colorway'),
                "model_year": tad.get('model_year'),
                "release_date": tad.get('release_date'),
                "size": tad.get('size'),
                "product_sex": tad.get('product_sex'),
                "condition": tad.get('condition'),
                "mpn": tad.get('mpn'),
                "battery_life": tad.get('battery_life'),
                "platform": tad.get('platform'),
                "power_supply_region": tad.get('power_supply_region'),
                "storage_capacity": tad.get('storage_capacity'),
                "screen_size": tad.get('screen_size'),
                "ports": tad.get('ports'),
                "graphics": tad.get('graphics'),
                "memory": tad.get('memory'),
            }

            for spec_name, value in spec_fields.items():
                if not value:
                    continue
                specification, created = PopUpProductSpecification.objects.get_or_create(
                    product_type=product_type,
                    name=spec_name
                )

                if not PopUpProductSpecificationValue.objects.filter(
                    product=product,
                    specification=specification,
                    value=value).exists():

                    PopUpProductSpecificationValue.objects.create(
                        product=product, specification=specification, value=value
                    )

            if PopUpProductImage.objects.filter(image=tad['image']).exists():
                self.stdout.write(self.style.WARNING(f"Image {tad['image']} already exists, skipping name..."))
                continue

            image = PopUpProductImage.objects.create(
                product=product,
                image = tad['image'], 
                alt_text = tad['alternative_text'], 
                is_feature = (str(tad['is_feature']).lower() == 'true'),
            )

            self.stdout.write(self.style.SUCCESS(f"Product '{product.product_title}' created successfully."))

    def parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            return None
        
    def safe_decimal(self, value):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None
    
