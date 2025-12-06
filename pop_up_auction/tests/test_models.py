from django.test import TestCase
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, 
                            PopUpProductType, PopUpProductSpecification, WinnerReservation,
                            PopUpProductSpecificationValue, PopUpProductImage)

from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta
from freezegun import freeze_time
from unittest.mock import patch
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model

"""
Tests In Order
 1. TestPopUpBrandModel
 2. TestPopUpCategoryModel
 3. TestPopUpTypesModel
 4. TestProducts
 5. TestProductsActiveAuction
 6. TestProductsUpcomingAuction
 7. TestProductsFinishedAuction
 8. TestPopUpProductSpecificationModel
 9. TestPopUpProductSpecificationValueModel
 10. 
 11. 
 12. 

"""

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
            buy_now_price="230.00",
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

        # Test buy_now_price
        self.assertEqual(str(prod_one.buy_now_price), "230.00")

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

        auction_start = make_aware(datetime(2025, 5, 29, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 6, 5, 12, 0, 0))
        

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            buy_now_price="230.00",
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
    def test_product_model_active_auction(self):

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


        auction_start = make_aware(datetime(2025, 11, 18, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 11, 24, 12, 0, 0))

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            buy_now_price="230.00",
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

        auction_start = make_aware(datetime(2025, 5, 22, 12, 0, 0))
        auction_end = make_aware(datetime(2025, 5, 29, 12, 0, 0))

        self.prod_one = PopUpProduct.objects.create(
            product_type_id=1, 
            category_id=1, 
            product_title="Jordan 3 Retro", 
            secondary_product_title="OG Rare Air",
            description="Brand new sneakers",
            slug="jordan-3-retro-og-rare-air",
            retail_price="150.00",
            buy_now_price="230.00",
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
            buy_now_price="190.00",
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



from django.core.files.uploadedfile import SimpleUploadedFile

class TestPopUpProductImageModel(TestCase):
    """Test suite for PopUpProductImage model"""

    def setUp(self):
        """Create test data"""
        # Create required foreign key objects
        self.product_type = PopUpProductType.objects.create(
            name="Sneakers"
        )
        self.category = PopUpCategory.objects.create(
            name="Athletic Shoes",
            slug="athletic-shoes"
        )
        self.brand = PopUpBrand.objects.create(
            name="Nike"
        )
        
        # Create product
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Test Sneakers",
            slug="test-sneakers",
            retail_price=Decimal("200.00"),
            is_active=True
        )

    

    def test_create_product_image_with_uploaded_file(self):
        """Test creating a product image with uploaded file"""
        # Create a simple test image file
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image,
            alt_text="Test image"
        )
        
        self.assertEqual(product_image.product, self.product)
        self.assertIsNotNone(product_image.image)
        self.assertEqual(product_image.alt_text, "Test image")

    def test_create_product_image_with_url(self):
        """Test creating a product image with external URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            alt_text="External image"
        )
        
        self.assertEqual(product_image.image_url, "https://example.com/image.jpg")
        self.assertEqual(product_image.alt_text, "External image")

    def test_is_feature_default_false(self):
        """Test that is_feature defaults to False"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertFalse(product_image.is_feature)

    def test_set_feature_image(self):
        """Test setting an image as featured"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            is_feature=True
        )
        
        self.assertTrue(product_image.is_feature)

    def test_multiple_images_per_product(self):
        """Test that a product can have multiple images"""
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg",
            is_feature=True
        )
        img2 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg"
        )
        img3 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image3.jpg"
        )
        
        self.assertEqual(self.product.product_image.count(), 3)
        self.assertIn(img1, self.product.product_image.all())
        self.assertIn(img2, self.product.product_image.all())
        self.assertIn(img3, self.product.product_image.all())

    def test_cascade_delete_product_deletes_images(self):
        """Test that deleting product deletes its images"""
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg"
        )
        img2 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg"
        )
        
        product_id = self.product.id
        self.product.delete()
        
        # Images should be deleted
        self.assertEqual(PopUpProductImage.objects.filter(product_id=product_id).count(), 0)

    def test_get_image_url_with_uploaded_file(self):
        """Test get_image_url returns uploaded file"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image
        )
        
        # Should return the actual URL of the uploaded file
        self.assertEqual(product_image.get_image_url(), product_image.image.url)


    def test_get_image_url_with_external_url(self):
        """Test get_image_url returns external URL when no uploaded file"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image= '',
            image_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(
            product_image.get_image_url(), 
            "https://example.com/image.jpg"
        )

    def test_get_image_url_fallback_to_default(self):
        """Test get_image_url returns default when no image or URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image= '',
        )
        
        expected_default = settings.STATIC_URL + 'images/default.png'
        self.assertEqual(product_image.get_image_url(), expected_default)


    def test_resolved_image_url_property(self):
        """Test resolved_image_url property"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(
            product_image.resolved_image_url,
            product_image.get_image_url()
        )

    def test_str_representation_with_uploaded_image(self):
        """Test __str__ with uploaded image"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image
        )
        
        # Should return the image URL
        str_repr = str(product_image)
        self.assertIn('test_image', str_repr)

    def test_str_representation_with_external_url(self):
        """Test __str__ with external URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(str(product_image), "https://example.com/image.jpg")

    def test_str_representation_with_no_image(self):
        """Test __str__ when no image or URL"""
        product_image = PopUpProductImage.objects.create(
            product=self.product
        )
        
        self.assertEqual(str(product_image), "No image")

    def test_alt_text_optional(self):
        """Test that alt_text is optional"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertIsNone(product_image.alt_text)

    def test_alt_text_max_length(self):
        """Test alt_text respects max_length"""
        long_alt_text = "A" * 255
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg",
            alt_text=long_alt_text
        )
        
        self.assertEqual(len(product_image.alt_text), 255)

    def test_timestamps_auto_populate(self):
        """Test that created_at and updated_at auto-populate"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        self.assertIsNotNone(product_image.created_at)
        self.assertIsNotNone(product_image.updated_at)

    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        original_updated_at = product_image.updated_at
        
        # Update the image
        product_image.alt_text = "Updated alt text"
        product_image.save()
        
        self.assertNotEqual(product_image.updated_at, original_updated_at)
        self.assertGreater(product_image.updated_at, original_updated_at)

    def test_filter_featured_images(self):
        """Test filtering for featured images"""
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg",
            is_feature=True
        )
        img2 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg",
            is_feature=False
        )
        img3 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image3.jpg",
            is_feature=True
        )
        
        featured_images = self.product.product_image.filter(is_feature=True)
        self.assertEqual(featured_images.count(), 2)
        self.assertIn(img1, featured_images)
        self.assertIn(img3, featured_images)
        self.assertNotIn(img2, featured_images)

    def test_get_featured_image(self):
        """Test getting the first featured image"""
        PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image1.jpg",
            is_feature=False
        )
        featured = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image2.jpg",
            is_feature=True
        )
        
        first_featured = self.product.product_image.filter(is_feature=True).first()
        self.assertEqual(first_featured, featured)

    def test_related_name_product_image(self):
        """Test the related_name 'product_image' works correctly"""
        PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/image.jpg"
        )
        
        # Access via related_name
        self.assertEqual(self.product.product_image.count(), 1)

    def test_image_priority_uploaded_over_url(self):
        """Test that uploaded image takes priority over external URL"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image,
            image_url="https://example.com/image.jpg"
        )
        
        # Should return uploaded image, not URL
        self.assertEqual(product_image.get_image_url(), product_image.image.url)

    def test_default_image_path(self):
        """Test default image is set correctly"""
        product_image = PopUpProductImage.objects.create(
            product=self.product
        )
        
        # Check that default exists in the path
        expected_default = settings.STATIC_URL + 'images/default.png'
        self.assertEqual(product_image.get_image_url(), expected_default)


    def test_upload_to_directory(self):
        """Test images are uploaded to correct directory"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
        
        product_image = PopUpProductImage.objects.create(
            product=self.product,
            image=image
        )
        
        # Check upload path
        self.assertIn('images/', product_image.image.name)

    def test_multiple_products_same_image_url(self):
        """Test that different products can use the same external URL"""
        product2 = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Another Sneaker",
            slug="another-sneaker",
            retail_price=Decimal("150.00")
        )
        
        img1 = PopUpProductImage.objects.create(
            product=self.product,
            image_url="https://example.com/shared-image.jpg"
        )
        img2 = PopUpProductImage.objects.create(
            product=product2,
            image_url="https://example.com/shared-image.jpg"
        )
        
        self.assertEqual(img1.image_url, img2.image_url)
        self.assertNotEqual(img1.product, img2.product)



class WinnerReservationModelTest(TestCase):
    """Test suite for WinnerReservation model"""

    def setUp(self):
        """Create test data"""
        # Create user
        self.user = User.objects.create_user(
            email="winner@example.com",
            password="testpass123",
            first_name="Winner",
            last_name="User"
        )
        self.user.is_active = True
        self.user.save()
        
        # Create another user for duplicate tests
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="testpass123"
        )
        self.user2.is_active = True
        self.user2.save()
        
        # Create required foreign key objects
        self.product_type = PopUpProductType.objects.create(name="Sneakers")
        self.category = PopUpCategory.objects.create(name="Athletic", slug="athletic")
        self.brand = PopUpBrand.objects.create(name="Nike")
        
        # Create product
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Test Sneakers",
            slug="test-sneakers",
            retail_price=Decimal("200.00"),
            reserve_price=Decimal("150.00"),
            is_active=True
        )
        
        # Create another product for testing
        self.product2 = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title="Another Sneaker",
            slug="another-sneaker",
            retail_price=Decimal("180.00")
        )

    def test_create_winner_reservation(self):
        """Test creating a winner reservation"""
        expires_at = timezone.now() + timedelta(hours=48)
        
        reservation = WinnerReservation.objects.create(
            user=self.user,
            product=self.product,
            expires_at=expires_at
        )
        
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.product, self.product)
        self.assertEqual(reservation.expires_at, expires_at)
        self.assertFalse(reservation.is_paid)
        self.assertFalse(reservation.is_expired)
        self.assertFalse(reservation.notification_sent)

#     def test_reserved_at_auto_populated(self):
#         """Test that reserved_at is automatically set"""
#         before = timezone.now()
        
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         after = timezone.now()
        
#         self.assertIsNotNone(reservation.reserved_at)
#         self.assertGreaterEqual(reservation.reserved_at, before)
#         self.assertLessEqual(reservation.reserved_at, after)

#     def test_expires_at_48_hours_from_now(self):
#         """Test setting expiration to 48 hours from now"""
#         now = timezone.now()
#         expires_at = now + timedelta(hours=48)
        
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=expires_at
#         )
        
#         # Check that expires_at is approximately 48 hours from now
#         time_diff = reservation.expires_at - now
#         self.assertAlmostEqual(
#             time_diff.total_seconds(),
#             48 * 3600,
#             delta=5  # Allow 5 seconds tolerance
#         )

#     def test_is_paid_default_false(self):
#         """Test that is_paid defaults to False"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         self.assertFalse(reservation.is_paid)
#         self.assertIsNone(reservation.paid_at)

#     def test_mark_as_paid(self):
#         """Test marking reservation as paid"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         paid_time = timezone.now()
#         reservation.is_paid = True
#         reservation.paid_at = paid_time
#         reservation.save()
        
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.is_paid)
#         self.assertEqual(reservation.paid_at, paid_time)

#     def test_is_expired_default_false(self):
#         """Test that is_expired defaults to False"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         self.assertFalse(reservation.is_expired)

#     def test_mark_as_expired(self):
#         """Test marking reservation as expired (simulating background task)"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() - timedelta(hours=1)  # Already expired
#         )
        
#         # Simulate background task marking as expired
#         reservation.is_expired = True
#         reservation.save()
        
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.is_expired)

#     def test_notification_sent_default_false(self):
#         """Test that notification_sent defaults to False"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         self.assertFalse(reservation.notification_sent)

#     def test_mark_notification_as_sent(self):
#         """Test marking notification as sent"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         reservation.notification_sent = True
#         reservation.save()
        
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.notification_sent)

#     def test_reminder_flags_default_false(self):
#         """Test that reminder flags default to False"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         self.assertFalse(reservation.reminder_24hr_sent)
#         self.assertFalse(reservation.reminder_1hr_sent)

#     def test_mark_24hr_reminder_sent(self):
#         """Test marking 24-hour reminder as sent"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         reservation.reminder_24hr_sent = True
#         reservation.save()
        
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.reminder_24hr_sent)
#         self.assertFalse(reservation.reminder_1hr_sent)

#     def test_mark_1hr_reminder_sent(self):
#         """Test marking 1-hour reminder as sent"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         reservation.reminder_1hr_sent = True
#         reservation.save()
        
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.reminder_1hr_sent)
#         self.assertFalse(reservation.reminder_24hr_sent)

#     def test_unique_together_constraint(self):
#         """Test that same product and user can't have duplicate reservations"""
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         # Try to create duplicate
#         with self.assertRaises(Exception):  # IntegrityError
#             WinnerReservation.objects.create(
#                 user=self.user,
#                 product=self.product,
#                 expires_at=timezone.now() + timedelta(hours=48)
#             )

#     def test_same_user_different_products(self):
#         """Test that same user can have reservations for different products"""
#         reservation1 = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         reservation2 = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product2,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         self.assertEqual(WinnerReservation.objects.filter(user=self.user).count(), 2)
#         self.assertNotEqual(reservation1.product, reservation2.product)

#     def test_same_product_different_users(self):
#         """Test that different users can have reservations for same product (sequential wins)"""
#         # First user wins, pays, reservation can be deleted
#         reservation1 = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
#         reservation1.is_paid = True
#         reservation1.save()
        
#         # After first user's reservation is handled, second user can win
#         reservation1.delete()  # Simulating cleanup after payment
        
#         reservation2 = WinnerReservation.objects.create(
#             user=self.user2,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         self.assertNotEqual(reservation2.user, self.user)

#     def test_cascade_delete_user(self):
#         """Test that deleting user deletes reservation"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         reservation_id = reservation.id
#         self.user.hard_delete()
        
#         self.assertFalse(
#             WinnerReservation.objects.filter(id=reservation_id).exists()
#         )

#     def test_cascade_delete_product(self):
#         """Test that deleting product deletes reservation"""
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         reservation_id = reservation.id
#         self.product.delete()
        
#         self.assertFalse(
#             WinnerReservation.objects.filter(id=reservation_id).exists()
#         )

#     def test_filter_unpaid_reservations(self):
#         """Test filtering unpaid reservations"""
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48),
#             is_paid=False
#         )
        
#         WinnerReservation.objects.create(
#             user=self.user2,
#             product=self.product2,
#             expires_at=timezone.now() + timedelta(hours=48),
#             is_paid=True
#         )
        
#         unpaid = WinnerReservation.objects.filter(is_paid=False)
#         self.assertEqual(unpaid.count(), 1)

#     def test_filter_expired_reservations(self):
#         """Test filtering expired reservations"""
#         # Create expired reservation
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() - timedelta(hours=1),
#             is_expired=True
#         )
        
#         # Create active reservation
#         WinnerReservation.objects.create(
#             user=self.user2,
#             product=self.product2,
#             expires_at=timezone.now() + timedelta(hours=48),
#             is_expired=False
#         )
        
#         expired = WinnerReservation.objects.filter(is_expired=True)
#         self.assertEqual(expired.count(), 1)

#     def test_filter_reservations_needing_24hr_reminder(self):
#         """Test finding reservations that need 24-hour reminder"""
#         # Expires in ~24 hours, reminder not sent
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=24),
#             reminder_24hr_sent=False
#         )
        
#         # Expires in ~24 hours, reminder already sent
#         WinnerReservation.objects.create(
#             user=self.user2,
#             product=self.product2,
#             expires_at=timezone.now() + timedelta(hours=24),
#             reminder_24hr_sent=True
#         )
        
#         needs_reminder = WinnerReservation.objects.filter(
#             reminder_24hr_sent=False,
#             expires_at__lte=timezone.now() + timedelta(hours=25),
#             expires_at__gte=timezone.now() + timedelta(hours=23)
#         )
        
#         self.assertEqual(needs_reminder.count(), 1)

#     def test_filter_reservations_needing_1hr_reminder(self):
#         """Test finding reservations that need 1-hour reminder"""
#         # Expires in ~1 hour, reminder not sent
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=1),
#             reminder_1hr_sent=False
#         )
        
#         # Expires in ~1 hour, reminder already sent
#         WinnerReservation.objects.create(
#             user=self.user2,
#             product=self.product2,
#             expires_at=timezone.now() + timedelta(hours=1),
#             reminder_1hr_sent=True
#         )
        
#         needs_reminder = WinnerReservation.objects.filter(
#             reminder_1hr_sent=False,
#             expires_at__lte=timezone.now() + timedelta(hours=2),
#             expires_at__gte=timezone.now()
#         )
        
#         self.assertEqual(needs_reminder.count(), 1)

#     def test_payment_workflow(self):
#         """Test complete payment workflow"""
#         # Create reservation
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48)
#         )
        
#         # Initial state
#         self.assertFalse(reservation.is_paid)
#         self.assertIsNone(reservation.paid_at)
        
#         # User pays
#         payment_time = timezone.now()
#         reservation.is_paid = True
#         reservation.paid_at = payment_time
#         reservation.save()
        
#         # Verify payment recorded
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.is_paid)
#         self.assertEqual(reservation.paid_at, payment_time)
#         self.assertFalse(reservation.is_expired)

#     def test_expiration_workflow(self):
#         """Test complete expiration workflow"""
#         # Create reservation that expires soon
#         reservation = WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(minutes=1)
#         )
        
#         # Initial state
#         self.assertFalse(reservation.is_expired)
        
#         # Simulate background task checking expiration
#         if timezone.now() > reservation.expires_at:
#             reservation.is_expired = True
#             reservation.save()
        
#         # For this test, manually mark as expired
#         reservation.is_expired = True
#         reservation.save()
        
#         reservation.refresh_from_db()
#         self.assertTrue(reservation.is_expired)

#     def test_get_user_active_reservations(self):
#         """Test getting all active reservations for a user"""
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product,
#             expires_at=timezone.now() + timedelta(hours=48),
#             is_expired=False,
#             is_paid=False
#         )
        
#         WinnerReservation.objects.create(
#             user=self.user,
#             product=self.product2,
#             expires_at=timezone.now() + timedelta(hours=48),
#             is_expired=True,  # Expired
#             is_paid=False
#         )
        
#         active_reservations = WinnerReservation.objects.filter(
#             user=self.user,
#             is_expired=False,
#             is_paid=False
#         )
        
#         self.assertEqual(active_reservations.count(), 1)


# coverage report | gets coverage report
# coverage html | gets coverage report in html. open index.html file in htmlcov directory
# run --omit='*/venv/*' manage.py test | command to run test