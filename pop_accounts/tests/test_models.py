import pytest
from django.test import TestCase
from pop_up_auction.models import PopUpProductSpecificationValue, PopUpProductSpecification
from pop_accounts.models import (PopUpCustomer,PopUpBid, CustomPopUpAccountManager, SoftDeleteManager, PopUpCustomerAddress)
from pop_up_auction.models import (PopUpProduct, PopUpCategory, PopUpBrand, PopUpProductType)
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from unittest.mock import patch
from django.core.mail import send_mail
from decimal import Decimal
from .conftest import create_seed_data


class TestPopUpCustomerModel(TestCase):
    def setUp(self):
        self.customer = PopUpCustomer.objects.create(
            email="testMail@gmail.com",
            first_name="Palo",
            last_name="Negro",
            middle_name="Olop",
            mobile_phone="555-555-5555",
            mobile_notification=True,
            shoe_size="9.5",
            size_gender="Male",
            favorite_brand="Jordan"
        )

    def test_pop_customer_model_entry(self):
        """
        Test PopUpCustomer Data Insertion/Types Field Attributes
        """

        self.assertEqual(str(self.customer.email), 'testMail@gmail.com')
        self.assertEqual(str(self.customer.first_name), 'Palo')
        self.assertEqual(str(self.customer.last_name), 'Negro')
        self.assertEqual(str(self.customer.middle_name), 'Olop')
        self.assertEqual(str(self.customer.mobile_phone), '555-555-5555')
        self.assertEqual(str(self.customer.mobile_notification), "True")
        self.assertEqual(str(self.customer.shoe_size), "9.5")
        self.assertEqual(str(self.customer.size_gender), "Male")
        self.assertEqual(str(self.customer.favorite_brand), "Jordan")


    def test_soft_delete_makrs_user_as_inactive_and_sets_deleted_at(self):
        self.customer.soft_delete()
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)
        self.assertIsNotNone(self.customer.deleted_at)
        self.assertTrue(self.customer.is_deleted)
    

    def test_restore_user_reset_is_active_and_deleted_at(self):
        self.customer.soft_delete()
        self.customer.restore()
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_active)
        self.assertIsNone(self.customer.deleted_at)
        self.assertFalse(self.customer.is_deleted)


    def test_str_returns_full_name(self):
        self.assertEqual(str(self.customer), "Palo Negro")

    @patch('pop_accounts.models.send_mail')
    def test_email_user_sends_email(self, mock_send_mail):
        self.customer.email_user("Subject", "Message")
        mock_send_mail.assert_called_once_with(
            "Subject",
            "Message",
            "l@1.com",
            [self.customer.email],
            fail_silently=False
        )

    def test_hard_delete_removes_instance(self):
        self.customer.hard_delete()
        with self.assertRaises(PopUpCustomer.DoesNotExist):
            PopUpCustomer.objects.get(id=self.customer.id)


    def test_soft_delete_user_not_returned_by_default_manager(self):
        self.customer.soft_delete()
        users = PopUpCustomer.objects.filter(email="testMail@gmail.com")
        self.assertEqual(users.count(), 0)


class TestUserInterestedInViewModels(TestCase):

    def test_user_can_mark_product_as_interested(self):
        product, _, _, user1, _ = create_seed_data()
        product.is_active = False
        product.inventory_status = "in_transit"
        product.save()

        user1.prods_interested_in.add(product)

        assert product in user1.prods_interested_in.all()
        assert user1.prods_interested_in.count() == 1
    
    def test_product_can_have_specifications(self):
        product, _, _, _, _ = create_seed_data()
        product.is_active = False
        product.inventory_status = "in_transit"
        product.save()

        specs = product.popupproductspecificationvalue_set.all()
        
        # assert specs.count() == 2
        # assert specs.first().value == "Black/Red"
        # assert specs.first().specification.name == "colorway"

        color_spec_value = product.popupproductspecificationvalue_set.get(specification__name="colorway")
        assert color_spec_value.value == "Black/Red"

        size_spec_value = product.popupproductspecificationvalue_set.get(specification__name="size")
        assert size_spec_value.value == "10"



class TestUserOnNoticeViewModels(TestCase):

    def test_user_can_mark_product_as_on_notice(self):
        product, _, _, user1, _ = create_seed_data()
        product.is_active = False
        product.inventory_status = "anticipated"
        product.save()

        user1.prods_on_notice_for.add(product)

        assert product in user1.prods_on_notice_for.all()
        assert user1.prods_on_notice_for.count() == 1


class TestPersonalInfoViewModels(TestCase):
    def setUp(self):
        # Create a user
        self.user = PopUpCustomer.objects.create_user(
            email="user1@example.com",
            password="Password123",
            first_name="John",
            last_name="Doe",
            is_active=True
        )

    def test_user_can_update_personal_info(self):
        """User model should allow updating personal profile info"""
        self.user.first_name = "Jane"
        self.user.middle_name = "M"
        self.user.last_name = "Smith"
        self.user.shoe_size = "10"
        self.user.size_gender = "M"
        self.user.favorite_brand = "Jordan"
        self.user.mobile_phone = "+1234567890"
        self.user.mobile_notification = True
        self.user.save()
    
        # Refresh from the database to confirm persistence
        updated_user = PopUpCustomer.objects.get(id=self.user.id)

        assert updated_user.first_name == "Jane"
        assert updated_user.middle_name == "M"
        assert updated_user.last_name == "Smith"
        assert updated_user.shoe_size == "10"
        assert updated_user.size_gender == "M"
        assert updated_user.favorite_brand == "Jordan"
        assert updated_user.mobile_phone == "+1234567890"
        assert updated_user.mobile_notification is True


# class TestPopUpBidModel(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.product, cls.user1, cls.user2 = create_seed_data()
    
#     def test_rejects_bid_not_higher_than_current(self):
#         PopUpBid.objects.create(
#             customer=self.user1,
#             product=self.product,
#             amount=Decimal('200'), # first bid okay
#         )
#         # Try to enter 200 again -> should raise error
#         with self.assertRaisesMessage(ValueError, 'higher than the current'):
#             PopUpBid.objects.create(
#                 customer=self.user2,
#                 product=self.product,
#                 amount=Decimal('200'),
#             )
    
#     def test_updates_highest_and_count(self):
#         self.assertEqual(self.product.bid_count, 0)
#         self.assertIsNone(self.product.current_highest_bid)

#         PopUpBid.objects.create(
#             customer=self.user1, product=self.product, amount=Decimal('210')
#         )

#         self.product.refresh_from_db()
#         self.assertEqual(self.product.bid_count, 1)
#         self.assertEqual(self.product.current_highest_bid, Decimal('210'))

#         # second (higher) bid
#         PopUpBid.objects.create(
#             customer=self.user2, product=self.product, amount=Decimal('225')
#         )
#         self.product.refresh_from_db()
#         self.assertEqual(self.product.bid_count, 2)
#         self.assertEqual(self.product.current_highest_bid, Decimal('225'))

    
#     def test_only_highest_bid_marked_winner(self):
#         b1 = PopUpBid.objects.create(
#             customer=self.user1, product=self.product, amount=Decimal('220')
#         )
#         b1.refresh_from_db()
#         self.assertTrue(b1.is_winning_bid)
    
    # def test_auto_bid_places_increment_and_stops(self):
    #     # user1 sets auto‑bid up to 300 at 10 USD increments
    #     auto = PopUpBid.objects.create(
    #         customer=self.user1, 
    #         product=self.product, 
    #         amount=Decimal('240'), 
    #         max_auto_bid=Decimal('300'),
    #         bid_increment=Decimal('10')
    #     )
    #     auto.refresh_from_db()
    
        
    #     print('self.product 1', self.product.current_highest_bid)

    #     # user2 comes in with 250 -> should trigger user1 auto-bid to 260
    #     user2_bid = PopUpBid.objects.create(
    #         customer=self.user2, product=self.product, amount=Decimal('250'),
    #     )
    #     print('self.product 2', self.product.current_highest_bid)
    #     user2_bid.save()

    #     bids = list(self.product.bids.order_by('amount'))
    #     amounts = [b.amount for b in bids]
    #     self.assertIn(Decimal('260'), amounts)
    #     self.assertEqual(self.product.current_highest_bid, Decimal('260'))

    #     # Ensure we did not exceed five recurssive rounds
    #     self.assertLessEqual(len(bids), 1 + 1 + 5) # origin + competitor + max auto rounds
    

    # Expired bids are inactive
    # def test_expired_bid_sets_inactive(self):
    #     past = now() - timedelta(days=1)
    #     bid = PopUpBid.objects.create(customer=self.user1, product=self.product, amount=Decimal('270'), expires_at=past)
    #     self.assertFalse(bid.is_active)




"""
Run Test
python3 manage.py test pop_accounts/tests
"""