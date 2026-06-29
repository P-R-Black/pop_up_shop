from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta
from django.utils import timezone as django_timezone
from unittest.mock import patch, MagicMock
from decimal import Decimal, ROUND_HALF_UP
from pop_up_email.utils import (
    send_auction_winner_email,
    send_24_hour_reminder_email,
    send_1_hour_reminder_email,
    send_order_confirmation_email,
    send_okay_to_ship_email,
    send_dispute_alert_to_customer,
    send_customer_shipping_details,
    send_friend_invite_email,
    get_admin_users,
    interested_in_products_update_and_notify_me_products_update,
    send_interested_in_and_coming_soon_product_update_to_users,
    send_success_notification,
    send_failure_notification,
)
from pop_up_auction.tests.conftest import (create_test_user,create_test_staff_user)


from pop_up_auction.models import PopUpProduct, PopUpCategory, PopUpProductType, PopUpBrand
from pop_up_bot.models import ScheduledRelease, ProcurementServiceRequest, ProcurementExecution, ProcurementRequest
from pop_up_auction.tests.conftest import create_test_user
from pop_accounts.models import PopUpCustomerProfile, PopUpBid
from pop_up_auction.models import PopUpProduct, PopUpCategory, PopUpProductType, PopUpBrand, WinnerReservation
from pop_up_cart.models import PopUpCartItem

User = get_user_model()

@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@popupshop.com'
)

class AuctionEmailTestCase(TestCase):
    """Tests for auction-related email functions"""

    def setUp(self):
        """Set up test user and product"""
        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
        )
        self.other_user, self.other_user_profile = create_test_user(
            "other@example.com", "testpass!23", "Other", "User2", "10", "female"
        )

        # Create category
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        
        # Create brand
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        
        # Create product type
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )
        self.product1 = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            slug='jordan-4-military-blue',
            buy_now_price=Decimal('215.00'),
            retail_price=Decimal('215.00'),
            inventory_status='in_inventory',
            is_active=True
        )

        now = django_timezone.now()


        self.auctioned_product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 3 Retro',
            secondary_product_title='OG Rare Air',
            slug='air-jordan-3-og-rare-air',
            buy_now_price=Decimal('215.00'),
            retail_price=Decimal('215.00'),
            reserve_price=Decimal('185.00'), 
            inventory_status='in_inventory',
            current_highest_bid=Decimal('350.00'), 
            auction_start_date=now - timedelta(days=5),  
            auction_end_date=now - timedelta(days=1), #django_timezone.now() + timedelta(days=2, hours=3), 
            bid_count=5, 
            is_active=True
        )

        PopUpBid.objects.create(
            customer=self.user_profile,
            product=self.auctioned_product,
            amount=Decimal('350.00'),
            timestamp=now - timedelta(days=1)
        )

    def test_send_auction_winner_email(self):
        """Test auction winner notification email"""
        html_message = send_auction_winner_email(self.user, self.product1)
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email details
        email = mail.outbox[0]
        self.assertEqual(email.subject, '🎉 You Won the Auction!')
        self.assertEqual(email.to, ['test@example.com'])
        self.assertEqual(email.from_email, 'noreply@popupshop.com')
        
        # Check content
        self.assertIn('Test', html_message)
        self.assertIn('Air Jordan 4', html_message)
        
        # Verify HTML message was returned
        self.assertIsNotNone(html_message)

    def test_send_24_hour_reminder_email(self):
        """Test 24-hour reminder email"""
        ended_auctions = PopUpProduct.objects.filter(
        auction_end_date__lte=now(),
        auction_finalized=False,
        is_active=True
        )


        for product in ended_auctions:
            highest_bid = product.bids.order_by('-amount', '-timestamp').first()
            print('highest_bid', highest_bid)

            if highest_bid:
                
                winner = highest_bid.customer.user
                print('winner', winner)
                product.winner = winner
                product.current_highest_bid = highest_bid.amount
                product.auction_finalized = True
                product.inventory_status = "sold_out"
                product.save()

                # Lock product in winner's cart
                try:
                    PopUpCartItem.objects.update_or_create(
                        user=winner, 
                        product=product, 
                        defaults={'quantity': 1, 'auction_locked': True, 'buy_now': False}
                        )                
                except Exception as e:
                    print('e', e)

                # Add WinnerReservation
                try:
                    reservation = WinnerReservation.objects.create(
                        user=winner,
                        product=product,
                        expires_at=now() + timedelta(hours=48),
                        is_paid=False,
                        is_expired=False,
                        notification_sent=True,
                        reminder_24hr_sent=False,
                        reminder_1hr_sent=False
                    )
                except Exception as e:
                    print('e', e)
            else:
                product.auction_finalized = True
                product.save()

        html_message = send_24_hour_reminder_email(self.user, self.auctioned_product)
        
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, '24 Hours Left to Purchase Your Auction Item')
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn('Test', email.body)
        self.assertIn('Air Jordan 3 Retro', email.body)
        
        # Verify HTML message was returned
        self.assertIsNotNone(html_message)

    def test_send_1_hour_reminder_email(self):
        """Test 1-hour reminder email"""

        ended_auctions = PopUpProduct.objects.filter(
        auction_end_date__lte=now(),
        auction_finalized=False,
        is_active=True
        )


        for product in ended_auctions:
            highest_bid = product.bids.order_by('-amount', '-timestamp').first()
            print('highest_bid', highest_bid)

            if highest_bid:
                
                winner = highest_bid.customer.user
                print('winner', winner)
                product.winner = winner
                product.current_highest_bid = highest_bid.amount
                product.auction_finalized = True
                product.inventory_status = "sold_out"
                product.save()

                # Lock product in winner's cart
                try:
                    PopUpCartItem.objects.update_or_create(
                        user=winner, 
                        product=product, 
                        defaults={'quantity': 1, 'auction_locked': True, 'buy_now': False}
                        )                
                except Exception as e:
                    print('e', e)

                # Add WinnerReservation
                try:
                    reservation = WinnerReservation.objects.create(
                        user=winner,
                        product=product,
                        expires_at=now() + timedelta(hours=48),
                        is_paid=False,
                        is_expired=False,
                        notification_sent=True,
                        reminder_24hr_sent=False,
                        reminder_1hr_sent=False
                    )
                except Exception as e:
                    print('e', e)
            else:
                product.auction_finalized = True
                product.save()


        html_message = send_1_hour_reminder_email(self.user, self.auctioned_product)
        
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, '1 Hours Left to Purchase Your Auction Item')
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn('Test', email.body)
        self.assertIn('Air Jordan 3 Retro', email.body)
        
        # Verify HTML message was returned
        self.assertIsNotNone(html_message)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@popupshop.com'
)

class OrderEmailTestCase(TestCase):
    """Tests for order-related email functions"""

    def setUp(self):
        """Set up test user and order data"""

        # Create users
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
        )
        self.order_id = '00000000-0000-0000-0000-000000000000'
        self.items = [
            {'name': 'Product 1', 'price': 50.00},
            {'name': 'Product 2', 'price': 75.00}
        ]
        self.total_paid = 125.00

    def test_send_order_confirmation_email_default_status(self):
        """Test order confirmation email with default pending status"""
        send_order_confirmation_email(
            self.user, 
            self.order_id, 
            self.items, 
            self.total_paid
        )
        
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, f'The Pop Up | Order No {self.order_id}')
        self.assertEqual(email.to, ['test@example.com'])

    def test_send_order_confirmation_email_custom_status(self):
        """Test order confirmation email with custom payment status"""
        send_order_confirmation_email(
            self.user, 
            self.order_id, 
            self.items, 
            self.total_paid,
            payment_status='completed'
        )
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, f'The Pop Up | Order No {self.order_id}')

    def test_send_okay_to_ship_email(self):
        """Test admin notification for OK to ship"""
        # Create admin users
        admin1, admin1_profile = create_test_staff_user(
            'admin1@example.com', 'staffPassword!232', 'Admin1',' User', '9', 'male'
            )
        
        admin2, admin2_profile = create_test_staff_user(
            'admin2@example.com', 'staffPassword!232', 'Admin2',' User', '9', 'female'
            )
        
        
        # Create mock order
        mock_order = MagicMock()
        mock_order.id = 123
        
        send_okay_to_ship_email(mock_order)
        
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, f'Order #{mock_order.id} - Approved for Shipment')
        self.assertIn('admin1@example.com', email.to)
        self.assertIn('admin2@example.com', email.to)

    def test_send_dispute_alert_to_customer(self):
        """Test dispute alert function"""
        mock_order = MagicMock()
        mock_order.__str__ = lambda self: '123'
        
        result = send_dispute_alert_to_customer(mock_order)
        
        self.assertEqual(result, 'Payment failed for order #123')

    def test_send_customer_shipping_details(self):
        """Test shipping notification email"""
        mock_order = MagicMock()
        mock_order.id = '00000000-0000-0000-0000-000000000000'
        
        send_customer_shipping_details(
            user=self.user,
            order=mock_order,
            carrier='usps',
            tracking_no='1Z999AA10123456784',
            shipped_at=now(),
            estimated_deliv=now() + timedelta(days=3),
            status='shipped'
        )
        
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Your order has shipped Order #00000000-0000-0000-0000-000000000000.')
        self.assertEqual(email.to, ['test@example.com'])

    def test_send_customer_shipping_details_all_carriers(self):
        """Test shipping email with different carriers"""
        carriers = ['usps', 'ups', 'FedEx']
        
        for carrier in carriers:
            mail.outbox = []  # Clear mailbox
            
            mock_order = MagicMock()
            mock_order.id = '00000000-0000-0000-0000-000000000000'
            
            send_customer_shipping_details(
                user=self.user,
                order=mock_order,
                carrier=carrier,
                tracking_no='TRACK123',
                shipped_at=now(),
                estimated_deliv=now() + timedelta(days=3),
                status='shipped'
            )
            
            self.assertEqual(len(mail.outbox), 1)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@popupshop.com',
    SITE_DOMAIN='http://testserver'
)
class FriendInviteEmailTestCase(TestCase):
    """Tests for friend invitation email"""

    def setUp(self):
        """Set up test user"""
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User1", "9", "male"
        )

    def test_send_friend_invite_email(self):
        """Test friend invitation email"""
        send_friend_invite_email(
            user=self.user,
            user_email='test@example.com',
            friend_name='Friend Name',
            friend_email='friend@example.com'
        )
        
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('invited you to join The Pop Up', email.subject)
        self.assertEqual(email.to, ['friend@example.com'])


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AdminUserTestCase(TestCase):
    """Tests for admin user retrieval"""

    def test_get_admin_users(self):
        """Test getting admin users"""
        # Create various users
        admin1, admin1_profile = create_test_staff_user(
            'admin1@example.com', 'staffPassword!234', 'Admin1',' User', '9', 'male'
            )
        
        admin2, admin2_profile = create_test_staff_user(
            'admin2@example.com', 'staffPassword!345', 'Admin2',' User', '9', 'female'
            )
        
        admin3, admin3_profile = create_test_staff_user(
            'admin3@example.com', 'staffPassword!456', 'Inactive',' User', '9', 'male'
            )
        admin3.is_active = False
        admin3.save()
        
        admin4, admin4_profile = create_test_staff_user(
            'admin4@example.com', 'staffPassword!567', 'Admin4',' User', '9', 'female'
            )
        admin4.is_staff = False
        admin4.save()

        
        # inactive_admin = User.objects.create_user(
        #     username='inactive',
        #     is_staff=True,
        #     is_active=False
        # )
        # regular_user = User.objects.create_user(
        #     username='regular',
        #     is_staff=False,
        #     is_active=True
        # )
        
        admins = get_admin_users()
        
        self.assertEqual(admins.count(), 2)
        self.assertIn(admin1, admins)
        self.assertIn(admin2, admins)
        self.assertNotIn(admin3, admins)
        self.assertNotIn(admin4, admins)


class ProductNotificationTestCase(TestCase):
    """Tests for product notification functions"""

    def setUp(self):
        """Set up test data"""
        # Create category
        self.basketball_category = PopUpCategory.objects.create(
            name='Basketball',
            slug='basketball'
        )
        
        # Create brand
        self.jordan_brand = PopUpBrand.objects.create(
            name='Jordan',
            slug='jordan'
        )
        
        # Create product type
        self.sneakers_type = PopUpProductType.objects.create(
            name='Sneakers',
            slug='sneakers'
        )

        self.product = PopUpProduct.objects.create(
            product_type=self.sneakers_type,
            category=self.basketball_category,
            brand=self.jordan_brand,
            product_title='Air Jordan 4',
            secondary_product_title='Retro Military Blue',
            slug='jordan-4-military-blue',
            buy_now_price=Decimal('215.00'),
            retail_price=Decimal('215.00'),
            inventory_status='in_inventory',
            is_active=True
        )

        
        # Create customer profiles
        self.user, self.user_profile = create_test_user(
            "test1@example.com", "testpass!23", "Test1", "User1", "9", "male"
        )

        self.user2, self.user_profile2 = create_test_user(
            "test2@example.com", "testpass!23", "Test2", "User1", "7", "male"
        )

        self.user3, self.user_profile3 = create_test_user(
            "test3@example.com", "testpass!23", "Test3", "User1", "7.5", "male"
        )


    def test_interested_in_products_update_interested_users(self):
        """Test retrieving emails of users interested in product"""
        # Add product to interested lists
        self.user_profile.prods_interested_in.add(self.product)
        self.user_profile2.prods_interested_in.add(self.product)
        
        emails = interested_in_products_update_and_notify_me_products_update(
            self.product.id
        )
        
        self.assertEqual(len(emails), 2)
        self.assertIn('test1@example.com', emails)
        self.assertIn('test2@example.com', emails)

    def test_interested_in_products_update_notified_users(self):
        """Test retrieving emails of users on notice list"""
        self.user_profile.prods_on_notice_for.add(self.product)
        
        emails = interested_in_products_update_and_notify_me_products_update(
            self.product.id
        )
        
        self.assertEqual(len(emails), 1)
        self.assertIn('test1@example.com', emails)

    def test_interested_in_products_update_both_lists(self):
        """Test no duplicate emails when user is on both lists"""
        self.user_profile.prods_interested_in.add(self.product)
        self.user_profile.prods_on_notice_for.add(self.product)
        
        emails = interested_in_products_update_and_notify_me_products_update(
            self.product.id
        )
        
        # Should only return one email (distinct)
        self.assertEqual(len(emails), 1)
        self.assertIn('test1@example.com', emails)

    def test_interested_in_products_update_nonexistent_product(self):
        """Test handling of non-existent product"""
        emails = interested_in_products_update_and_notify_me_products_update(99999)
        
        self.assertEqual(emails, [])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@popupshop.com'
    )

    def test_send_interested_update_no_users(self):
        """Test sending updates when no users are interested"""
        send_interested_in_and_coming_soon_product_update_to_users(self.product)
        
        # No emails should be sent
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@popupshop.com'
    )
    def test_send_interested_update_with_users(self):
        """Test sending updates to interested users"""
        self.user_profile.prods_interested_in.add(self.product)
        self.user_profile2.prods_on_notice_for.add(self.product)
        
        buy_date = now() + timedelta(days=7)
        auction_date = now() + timedelta(days=5)
        
        send_interested_in_and_coming_soon_product_update_to_users(
            self.product,
            buy_now_start_date=buy_date,
            auction_start_date=auction_date
        )
        
        # Two emails should be sent (one per user)
        self.assertEqual(len(mail.outbox), 2)
        
        # Check recipients
        recipients = [email.to[0] for email in mail.outbox]
        self.assertIn('test1@example.com', recipients)
        self.assertIn('test2@example.com', recipients)
        
        # Check subject
        for email in mail.outbox:
            self.assertIn('Air Jordan 4 Retro Military Blue', email.subject)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@popupshop.com'
    )
    def test_send_interested_update_no_duplicate_emails(self):
        """Test that users on both lists only receive one email"""
        # Add user to both lists
        self.user_profile.prods_interested_in.add(self.product)
        self.user_profile.prods_on_notice_for.add(self.product)
        
        send_interested_in_and_coming_soon_product_update_to_users(self.product)
        
        # Only one email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'test1@example.com')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@popupshop.com'
    )
    def test_send_interested_update_without_dates(self):
        """Test sending updates without specific dates"""
        self.user_profile.prods_interested_in.add(self.product)
        
        send_interested_in_and_coming_soon_product_update_to_users(self.product)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to[0], 'test1@example.com')


""" New Test """
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@popupshop.com',
    SITE_URL='https://thepopup.com',
)
class ProcurementSuccessEmailTestCase(TestCase):
    """Tests for send_success_notification"""
 
    def setUp(self):
        self.user, self.user_profile = create_test_user(
            'buyer@example.com', 'testpass!23', 'Jordan', 'Buyer', '10', 'male'
        )
 
        self.product_type = PopUpProductType.objects.create(
            name='Sneakers', slug='sneakers'
        )
        self.category = PopUpCategory.objects.create(
            name='Basketball', slug='basketball'
        )
        self.brand = PopUpBrand.objects.create(
            name='Nike', slug='nike'
        )
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='aj1-chicago',
            retail_price=Decimal('180.00'),
            inventory_status='anticipated',
            is_active=True,
        )
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='DZ5485-612',
            release_date=django_timezone.now() + timedelta(days=1),
            search_method='direct_url',
            retail_price=Decimal('180.00'),
            status='scheduled',
        )
        self.proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Air Jordan 1',
            target_size='10',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
        )
        self.service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='10',
            sex='Mens',
            service_fee=Decimal('15.00'),
            fee_paid_at=django_timezone.now(),
            status='success',
            procurement_request=self.proc_request,
        )
        self.execution = ProcurementExecution.objects.create(
            procurement_request=self.proc_request,
            status='success',
            strategy_used='fastest',
            winning_site='nike',
            order_id='ORD-NIKE-98765',
            item_price=Decimal('180.00'),
            started_at=django_timezone.now(),
            completed_at=django_timezone.now(),
        )
 
    # ------------------------------------------------------------------
    # Email sending
    # ------------------------------------------------------------------
 
    def test_success_email_is_sent(self):
        """One email is sent on success."""
        send_success_notification(self.service_request, self.execution)
        self.assertEqual(len(mail.outbox), 1)
 
    def test_success_email_recipient(self):
        """Email goes to the user who paid for procurement."""
        send_success_notification(self.service_request, self.execution)
        self.assertEqual(mail.outbox[0].to, ['buyer@example.com'])
 
    def test_success_email_from_address(self):
        send_success_notification(self.service_request, self.execution)
        self.assertEqual(mail.outbox[0].from_email, 'noreply@popupshop.com')
 
    def test_success_email_subject_contains_product_title(self):
        send_success_notification(self.service_request, self.execution)
        self.assertIn('Air Jordan 1', mail.outbox[0].subject)
 
    def test_success_email_subject_contains_checkmark(self):
        send_success_notification(self.service_request, self.execution)
        self.assertIn('✅', mail.outbox[0].subject)
 
    # ------------------------------------------------------------------
    # HTML content
    # ------------------------------------------------------------------
 
    def test_success_email_contains_user_first_name(self):
        send_success_notification(self.service_request, self.execution)
        self.assertIn('Jordan', mail.outbox[0].alternatives[0][0])
 
    def test_success_email_contains_product_title(self):
        send_success_notification(self.service_request, self.execution)
        self.assertIn('Air Jordan 1', mail.outbox[0].alternatives[0][0])
 
    def test_success_email_contains_size(self):
        send_success_notification(self.service_request, self.execution)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('10', html)
 
    def test_success_email_contains_sex(self):
        send_success_notification(self.service_request, self.execution)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Mens', html)
 
    def test_success_email_contains_service_fee(self):
        send_success_notification(self.service_request, self.execution)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('15', html)
 
    def test_success_email_is_html(self):
        """Email must be sent as HTML (not plain text only)."""
        send_success_notification(self.service_request, self.execution)
        email = mail.outbox[0]
        self.assertTrue(
            hasattr(email, 'alternatives') and len(email.alternatives) > 0,
            'Email should have an HTML alternative'
        )
 
    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
 
    def test_success_email_does_not_raise_on_send_failure(self):
        """Email send errors should be caught — task must not crash."""
        from unittest.mock import patch
        with patch('pop_up_email.utils.send_mail', side_effect=Exception('SMTP down')):
            # Should not raise
            send_success_notification(self.service_request, self.execution)
 
 
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@popupshop.com',
    SITE_URL='https://thepopup.com',
)
class ProcurementFailureEmailTestCase(TestCase):
    """Tests for send_failure_notification"""
 
    def setUp(self):
        self.user, self.user_profile = create_test_user(
            'buyer@example.com', 'testpass!23', 'Jordan', 'Buyer', '10', 'male'
        )
 
        self.product_type = PopUpProductType.objects.create(
            name='Sneakers', slug='sneakers'
        )
        self.category = PopUpCategory.objects.create(
            name='Basketball', slug='basketball'
        )
        self.brand = PopUpBrand.objects.create(
            name='Nike', slug='nike'
        )
        self.product = PopUpProduct.objects.create(
            product_type=self.product_type,
            category=self.category,
            brand=self.brand,
            product_title='Air Jordan 1',
            secondary_product_title='High OG Chicago',
            slug='aj1-chicago-fail',
            retail_price=Decimal('180.00'),
            inventory_status='anticipated',
            is_active=True,
        )
        self.release = ScheduledRelease.objects.create(
            product=self.product,
            sku='DZ5485-612',
            release_date=django_timezone.now() + timedelta(days=1),
            search_method='direct_url',
            retail_price=Decimal('180.00'),
            status='scheduled',
        )
        self.proc_request = ProcurementRequest.objects.create(
            user=self.user,
            product=self.product,
            product_name='Air Jordan 1',
            target_size='10',
            max_price=Decimal('200.00'),
            procurement_type='inventory',
        )
        self.service_request = ProcurementServiceRequest.objects.create(
            user=self.user,
            scheduled_release=self.release,
            size='10',
            sex='Mens',
            service_fee=Decimal('15.00'),
            fee_paid_at=django_timezone.now(),
            status='failed',
            procurement_request=self.proc_request,
        )
 
    # ------------------------------------------------------------------
    # Email sending
    # ------------------------------------------------------------------
 
    def test_failure_email_is_sent(self):
        send_failure_notification(
            self.service_request, 'Item sold out', error_type='out_of_stock'
        )
        self.assertEqual(len(mail.outbox), 1)
 
    def test_failure_email_recipient(self):
        send_failure_notification(
            self.service_request, 'Item sold out', error_type='out_of_stock'
        )
        self.assertEqual(mail.outbox[0].to, ['buyer@example.com'])
 
    def test_failure_email_from_address(self):
        send_failure_notification(
            self.service_request, 'Item sold out', error_type='out_of_stock'
        )
        self.assertEqual(mail.outbox[0].from_email, 'noreply@popupshop.com')
 
    def test_failure_email_subject_contains_product_title(self):
        send_failure_notification(
            self.service_request, 'Item sold out', error_type='out_of_stock'
        )
        self.assertIn('Air Jordan 1', mail.outbox[0].subject)
 
    # ------------------------------------------------------------------
    # Non-refundable errors (market failures)
    # ------------------------------------------------------------------
 
    def test_non_refundable_out_of_stock_email_content(self):
        """out_of_stock is non-refundable — email should NOT mention refund."""
        send_failure_notification(
            self.service_request, 'Sold out', error_type='out_of_stock'
        )
        html = mail.outbox[0].alternatives[0][0]
        # Should contain non-refundable policy explanation
        self.assertIn('non-refundable', html)
        # Should NOT say refund was issued
        self.assertNotIn('Refund Issued', html)
 
    def test_non_refundable_lost_to_bots_email_content(self):
        send_failure_notification(
            self.service_request, 'Lost race', error_type='lost_to_bots'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('non-refundable', html)
        self.assertNotIn('Refund Issued', html)
 
    def test_non_refundable_item_not_found(self):
        send_failure_notification(
            self.service_request, 'Not found', error_type='item_not_found'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('non-refundable', html)
 
    # ------------------------------------------------------------------
    # Refundable errors (code/bot failures)
    # ------------------------------------------------------------------
 
    def test_refundable_bot_crash_email_content(self):
        """bot_crash is refundable — email should confirm refund was issued."""
        send_failure_notification(
            self.service_request, 'Bot crashed', error_type='bot_crash'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Refund Issued', html)
        self.assertNotIn('non-refundable', html)
 
    def test_refundable_rate_limited_email_content(self):
        send_failure_notification(
            self.service_request, 'Rate limited', error_type='rate_limited'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Refund Issued', html)
 
    def test_refundable_site_structure_changed(self):
        send_failure_notification(
            self.service_request,
            'Selectors broken',
            error_type='site_structure_changed'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Refund Issued', html)
 
    def test_refundable_unknown_error(self):
        send_failure_notification(
            self.service_request, 'Unknown', error_type='unknown_error'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Refund Issued', html)
 
    # ------------------------------------------------------------------
    # Content common to all failure emails
    # ------------------------------------------------------------------
 
    def test_failure_email_contains_user_first_name(self):
        send_failure_notification(
            self.service_request, 'Sold out', error_type='out_of_stock'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Jordan', html)
 
    def test_failure_email_contains_product_title(self):
        send_failure_notification(
            self.service_request, 'Sold out', error_type='out_of_stock'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('Air Jordan 1', html)
 
    def test_failure_email_contains_size(self):
        send_failure_notification(
            self.service_request, 'Sold out', error_type='out_of_stock'
        )
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('10', html)
 
    def test_failure_email_is_html(self):
        send_failure_notification(
            self.service_request, 'Sold out', error_type='out_of_stock'
        )
        email = mail.outbox[0]
        self.assertTrue(
            hasattr(email, 'alternatives') and len(email.alternatives) > 0,
            'Email should have an HTML alternative'
        )
 
    def test_failure_email_no_error_type_defaults_gracefully(self):
        """Calling without error_type should not raise."""
        send_failure_notification(self.service_request, 'Something went wrong')
        self.assertEqual(len(mail.outbox), 1)
 
    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------
 
    def test_failure_email_does_not_raise_on_send_failure(self):
        from unittest.mock import patch
        with patch('pop_up_email.utils.send_mail', side_effect=Exception('SMTP down')):
            send_failure_notification(
                self.service_request, 'Sold out', error_type='out_of_stock'
            )
 