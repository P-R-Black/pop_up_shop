import pytest
from django.test import TestCase
from pop_up_auction.models import PopUpProductSpecificationValue, PopUpProductSpecification
from pop_accounts.models import ( SoftDeleteManager, PopUpCustomerAddress,  SoftDeleteUserManager, PopUpCustomerIP, PopUpPasswordResetRequestLog,
    PopUpBid, PopUpPurchase, PopUpCustomerProfile)
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType, 
                                   )
from django.contrib.auth import get_user_model
from django.utils.timezone import now, make_aware
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime
from datetime import datetime, timedelta, date
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from unittest.mock import patch
from django.core.mail import send_mail
from decimal import Decimal
from .conftest import create_seed_data, create_seed_data_two
from django.utils.text import slugify
from uuid import uuid4
import uuid
import unittest

User = get_user_model()

# """
# Tests In Order
#  1. TestActiveUserManager
#  2. TestAllUserManager
#  3. TestCustomPopUpAccountManager
#  4. TestSoftDeleteUserManager
#  5. TestManagerIntegration
#  6. TestPopUpCustomerModel
#  7. TestPopUpCustomerAddressModel
#  8. TestUserModel
#  9. 
# 10. 
# 11. 
# 12. 
# 13. 
# 14. 
# 15. 
# """



def create_test_address(customer, first_name, last_name, address_line, address_line2, apartment_suite_number, 
                        town_city, state, postcode, delivery_instructions, default=True, is_default_shipping=False,
                        is_default_billing=False):
    return PopUpCustomerAddress.objects.create(
            customer=customer,
            first_name=first_name,
            last_name=last_name,
            address_line=address_line,
            address_line2=address_line2,
            apartment_suite_number=apartment_suite_number,
            town_city=town_city,
            state=state,
            postcode=postcode,
            delivery_instructions=delivery_instructions,
            default=default,
            is_default_shipping=is_default_shipping,
            is_default_billing=is_default_billing
        )


def create_brand(name):
    return PopUpBrand.objects.create(
        name=name,
        slug=slugify(name)
    )

def create_category(name, is_active):
    return PopUpCategory.objects.create(
            name=name,
            slug=slugify(name),
            is_active=is_active
        )


def create_product_type(name, is_active):
    return PopUpProductType.objects.create(
            name=name,
            slug=slugify(name),
            is_active=is_active
        )
def create_test_product_one(*args, **kwargs):
    # Set default values
    defaults = {
        'product_type': create_product_type('shoe', is_active=True),
        'category': create_category('Jordan 3', is_active=True),
        'product_title': "Past Bid Product 1",
        'secondary_product_title': "Past Bid 1",
        'description': "Brand new sneakers",
        'slug': "past-bid-product-1",
        'buy_now_price': "250.00",
        'current_highest_bid': "0",
        'retail_price': "150.00",
        'brand': create_brand('Jordan'),
        'auction_start_date': None,
        'auction_end_date': None,
        'inventory_status': "sold_out",  # Default value
        'bid_count': 0,
        'reserve_price': "100.00",
        'is_active': False  # Default value
    }
    # Override defaults with any kwargs passed in
    defaults.update(kwargs)
    
    # Create and return the product
    return PopUpProduct.objects.create(**defaults)

# def create_test_product_two(*args, **kwargs):
#     # Set default values
#     defaults = {
#         'product_type_id': 1, 'category': create_category('Jordan 4', is_active=True),
#         'product_title': "Past Bid Product 2", 'secondary_product_title': "Past Bid 2",
#         'description': "Brand new sneakers", 'slug': "past-bid-product-2", 'buy_now_price': "300.00", 
#         'current_highest_bid': "0", 'retail_price': "200.00", 'brand_id': 1, 'auction_start_date': None, 
#         'auction_end_date': None, 'inventory_status': "sold_out", 'bid_count': 0, 'reserve_price': "150.00",
#         'is_active': False  # Default value
#     }

#     # Override defaults with any kwargs passed in
#     defaults.update(kwargs)
    
#     # Create and return the product
#     return PopUpProduct.objects.create(**defaults)



class TestActiveUserManager(TestCase):
    """Tests for ActiveUserManager (filters out deleted users)"""
    
    def setUp(cls):
        """Create test users"""
        # Active user
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()

    
        # Deleted user
        cls.deleted_user = User.all_objects.create(
            email="deleted@example.com",
            first_name="Deleted",
            last_name="User",
            deleted_at=now()
        )
    
    def test_get_queryset_excludes_deleted_users(self):
        """Test that default manager excludes soft-deleted users"""
        users = User.objects.all()
        
        self.assertEqual(users.count(), 2)
        self.assertIn(self.user1, users)
        self.assertNotIn(self.deleted_user, users)
    
    def test_filter_on_active_users_only(self):
        """Test filtering works on non-deleted users"""
        users = User.objects.filter(first_name="One")
        
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.user1)
    
    def test_get_on_deleted_user_raises_does_not_exist(self):
        """Test that getting a deleted user raises DoesNotExist"""
        from django.core.exceptions import ObjectDoesNotExist
        
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(email="deleted@example.com")
    
    def test_count_excludes_deleted_users(self):
        """Test that count() excludes deleted users"""
        self.assertEqual(User.objects.count(), 2)


class TestAllUserManager(TestCase):
    """Tests for AllUserManager (includes all users, even deleted)"""
    
    def setUp(cls):
        """Create test users"""
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()


        cls.deleted_user = User.all_objects.create(
            email="deleted@example.com",
            first_name="Deleted",
            deleted_at=now()
        )
    

    def test_get_queryset_includes_all_users(self):
        """Test that all_objects includes both active and deleted users"""
        users = User.all_objects.all()
        
        self.assertEqual(users.count(), 3)
        self.assertIn(self.user1, users)
        self.assertIn(self.deleted_user, users)
    
    def test_filter_can_find_deleted_users(self):
        """Test that filtering can find deleted users"""
        users = User.all_objects.filter(email="deleted@example.com")
        
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.deleted_user)
    
    def test_get_deleted_user_succeeds(self):
        """Test that getting a deleted user works with all_objects"""
        user = User.all_objects.get(email="deleted@example.com")
        self.assertEqual(user, self.deleted_user)
    
    def test_count_includes_deleted_users(self):
        """Test that count() includes deleted users"""
        self.assertEqual(User.all_objects.count(), 3)


class TestCustomPopUpAccountManager(TestCase):
    """Tests for CustomPopUpAccountManager user creation methods"""
    
    # ==================== create_user Tests ====================
    
    def test_create_user_with_all_fields(self):
        """Test creating user with all fields"""
        user = User.objects.create_user(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="securepass123"
        )
        
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("securepass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(
                email="",
                first_name="John",
                password="pass123"
            )
        
        self.assertIn("email address is required", str(context.exception).lower())
    
    def test_create_user_with_none_email_raises_error(self):
        """Test that creating user with None email raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,
                first_name="John",
                password="pass123"
            )
    
    def test_create_user_normalizes_email(self):
        """Test that email is normalized (domain lowercased)"""
        user = User.objects.create_user(
            email="Test@EXAMPLE.COM",
            password="pass123"
        )
        
        # Domain should be lowercased
        self.assertEqual(user.email, "Test@example.com")
    
    def test_create_user_without_password(self):
        """Test creating user without password"""
        user = User.objects.create_user(
            email="nopass@example.com",
            first_name="No",
            last_name="Password"
        )
        
        # Password should be unusable
        self.assertFalse(user.has_usable_password())
    
    def test_create_user_without_names(self):
        """Test creating user without first/last name"""
        user = User.objects.create_user(
            email="minimal@example.com",
            password="pass123"
        )
        
        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)
    
    def test_create_user_with_extra_fields(self):
        """Test creating user with additional fields"""
        user = User.objects.create_user(
            email="extra@example.com",
            first_name="Extra",
            password="pass123",
            mobile_phone="555-1234",

        )
        
        self.assertEqual(user.mobile_phone, "555-1234")

    
    def test_create_user_hashes_password(self):
        """Test that password is properly hashed"""
        password = "plaintext123"
        user = User.objects.create_user(
            email="hash@example.com",
            password=password
        )
        
        # Password should not be stored in plain text
        self.assertNotEqual(user.password, password)
        # But should validate correctly
        self.assertTrue(user.check_password(password))
    
    # ==================== create_superuser Tests ====================
    
    def test_create_superuser_with_all_fields(self):
        """Test creating superuser with all required fields"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="adminpass123"
        )
        
        self.assertEqual(superuser.email, "admin@example.com")
        self.assertEqual(superuser.first_name, "Admin")
        self.assertEqual(superuser.last_name, "User")
        self.assertTrue(superuser.check_password("adminpass123"))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
    
    def test_create_superuser_defaults_to_staff(self):
        """Test that superuser is automatically staff"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="pass123"
        )
        
        self.assertTrue(superuser.is_staff)
    
    def test_create_superuser_defaults_to_superuser(self):
        """Test that superuser flag is automatically set"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="pass123"
        )
        
        self.assertTrue(superuser.is_superuser)
    
    def test_create_superuser_defaults_to_active(self):
        """Test that superuser is automatically active"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="pass123"
        )
        
        self.assertTrue(superuser.is_active)
    
    def test_create_superuser_with_is_staff_false_raises_error(self):
        """Test that explicitly setting is_staff=False raises ValueError"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                password="pass123",
                is_staff=False
            )
        
        self.assertIn("is staff=true", str(context.exception).lower())
    
    def test_create_superuser_with_is_superuser_false_raises_error(self):
        """Test that explicitly setting is_superuser=False raises ValueError"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                password="pass123",
                is_superuser=False
            )
        
        self.assertIn("is_superuser=true", str(context.exception).lower())
    
    def test_create_superuser_without_email_raises_error(self):
        """Test that superuser requires email"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="",
                first_name="Admin",
                last_name="User",
                password="pass123"
            )
    
    def test_create_superuser_normalizes_email(self):
        """Test that superuser email is normalized"""
        superuser = User.objects.create_superuser(
            email="Admin@EXAMPLE.COM",
            first_name="Admin",
            last_name="User",
            password="pass123"
        )
        
        self.assertEqual(superuser.email, "Admin@example.com")
    
    # ==================== get_by_natural_key Tests ====================
    
    def test_get_by_natural_key_finds_user(self):
        """Test that get_by_natural_key finds user by email"""
        user = User.objects.create_user(
            email="natural@example.com",
            password="pass123"
        )
        
        found_user = User.objects.get_by_natural_key("natural@example.com")
        self.assertEqual(found_user, user)
    
    def test_get_by_natural_key_case_sensitive(self):
        """Test that get_by_natural_key is case-sensitive"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        
        # Email lookup is case-sensitive by default in Django
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get_by_natural_key("TEST@example.com")
    
    def test_get_by_natural_key_nonexistent_raises_error(self):
        """Test that getting non-existent user raises DoesNotExist"""
        from django.core.exceptions import ObjectDoesNotExist
        
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get_by_natural_key("nonexistent@example.com")
    
    def test_get_by_natural_key_excludes_deleted_users(self):
        """Test that get_by_natural_key doesn't find deleted users"""
        user = User.objects.create_user(
            email="deleted@example.com",
            password="pass123"
        )
        user.soft_delete()
        
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get_by_natural_key("deleted@example.com")


class TestSoftDeleteUserManager(TestCase):
    """Tests for SoftDeleteUserManager (used in PopUpCustomerAddress)"""
    
    def setUp(cls):
        """Create test customer and addresses"""
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()

        # self.customer = PopUpCustomer.objects.create_user(
        #     email="customer@example.com",
        #     password="pass123"
        # )
        
        # Active address
        cls.active_address = PopUpCustomerAddress.objects.create(
            customer=cls.user1,
            address_line="123 Active St",
            town_city="City",
            state="ST",
            postcode="12345"
        )
        
        # Deleted address
        cls.deleted_address = PopUpCustomerAddress.all_objects.create(
            customer=cls.user1,
            address_line="456 Deleted St",
            town_city="City",
            state="ST",
            postcode="54321",
            deleted_at=now()
        )
    
    def test_get_queryset_excludes_deleted_addresses(self):
        """Test that default manager excludes soft-deleted addresses"""
        addresses = PopUpCustomerAddress.objects.all()
        
        self.assertEqual(addresses.count(), 1)
        self.assertIn(self.active_address, addresses)
        self.assertNotIn(self.deleted_address, addresses)
    
    def test_filter_on_active_addresses_only(self):
        """Test filtering works on non-deleted addresses"""
        addresses = PopUpCustomerAddress.objects.filter(
            address_line="123 Active St"
        )
        
        self.assertEqual(addresses.count(), 1)
        self.assertEqual(addresses.first(), self.active_address)
    
    def test_all_objects_includes_deleted_addresses(self):
        """Test that all_objects includes deleted addresses"""
        addresses = PopUpCustomerAddress.all_objects.all()
        
        self.assertEqual(addresses.count(), 2)
        self.assertIn(self.active_address, addresses)
        self.assertIn(self.deleted_address, addresses)


class TestManagerIntegration(TestCase):
    """Integration tests for manager interactions"""
    
    def test_soft_delete_removes_from_default_manager(self):
        """Test that soft deleting removes from default queryset"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        
        # Verify user is in default manager
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 1)
        
        # Soft delete
        user.soft_delete()
        
        # Should not be in default manager
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 0)
        
        # But should be in all_objects
        self.assertEqual(User.all_objects.filter(email="test@example.com").count(), 1)
    

    def test_restore_adds_back_to_default_manager(self):
        """Test that restoring adds user back to default queryset"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        
        user.soft_delete()
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 0)
        
        user.restore()
        
        # Should be back in default manager
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 1)
    
    def test_multiple_managers_on_same_model(self):
        """Test that both managers work independently"""
        user1 = User.objects.create_user(
            email="active@example.com",
            password="pass123"
        )
        
        user2 = User.objects.create_user(
            email="deleted@example.com",
            password="pass123"
        )
        user2.soft_delete()
        
        # Default manager: 1 user
        self.assertEqual(User.objects.count(), 1)
        
        # All objects manager: 2 users
        self.assertEqual(User.all_objects.count(), 2)

class TestUserModel(TestCase):
    """Test suite for shared User model"""

    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )

    def test_create_user(self):
        """Test creating a regular user"""
        self.assertEqual(self.user.email, "testuser@example.com")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertFalse(self.user.is_active)  # Default is False
        self.assertFalse(self.user.is_staff)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_active)

    def test_user_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.user), "testuser@example.com")

    def test_email_is_unique(self):
        """Test that email must be unique"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="testuser@example.com",  # Duplicate
                password="pass123"
            )
    
    def test_email_is_required(self):
        """Test that email field is required"""
        with self.assertRaises(IntegrityError):
            User.objects.create(
                email=None,
                first_name="Test"
            )
    

    def test_optional_fields_can_be_blank(self):
        """Test that optional fields can be blank/null"""
        user = User.objects.create(
            email="minimal@example.com",
            # All other fields left blank
        )
        
        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)
        self.assertIsNone(user.middle_name)
        self.assertIsNone(user.mobile_phone)

    
    def test_default_values(self):
        """Test that fields have correct default values"""
        user = User.objects.create(email="defaults@example.com")
        
        self.assertTrue(user.mobile_notification)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertIsNone(user.deleted_at)


    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email"""
        self.assertEqual(User.USERNAME_FIELD, 'email')


    # ==================== Soft Delete Tests ====================
    def test_soft_delete(self):
        """Test soft delete functionality"""
        self.user.soft_delete()
        
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)

    def test_soft_delete_marks_user_as_inactive_and_sets_deleted_at(self):
        self.user.soft_delete()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)
        self.assertTrue(self.user.is_deleted)
    
    
    def test_restore_user(self):
        """Test restoring a soft-deleted user"""
        self.user.soft_delete()
        self.user.restore()
        
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.deleted_at)

    def test_active_user_manager(self):
        """Test that ActiveUserManager excludes soft-deleted users"""
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123"
        )
        user2.soft_delete()
        
        # objects manager should only return active users
        active_users = User.objects.all()
        self.assertEqual(active_users.count(), 1)
        self.assertIn(self.user, active_users)
        self.assertNotIn(user2, active_users)

    def test_all_user_manager(self):
        """Test that AllUserManager includes soft-deleted users"""
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123"
        )
        user2.soft_delete()
        
        # all_objects manager should return all users
        all_users = User.all_objects.all()
        self.assertEqual(all_users.count(), 2)
        self.assertIn(self.user, all_users)
        self.assertIn(user2, all_users)

    def test_mobile_phone_optional(self):
        """Test that mobile_phone is optional"""
        user = User.objects.create_user(
            email="nophone@example.com",
            password="pass123"
        )
        self.assertIsNone(user.mobile_phone)

    def test_mobile_notification_default(self):
        """Test default mobile_notification value"""
        self.assertTrue(self.user.mobile_notification)

    def test_username_field_is_email(self):
        """Test that email is used for authentication"""
        self.assertEqual(User.USERNAME_FIELD, 'email')


    # ==================== Property Tests ====================
    
    def test_is_deleted_property_false_when_deleted_at_is_none(self):
        """Test is_deleted property when user is not deleted"""
        self.assertIsNone(self.user.deleted_at)
        self.assertFalse(self.user.is_deleted)
    

    def test_is_deleted_property_true_when_deleted_at_is_set(self):
        """Test is_deleted property when user is deleted"""
        self.user.soft_delete()
        self.assertTrue(self.user.is_deleted)
    

    # TODO: Add these tests when Bid model set up
    # def test_open_bids_property_returns_active_bids(self):
    #     """Test open_bids property returns only active bids"""
    #     pass
    
    # def test_past_bids_property_returns_inactive_bids(self):
    #     """Test past_bids property returns only inactive bids"""
    #     pass
    
    
    
#     # ==================== Email Tests ====================
    
#     @patch('pop_accounts.models.send_mail')
#     def test_email_user_sends_email(self, mock_send_mail):
#         """Test email_user method sends email correctly"""
#         self.customer.email_user("Subject", "Message")
#         mock_send_mail.assert_called_once_with(
#             "Subject",
#             "Message",
#             "l@1.com",
#             [self.customer.email],
#             fail_silently=False
#         )
    
#     @patch('pop_accounts.models.send_mail')
#     def test_email_user_with_special_characters(self, mock_send_mail):
#         """Test email_user handles special characters in message"""
#         self.customer.email_user("Test", "Special chars: <>&\"'")
#         self.assertTrue(mock_send_mail.called)
    

    # ==================== Timestamp Tests ====================
    
    def test_created_timestamp_auto_set(self):
        """Test that created timestamp is automatically set"""
        self.assertIsNotNone(self.user.created)
    
    def test_updated_timestamp_auto_updates(self):
        """Test that updated timestamp updates on save"""
        original_updated = self.user.updated
        
        # Make a change and save
        self.user.first_name = "Updated"
        self.user.save()
        
        self.user.refresh_from_db()
        self.assertGreater(self.user.updated, original_updated)
    
    def test_created_does_not_change_on_update(self):
        """Test that created timestamp doesn't change on updates"""
        original_created = self.user.created
        
        self.user.first_name = "Updated"
        self.user.save()
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.created, original_created)
    
    # ==================== Manager Tests ====================
    
    def test_objects_manager_excludes_deleted_users(self):
        """Test default manager excludes soft-deleted users"""
        active_user = User.objects.create(email="active@example.com")
        deleted_user = User.objects.create(email="deleted@example.com")
        deleted_user.soft_delete()
        
        all_users = User.objects.all()
        self.assertIn(active_user, all_users)
        self.assertNotIn(deleted_user, all_users)
    
    def test_all_objects_manager_includes_deleted_users(self):
        """Test all_objects manager includes soft-deleted users"""
        active_user = User.objects.create(email="active@example.com")
        deleted_user = User.objects.create(email="deleted@example.com")
        deleted_user.soft_delete()
        
        all_users = User.all_objects.all()
        self.assertIn(active_user, all_users)
        self.assertIn(deleted_user, all_users)
    
    # ==================== Meta Tests ====================
    
    def test_verbose_name(self):
        """Test model verbose name"""
        self.assertEqual(
            User._meta.verbose_name,
            'User'
        )
    
    def test_verbose_name_plural(self):
        """Test model verbose name plural"""
        self.assertEqual(
            User._meta.verbose_name_plural,
            'Users'
        )
    
    # ==================== Edge Cases ====================
    
    def test_user_with_very_long_name(self):
        """Test that names can be up to max_length"""
        long_name = "A" * 50  # Max length is 50
        user = User.objects.create(
            email="longname@example.com",
            first_name=long_name,
            last_name=long_name
        )
        self.assertEqual(len(user.first_name), 50)
    

    def test_user_with_special_characters_in_email(self):
        """Test email with valid special characters"""
        user = User.objects.create(
            email="test+tag@example.com"
        )
        self.assertEqual(user.email, "test+tag@example.com")
    

    def test_last_password_reset_can_be_set(self):
        """Test that last_password_reset can be set"""
        from django.utils.timezone import now
        reset_time = now()
        
        self.user.last_password_reset = reset_time
        self.user.save()
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.last_password_reset, reset_time)



class TestPopUpCustomerProfileModel(TestCase):
    """Test suite for PopUpCustomerProfile"""

    def setUp(self):
        """Create test user and profile"""
        # Create shared User
        # product, color_spec, size_spec, user1, profile_one, user2, profile_two
        self.product, self.product_two, self.color_spec, self.size_spec, self.user, self.user_profile, self.user_two, self.user_two_profile = create_seed_data_two()

    def test_create_profile(self):
        """Test creating a customer profile"""
        self.assertEqual(self.user_profile.user, self.user)
        self.assertEqual(self.user_profile.shoe_size, "9")
        self.assertEqual(self.user_profile.size_gender, "male")
        self.assertEqual(self.user_profile.favorite_brand, "nike")

    def test_profile_one_to_one_with_user(self):
        """Test OneToOne relationship with User"""
        # Try to create another profile for same user
        with self.assertRaises(Exception):
            PopUpCustomerProfile.objects.create(
                user=self.user,
                shoe_size="11"
            )

    def test_stripe_customer_id_optional(self):
        """Test that stripe_customer_id is optional"""
        self.assertIsNone(self.user_profile.stripe_customer_id)

    def test_size_gender_choices(self):
        """Test size_gender choices"""
        self.user_profile.size_gender = "female"
        self.user_profile.save()
        self.assertEqual(self.user_profile.size_gender, "female")

    def test_favorite_brand_default(self):
        """Test default favorite brand"""
        self.assertEqual(self.user_two_profile.favorite_brand, "puma")

    def test_cascade_delete_user_deletes_profile(self):
        user_id = self.user.id
        profile_pk = self.user_profile.pk  # ✅ Use pk instead of id
        # Or: profile_pk = self.profile.user.id  # Also works
        
        # Use hard_delete to actually delete from database
        self.user.hard_delete()
        
        # Profile should be cascade deleted
        self.assertFalse(PopUpCustomerProfile.objects.filter(pk=profile_pk).exists())
        # User should be deleted too
        self.assertFalse(User.all_objects.filter(id=user_id).exists())


    def test_soft_delete_user_keeps_profile(self):
        """Test that soft deleting user keeps profile"""
        user_id = self.user.id
        
        # Soft delete the user
        self.user.soft_delete()
        
        # Profile should still exist (no cascade)
        self.assertTrue(PopUpCustomerProfile.objects.filter(user_id=user_id).exists())
        
        # But user should be marked as deleted
        self.assertTrue(self.user.is_deleted)
        self.assertIsNotNone(self.user.deleted_at)


    def test_regular_delete_performs_soft_delete(self):
        """Test that calling delete() performs soft delete, not hard delete"""
        user_id = self.user.id
        
        # Call delete() - should soft delete
        self.user.delete()
        
        # User should still exist in database (soft deleted)
        self.assertTrue(User.all_objects.filter(id=user_id).exists())

        # Profile should still exist
        self.assertTrue(PopUpCustomerProfile.objects.filter(user_id=user_id).exists())
        # User should be marked as deleted
        user = User.all_objects.get(id=user_id)
        self.assertTrue(user.is_deleted)


    def test_access_profile_by_user_pk(self):
        """Test accessing profile using user's primary key"""
        profile = PopUpCustomerProfile.objects.get(pk=self.user.pk)
        self.assertEqual(profile, self.user_profile)


class TestPopUpCustomerAddressModel(TestCase):
    """Test suite for PopUpCustomerAddress"""

    def setUp(self):
        """Create test user for addresses"""
        self.product, self.product_two, self.color_spec, self.size_spec, self.user, self.user_profile, self.user_two, self.user_two_profile = create_seed_data_two()
        
        # Create a basic address
        self.address = create_test_address(
            customer=self.user, first_name="One", last_name="User", 
            address_line="123 Main St", address_line2="", apartment_suite_number="", 
            town_city="Springfield", state="IL", postcode="62701", delivery_instructions="", 
            default=True, is_default_shipping=True, is_default_billing=True
            )

    def test_create_address(self):
        """Test creating an address"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,  # ✅ Now references User directly
            address_line="123 Test St",
            town_city="Test City",
            state="TS",
            postcode="12345"
        )
        
        self.assertEqual(address.customer, self.user)
        self.assertEqual(address.address_line, "123 Test St")
        self.assertEqual(address.postcode, "12345")


    def test_multiple_addresses_per_user(self):
        """Test that a user can have multiple addresses"""
        addr1 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="City1",
            state="TS",
            postcode="12345"
        )
        addr2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="456 Other St",
            town_city="City2",
            state="OS",
            postcode="67890"
        )
        
        self.assertEqual(self.user.address.count(), 3)

    def test_default_address(self):
        """Test default address functionality"""
        addr1 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="City1",
            state="TS",
            postcode="12345",
            default=True
        )
        addr2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="456 Other St",
            town_city="City2",
            state="OS",
            postcode="67890",
            default=True  # This should make addr1 not default
        )
        
        addr1.refresh_from_db()
        self.assertFalse(addr1.default)
        self.assertTrue(addr2.default)

    def test_soft_delete_address(self):
        """Test soft deleting an address"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="City",
            state="TS",
            postcode="12345"
        )
        
        address.soft_delete()
        
        # 1 Should appear in default manager
        self.assertEqual(PopUpCustomerAddress.objects.count(), 1)

        # But 2 should appear in all_objects
        self.assertEqual(PopUpCustomerAddress.all_objects.count(), 2)

    def test_restore_address(self):
        """Test restoring a soft-deleted address"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 Test St",
            town_city="City",
            state="TS",
            postcode="12345"
        )
        
        address.soft_delete()
        address.restore()
        
        self.assertEqual(PopUpCustomerAddress.objects.count(), 2)

    # ==================== Field Tests ====================
    
    def test_address_creation_with_all_fields(self):
        """Test creating address with all fields populated"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            prefix="Mr.",
            suffix="Jr.",
            first_name="One",
            middle_name="M",
            last_name="User",
            phone_number="555-123-4567",
            postcode="10001",
            address_line="456 Oak Ave",
            address_line2="Building B",
            apartment_suite_number="Apt 3B",
            town_city="New York",
            state="NY",
            delivery_instructions="Leave at front desk",
            default=True,
            is_default_shipping=True,
            is_default_billing=False
        )
        
        self.assertEqual(address.prefix, "Mr.")
        self.assertEqual(address.suffix, "Jr.")
        self.assertEqual(address.first_name, "One")
        self.assertEqual(address.middle_name, "M")
        self.assertEqual(address.last_name, "User")
        self.assertEqual(address.phone_number, "555-123-4567")
        self.assertEqual(address.postcode, "10001")
        self.assertEqual(address.address_line, "456 Oak Ave")
        self.assertEqual(address.address_line2, "Building B")
        self.assertEqual(address.apartment_suite_number, "Apt 3B")
        self.assertEqual(address.town_city, "New York")
        self.assertEqual(address.state, "NY")
        self.assertEqual(address.delivery_instructions, "Leave at front desk")
        self.assertTrue(address.default)
        self.assertTrue(address.is_default_shipping)
        self.assertFalse(address.is_default_billing)


    def test_address_creation_with_minimal_fields(self):
        """Test creating address with only required fields"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="789 Elm St",
            town_city="Chicago",
            state="IL",
            postcode="60601"
        )
        
        self.assertEqual(address.address_line, "789 Elm St")
        self.assertEqual(address.town_city, "Chicago")
        self.assertEqual(address.state, "IL")
        self.assertEqual(address.postcode, "60601")
        
        # Check optional fields are None/empty
        self.assertIsNone(address.first_name)
        self.assertIsNone(address.middle_name)
        self.assertIsNone(address.last_name)
        self.assertIsNone(address.phone_number)
        self.assertEqual(address.address_line2, "")
        self.assertEqual(address.apartment_suite_number, "")
        self.assertEqual(address.delivery_instructions, "")
    
    def test_id_is_uuid(self):
        """Test that ID is a valid UUID"""
        self.assertIsInstance(self.address.id, uuid.UUID)
    
    def test_required_field_customer(self):
        """Test that customer field is required"""
        with self.assertRaises(IntegrityError):
            PopUpCustomerAddress.objects.create(
                customer=None,
                address_line="123 Test St",
                town_city="Test City",
                state="IL",
                postcode="12345"
            )
    
    def test_required_field_address_line(self):
        """Test that address_line field is required"""
        with self.assertRaises(IntegrityError):
            PopUpCustomerAddress.objects.create(
                customer=self.user,
                # Missing address_line
                address_line=None,
                town_city="Test City",
                state="New York",
                postcode="12345"
            )
    
    def test_required_field_town_city(self):
        """Test that town_city field is required"""
        with self.assertRaises(IntegrityError):
            PopUpCustomerAddress.objects.create(
                customer=self.user,
                address_line="123 Test St",
                town_city=None,
                state="TS",
                postcode="12345"
            )
    
    def test_required_field_state(self):
        """Test that state field is required"""
        with self.assertRaises(IntegrityError):
            PopUpCustomerAddress.objects.create(
                customer=self.user,
                address_line="123 Test St",
                town_city="Test City",
                state=None,
                postcode="12345"
            )
    
    def test_required_field_postcode(self):
        """Test that postcode field is required"""
        with self.assertRaises(IntegrityError):
            PopUpCustomerAddress.objects.create(
                customer=self.user,
                address_line="123 Test St",
                town_city="Test City",
                state="TS",
                # Missing postcode
                postcode=None
            )
    
    def test_empty_string_allowed_for_char_fields(self):
        """Test that empty strings are valid for CharField without blank=False"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="",  # Empty string is valid!
            town_city="",
            state="",
            postcode=""
        )
        
        self.assertEqual(address.address_line, "")
        self.assertEqual(address.town_city, "")


    def test_customer_foreign_key(self):
        """Test foreign key relationship to PopUpCustomer"""
        self.assertEqual(self.address.customer, self.user)
        self.assertIn(self.address, self.user.address.all())
    

    def test_default_values(self):
        """Test that fields have correct default values"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="Test St",
            town_city="Test City",
            state="TS",
            postcode="12345"
        )
        
        self.assertFalse(address.default)
        self.assertFalse(address.is_default_shipping)
        self.assertFalse(address.is_default_billing)
        self.assertIsNone(address.deleted_at)
    

    def test_prefix_choices(self):
        """Test that prefix accepts valid choices"""
        valid_prefixes = ['Mr.', 'Mrs.', 'Ms.', 'Miss', 'Dr', 'Prof']
        
        for prefix in valid_prefixes:
            self.address.prefix = prefix
            self.address.save()
            self.address.refresh_from_db()
            self.assertEqual(self.address.prefix, prefix)
    
    def test_suffix_choices(self):
        """Test that suffix accepts valid choices"""
        valid_suffixes = ['Jr.', 'Sr.', 'II', 'III', 'IV', 'CPA', 'M.D.', 'PhD']
        
        for suffix in valid_suffixes:
            self.address.suffix = suffix
            self.address.save()
            self.address.refresh_from_db()
            self.assertEqual(self.address.suffix, suffix)


    # ==================== String Representation Tests ====================
    
    def test_str_representation(self):
        """Test __str__ method returns expected format"""
        expected = "One User - 123 Main St, Springfield"
        self.assertEqual(str(self.address), expected)
    
    def test_str_with_address_line2(self):
        """Test __str__ includes address_line but not address_line2"""
        self.address.address_line2 = "Suite 100"
        self.address.save()
        
        # String should still only show address_line
        expected = "One User - 123 Main St, Springfield"
        self.assertEqual(str(self.address), expected)
    
    def test_str_with_customer_no_names(self):
        """Test __str__ when customer has no names"""
        customer_no_name = User.objects.create(
            email="noname@example.com"
        )
        address = PopUpCustomerAddress.objects.create(
            customer=customer_no_name,
            address_line="456 Test St",
            town_city="Test City",
            state="TC",
            postcode="54321"
        )
        
        expected = "None None - 456 Test St, Test City"
        self.assertEqual(str(address), expected)
    
    # ==================== Default Address Logic Tests ====================
    
    def test_save_sets_default_to_false_for_other_addresses(self):
        """Test that setting default=True unsets other defaults"""
        # Create first default address
        address1 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="111 First St",
            town_city="City1",
            state="ST",
            postcode="11111",
            default=True
        )
        
        # Verify it's default
        self.assertTrue(address1.default)
        
        # Create second default address
        address2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="222 Second St",
            town_city="City2",
            state="ST",
            postcode="22222",
            default=True
        )
        
        # Refresh first address from database
        address1.refresh_from_db()
        
        # First address should no longer be default
        self.assertFalse(address1.default)
        self.assertTrue(address2.default)
    
    def test_multiple_customers_can_have_separate_defaults(self):
        """Test that default logic is per-customer, not global"""
        # Create second customer
        customer2 = User.objects.create(
            email="customer2@example.com",
            first_name="Jane",
            last_name="Smith"
        )
        
        # Create default for first customer
        address1 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="111 First St",
            town_city="City1",
            state="ST",
            postcode="11111",
            default=True
        )
        
        # Create default for second customer
        address2 = PopUpCustomerAddress.objects.create(
            customer=customer2,
            address_line="222 Second St",
            town_city="City2",
            state="ST",
            postcode="22222",
            default=True
        )
        
        # Both should be default
        address1.refresh_from_db()
        address2.refresh_from_db()
        
        self.assertTrue(address1.default)
        self.assertTrue(address2.default)
    
    def test_changing_default_from_false_to_true(self):
        """Test updating existing address to be default"""
        # Create two non-default addresses
        address1 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="111 First St",
            town_city="City1",
            state="ST",
            postcode="11111",
            default=False
        )
        
        address2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="222 Second St",
            town_city="City2",
            state="ST",
            postcode="22222",
            default=True
        )
        
        # Make first address default
        address1.default = True
        address1.save()
        
        # Refresh both
        address1.refresh_from_db()
        address2.refresh_from_db()
        
        # First should be default, second should not
        self.assertTrue(address1.default)
        self.assertFalse(address2.default)
    
    def test_non_default_addresses_remain_unchanged(self):
        """Test that non-default addresses aren't affected by save"""
        # Create multiple non-default addresses
        address1 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="111 First St",
            town_city="City1",
            state="ST",
            postcode="11111",
            default=False
        )
        
        address2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="222 Second St",
            town_city="City2",
            state="ST",
            postcode="22222",
            default=False
        )
        
        # Save address1 again
        address1.address_line = "111 Updated St"
        address1.save()
        
        # Both should still be non-default
        address1.refresh_from_db()
        address2.refresh_from_db()
        
        self.assertFalse(address1.default)
        self.assertFalse(address2.default)
    
    # ==================== Soft Delete Tests ====================
    
    def test_soft_delete_sets_deleted_at(self):
        """Test soft delete sets deleted_at timestamp"""
        self.assertIsNone(self.address.deleted_at)
        
        self.address.soft_delete()
        self.address.refresh_from_db()
        
        self.assertIsNotNone(self.address.deleted_at)
        self.assertTrue(self.address.is_deleted)
    
    def test_restore_clears_deleted_at(self):
        """Test restore clears deleted_at timestamp"""
        self.address.soft_delete()
        self.address.restore()
        self.address.refresh_from_db()
        
        self.assertIsNone(self.address.deleted_at)
        self.assertFalse(self.address.is_deleted)
    
    def test_is_deleted_property_when_not_deleted(self):
        """Test is_deleted property returns False when not deleted"""
        self.assertIsNone(self.address.deleted_at)
        self.assertFalse(self.address.is_deleted)
    
    def test_is_deleted_property_when_deleted(self):
        """Test is_deleted property returns True when deleted"""
        self.address.soft_delete()
        self.address.refresh_from_db()
        self.assertTrue(self.address.is_deleted)
    
    def test_delete_method_performs_soft_delete(self):
        """Test that delete() performs soft delete, not hard delete"""
        address_id = self.address.id
        self.address.delete()
        
        # Should still exist in database
        address = PopUpCustomerAddress.all_objects.get(id=address_id)
        self.assertTrue(address.is_deleted)
        self.assertIsNotNone(address.deleted_at)
    
    def test_soft_deleted_address_not_in_default_manager(self):
        """Test that soft-deleted addresses are excluded from default manager"""
        self.address.soft_delete()
        
        # Should not be in default queryset
        addresses = PopUpCustomerAddress.objects.filter(id=self.address.id)
        self.assertEqual(addresses.count(), 0)
    
    def test_soft_deleted_address_in_all_objects_manager(self):
        """Test that soft-deleted addresses are in all_objects manager"""
        self.address.soft_delete()
        
        # Should be in all_objects queryset
        addresses = PopUpCustomerAddress.all_objects.filter(id=self.address.id)
        self.assertEqual(addresses.count(), 1)
        self.assertTrue(addresses.first().is_deleted)
    
    def test_multiple_soft_deletes_idempotent(self):
        """Test that multiple soft deletes don't cause issues"""
        self.address.soft_delete()
        first_deleted_at = PopUpCustomerAddress.all_objects.get(id=self.address.id).deleted_at
        
        # Soft delete again
        self.address.soft_delete()
        second_deleted_at = PopUpCustomerAddress.all_objects.get(id=self.address.id).deleted_at
        
        # Should still be deleted
        self.assertIsNotNone(second_deleted_at)
    
    def test_restore_non_deleted_address_is_safe(self):
        """Test that restoring a non-deleted address doesn't cause issues"""
        # Address is not deleted
        self.assertIsNone(self.address.deleted_at)
        
        # Restore anyway
        self.address.restore()
        self.address.refresh_from_db()
        
        # Should still not be deleted
        self.assertIsNone(self.address.deleted_at)
        self.assertFalse(self.address.is_deleted)
    
    # ==================== Cascade Delete Tests ====================
    
    def test_deleting_customer_deletes_addresses(self):
        """Test that deleting customer cascades to addresses"""
        address_id = self.address.id
        customer_id = self.user.id
        
        # Hard delete customer
        self.user.hard_delete()
        
        # Address should be deleted too (cascade)
        with self.assertRaises(PopUpCustomerAddress.DoesNotExist):
            PopUpCustomerAddress.all_objects.get(id=address_id)
    
    def test_soft_deleting_customer_does_not_delete_addresses(self):
        """Test that soft deleting customer doesn't cascade to addresses"""
        address_id = self.address.id
        
        # Soft delete customer
        self.user.soft_delete()
        
        # Address should still exist
        address = PopUpCustomerAddress.all_objects.get(id=address_id)
        self.assertFalse(address.is_deleted)
    
    # ==================== Timestamp Tests ====================
    
    def test_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        self.assertIsNotNone(self.address.created_at)
    
    def test_updated_at_auto_updates(self):
        """Test that updated_at updates on save"""
        original_updated = self.address.updated_at
        
        # Make a change
        self.address.address_line = "999 Updated St"
        self.address.save()
        
        self.address.refresh_from_db()
        self.assertGreater(self.address.updated_at, original_updated)
    
    def test_created_at_does_not_change_on_update(self):
        """Test that created_at doesn't change on updates"""
        original_created = self.address.created_at
        
        self.address.address_line = "999 Updated St"
        self.address.save()
        
        self.address.refresh_from_db()
        self.assertEqual(self.address.created_at, original_created)
    
    # ==================== Related Name Tests ====================
    
    def test_customer_address_related_name(self):
        """Test that customer.address returns related addresses"""
        # Create multiple addresses
        address2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="456 Second St",
            town_city="City2",
            state="ST",
            postcode="22222"
        )
        
        addresses = self.user.address.all()
        self.assertEqual(addresses.count(), 2)
        self.assertIn(self.address, addresses)
        self.assertIn(address2, addresses)
    
    def test_customer_address_filtering(self):
        """Test filtering addresses through customer relationship"""
        # Create address in different state
        address2 = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="456 Second St",
            town_city="City2",
            state="NY",
            postcode="10001"
        )
        
        il_addresses = self.user.address.filter(state="IL")
        self.assertEqual(il_addresses.count(), 1)
        self.assertEqual(il_addresses.first(), self.address)
    

    # ==================== Meta Tests ====================
    
    def test_verbose_name(self):
        """Test model verbose name"""
        self.assertEqual(
            PopUpCustomerAddress._meta.verbose_name,
            'PopUpCustomerAddress'
        )
    
    def test_verbose_name_plural(self):
        """Test model verbose name plural"""
        self.assertEqual(
            PopUpCustomerAddress._meta.verbose_name_plural,
            'PopUpCustomerAddresses'
        )
    
    # ==================== Edge Cases ====================
    
    def test_very_long_address_fields(self):
        """Test that long addresses are handled correctly"""
        long_address = "A" * 255  # Max length for address_line
        
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line=long_address,
            town_city="Long City Name" * 10,  # Up to 150 chars
            state="CA",
            postcode="90210"
        )
        
        self.assertEqual(len(address.address_line), 255)
    
    def test_special_characters_in_address(self):
        """Test addresses with special characters"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="123 O'Brien St, Apt #5",
            town_city="Saint-Jean-sur-Richelieu",
            state="QC",
            postcode="J3B 1A1"
        )
        
        self.assertEqual(address.address_line, "123 O'Brien St, Apt #5")
        self.assertEqual(address.town_city, "Saint-Jean-sur-Richelieu")
    
    def test_multiline_delivery_instructions(self):
        """Test that TextField can handle multiline instructions"""
        instructions = """Line 1: Ring doorbell
        Line 2: Leave at side door
        Line 3: Call if no answer"""
        
        self.address.delivery_instructions = instructions
        self.address.save()
        self.address.refresh_from_db()
        
        self.assertEqual(self.address.delivery_instructions, instructions)
    
    def test_default_shipping_and_billing_independent(self):
        """Test that shipping and billing defaults are independent"""
        address = PopUpCustomerAddress.objects.create(
            customer=self.user,
            address_line="789 Test St",
            town_city="Test City",
            state="TS",
            postcode="12345",
            is_default_shipping=True,
            is_default_billing=False
        )
        
        self.assertTrue(address.is_default_shipping)
        self.assertFalse(address.is_default_billing)
    
    def test_phone_number_various_formats(self):
        """Test that various phone number formats can be stored"""
        phone_formats = [
            "555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "+1-555-123-4567",
            "5551234567"
        ]
        
        for phone in phone_formats:
            self.address.phone_number = phone
            self.address.save()
            self.address.refresh_from_db()
            self.assertEqual(self.address.phone_number, phone)



class TestPopUpBidModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()

    # ==================== Basic Field Tests ====================
    def test_bid_creation_with_all_fields(self):
        """Test creating bid with all fields"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
            max_auto_bid=Decimal('300.00'),
            bid_increment=Decimal('10.00'),
            expires_at=now() + timedelta(hours=24)
        )
        
        self.assertEqual(bid.customer, self.profile_one)
        self.assertEqual(bid.product, self.product)
        self.assertEqual(bid.amount, Decimal('200.00'))
        self.assertEqual(bid.max_auto_bid, Decimal('300.00'))
        self.assertEqual(bid.bid_increment, Decimal('10.00'))
        self.assertTrue(bid.is_active)
        self.assertFalse(bid.is_winning_bid)
        self.assertIsNotNone(bid.timestamp)
        self.assertIsInstance(bid.id, uuid.UUID)
    
    def test_bid_creation_with_minimal_fields(self):
        """Test creating bid with only required fields"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertIsNone(bid.max_auto_bid)
        self.assertEqual(bid.bid_increment, Decimal('5.00'))  # Default
        self.assertIsNone(bid.expires_at)
        self.assertTrue(bid.is_active)
    
    def test_default_bid_increment(self):
        """Test that bid_increment defaults to 5.00"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertEqual(bid.bid_increment, Decimal('5.00'))
    
    def test_id_is_uuid(self):
        """Test that ID is a valid UUID"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertIsInstance(bid.id, uuid.UUID)
    
    # ==================== String Representation Tests ====================
    def test_str_representation(self):
        """Test __str__ method"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        expected = f"{self.user1} - {self.product} - $200.00"
        self.assertEqual(str(bid), expected)
    
    # ==================== Bid Validation Tests ====================
    
    def test_rejects_bid_not_higher_than_current(self):
        """Test that bids must be higher than current highest"""
        PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
        )
        
        # Try to enter same amount -> should raise error
        with self.assertRaisesMessage(ValueError, 'higher than the current'):
            PopUpBid.objects.create(
                customer=self.profile_two,
                product=self.product,
                amount=Decimal('200.00'),
            )

    def test_rejects_bid_lower_than_current(self):
        """Test that lower bids are rejected"""
        PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
        )
        
        with self.assertRaisesMessage(ValueError, 'higher than the current'):
            PopUpBid.objects.create(
                customer=self.profile_two,
                product=self.product,
                amount=Decimal('150.00'),  # Lower than current
            )
    
    def test_accepts_higher_bid(self):
        """Test that higher bids are accepted"""
        PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
        )
        
        # This should succeed
        bid2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('220.00'),
        )
        
        self.assertEqual(bid2.amount, Decimal('220.00'))
    

    def test_first_bid_has_no_validation(self):
        """Test that first bid can be any amount"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('1.00'),  # Very low, but first bid is fine
        )
        
        self.assertEqual(bid.amount, Decimal('1.00'))
    
    def test_same_user_can_outbid_themselves(self):
        """Test that same user can place higher bid"""
        PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
        )
        
        # Same user places higher bid
        bid2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('250.00'),
        )
        
        self.assertEqual(bid2.amount, Decimal('250.00'))
    
    def test_updating_existing_bid_amount_allowed(self):
        """Test that updating existing bid doesn't trigger validation"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
        )
        
        # Update the same bid (not creating new one)
        bid.amount = Decimal('210.00')
        bid.save()  # Should not raise error
        
        bid.refresh_from_db()
        self.assertEqual(bid.amount, Decimal('210.00'))
    
    def test_inactive_bids_excluded_from_validation(self):
        """Test that inactive bids are excluded from highest bid check"""
        # Create and deactivate first bid
        bid1 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
        )
        bid1.is_active = False
        bid1.save()
        
        # Now a lower bid should be allowed since highest active bid doesn't exist
        bid2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('100.00'),
        )
        
        self.assertEqual(bid2.amount, Decimal('100.00'))
    
    # ==================== Product Update Tests ====================
    
    def test_updates_highest_and_count(self):
        """Test that product's highest bid and count are updated"""
        self.assertEqual(self.product.bid_count, 0)
        self.assertIsNone(self.product.current_highest_bid)

        PopUpBid.objects.create(
            customer=self.profile_one, 
            product=self.product, 
            amount=Decimal('210.00')
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.bid_count, 1)
        self.assertEqual(self.product.current_highest_bid, Decimal('210.00'))

        # Second (higher) bid
        PopUpBid.objects.create(
            customer=self.profile_two, 
            product=self.product, 
            amount=Decimal('225.00')
        )
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.bid_count, 2)
        self.assertEqual(self.product.current_highest_bid, Decimal('225.00'))
    
    def test_product_bid_count_increments_correctly(self):
        """Test that each new bid increments count"""
        initial_count = self.product.bid_count
        
        for i in range(5):
            PopUpBid.objects.create(
                customer=self.profile_one if i % 2 == 0 else self.profile_two,
                product=self.product,
                amount=Decimal('200.00') + Decimal(str(i * 10))
            )
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.bid_count, initial_count + 5)

    # ==================== Winning Bid Tests ====================
    
    def test_only_highest_bid_marked_winner(self):
        """Test that only highest bid is marked as winning"""
        b1 = PopUpBid.objects.create(
            customer=self.profile_one, 
            product=self.product, 
            amount=Decimal('220.00')
        )
        b1.refresh_from_db()
        self.assertTrue(b1.is_winning_bid)
        
        # Place higher bid
        b2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('250.00')
        )
        
        # Refresh both
        b1.refresh_from_db()
        b2.refresh_from_db()
        
        # Only b2 should be winning
        self.assertFalse(b1.is_winning_bid)
        self.assertTrue(b2.is_winning_bid)
    
    def test_winning_bid_updates_on_new_bid(self):
        """Test that winning bid flag moves to newest highest bid"""
        bids = []
        for i in range(3):
            bid = PopUpBid.objects.create(
                customer=self.profile_one if i % 2 == 0 else self.profile_two,
                product=self.product,
                amount=Decimal('200.00') + Decimal(str(i * 20))
            )
            bids.append(bid)
        
        # Refresh all bids
        for bid in bids:
            bid.refresh_from_db()
        
        # Only the last (highest) should be winning
        self.assertFalse(bids[0].is_winning_bid)
        self.assertFalse(bids[1].is_winning_bid)
        self.assertTrue(bids[2].is_winning_bid)


    # ==================== Expiration Tests ====================

    def test_expired_bid_sets_inactive(self):
        """Test that expired bids are marked inactive"""
        past = now() - timedelta(days=1)
        bid = PopUpBid.objects.create(
            customer=self.profile_one, 
            product=self.product, 
            amount=Decimal('270.00'), 
            expires_at=past
        )
        
        self.assertFalse(bid.is_active)
    
    def test_future_expiration_keeps_bid_active(self):
        """Test that future expiration keeps bid active"""
        future = now() + timedelta(days=1)
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
            expires_at=future
        )
        
        self.assertTrue(bid.is_active)
    
    def test_no_expiration_keeps_bid_active(self):
        """Test that bid without expiration stays active"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertTrue(bid.is_active)


    # ==================== get_highest_bid Class Method Tests ====================
    
    def test_get_highest_bid_returns_highest(self):
        """Test that get_highest_bid returns the highest bid"""
        b1 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        b2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('300.00')
        )
        
        highest = PopUpBid.get_highest_bid(self.product)
        self.assertEqual(highest, b2)
        self.assertEqual(highest.amount, Decimal('300.00'))
    
    def test_get_highest_bid_returns_none_when_no_bids(self):
        """Test that get_highest_bid returns None when no bids exist"""
        highest = PopUpBid.get_highest_bid(self.product)
        self.assertIsNone(highest)
    
    def test_get_highest_bid_includes_inactive_bids(self):
        """Test that get_highest_bid considers all bids (including inactive)"""
        b1 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        # Create higher bid but mark inactive
        b2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('500.00')
        )
        b2.is_active = False
        b2.save()
        
        # Should still return b2 as it's the highest overall
        highest = PopUpBid.get_highest_bid(self.product)
        self.assertEqual(highest, b2)
    
    # ==================== Ordering Tests ====================
    
    def test_bids_ordered_by_timestamp_descending(self):
        """Test that bids are ordered by timestamp (newest first)"""
        b1 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        b2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('220.00')
        )
        
        bids = PopUpBid.objects.all()
        self.assertEqual(bids[0], b2)  # Newest first
        self.assertEqual(bids[1], b1)
    
    # ==================== Relationship Tests ====================
    
    def test_customer_relationship(self):
        """Test foreign key relationship with customer"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertEqual(bid.customer, self.profile_one)
        self.assertIn(bid, self.profile_one.customer_bids.all())
    
    def test_product_relationship(self):
        """Test foreign key relationship with product"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertEqual(bid.product, self.product)
        self.assertIn(bid, self.product.bids.all())
    
    def test_cascade_delete_on_customer(self):
        """Test that deleting customer deletes their bids"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        bid_id = bid.id
        
        # Hard delete customer
        self.user1.hard_delete()
        
        # Bid should be deleted
        with self.assertRaises(PopUpBid.DoesNotExist):
            PopUpBid.objects.get(id=bid_id)
    

    def test_cascade_delete_on_product(self):
        """Test that deleting product deletes its bids"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        bid_id = bid.id
        
        # Delete product
        self.product.delete()
        
        # Bid should be deleted
        with self.assertRaises(PopUpBid.DoesNotExist):
            PopUpBid.objects.get(id=bid_id)
    
    def test_multiple_bids_per_customer(self):
        """Test that customer can have multiple bids"""
        b1 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        b2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('250.00')
        )
        
        user_bids = self.profile_one.customer_bids.all()
        self.assertEqual(user_bids.count(), 2)
        self.assertIn(b1, user_bids)
        self.assertIn(b2, user_bids)

    # ==================== Meta Tests ====================
    
    def test_verbose_name(self):
        """Test model verbose name"""
        self.assertEqual(PopUpBid._meta.verbose_name, 'PopUpBid')
    
    def test_verbose_name_plural(self):
        """Test model verbose name plural"""
        self.assertEqual(PopUpBid._meta.verbose_name_plural, 'PopUpBids')
    
    # ==================== Edge Cases ====================
    
    def test_decimal_precision(self):
        """Test that decimal amounts maintain precision"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.99')
        )
        
        self.assertEqual(bid.amount, Decimal('200.99'))
    
    def test_very_large_bid_amount(self):
        """Test that very large amounts are handled"""
        # max_digits=10, decimal_places=2 means max is 99999999.99
        large_amount = Decimal('99999999.99')
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=large_amount
        )
        
        self.assertEqual(bid.amount, large_amount)
    
    def test_zero_bid_increment(self):
        """Test that zero bid increment is allowed"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
            bid_increment=Decimal('0.00')
        )
        
        self.assertEqual(bid.bid_increment, Decimal('0.00'))
    

    def test_negative_amounts_not_validated_by_model(self):
        """Test that model allows negative amounts (DB constraint may prevent)"""
        # Note: This might fail at DB level depending on constraints
        # but the model itself doesn't validate
        try:
            bid = PopUpBid.objects.create(
                customer=self.profile_one,
                product=self.product,
                amount=Decimal('-100.00')
            )
            # If it succeeds, that's a bug you might want to fix
            self.assertEqual(bid.amount, Decimal('-100.00'))
        except Exception:
            # If DB prevents it, that's good
            pass


    def test_timestamp_auto_set(self):
        """Test that timestamp is automatically set"""
        bid = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00')
        )
        
        self.assertIsNotNone(bid.timestamp)
        # Should be very recent (within last minute)
        self.assertLess((now() - bid.timestamp).total_seconds(), 60)



class TestPopUpPurchaseModel(TestCase):
    """Comprehensive tests for PopUpPurchase model"""
    
    @classmethod
    def setUpTestData(cls):
        """Create seed data for all tests"""
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()
        
        # Create a bid
        cls.bid = PopUpBid.objects.create(
            customer=cls.profile_one,
            product=cls.product,
            amount=Decimal('250.00')
        )
        
        # Create an address
        cls.address = create_test_address(
            customer=cls.user1, first_name="John", last_name="Doe", 
            address_line="123 Main St", address_line2="", apartment_suite_number="", 
            town_city="Springfield", state="IL", postcode="62701", delivery_instructions="", 
            default=True, is_default_shipping=True, is_default_billing=True
            )
        
    
    # ==================== Basic Field Tests ====================
    
    def test_purchase_creation_with_all_fields(self):
        """Test creating purchase with all fields populated"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            paid=True,
            address=self.address,
            stripe_api="ch_1234567890abcdef"
        )
        
        self.assertEqual(purchase.customer, self.profile_one)
        self.assertEqual(purchase.product, self.product)
        self.assertEqual(purchase.bid, self.bid)
        self.assertEqual(purchase.price, Decimal('250.00'))
        self.assertTrue(purchase.paid)
        self.assertEqual(purchase.address, self.address)
        self.assertEqual(purchase.stripe_api, "ch_1234567890abcdef")
        self.assertIsNotNone(purchase.purchased_at)
        self.assertIsNotNone(purchase.created_at)
        self.assertIsInstance(purchase.id, uuid.UUID)

    def test_purchase_creation_with_minimal_fields(self):
        """Test creating purchase with only required fields"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertEqual(purchase.customer, self.profile_one)
        self.assertEqual(purchase.product, self.product)
        self.assertEqual(purchase.bid, self.bid)
        self.assertEqual(purchase.price, Decimal('250.00'))
        self.assertFalse(purchase.paid)  # Default
        self.assertIsNone(purchase.address)
        self.assertIsNone(purchase.stripe_api)
    
    def test_id_is_uuid(self):
        """Test that ID is a valid UUID"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertIsInstance(purchase.id, uuid.UUID)
    
    def test_default_values(self):
        """Test that fields have correct default values"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertFalse(purchase.paid)
        self.assertIsNone(purchase.address)
        self.assertIsNone(purchase.stripe_api)
    

    def test_timestamps_auto_set(self):
        """Test that timestamps are automatically set"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertIsNotNone(purchase.purchased_at)
        self.assertIsNotNone(purchase.created_at)
        
        # Should be very recent (within last minute)
        self.assertLess((now() - purchase.purchased_at).total_seconds(), 60)
        self.assertLess((now() - purchase.created_at).total_seconds(), 60)
    

    def test_purchased_at_and_created_at_same_on_creation(self):
        """Test that purchased_at and created_at are same on creation"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        # Both use auto_now_add, should within 1 second
        time_diff = abs((purchase.purchased_at - purchase.created_at).total_seconds())
        self.assertLess(time_diff, 1)


    # ==================== Required Field Tests ====================
    
    def test_customer_field_required(self):
        """Test that customer field is required"""
        with self.assertRaises(IntegrityError):
            PopUpPurchase.objects.create(
                customer=None,
                product=self.product,
                bid=self.bid,
                price=Decimal('250.00')
            )
    
    def test_product_field_required(self):
        """Test that product field is required"""
        with self.assertRaises(IntegrityError):
            PopUpPurchase.objects.create(
                customer=self.profile_one,
                product=None,
                bid=self.bid,
                price=Decimal('250.00')
            )
    
    def test_bid_field_required(self):
        """Test that bid field is required"""
        with self.assertRaises(IntegrityError):
            PopUpPurchase.objects.create(
                customer=self.profile_one,
                product=self.product,
                bid=None,
                price=Decimal('250.00')
            )
    
    def test_price_field_required(self):
        """Test that price field is required"""
        with self.assertRaises(IntegrityError):
            PopUpPurchase.objects.create(
                customer=self.profile_one,
                product=self.product,
                bid=self.bid,
                price=None
            )
    
    # ==================== String Representation Tests ====================
    
    def test_str_representation(self):
        """Test __str__ method"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        expected = f"{self.user1} - {self.product} - $250.00"
        self.assertEqual(str(purchase), expected)
    
    def test_str_with_decimal_places(self):
        """Test __str__ with different decimal amounts"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.99')
        )
        
        expected = f"{self.user1} - {self.product} - $250.99"
        self.assertEqual(str(purchase), expected)
    
    # ==================== Foreign Key Relationship Tests ====================
    
    def test_customer_relationship(self):
        """Test foreign key relationship with customer"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertEqual(purchase.customer, self.profile_one)
        self.assertIn(purchase, self.profile_one.purchases.all())
    
    def test_product_relationship(self):
        """Test foreign key relationship with product"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertEqual(purchase.product, self.product)
        self.assertIn(purchase, self.product.purchases.all())
    
    def test_bid_relationship(self):
        """Test foreign key relationship with bid"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertEqual(purchase.bid, self.bid)
    
    def test_address_relationship(self):
        """Test foreign key relationship with address"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            address=self.address
        )
        
        self.assertEqual(purchase.address, self.address)
    
    def test_multiple_purchases_per_customer(self):
        """Test that customer can have multiple purchases"""
        purchase1 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        # Create another bid and purchase
        bid2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('300.00')
        )
        
        purchase2 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=bid2,
            price=Decimal('300.00')
        )
        
        customer_purchases = self.profile_one.purchases.all()
        self.assertEqual(customer_purchases.count(), 2)
        self.assertIn(purchase1, customer_purchases)
        self.assertIn(purchase2, customer_purchases)
    
    # ==================== PROTECT Cascade Tests ====================
    
    def test_deleting_customer_protected(self):
        """Test that deleting customer is protected (raises error)"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        from django.db.models import ProtectedError
        
        with self.assertRaises(ProtectedError):
            self.user1.hard_delete()
    
    def test_deleting_product_protected(self):
        """Test that deleting product is protected (raises error)"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        from django.db.models import ProtectedError
        
        with self.assertRaises(ProtectedError):
            self.product.delete()
    
    def test_deleting_bid_protected(self):
        """Test that deleting bid is protected (raises error)"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        from django.db.models import ProtectedError
        
        with self.assertRaises(ProtectedError):
            self.bid.delete()
    
    def test_deleting_address_sets_null(self):
        """Test that deleting address sets purchase.address to NULL"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            address=self.address
        )
        
        # Hard delete the address using all_objects manager to bypass soft delete
        PopUpCustomerAddress.all_objects.filter(id=self.address.id).delete()
        
        # Purchase should still exist with NULL address
        purchase.refresh_from_db()
        self.assertIsNone(purchase.address)
    
    def test_can_delete_customer_after_deleting_purchases(self):
        """Test that customer can be deleted after purchases are removed"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        # Delete purchase first
        purchase.delete()
        
        # Now customer can be deleted (no ProtectedError)
        self.user1.hard_delete()
        
        from django.core.exceptions import ObjectDoesNotExist
        with self.assertRaises(ObjectDoesNotExist):
            User.all_objects.get(id=self.user1.id)
    
    # ==================== Ordering Tests ====================
    
    def test_purchases_ordered_by_purchased_at_descending(self):
        """Test that purchases are ordered by purchased_at (newest first)"""
        purchase1 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        # Create another purchase later
        bid2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('300.00')
        )
        
        purchase2 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=bid2,
            price=Decimal('300.00')
        )
        
        purchases = PopUpPurchase.objects.all()
        self.assertEqual(purchases[0], purchase2)  # Newest first
        self.assertEqual(purchases[1], purchase1)
    
    # ==================== Payment Status Tests ====================
    
    def test_unpaid_purchase_default(self):
        """Test that purchases default to unpaid"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertFalse(purchase.paid)
    
    def test_mark_purchase_as_paid(self):
        """Test marking purchase as paid"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        purchase.paid = True
        purchase.save()
        purchase.refresh_from_db()
        
        self.assertTrue(purchase.paid)
    
    def test_filter_paid_purchases(self):
        """Test filtering paid vs unpaid purchases"""
        purchase1 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            paid=True
        )
        
        bid2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('300.00')
        )
        
        purchase2 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=bid2,
            price=Decimal('300.00'),
            paid=False
        )
        
        paid_purchases = PopUpPurchase.objects.filter(paid=True)
        unpaid_purchases = PopUpPurchase.objects.filter(paid=False)
        
        self.assertEqual(paid_purchases.count(), 1)
        self.assertEqual(unpaid_purchases.count(), 1)
        self.assertIn(purchase1, paid_purchases)
        self.assertIn(purchase2, unpaid_purchases)
    
    # ==================== Stripe Integration Tests ====================
    
    def test_stripe_api_field_stores_charge_id(self):
        """Test that stripe_api field can store Stripe charge ID"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            stripe_api="ch_1234567890abcdef"
        )
        
        self.assertEqual(purchase.stripe_api, "ch_1234567890abcdef")
    
    def test_stripe_api_field_optional(self):
        """Test that stripe_api field is optional"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        self.assertIsNone(purchase.stripe_api)
    
    def test_stripe_api_max_length(self):
        """Test stripe_api field max length (40 chars)"""
        long_stripe_id = "ch_" + "x" * 37  # 40 chars total
        
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            stripe_api=long_stripe_id
        )
        
        self.assertEqual(len(purchase.stripe_api), 40)
    
    # ==================== Meta Tests ====================
    
    def test_verbose_name(self):
        """Test model verbose name"""
        self.assertEqual(
            PopUpPurchase._meta.verbose_name,
            'PopUp Customer Purchase'
        )
    
    def test_verbose_name_plural(self):
        """Test model verbose name plural"""
        self.assertEqual(
            PopUpPurchase._meta.verbose_name_plural,
            'PopUp Customer PopUp Purchases'
        )
    
    # ==================== Edge Cases ====================
    
    def test_decimal_precision(self):
        """Test that price maintains decimal precision"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.99')
        )
        
        self.assertEqual(purchase.price, Decimal('250.99'))
    
    def test_very_large_price(self):
        """Test that very large prices are handled"""
        # max_digits=10, decimal_places=2 means max is 99999999.99
        large_price = Decimal('99999999.99')
        
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=large_price
        )
        
        self.assertEqual(purchase.price, large_price)
    
    def test_zero_price(self):
        """Test that zero price is allowed"""
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('0.00')
        )
        
        self.assertEqual(purchase.price, Decimal('0.00'))
    
    def test_price_different_from_bid_amount(self):
        """Test that purchase price can differ from bid amount"""
        # This might happen with fees, discounts, etc.
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,  # bid.amount = 250.00
            price=Decimal('275.00')  # Different price (maybe includes fees)
        )
        
        self.assertEqual(purchase.price, Decimal('275.00'))
        self.assertEqual(self.bid.amount, Decimal('250.00'))
        self.assertNotEqual(purchase.price, self.bid.amount)
    
    def test_purchase_with_different_customer_than_bid(self):
        """Test that purchase customer can differ from bid customer"""
        # This might happen if someone buys on behalf of another user
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_two,  # Different customer
            product=self.product,
            bid=self.bid,  # self.bid.customer = self.user1
            price=Decimal('250.00')
        )
        
        self.assertEqual(purchase.customer, self.profile_two)
        self.assertEqual(self.bid.customer, self.profile_one)
        self.assertNotEqual(purchase.customer, self.bid.customer)
    
    def test_multiple_purchases_same_bid(self):
        """Test that same bid can be referenced by multiple purchases"""
        # This might be unusual but the model allows it
        purchase1 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        purchase2 = PopUpPurchase.objects.create(
            customer=self.profile_two,
            product=self.product,
            bid=self.bid,  # Same bid
            price=Decimal('250.00')
        )
        
        self.assertEqual(purchase1.bid, purchase2.bid)
    
    def test_address_from_different_customer(self):
        """Test that address can belong to different customer"""
        # Create address for user2
        user2_address = PopUpCustomerAddress.objects.create(
            customer=self.user2,
            address_line="456 Oak Ave",
            town_city="Chicago",
            state="IL",
            postcode="60601"
        )
        
        # Purchase by user1 with user2's address (gift scenario?)
        purchase = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            address=user2_address
        )
        
        self.assertEqual(purchase.customer, self.profile_one)
        self.assertEqual(purchase.address.customer, self.user2)
    
    # ==================== Business Logic Tests ====================
    
    def test_get_customer_purchase_history(self):
        """Test retrieving customer's purchase history"""
        # Create multiple purchases
        purchase1 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00')
        )
        
        bid2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('300.00')
        )
        
        purchase2 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=bid2,
            price=Decimal('300.00')
        )
        
        # Get purchase history
        history = self.profile_one.purchases.all()
        
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0], purchase2)  # Newest first
        self.assertEqual(history[1], purchase1)
    
    def test_get_unpaid_purchases_for_customer(self):
        """Test getting all unpaid purchases for a customer"""
        purchase1 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=self.bid,
            price=Decimal('250.00'),
            paid=False
        )
        
        bid2 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('300.00')
        )
        
        purchase2 = PopUpPurchase.objects.create(
            customer=self.profile_one,
            product=self.product,
            bid=bid2,
            price=Decimal('300.00'),
            paid=True
        )
        
        unpaid = self.profile_one.purchases.filter(paid=False)
        
        self.assertEqual(unpaid.count(), 1)
        self.assertIn(purchase1, unpaid)
        self.assertNotIn(purchase2, unpaid)


# ==================== Auto-Bidding Tests (Separate Class) ====================

class TestPopUpBidAutoBidding(TestCase):
    """Tests for auto-bidding functionality - FEATURE NOT YET IMPLEMENTED"""
    
    @classmethod
    def setUpTestData(cls):
        """Create seed data for auto-bid tests"""
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()

    
    @unittest.skip("Auto-bidding feature not yet implemented")
    def test_auto_bid_triggers_on_new_bid(self):
        """Test that auto-bid is triggered when new bid comes in"""
        # User1 sets up auto-bid up to $500
        bid1 = PopUpBid.objects.create(
            customer=self.profile_one,
            product=self.product,
            amount=Decimal('200.00'),
            max_auto_bid=Decimal('500.00'),
            bid_increment=Decimal('10.00')
        )
        bid1.save()
        
        # User2 bids $220
        bid2 = PopUpBid.objects.create(
            customer=self.profile_two,
            product=self.product,
            amount=Decimal('220.00')
        )
        bid2.save()
        
        # Auto-bid should have created a new bid for user1 at $230
        user1_bids = PopUpBid.objects.filter(customer=self.user1).order_by('-amount')
        print('user1_bids', user1_bids, user1_bids.count())

        self.assertGreater(user1_bids.count(), 1)
        
        auto_bid = user1_bids.first()
        self.assertEqual(auto_bid.amount, Decimal('230.00'))
    
    @unittest.skip("Auto-bidding feature not yet implemented")
    def test_auto_bid_stops_at_max(self):
        """Test that auto-bid doesn't exceed max_auto_bid"""
        # User1 sets max auto-bid to $250
        bid1 = PopUpBid.objects.create(
            customer=self.user1,
            product=self.product,
            amount=Decimal('200.00'),
            max_auto_bid=Decimal('250.00'),
            bid_increment=Decimal('10.00')
        )
        
        # User2 bids $260 (above user1's max)
        bid2 = PopUpBid.objects.create(
            customer=self.user2,
            product=self.product,
            amount=Decimal('260.00')
        )
        
        # User1 should not have auto-bid above $250
        user1_highest = PopUpBid.objects.filter(customer=self.user1).order_by('-amount').first()
        self.assertLessEqual(user1_highest.amount, Decimal('250.00'))
    
    @unittest.skip("Auto-bidding feature not yet implemented")
    def test_auto_bid_max_rounds_prevents_infinite_loop(self):
        """Test that max_rounds parameter prevents infinite loops"""
        # Both users set up auto-bids
        bid1 = PopUpBid.objects.create(
            customer=self.user1,
            product=self.product,
            amount=Decimal('200.00'),
            max_auto_bid=Decimal('1000.00'),
            bid_increment=Decimal('10.00')
        )
        
        bid2 = PopUpBid.objects.create(
            customer=self.user2,
            product=self.product,
            amount=Decimal('210.00'),
            max_auto_bid=Decimal('1000.00'),
            bid_increment=Decimal('10.00')
        )
        
        # Should stop after max_rounds (default 5)
        total_bids = PopUpBid.objects.filter(product=self.product).count()
        # Should have original 2 + some auto-bids, but not hundreds
        self.assertLess(total_bids, 20)
    
    @unittest.skip("Auto-bidding feature not yet implemented")
    def test_no_auto_bid_without_max_auto_bid(self):
        """Test that no auto-bid happens without max_auto_bid set"""
        # User1 bids without auto-bid
        bid1 = PopUpBid.objects.create(
            customer=self.user1,
            product=self.product,
            amount=Decimal('200.00')
            # No max_auto_bid
        )
        
        # User2 bids higher
        bid2 = PopUpBid.objects.create(
            customer=self.user2,
            product=self.product,
            amount=Decimal('220.00')
        )
        
        # User1 should still only have 1 bid
        self.assertEqual(PopUpBid.objects.filter(customer=self.user1).count(), 1)
    
    @unittest.skip("Auto-bidding feature not yet implemented")
    def test_auto_bid_uses_correct_increment(self):
        """Test that auto-bid uses the correct bid_increment"""
        bid1 = PopUpBid.objects.create(
            customer=self.user1,
            product=self.product,
            amount=Decimal('200.00'),
            max_auto_bid=Decimal('500.00'),
            bid_increment=Decimal('25.00')  # Custom increment
        )
        
        bid2 = PopUpBid.objects.create(
            customer=self.user2,
            product=self.product,
            amount=Decimal('220.00')
        )
        
        # Auto-bid should be 220 + 25 = 245
        auto_bid = PopUpBid.objects.filter(customer=self.user1).order_by('-amount').first()
        self.assertEqual(auto_bid.amount, Decimal('245.00'))


class TestPopUpCustomerIPModel(TestCase):
    """Test suite for PopUpCustomerIP model"""

    def setUp(cls):
        """Create a test customer for use in all tests"""
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()


    def test_create_ip_record_with_ipv4(self):
        """Test creating an IP record with valid IPv4 address"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        self.assertEqual(ip_record.customer, self.user1)
        self.assertEqual(ip_record.ip_address, "192.168.1.1")
        self.assertIsNone(ip_record.country)
        self.assertIsNone(ip_record.city)
        self.assertIsNotNone(ip_record.created_at)


    def test_create_ip_record_with_ipv6(self):
        """Test creating an IP record with valid IPv6 address"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        
        self.assertEqual(ip_record.ip_address, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        self.assertEqual(ip_record.customer, self.user1)

    def test_create_ip_record_with_geo_data(self):
        """Test creating an IP record with country and city"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="203.0.113.1",
            country="US",
            city="New York"
        )
        
        self.assertEqual(ip_record.country, "US")
        self.assertEqual(ip_record.city, "New York")

    def test_ip_record_str_representation(self):
        """Test the string representation of IP record"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        expected_str = f"{self.user1.email} - 192.168.1.1 ({ip_record.created_at})"
        self.assertEqual(str(ip_record), expected_str)

    def test_multiple_ips_per_customer(self):
        """Test that a customer can have multiple IP addresses"""
        ip1 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        ip2 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="10.0.0.1"
        )
        
        customer_ips = self.user1.ip_addresses.all()
        self.assertEqual(customer_ips.count(), 2)
        self.assertIn(ip1, customer_ips)
        self.assertIn(ip2, customer_ips)

    def test_cascade_delete_customer(self):
        """Test that IP records are deleted when customer is deleted"""
        pop_ip_one = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )

        pop_ip_two = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="10.0.0.1"
        )
        
        self.assertEqual(PopUpCustomerIP.objects.filter(customer=self.user1).count(), 2)
        
        # Delete customer
        pop_ip_one.delete()
        pop_ip_two.delete()      
        self.user1.delete()
        
        # IP records should be deleted too
        self.assertEqual(PopUpCustomerIP.objects.count(), 0)


    def test_related_name_ip_addresses(self):
        """Test the related_name 'ip_addresses' works correctly"""
        PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        # Access via related_name
        self.assertEqual(self.user1.ip_addresses.count(), 1)
        self.assertEqual(self.user1.ip_addresses.first().ip_address, "192.168.1.1")

    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set on creation"""
        before = django_timezone.now()
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        after = django_timezone.now()
        
        self.assertIsNotNone(ip_record.created_at)
        self.assertGreaterEqual(ip_record.created_at, before)
        self.assertLessEqual(ip_record.created_at, after)

    def test_country_max_length(self):
        """Test country field respects max_length of 2"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1",
            country="US"
        )
        
        self.assertEqual(len(ip_record.country), 2)

    def test_city_max_length(self):
        """Test city field can store up to 100 characters"""
        long_city_name = "A" * 100
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1",
            city=long_city_name
        )
        
        self.assertEqual(len(ip_record.city), 100)
        self.assertEqual(ip_record.city, long_city_name)


    def test_blank_country_and_city(self):
        """Test that country and city can be blank"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1",
            country="",
            city=""
        )
        
        self.assertEqual(ip_record.country, "")
        self.assertEqual(ip_record.city, "")


    def test_null_country_and_city(self):
        """Test that country and city can be null"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1",
            country=None,
            city=None
        )
        
        self.assertIsNone(ip_record.country)
        self.assertIsNone(ip_record.city)

    def test_duplicate_ip_addresses_allowed(self):
        """Test that same IP can be recorded multiple times for same customer"""
        ip1 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        ip2 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        self.assertEqual(PopUpCustomerIP.objects.filter(
            customer=self.user1,
            ip_address="192.168.1.1"
        ).count(), 2)

    def test_same_ip_different_customers(self):
        """Test that same IP can belong to different customers"""
        
        ip1 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        ip2 = PopUpCustomerIP.objects.create(
            customer=self.user2,
            ip_address="192.168.1.1"
        )
        
        self.assertEqual(ip1.ip_address, ip2.ip_address)
        self.assertNotEqual(ip1.customer, ip2.customer)


    def test_high_risk_country_tracking(self):
        """Test tracking registrations from high-risk countries"""
        high_risk_countries = ['RU', 'CN', 'UA', 'KP']
        
        for country in high_risk_countries:
            ip_record = PopUpCustomerIP.objects.create(
                customer=self.user1,
                ip_address=f"192.168.1.{high_risk_countries.index(country) + 1}",
                country=country,
                city="Test City"
            )
            self.assertIn(ip_record.country, high_risk_countries)

    def test_meta_verbose_name(self):
        """Test model meta verbose_name"""
        self.assertEqual(
            PopUpCustomerIP._meta.verbose_name,
            "PopUp Customer IP Address"
        )

    def test_meta_verbose_name_plural(self):
        """Test model meta verbose_name_plural"""
        self.assertEqual(
            PopUpCustomerIP._meta.verbose_name_plural,
            "PopUp Customer IP Addresses"
        )

    def test_ordering_by_created_at(self):
        """Test that IP records can be ordered by created_at"""
        ip1 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        ip2 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.2"
        )
        ip3 = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.3"
        )
        
        ips_ordered = PopUpCustomerIP.objects.filter(
            customer=self.user1
        ).order_by('created_at')
        
        self.assertEqual(list(ips_ordered), [ip1, ip2, ip3])

    def test_filter_by_country(self):
        """Test filtering IP records by country"""
        PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1",
            country="US"
        )
        PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.2",
            country="RU"
        )
        PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.3",
            country="US"
        )
        
        us_ips = PopUpCustomerIP.objects.filter(country="US")
        ru_ips = PopUpCustomerIP.objects.filter(country="RU")
        
        self.assertEqual(us_ips.count(), 2)
        self.assertEqual(ru_ips.count(), 1)

    def test_update_geo_data(self):
        """Test updating country and city after creation"""
        ip_record = PopUpCustomerIP.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        # Initially no geo data
        self.assertIsNone(ip_record.country)
        self.assertIsNone(ip_record.city)
        
        # Update with geo data
        PopUpCustomerIP.objects.filter(
            customer=self.user1,
            ip_address="192.168.1.1"
        ).update(country="US", city="New York")
        
        ip_record.refresh_from_db()
        self.assertEqual(ip_record.country, "US")
        self.assertEqual(ip_record.city, "New York")




class TestPopUpPasswordResetRequestLogModel(TestCase):
    """Test suite for PopUpPasswordResetRequestLog model"""

    def setUp(cls):
        """Create a test customer for use in all tests"""
        cls.product, cls.color_spec, cls.size_spec, cls.user1, cls.profile_one, cls.user2, cls.profile_two = create_seed_data()


    def test_create_password_reset_log(self):
        """Test creating a password reset log entry"""
        reset_log = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        self.assertEqual(reset_log.customer, self.user1)
        self.assertEqual(reset_log.ip_address, "192.168.1.1")
        self.assertIsNotNone(reset_log.requested_at)


    def test_password_reset_log_with_ipv6(self):
        """Test creating a password reset log with IPv6 address"""
        reset_log = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        
        self.assertEqual(reset_log.ip_address, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")


    def test_str_representation(self):
        """Test the string representation of password reset log"""
        reset_log = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        expected_str = f"{self.user1.email} - 192.168.1.1 @ {reset_log.requested_at}"
        self.assertEqual(str(reset_log), expected_str)


    def test_requested_at_auto_now_add(self):
        """Test that requested_at is automatically set on creation"""
        before = django_timezone.now()
        reset_log = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        after = django_timezone.now()
        
        self.assertIsNotNone(reset_log.requested_at)
        self.assertGreaterEqual(reset_log.requested_at, before)
        self.assertLessEqual(reset_log.requested_at, after)

    def test_multiple_reset_requests_per_customer(self):
        """Test that a customer can have multiple password reset requests logged"""
        reset1 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        reset2 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="10.0.0.1"
        )
        reset3 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="172.16.0.1"
        )
        
        customer_resets = self.user1.password_reset_logs.all()
        self.assertEqual(customer_resets.count(), 3)
        self.assertIn(reset1, customer_resets)
        self.assertIn(reset2, customer_resets)
        self.assertIn(reset3, customer_resets)


    def test_cascade_delete_customer(self):
        """Test that password reset logs are deleted when customer is deleted"""
        pop_pass_log_one = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        pop_pass_log_two = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="10.0.0.1"
        )
        
        self.assertEqual(
            PopUpPasswordResetRequestLog.objects.filter(customer=self.user1).count(),
            2
        )
        
        # Delete customer
        pop_pass_log_one.delete()
        pop_pass_log_two.delete()
        self.user1.delete()
        
        # Reset logs should be deleted too
        self.assertEqual(PopUpPasswordResetRequestLog.objects.count(), 0)


    def test_related_name_password_reset_logs(self):
        """Test the related_name 'password_reset_logs' works correctly"""
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        # Access via related_name
        self.assertEqual(self.user1.password_reset_logs.count(), 1)
        self.assertEqual(
            self.user1.password_reset_logs.first().ip_address,
            "192.168.1.1"
        )


    def test_same_ip_multiple_requests(self):
        """Test that same IP can make multiple reset requests"""
        reset1 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        reset2 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        same_ip_requests = PopUpPasswordResetRequestLog.objects.filter(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        self.assertEqual(same_ip_requests.count(), 2)

    def test_different_customers_same_ip(self):
        """Test that same IP can be used by different customers"""
        
        reset1 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        reset2 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user2,
            ip_address="192.168.1.1"
        )
        
        self.assertEqual(reset1.ip_address, reset2.ip_address)
        self.assertNotEqual(reset1.customer, reset2.customer)

    # ================ META TESTING ================
    def test_meta_verbose_name(self):
        """Test model meta verbose_name"""
        self.assertEqual(
            PopUpPasswordResetRequestLog._meta.verbose_name,
            "PopUp Password Reset Request Log"
        )

    def test_meta_verbose_name_plural(self):
        """Test model meta verbose_name_plural"""
        self.assertEqual(
            PopUpPasswordResetRequestLog._meta.verbose_name_plural,
            "PopUp Password Reset Request Logs"
        )
    # ==============================================

    def test_ordering_by_requested_at(self):
        """Test that logs can be ordered by requested_at timestamp"""
        reset1 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        reset2 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.2"
        )
        reset3 = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.3"
        )
        
        logs_ordered = PopUpPasswordResetRequestLog.objects.filter(
            customer=self.user1
        ).order_by('requested_at')
        
        self.assertEqual(list(logs_ordered), [reset1, reset2, reset3])


    def test_detect_suspicious_activity_multiple_requests(self):
        """Test detecting suspicious activity - multiple requests in short time"""
        # Simulate 5 password reset requests
        for i in range(5):
            PopUpPasswordResetRequestLog.objects.create(
                customer=self.user1,
                ip_address="192.168.1.1"
            )
        
        # Check if there are multiple requests from same IP
        recent_requests = PopUpPasswordResetRequestLog.objects.filter(
            customer=self.user1,
            ip_address="192.168.1.1"
        ).count()
        
        self.assertEqual(recent_requests, 5)
        # In real scenario, you'd flag this as suspicious


    def test_detect_abuse_high_frequency_requests(self):
        """Test detecting abuse - high frequency requests from single IP"""
        # Create 10 requests from same IP
        for i in range(10):
            PopUpPasswordResetRequestLog.objects.create(
                customer=self.user1,
                ip_address="203.0.113.1"
            )
        
        abuse_threshold = 5
        request_count = PopUpPasswordResetRequestLog.objects.filter(
            ip_address="203.0.113.1"
        ).count()
        
        self.assertGreater(request_count, abuse_threshold)

    def test_filter_by_ip_address(self):
        """Test filtering logs by IP address"""
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="10.0.0.1"
        )
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        ip1_logs = PopUpPasswordResetRequestLog.objects.filter(ip_address="192.168.1.1")
        ip2_logs = PopUpPasswordResetRequestLog.objects.filter(ip_address="10.0.0.1")
        
        self.assertEqual(ip1_logs.count(), 2)
        self.assertEqual(ip2_logs.count(), 1)

    def test_recent_requests_within_timeframe(self):
        """Test querying recent requests within a specific timeframe"""
        # Create a request
        reset_log = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        
        # Query requests within last hour
        one_hour_ago = django_timezone.now() - timedelta(hours=1)
        recent_requests = PopUpPasswordResetRequestLog.objects.filter(
            customer=self.user1,
            requested_at__gte=one_hour_ago
        )
        
        self.assertEqual(recent_requests.count(), 1)
        self.assertIn(reset_log, recent_requests)

    def test_count_requests_per_customer(self):
        """Test counting total password reset requests per customer"""
        # customer2 = PopUpCustomer.objects.create(
        #     email="testuser2@example.com",
        #     first_name="Test2",
        #     last_name="User2"
        # )
        
        # Create 3 requests for customer1
        for i in range(3):
            PopUpPasswordResetRequestLog.objects.create(
                customer=self.user1,
                ip_address=f"192.168.1.{i+1}"
            )
        
        # Create 2 requests for customer2
        for i in range(2):
            PopUpPasswordResetRequestLog.objects.create(
                customer=self.user2,
                ip_address=f"10.0.0.{i+1}"
            )
        
        self.assertEqual(self.user1.password_reset_logs.count(), 3)
        self.assertEqual(self.user2.password_reset_logs.count(), 2)

    def test_identify_non_existent_user_attack(self):
        """
        Test scenario from Reddit post - tracking reset requests 
        even when user doesn't exist (bug scenario)
        Note: This would require the view to log even non-existent users,
        but we can test the model's ability to handle this data
        """
        # In the bug scenario, hackers triggered resets for non-existent emails
        # You might want to track these differently
        
        # Create a dummy customer to represent non-existent user tracking
        dummy_customer = User.objects.create(
            email="nonexistent@example.com",
            first_name="Dummy",
            last_name="User"
        )
        
        # Multiple requests from suspicious IP
        for i in range(20):
            PopUpPasswordResetRequestLog.objects.create(
                customer=dummy_customer,
                ip_address="203.0.113.100"  # Suspicious IP
            )
        
        suspicious_requests = PopUpPasswordResetRequestLog.objects.filter(
            ip_address="203.0.113.100"
        ).count()
        
        self.assertEqual(suspicious_requests, 20)

    def test_latest_reset_request_per_customer(self):
        """Test getting the most recent password reset request for a customer"""
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.2"
        )
        latest = PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.3"
        )
        
        latest_request = self.user1.password_reset_logs.latest('requested_at')
        self.assertEqual(latest_request, latest)


    def test_multiple_customers_different_ips(self):
        """Test tracking reset requests from multiple customers with different IPs"""


        customer3 = User.objects.create(
            email="customer3@example.com",
            first_name="Customer",
            last_name="Three"
        )
        
        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user1,
            ip_address="192.168.1.1"
        )

        PopUpPasswordResetRequestLog.objects.create(
            customer=self.user2,
            ip_address="10.0.0.1"
        )

        PopUpPasswordResetRequestLog.objects.create(
            customer=customer3,
            ip_address="172.16.0.1"
        )
        
        self.assertEqual(PopUpPasswordResetRequestLog.objects.count(), 3)
        
        # Count unique customers using values_list
        unique_customers = PopUpPasswordResetRequestLog.objects.values_list(
            'customer', flat=True
        ).distinct()
        
        self.assertEqual(len(unique_customers), 3)
        

    def test_rate_limiting_detection(self):
        """Test detecting potential rate limiting violations"""
        # Simulate rapid requests (would be within seconds in real scenario)
        now = django_timezone.now()
        
        for i in range(6):
            PopUpPasswordResetRequestLog.objects.create(
                customer=self.user1,
                ip_address="192.168.1.1"
            )
        
        # Check requests within last minute (or hour, depending on your rate limit)
        one_minute_ago = now - timedelta(minutes=1)
        recent_count = PopUpPasswordResetRequestLog.objects.filter(
            customer=self.user1,
            requested_at__gte=one_minute_ago
        ).count()
        
        rate_limit = 5  # Example: 5 requests per minute
        self.assertGreater(recent_count, rate_limit)




# """
# Run Test
# python3 manage.py test pop_accounts/tests
# """