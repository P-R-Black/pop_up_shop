from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from pop_up_payment.models import PopUpPayment
from pop_up_order.models import PopUpCustomerOrder
from pop_accounts.models import PopUpCustomerAddress
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand)


def create_test_address(customer, first_name, last_name, address_line, address_line2, 
                       apartment_suite_number, town_city, state, postcode, 
                       delivery_instructions, default=True, is_default_shipping=False,
                       is_default_billing=False):
    
    """Helper function to create customer address"""
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
    

class TestPopUpPaymentModel(TestCase):
    """Test suite for PopUpPayment model"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create billing address
        self.billing_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 Billing St",
            address_line2="",
            apartment_suite_number="",
            town_city="Billing City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=False,
            is_default_billing=True
        )
        
        # Create shipping address (same ZIP)
        self.shipping_address_same_zip = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Shipping Ave",
            address_line2="",
            apartment_suite_number="",
            town_city="Shipping City",
            state="Florida",
            postcode="12345",  # Same ZIP
            delivery_instructions="",
            default=True,
            is_default_shipping=True
        )
        
        # Create shipping address (different ZIP)
        self.shipping_address_diff_zip = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="789 Other St",
            address_line2="",
            apartment_suite_number="",
            town_city="Other City",
            state="Texas",
            postcode="67890",  # Different ZIP
            delivery_instructions="",
            default=False
        )
        
        # Create test order
        self.order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name=f"{self.user.first_name} {self.user.last_name}",
            email=self.user.email,
            # address1='123 Billing St',
            # address2='',
            # apartment_suite_number='',
            # city='Billing City',
            # state='FL',
            # postal_code="12345",
            phone="555-123-4567",
            # billing_status=True,
            billing_address=self.billing_address,
            shipping_address=self.shipping_address_same_zip,
            total_paid=Decimal('215.00')
        )
    
    # ─── Model Creation & Defaults ─────────────────────────────────
    
    def test_payment_creation_with_defaults(self):
        """Test creating payment with default values"""
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertEqual(payment.status, 'pending')
        self.assertFalse(payment.suspicious_flagged)
        self.assertFalse(payment.notified_ready_to_ship)
        self.assertIsNotNone(payment.created_at)
    
    def test_payment_creation_with_all_fields(self):
        """Test creating payment with all fields specified"""
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            status='paid',
            payment_reference='pi_test_123',
            payment_method='stripe',
            suspicious_flagged=True,
            notified_ready_to_ship=True
        )
        
        self.assertEqual(payment.status, 'paid')
        self.assertEqual(payment.payment_reference, 'pi_test_123')
        self.assertTrue(payment.suspicious_flagged)
        self.assertTrue(payment.notified_ready_to_ship)
    
    def test_payment_method_choices(self):
        """Test all payment method choices"""
        methods = ['stripe', 'paypal', 'venmo', 'apple_pay', 'google_pay']
        
        for method in methods:
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('100.00'),
                payment_method=method
            )
            self.assertEqual(payment.payment_method, method)
            payment.delete()  # Clean up for next iteration
    
    def test_status_choices(self):
        """Test all status choices"""
        statuses = ['pending', 'processing', 'in_review', 'disputed', 'paid', 'failed']
        
        for status in statuses:
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('100.00'),
                payment_method='stripe',
                status=status
            )
            self.assertEqual(payment.status, status)
            payment.delete()
    
    def test_one_to_one_relationship_with_order(self):
        """Test that one order can only have one payment"""
        payment1 = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        # Attempting to create another payment for same order should raise error
        with self.assertRaises(Exception):
            payment2 = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='paypal'
            )
    
    def test_ordering_by_created_at_descending(self):
        """Test that payments are ordered by created_at descending"""
        # Create another order for second payment
        order2 = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name=f"{self.user.first_name} {self.user.last_name}",
            email=self.user.email,
            phone="555-123-4567",
            billing_address=self.billing_address,
            shipping_address=self.shipping_address_same_zip,
            total_paid=Decimal('100.00')
        )
        
        payment1 = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        # Wait a moment
        import time
        time.sleep(0.01)
        
        payment2 = PopUpPayment.objects.create(
            order=order2,
            amount=Decimal('100.00'),
            payment_method='paypal'
        )
        
        payments = PopUpPayment.objects.all()
        self.assertEqual(payments[0], payment2)  # Most recent first
        self.assertEqual(payments[1], payment1)
    
    # ─── is_suspicious() Method ────────────────────────────────────
    
    def test_is_suspicious_high_amount_over_500(self):
        """Test that orders over $500 are flagged as suspicious"""
        self.order.total_paid = Decimal('600.00')
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('600.00'),
            payment_method='stripe'
        )
        
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_amount_exactly_500(self):
        """Test that order of exactly $500 is not suspicious"""
        self.order.total_paid = Decimal('500.00')
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('500.00'),
            payment_method='stripe'
        )
        
        self.assertFalse(payment.is_suspicious())
    
    def test_is_suspicious_different_billing_shipping_zip(self):
        """Test that different billing/shipping ZIPs are flagged"""
        self.order.shipping_address = self.shipping_address_diff_zip
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_same_billing_shipping_zip(self):
        """Test that same billing/shipping ZIPs are not flagged"""
        # Order already has same ZIP in setUp
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertFalse(payment.is_suspicious())
    
    def test_is_suspicious_missing_phone(self):
        """Test that missing phone number is flagged"""
        self.order.phone = None
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_empty_phone(self):
        """Test that empty phone string is flagged"""
        self.order.phone = ""
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_invalid_email_no_at_symbol(self):
        """Test that email without @ symbol is flagged"""
        self.order.email = "invalidemail.com"
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_valid_email(self):
        """Test that valid email is not flagged"""
        # Order already has valid email in setUp
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertFalse(payment.is_suspicious())
    
    def test_is_suspicious_missing_billing_address(self):
        """Test that missing billing address is not flagged as suspicious"""
        self.order.billing_address = None
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        # Should return True due to exception handling
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_missing_shipping_address(self):
        """Test that missing shipping address triggers exception handling"""
        self.order.shipping_address = None
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        # Should return True due to exception handling
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_multiple_red_flags(self):
        """Test order with multiple suspicious indicators"""
        self.order.total_paid = Decimal('600.00')
        self.order.shipping_address = self.shipping_address_diff_zip
        self.order.phone = None
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('600.00'),
            payment_method='stripe'
        )
        
        self.assertTrue(payment.is_suspicious())
    
    def test_is_suspicious_clean_order(self):
        """Test completely clean order is not suspicious"""
        self.order.total_paid = Decimal('215.00')  # Under 500
        # Same ZIP (already set in setUp)
        self.order.phone = "555-123-4567"
        self.order.email = "valid@email.com"
        self.order.save()
        
        payment = PopUpPayment.objects.create(
            order=self.order,
            amount=Decimal('215.00'),
            payment_method='stripe'
        )
        
        self.assertFalse(payment.is_suspicious())
    
    # ─── calculate_shipping_release_datetime() ────────────────────
    
    def test_shipping_release_monday_before_4pm(self):
        """Test Mon before 4PM -> 48 hour wait"""
        # Create payment on Monday at 2 PM
        monday_2pm = timezone.make_aware(
            timezone.datetime(2026, 2, 2, 14, 0, 0)  # Monday Feb 2
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = monday_2pm
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            expected = monday_2pm + timedelta(hours=48)
            
            self.assertEqual(release_time, expected)
    
    def test_shipping_release_monday_after_4pm(self):
        """Test Mon after 4PM -> 60 hour wait"""
        # Create payment on Monday at 5 PM
        monday_5pm = timezone.make_aware(
            timezone.datetime(2026, 2, 2, 17, 0, 0)  # Monday Feb 2
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = monday_5pm
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            expected = monday_5pm + timedelta(hours=60)
            
            self.assertEqual(release_time, expected)
    
    def test_shipping_release_wednesday_before_4pm(self):
        """Test Wed before 4PM -> 48 hour wait"""
        wednesday_10am = timezone.make_aware(
            timezone.datetime(2026, 2, 4, 10, 0, 0)  # Wednesday Feb 4
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = wednesday_10am
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            expected = wednesday_10am + timedelta(hours=48)
            
            self.assertEqual(release_time, expected)
    
    def test_shipping_release_wednesday_after_4pm(self):
        """Test Wed after 4PM -> 60 hour wait"""
        wednesday_6pm = timezone.make_aware(
            timezone.datetime(2026, 2, 4, 18, 0, 0)  # Wednesday Feb 4
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = wednesday_6pm
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            expected = wednesday_6pm + timedelta(hours=60)
            
            self.assertEqual(release_time, expected)
    
    def test_shipping_release_thursday_before_4pm(self):
        """Test Thursday before 4PM -> wait until Monday ~8pm"""
        thursday_2pm = timezone.make_aware(
            timezone.datetime(2026, 2, 5, 14, 0, 0)  # Thursday Feb 5
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = thursday_2pm
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            # Should be 4 days + (20 - 14) hours = Mon at 8pm
            expected = thursday_2pm + timedelta(days=4, hours=6)
            
            self.assertEqual(release_time, expected)
    
    def test_shipping_release_thursday_after_4pm(self):
        """Test Thursday after 4PM -> Wednesday 8 AM"""
        thursday_5pm = timezone.make_aware(
            timezone.datetime(2026, 2, 5, 17, 0, 0)  # Thursday Feb 5
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = thursday_5pm
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            # 5 days later at 8 AM
            expected_date = thursday_5pm + timedelta(days=5)
            expected = expected_date.replace(hour=8, minute=0)
            
            self.assertEqual(release_time.date(), expected.date())
            self.assertEqual(release_time.hour, 8)
            self.assertEqual(release_time.minute, 0)
    
    def test_shipping_release_friday(self):
        """Test Friday -> following Tuesday 8 AM"""
        friday_3pm = timezone.make_aware(
            timezone.datetime(2026, 2, 6, 15, 0, 0)  # Friday Feb 6
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = friday_3pm
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            # Friday (4) -> 7 - 4 + 2 = 5 days -> Tuesday
            expected_days = 7 - 4 + 2
            expected_date = friday_3pm + timedelta(days=expected_days)
            expected = expected_date.replace(hour=8, minute=0)
            
            self.assertEqual(release_time.date(), expected.date())
            self.assertEqual(release_time.hour, 8)
    
    def test_shipping_release_saturday(self):
        """Test Saturday -> following Tuesday 8 AM"""
        saturday_noon = timezone.make_aware(
            timezone.datetime(2026, 2, 7, 12, 0, 0)  # Saturday Feb 7
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = saturday_noon
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            # Saturday (5) -> 7 - 5 + 2 = 4 days -> Tuesday
            expected_days = 7 - 5 + 2
            expected_date = saturday_noon + timedelta(days=expected_days)
            
            self.assertEqual(release_time.date(), expected_date.date())
            self.assertEqual(release_time.hour, 8)
    
    def test_shipping_release_sunday(self):
        """Test Sunday -> following Tuesday 8 AM"""
        sunday_9am = timezone.make_aware(
            timezone.datetime(2026, 2, 8, 9, 0, 0)  # Sunday Feb 8
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = sunday_9am
            payment.save()
            
            release_time = payment.calculate_shipping_release_datetime()
            # Sunday (6) -> 7 - 6 + 2 = 3 days -> Tuesday
            expected_days = 7 - 6 + 2
            expected_date = sunday_9am + timedelta(days=expected_days)
            
            self.assertEqual(release_time.date(), expected_date.date())
            self.assertEqual(release_time.hour, 8)
    
    # ─── release_at_computed Property ──────────────────────────────
    
    def test_release_at_computed_property(self):
        """Test that release_at_computed calls calculate_shipping_release_datetime"""
        monday_2pm = timezone.make_aware(
            timezone.datetime(2026, 2, 2, 14, 0, 0)
        )
        
        with timezone.override('America/New_York'):
            payment = PopUpPayment.objects.create(
                order=self.order,
                amount=Decimal('215.00'),
                payment_method='stripe'
            )
            payment.created_at = monday_2pm
            payment.save()
            
            # Both should return the same value
            self.assertEqual(
                payment.release_at_computed,
                payment.calculate_shipping_release_datetime()
            )