from django.test import TestCase
from auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, 
                            PopUpProductType, PopUpProductSpecification, 
                            PopUpProductSpecificationValue)

from django.utils.timezone import now
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from freezegun import freeze_time
from unittest.mock import patch

class TestPopUpBrandModel(TestCase):
    def setUp(self):
        self.brand_one = PopUpBrand.objects.create(name='Nike', slug='nike')
        self.brand_two = PopUpBrand.objects.create(name='Fear of God', slug='fear-of-god')

    
    def test_brand_mode_entry(self):
        """
        Test Brand model data insertion/types field attributes
        """
        brand_one = self.brand_one
        brand_two = self.brand_two
        self.assertTrue(isinstance(brand_one, PopUpBrand))
        self.assertTrue(isinstance(brand_two, PopUpBrand))


class TestPopUpCategoryModel(TestCase):

    def setUp(self):
        self.data_one = PopUpCategory.objects.create(name='Jordan 11', slug='jordan-11')
        self.data_two = PopUpCategory.objects.create(name='Collectable', slug='collectable')
    
    def test_category_model_entry(self):
        """
        Test Category model data insertion/types.field attributes
        """
        data_one = self.data_one
        data_two = self.data_two
        self.assertTrue(isinstance(data_one, PopUpCategory))
        self.assertTrue(isinstance(data_two, PopUpCategory))


class TestPopUpTypesModel(TestCase):

    def setUp(self):
        self.data_one = PopUpProductType.objects.create(name='shoe', slug='shoe')
        self.data_two = PopUpProductType.objects.create(name='gaming system', slug='gaming-system')
    
    def test_type_model_entry(self):
        """
        Test Type model data insertion/types field attributes
        """
        data_one = self.data_one
        data_two = self.data_two
        self.assertTrue(isinstance(data_one, PopUpProductType))
        self.assertEqual(str(data_one), 'shoe')

        self.assertTrue(isinstance(data_two, PopUpProductType))
        self.assertEqual(str(data_two), 'gaming system')
    
   
class TestProducts(TestCase):
    """
    Test Products model data insertion/types field attributes
    """
    def setUp(self):
        PopUpCategory.objects.create(name='Jordan 3', slug='jordan-3')
        PopUpBrand.objects.create(name='Jordan', slug='jordan')
        PopUpProductType.objects.create(name='shoe', slug='shoe')

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            starting_price="230.00",
            brand_id=1,
            auction_start_date=None,
            auction_end_date=None,
            inventory_status="in_inventory",
            bid_count="0",
            reserve_price="0",
            is_active=True)
    
    def test_product_model_entry(self):
        prod_one = self.prod_one

        # Test product_type_id
        self.assertEqual(int(prod_one.product_type_id), 1)

        # Test product_type
        self.assertEqual(str(prod_one.product_type), "shoe")

        # Test category_id
        self.assertEqual(int(prod_one.category_id), 1)

        # Test category
        self.assertEqual(str(prod_one.category), "Jordan 3")

        # Test product_title
        self.assertEqual(str(prod_one.product_title), "Jordan 3 Retro")

        # Test secondary_product_title
        self.assertEqual(str(prod_one.secondary_product_title), "OG Rare Air")

        # Test description
        self.assertEqual(str(prod_one.description), "Brand new sneakers")

        # Test slug
        self.assertEqual(str(prod_one.slug), "jordan-3-retro-og-rare-air")

        # Test retail_price
        self.assertEqual(str(prod_one.retail_price), "150.00")

        # Test starting_price
        self.assertEqual(str(prod_one.starting_price), "230.00")

        # Test brand_id
        self.assertEqual(int(prod_one.brand_id), 1)

        # Test brand_name
        self.assertEqual(str(prod_one.brand), "Jordan")

        # Test auction_start_date
        self.assertEqual(prod_one.auction_start_date, None)

        # Test auction_end_date
        self.assertEqual(prod_one.auction_end_date, None)

        # Test inventory_status
        self.assertEqual(str(prod_one.inventory_status), "in_inventory")

        # Test bid_count
        self.assertEqual(str(prod_one.bid_count), "0")

        # Test reserve_price
        self.assertEqual(str(prod_one.reserve_price), "0")

        # Test is_active
        self.assertEqual(prod_one.is_active, True)
        
        self.assertTrue(isinstance(prod_one, PopUpProduct))




class TestProductsActiveAuction(TestCase):
    """
    Test an Active Auction
    """
    # freeze_time("2025-05-17 12:00:00")
    def setUp(self):
        PopUpCategory.objects.create(name='Jordan 3', slug='jordan-3')
        PopUpBrand.objects.create(name='Jordan', slug='jordan')
        PopUpProductType.objects.create(name='shoe', slug='shoe')

        auction_start = make_aware(datetime(2025, 5, 10, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 5, 18, 12, 0, 0))
        

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            starting_price="230.00",
            brand_id=1,
            auction_start_date=auction_start,
            auction_end_date=auction_end,
            inventory_status="in_inventory",
            bid_count="0",
            reserve_price="0",
            is_active=True)
    
        print('start', self.prod_one.auction_start_date)
        print('end', self.prod_one.auction_end_date)

    # freeze_time("2025-05-17 12:00:00")
    def test_product_model_active_auction(self, mock_now):

        prod_one = self.prod_one
        status = prod_one.auction_status
        duration = prod_one.auction_duration

        self.assertTrue(isinstance(prod_one, PopUpProduct))
        self.assertEqual(status, "Ongoing")  # since the date is in the future
        self.assertEqual(duration["days"], 7)
        self.assertEqual(duration["hours"], 0)


class TestProductsUpcomingAuction(TestCase):
    """
    Test An Upcoming Auction
    """
    def setUp(self):
        PopUpCategory.objects.create(name='Jordan 3', slug='jordan-3')
        PopUpBrand.objects.create(name='Jordan', slug='jordan')
        PopUpProductType.objects.create(name='shoe', slug='shoe')

        auction_start = make_aware(datetime(2025, 5, 23, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 4, 30, 12,0, 0))

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            starting_price="230.00",
            brand_id=1,
            auction_start_date=auction_start,
            auction_end_date=auction_end,
            inventory_status="in_inventory",
            bid_count="0",
            reserve_price="0",
            is_active=True)
    
    def test_product_model_active_auction(self):
        prod_one = self.prod_one
        status = prod_one.auction_status
        duration = prod_one.auction_duration

        self.assertTrue(isinstance(prod_one, PopUpProduct))
        self.assertEqual(status, "Upcoming")  # since the date is in the future
        self.assertEqual(duration["days"], 7)
        self.assertEqual(duration["hours"], 0)
    

class TestProductsFinishedAuction(TestCase):
    """
    Test A Finished Auction
    """
    def setUp(self):
        PopUpCategory.objects.create(name='Jordan 3', slug='jordan-3')
        PopUpBrand.objects.create(name='Jordan', slug='jordan')
        PopUpProductType.objects.create(name='shoe', slug='shoe')

        auction_start = make_aware(datetime(2025, 4, 6, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 4, 13, 12,0, 0))

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            starting_price="230.00",
            brand_id=1,
            auction_start_date=auction_start,
            auction_end_date=auction_end,
            inventory_status="in_inventory",
            bid_count="0",
            reserve_price="0",
            is_active=True)
    
    def test_product_model_active_auction(self):
        prod_one = self.prod_one
        status = prod_one.auction_status
        duration = prod_one.auction_duration

        self.assertTrue(isinstance(prod_one, PopUpProduct))
        self.assertEqual(status, "Ended")  # since the date is in the future
        self.assertEqual(duration["days"], 7)
        self.assertEqual(duration["hours"], 0)


class TestPopUpProductSpecificationModel(TestCase):

    def setUp(self):
        self.product_type = PopUpProductType.objects.create(name='Shoe', slug='shoe')

    def test_specification_creation(self):
        spec = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='Color'
        )
        self.assertEqual(spec.name, 'Color')
        self.assertEqual(spec.product_type.name, 'Shoe')
        self.assertTrue(isinstance(spec, PopUpProductSpecification))
        self.assertEqual(str(spec), 'Color')

    def test_specification_unique_constraint(self):
        PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name='Size'
        )
        with self.assertRaises(Exception):
            # Should raise an IntegrityError due to unique_together
            PopUpProductSpecification.objects.create(
                product_type=self.product_type,
                name='Size'
            )

class TestPopUpProductSpecificationValueModel(TestCase):
    def setUp(self):
        self.product_type = PopUpProductType.objects.create(name='Shoe', slug='shoe')
        self.category = PopUpCategory.objects.create(name='Sneakers', slug='sneakers')
        self.brand = PopUpBrand.objects.create(name='Nike', slug='nike')

        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            product_title="Nike Air Max",
            secondary_product_title="Limited Edition",
            description="Comfortable and stylish",
            slug="nike-air-max",
            retail_price="120.00",
            starting_price="190.00",
            brand=self.brand,
            auction_start_date=now(),
            auction_end_date=now() + timedelta(days=5),
            inventory_status="in_inventory",
            bid_count=0,
            reserve_price="0.00",
            is_active=True,
        )

        self.specification = PopUpProductSpecification.objects.create(
            product_type=self.product_type,
            name="Color"
        )

    def test_specification_value_creation(self):
        value = PopUpProductSpecificationValue.objects.create(
            product=self.product,
            specification=self.specification,
            value="Red"
        )

        self.assertEqual(value.value, "Red")
        self.assertEqual(value.product.product_title, "Nike Air Max")
        self.assertEqual(value.specification.name, "Color")
        self.assertEqual(str(value), "Red")

"""
THINGS TO TEST
1. Number of days left in auction.
2. Auction completed
"""

# coverage report | gets coverage report
# coverage html | gets coverage report in html. open index.html file in htmlcov directory
# run --omit='*/venv/*' manage.py test | command to run test