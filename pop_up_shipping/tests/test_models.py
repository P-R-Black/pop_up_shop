from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from pop_up_shipping.models import PopUpShipment
from pop_up_order.models import PopUpCustomerOrder
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_address)


class TestPopUpShipmentModel(TestCase):
    """Test suite for PopUpShipment model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        self.shipping_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 Test St",
            address_line2="",
            apartment_suite_number="",
            town_city="Test City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=True,
            is_default_shipping=True,
            is_default_billing=False
        )
        
        self.billing_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="456 Billing Ave",
            address_line2="",
            apartment_suite_number="",
            town_city="Billing City",
            state="Florida",
            postcode="12345",
            delivery_instructions="",
            default=False,
            is_default_shipping=False,
            is_default_billing=True
        )
        
        # Create test order
        self.order = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name=f"{self.user.first_name} {self.user.last_name}",
            email=self.user.email,
            phone="555-123-4567",
            billing_address=self.billing_address,
            shipping_address=self.shipping_address,
            total_paid=Decimal('215.00')
        )
        
        # Create second order for tests that need multiple orders
        self.order2 = PopUpCustomerOrder.objects.create(
            user=self.user,
            full_name=f"{self.user.first_name} {self.user.last_name}",
            email=self.user.email,
            phone="555-123-4567",
            billing_address=self.billing_address,
            shipping_address=self.shipping_address,
            total_paid=Decimal('180.00')
        )
    
    # ─── Model Creation & Defaults ─────────────────────────────────
    
    def test_shipment_creation_with_defaults(self):
        """Test creating shipment with default values"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        self.assertEqual(shipment.carrier, 'n/a')
        self.assertEqual(shipment.status, 'pending')
        self.assertIsNone(shipment.tracking_number)
        self.assertIsNone(shipment.shipped_at)
        self.assertIsNone(shipment.estimated_delivery)
        self.assertIsNone(shipment.delivered_at)
    
    def test_shipment_creation_with_all_fields(self):
        """Test creating shipment with all fields specified"""
        shipped_time = timezone.now()
        estimated_delivery = shipped_time + timedelta(days=5)
        
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps',
            tracking_number='9400111899223744890025',
            shipped_at=shipped_time,
            estimated_delivery=estimated_delivery,
            status='shipped'
        )
        
        self.assertEqual(shipment.carrier, 'usps')
        self.assertEqual(shipment.tracking_number, '9400111899223744890025')
        self.assertEqual(shipment.shipped_at, shipped_time)
        self.assertEqual(shipment.estimated_delivery, estimated_delivery)
        self.assertEqual(shipment.status, 'shipped')
    
    def test_shipment_str_representation(self):
        """Test __str__ returns order_id"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        self.assertEqual(str(shipment), str(self.order.id))
    
    # ─── Carrier Choices ───────────────────────────────────────────
    
    def test_carrier_default_is_na(self):
        """Test that carrier defaults to n/a"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        self.assertEqual(shipment.carrier, 'n/a')
    
    def test_carrier_usps(self):
        """Test setting carrier to USPS"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps'
        )
        
        self.assertEqual(shipment.carrier, 'usps')
    
    def test_carrier_ups(self):
        """Test setting carrier to UPS"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='ups'
        )
        
        self.assertEqual(shipment.carrier, 'ups')
    
    def test_carrier_fedex(self):
        """Test setting carrier to FedEx"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='FedEx'
        )
        
        self.assertEqual(shipment.carrier, 'FedEx')
    
    # ─── Status Choices ────────────────────────────────────────────
    
    def test_status_default_is_pending(self):
        """Test that status defaults to pending"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        self.assertEqual(shipment.status, 'pending')
    
    def test_status_transitions(self):
        """Test typical shipment status flow: pending -> shipped -> delivered"""
        shipment = PopUpShipment.objects.create(order=self.order)
        self.assertEqual(shipment.status, 'pending')
        
        # Admin ships order
        shipment.status = 'shipped'
        shipment.carrier = 'usps'
        shipment.tracking_number = '9400111899223744890025'
        shipment.shipped_at = timezone.now()
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'shipped')
        self.assertIsNotNone(shipment.shipped_at)
        
        # Order delivered
        shipment.status = 'delivered'
        shipment.delivered_at = timezone.now()
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'delivered')
        self.assertIsNotNone(shipment.delivered_at)
    
    def test_status_cancelled(self):
        """Test setting status to cancelled"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            status='cancelled'
        )
        
        self.assertEqual(shipment.status, 'cancelled')
    
    def test_status_in_dispute(self):
        """Test setting status to in_dispute"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            status='in_dispute'
        )
        
        self.assertEqual(shipment.status, 'in_dispute')
    
    def test_status_returned(self):
        """Test setting status to returned"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            status='returned'
        )
        
        self.assertEqual(shipment.status, 'returned')
    
    # ─── One-to-One Relationship ───────────────────────────────────
    
    def test_one_shipment_per_order(self):
        """Test that each order can only have one shipment"""
        PopUpShipment.objects.create(order=self.order)
        
        with self.assertRaises(Exception):
            PopUpShipment.objects.create(order=self.order)
    
    def test_shipment_accessible_from_order(self):
        """Test that shipment can be accessed via order.shipment"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='ups',
            status='shipped'
        )
        
        # Access shipment through related_name
        self.assertEqual(self.order.shipment, shipment)
        self.assertEqual(self.order.shipment.carrier, 'ups')
    
    def test_different_orders_can_have_shipments(self):
        """Test that different orders can each have their own shipment"""
        shipment1 = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps',
            tracking_number='TRACKING_1'
        )
        
        shipment2 = PopUpShipment.objects.create(
            order=self.order2,
            carrier='ups',
            tracking_number='TRACKING_2'
        )
        
        self.assertEqual(PopUpShipment.objects.count(), 2)
        self.assertEqual(self.order.shipment.tracking_number, 'TRACKING_1')
        self.assertEqual(self.order2.shipment.tracking_number, 'TRACKING_2')
    
    # ─── Tracking Number ──────────────────────────────────────────
    
    def test_tracking_number_nullable(self):
        """Test that tracking number can be null (before shipping)"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        self.assertIsNone(shipment.tracking_number)
    
    def test_tracking_number_set_when_shipped(self):
        """Test setting tracking number when admin ships order"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        shipment.tracking_number = '1Z999AA10123456784'
        shipment.carrier = 'ups'
        shipment.status = 'shipped'
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.tracking_number, '1Z999AA10123456784')
    
    def test_tracking_number_blank(self):
        """Test that tracking number can be blank string"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            tracking_number=''
        )
        
        self.assertEqual(shipment.tracking_number, '')
    
    # ─── Admin Workflow (typical admin updates) ───────────────────
    
    def test_admin_ships_order_workflow(self):
        """Test complete workflow when admin ships an order"""
        # Order is placed - shipment starts as pending
        shipment = PopUpShipment.objects.create(order=self.order)
        self.assertEqual(shipment.status, 'pending')
        self.assertEqual(shipment.carrier, 'n/a')
        
        # Admin selects carrier and enters tracking number
        shipped_time = timezone.now()
        shipment.carrier = 'usps'
        shipment.tracking_number = '9400111899223744890025'
        shipment.shipped_at = shipped_time
        shipment.estimated_delivery = shipped_time + timedelta(days=3)
        shipment.status = 'shipped'
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'shipped')
        self.assertEqual(shipment.carrier, 'usps')
        self.assertEqual(shipment.tracking_number, '9400111899223744890025')
        self.assertIsNotNone(shipment.shipped_at)
        self.assertIsNotNone(shipment.estimated_delivery)
    
    def test_admin_marks_order_delivered(self):
        """Test admin marking order as delivered"""
        delivered_time = timezone.now()
        
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='fedex',
            tracking_number='ABC123',
            status='shipped',
            shipped_at=timezone.now() - timedelta(days=3)
        )
        
        # Admin marks as delivered
        shipment.status = 'delivered'
        shipment.delivered_at = delivered_time
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'delivered')
        self.assertEqual(shipment.delivered_at, delivered_time)
    
    def test_admin_cancels_shipment(self):
        """Test admin cancelling a pending shipment"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        shipment.status = 'cancelled'
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'cancelled')
    
    def test_admin_flags_disputed_shipment(self):
        """Test admin flagging a shipment as in dispute"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='ups',
            tracking_number='UPS123',
            status='shipped'
        )
        
        shipment.status = 'in_dispute'
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'in_dispute')
    
    def test_admin_marks_order_returned(self):
        """Test admin marking an order as returned"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps',
            tracking_number='USPS123',
            status='delivered',
            shipped_at=timezone.now() - timedelta(days=5),
            delivered_at=timezone.now() - timedelta(days=2)
        )
        
        shipment.status = 'returned'
        shipment.save()
        
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'returned')
    
    # ─── Timestamps ────────────────────────────────────────────────
    
    def test_shipped_at_null_before_shipping(self):
        """Test that shipped_at is null before admin ships"""
        shipment = PopUpShipment.objects.create(order=self.order)
        
        self.assertIsNone(shipment.shipped_at)
    
    def test_delivered_at_null_before_delivery(self):
        """Test that delivered_at is null before delivery"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            status='shipped',
            shipped_at=timezone.now()
        )
        
        self.assertIsNone(shipment.delivered_at)
    
    def test_estimated_delivery_set_by_admin(self):
        """Test that admin can set estimated delivery date"""
        shipped_time = timezone.now()
        estimated = shipped_time + timedelta(days=5)
        
        shipment = PopUpShipment.objects.create(
            order=self.order,
            status='shipped',
            shipped_at=shipped_time,
            estimated_delivery=estimated
        )
        
        self.assertEqual(shipment.estimated_delivery, estimated)
    
    def test_delivery_before_estimated(self):
        """Test order delivered before estimated delivery date"""
        shipped_time = timezone.now() - timedelta(days=3)
        estimated = shipped_time + timedelta(days=5)
        delivered_early = shipped_time + timedelta(days=2)  # Delivered early
        
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='ups',
            status='delivered',
            shipped_at=shipped_time,
            estimated_delivery=estimated,
            delivered_at=delivered_early
        )
        
        # Delivered before estimated
        self.assertLess(shipment.delivered_at, shipment.estimated_delivery)
    
    def test_delivery_after_estimated(self):
        """Test order delivered after estimated delivery date (late)"""
        shipped_time = timezone.now() - timedelta(days=7)
        estimated = shipped_time + timedelta(days=3)
        delivered_late = shipped_time + timedelta(days=6)  # Delivered late
        
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps',
            status='delivered',
            shipped_at=shipped_time,
            estimated_delivery=estimated,
            delivered_at=delivered_late
        )
        
        # Delivered after estimated
        self.assertGreater(shipment.delivered_at, shipment.estimated_delivery)
    
    # ─── Cascade Delete ────────────────────────────────────────────
    
    def test_shipment_deleted_when_order_deleted(self):
        """Test that shipment is deleted when order is deleted (CASCADE)"""
        shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps',
            status='shipped'
        )
        shipment_id = shipment.id
        
        # Delete the order
        self.order.delete()
        
        # Shipment should also be deleted
        self.assertFalse(PopUpShipment.objects.filter(id=shipment_id).exists())