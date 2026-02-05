from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from pop_up_order.models import PopUpCustomerOrder
from pop_up_shipping.models import PopUpShipment
from pop_up_auction.tests.conftest import (
    create_seed_data, create_test_user, create_test_product_one, create_test_product_two, create_test_product, 
    create_product_type, create_category, create_brand, create_test_address)


class TestGenerateShippingLabelView(TestCase):
    """Test suite for generate_shipping_label view"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user, self.user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        
        # Create admin user
        self.admin_user, self.admin_profile = create_test_user(
            "admin@example.com", "adminpass!23", "Admin", "User", "10", "male"
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        
        # Create addresses
        self.shipping_address = create_test_address(
            customer=self.user,
            first_name="Test",
            last_name="User",
            address_line="123 Test St",
            address_line2="Apt 4B",
            apartment_suite_number="4B",
            town_city="Test City",
            state="Florida",
            postcode="12345",
            delivery_instructions="Leave at door",
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
        
        # Create shipment for the order
        self.shipment = PopUpShipment.objects.create(
            order=self.order,
            carrier='usps',
            tracking_number='9400111899223744890025',
            status='shipped'
        )
    
    # ─── Basic Rendering ───────────────────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_renders_successfully(self, mock_shipments, mock_orders):
        """Test that shipping label page renders"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pop_up_shipping/shipping_details.html')
    
    # ─── ADMIN_SHIPPING Configuration ──────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    @patch('pop_up_shipping.views.ADMIN_SHIPPING', {
        'page_title': 'Generate Shipping Label',
        'ship_from_options': [
            {
                'organization': 'The Pop Up Shop',
                'street_address': '100 Warehouse Blvd',
                'city': 'Orlando',
                'state': 'FL',
                'zip_code': '32801'
            }
        ]
    })

    def test_generate_shipping_label_displays_page_title(self, mock_shipments, mock_orders):
        """Test that ADMIN_SHIPPING page_title is displayed"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate Shipping Label')
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    @patch('pop_up_shipping.views.ADMIN_SHIPPING', {
        'page_title': 'Shipping Labels',
        'ship_from_options': [
            {
                'organization': 'Warehouse A',
                'street_address': '100 Main St',
                'city': 'Tampa',
                'state': 'FL',
                'zip_code': '33601'
            },
            {
                'organization': 'Warehouse B',
                'street_address': '200 Second Ave',
                'city': 'Miami',
                'state': 'FL',
                'zip_code': '33101'
            }
        ]
    })

    def test_generate_shipping_label_displays_ship_from_options(self, mock_shipments, mock_orders):
        """Test that multiple ship_from_options are displayed"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Both warehouse options should appear
        self.assertContains(response, 'Warehouse A')
        self.assertContains(response, 'Warehouse B')
        self.assertContains(response, '100 Main St')
        self.assertContains(response, '200 Second Ave')
        self.assertContains(response, 'Tampa')
        self.assertContains(response, 'Miami')
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    @patch('pop_up_shipping.views.ADMIN_SHIPPING', {
        'page_title': 'Shipping',
        'ship_from_options': [
            {
                'organization': 'The Pop Up',
                'street_address': '555 Ship St',
                'city': 'Orlando',
                'state': 'FL',
                'zip_code': '32801'
            }
        ]
    })
    def test_generate_shipping_label_displays_from_address_radio_buttons(self, mock_shipments, mock_orders):
        """Test that radio buttons are rendered for ship from addresses"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="radio"')
        self.assertContains(response, 'name="shipping_to"')
        self.assertContains(response, 'from_address_selection')
    
    # ─── Order Information ─────────────────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_displays_order_id(self, mock_shipments, mock_orders):
        """Test that order ID is displayed"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.id))
    
    # ─── Shipping Address Display ──────────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_displays_customer_name(self, mock_shipments, mock_orders):
        """Test that customer shipping name is displayed"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # First and last name from shipping address
        self.assertContains(response, self.shipping_address.first_name)
        self.assertContains(response, self.shipping_address.last_name)
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_displays_street_address(self, mock_shipments, mock_orders):
        """Test that street address is displayed"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '123 Test St')
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_displays_address_line2(self, mock_shipments, mock_orders):
        """Test that address line 2 is displayed when present"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Apt 4B')
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_displays_city_state_zip(self, mock_shipments, mock_orders):
        """Test that city, state, and ZIP are displayed"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test City')
        self.assertContains(response, 'Florida')
        self.assertContains(response, '12345')
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_displays_delivery_instructions(self, mock_shipments, mock_orders):
        """Test that delivery instructions are displayed when present"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leave at door')
    
    # ─── Print Functionality ───────────────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_includes_print_button(self, mock_shipments, mock_orders):
        """Test that print button is present"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Print Shipping Info')
        self.assertContains(response, "printDiv('print_section')")
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_includes_print_section(self, mock_shipments, mock_orders):
        """Test that printable section is properly marked"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="print_section"')
    
    # ─── 404 Handling ──────────────────────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_nonexistent_order_returns_404(self, mock_shipments, mock_orders):
        """Test that requesting label for non-existent order returns 404"""
        self.client.force_login(self.admin_user)
        
        fake_uuid = '99999999-9999-9999-9999-999999999999'
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': fake_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    # ─── Helper Function Calls ─────────────────────────────────────
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_calls_admin_shipments(self, mock_shipments, mock_orders):
        """Test that admin_shipments helper is called"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        mock_shipments.assert_called_once_with(self.order.id)
    
    @patch('pop_up_shipping.views.admin_orders')
    @patch('pop_up_shipping.views.admin_shipments')
    def test_generate_shipping_label_calls_admin_orders(self, mock_shipments, mock_orders):
        """Test that admin_orders helper is called"""
        mock_shipments.return_value = [self.shipment]
        mock_orders.return_value = [self.order]
        
        self.client.force_login(self.admin_user)
        
        url = reverse('pop_up_shipping:generate_shipping_label', kwargs={'order_id': self.order.id})
        response = self.client.get(url)
        
        mock_orders.assert_called_once_with(self.order.id)