# ============================================================
# End-to-end tests for the procurement service fee refund flow.
# Tests cover:
#   - auto_refund_service_fee() in tasks.py
#   - should_refund_service_fee() logic
#   - ServiceFeePaymentHandler.refund_payment() routing
#   - ServicePayment creation in CreateOrderAfterPaymentView
# ============================================================

import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from pop_up_auction.models import (
    PopUpProduct, PopUpProductType, PopUpCategory, PopUpBrand
)
from pop_up_bot.models import (
    ScheduledRelease, ProcurementServiceRequest,
    ProcurementRequest, ProcurementExecution,
)
from pop_up_cart.models import ProcurementCartItem
from pop_up_payment.models import ServicePayment
from pop_up_bot.tasks import (
    auto_refund_service_fee,
    should_refund_service_fee,
    REFUNDABLE_ERRORS,
    NON_REFUNDABLE_ERRORS,
)
from pop_up_auction.tests.conftest import create_test_user, create_test_address


# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------

def make_product():
    pt = PopUpProductType.objects.get_or_create(name='Sneakers', slug='sneakers')[0]
    cat = PopUpCategory.objects.get_or_create(name='Basketball', slug='basketball')[0]
    brand = PopUpBrand.objects.get_or_create(name='Nike', slug='nike')[0]
    return PopUpProduct.objects.create(
        product_type=pt, category=cat, brand=brand,
        product_title='Air Jordan 1',
        secondary_product_title='High OG Chicago',
        slug='aj1-refund-test',
        retail_price=Decimal('180.00'),
        inventory_status='anticipated',
        is_active=True,
    )


def make_release(product):
    return ScheduledRelease.objects.create(
        product=product,
        sku='DZ5485-612',
        release_date=timezone.now() + timezone.timedelta(days=1),
        retail_price=Decimal('180.00'),
        search_method='direct_url',
        status='scheduled',
    )


def make_psr(user, release, size='10', sex='Mens'):
    req = ProcurementRequest.objects.create(
        user=user, product=release.product,
        product_name='Air Jordan 1', target_size=size,
        max_price=Decimal('200.00'), procurement_type='inventory',
    )
    psr = ProcurementServiceRequest.objects.create(
        user=user, scheduled_release=release,
        size=size, sex=sex,
        service_fee=Decimal('15.00'),
        fee_paid_at=timezone.now(),
        status='pending',
        procurement_request=req,
    )
    return psr, req


def make_execution(req, status='failed', error_type='out_of_stock'):
    return ProcurementExecution.objects.create(
        procurement_request=req,
        status=status,
        strategy_used='fastest',
        error_type=error_type,
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )


def make_service_payment(psr, payment_method='stripe',
                          payment_reference='pi_test_123'):
    return ServicePayment.objects.create(
        service_request=psr,
        amount=Decimal('15.00'),
        status='paid',
        payment_method=payment_method,
        payment_reference=payment_reference,
    )


# ============================================================
# 1. should_refund_service_fee() logic
# ============================================================

class ShouldRefundServiceFeeTestCase(TestCase):
    """Tests for the refundable/non-refundable error type logic."""

    def test_bot_crash_is_refundable(self):
        self.assertTrue(should_refund_service_fee('bot_crash'))

    def test_rate_limited_is_refundable(self):
        self.assertTrue(should_refund_service_fee('rate_limited'))

    def test_site_structure_changed_is_refundable(self):
        self.assertTrue(should_refund_service_fee('site_structure_changed'))

    def test_exception_is_refundable(self):
        self.assertTrue(should_refund_service_fee('exception'))

    def test_unknown_error_is_refundable(self):
        self.assertTrue(should_refund_service_fee('unknown_error'))

    def test_out_of_stock_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee('out_of_stock'))

    def test_lost_to_bots_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee('lost_to_bots'))

    def test_item_not_found_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee('item_not_found'))

    def test_sold_out_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee('sold_out'))

    def test_coming_soon_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee('coming_soon'))

    def test_none_error_type_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee(None))

    def test_empty_string_is_not_refundable(self):
        self.assertFalse(should_refund_service_fee(''))

    def test_all_refundable_errors_return_true(self):
        for error_type in REFUNDABLE_ERRORS:
            self.assertTrue(
                should_refund_service_fee(error_type),
                f"Expected {error_type} to be refundable"
            )

    def test_all_non_refundable_errors_return_false(self):
        for error_type in NON_REFUNDABLE_ERRORS:
            self.assertFalse(
                should_refund_service_fee(error_type),
                f"Expected {error_type} to be non-refundable"
            )


# ============================================================
# 2. auto_refund_service_fee() end-to-end
# ============================================================

class AutoRefundServiceFeeTestCase(TestCase):
    """Tests for auto_refund_service_fee() in tasks.py."""

    def setUp(self):
        self.user, _ = create_test_user(
            'refund@test.com', 'testpass!23', 'Refund', 'User', '10', 'male'
        )
        self.product = make_product()
        self.release = make_release(self.product)
        self.psr, self.req = make_psr(self.user, self.release)

    # ------------------------------------------------------------------
    # Non-refundable errors — fee kept
    # ------------------------------------------------------------------

    def test_out_of_stock_does_not_refund(self):
        make_service_payment(self.psr)
        result = auto_refund_service_fee(self.req, error_type='out_of_stock')
        self.assertFalse(result)

        payment = ServicePayment.objects.get(service_request=self.psr)
        self.assertEqual(payment.status, 'paid')

    def test_lost_to_bots_does_not_refund(self):
        make_service_payment(self.psr)
        result = auto_refund_service_fee(self.req, error_type='lost_to_bots')
        self.assertFalse(result)

    def test_item_not_found_does_not_refund(self):
        make_service_payment(self.psr)
        result = auto_refund_service_fee(self.req, error_type='item_not_found')
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # Refundable errors — fee returned
    # ------------------------------------------------------------------

    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler')
    def test_bot_crash_triggers_refund(self, mock_handler_class):
        mock_handler = MagicMock()
        mock_handler.refund_payment.return_value = (True, 're_test_botcrash123')
        mock_handler_class.return_value = mock_handler

        make_service_payment(self.psr)
        result = auto_refund_service_fee(
            self.req, error_type='bot_crash',
            reason='Bot crashed during checkout'
        )

        self.assertTrue(result)
        payment = ServicePayment.objects.get(service_request=self.psr)
        self.assertEqual(payment.status, 'refunded')
        self.assertEqual(payment.refund_reference, 're_test_botcrash123')
        self.assertIsNotNone(payment.refunded_at)

    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler')
    def test_rate_limited_triggers_refund(self, mock_handler_class):
        mock_handler = MagicMock()
        mock_handler.refund_payment.return_value = (True, 're_test_ratelimit456')
        mock_handler_class.return_value = mock_handler

        make_service_payment(self.psr)
        result = auto_refund_service_fee(self.req, error_type='rate_limited')

        self.assertTrue(result)
        payment = ServicePayment.objects.get(service_request=self.psr)
        self.assertEqual(payment.status, 'refunded')

    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler')
    def test_site_structure_changed_triggers_refund(self, mock_handler_class):
        mock_handler = MagicMock()
        mock_handler.refund_payment.return_value = (True, 're_test_selector789')
        mock_handler_class.return_value = mock_handler

        make_service_payment(self.psr)
        result = auto_refund_service_fee(
            self.req, error_type='site_structure_changed'
        )
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_no_service_payment_returns_false(self):
        """If no ServicePayment exists, refund gracefully returns False."""
        result = auto_refund_service_fee(self.req, error_type='bot_crash')
        self.assertFalse(result)

    def test_already_refunded_payment_returns_false(self):
        """Don't double-refund."""
        payment = make_service_payment(self.psr)
        payment.mark_refunded('re_already_done')

        result = auto_refund_service_fee(self.req, error_type='bot_crash')
        self.assertFalse(result)

    def test_failed_payment_status_returns_false(self):
        """If payment itself failed, nothing to refund."""
        payment = make_service_payment(self.psr)
        payment.status = 'failed'
        payment.save()

        result = auto_refund_service_fee(self.req, error_type='bot_crash')
        self.assertFalse(result)

    def test_no_service_request_linked_returns_false(self):
        """ProcurementRequest with no linked service request."""
        standalone_req = ProcurementRequest.objects.create(
            user=self.user, product=self.product,
            product_name='Air Jordan 1', target_size='10',
            max_price=Decimal('200.00'), procurement_type='inventory',
        )
        result = auto_refund_service_fee(standalone_req, error_type='bot_crash')
        self.assertFalse(result)

    @patch('pop_up_bot.tasks.ServiceFeePaymentHandler')
    def test_stripe_refund_failure_returns_false(self, mock_handler_class):
        """If Stripe refund API call fails, return False and don't mark refunded."""
        mock_handler = MagicMock()
        mock_handler.refund_payment.return_value = (False, 'Stripe API error')
        mock_handler_class.return_value = mock_handler

        make_service_payment(self.psr)
        result = auto_refund_service_fee(self.req, error_type='bot_crash')

        self.assertFalse(result)
        payment = ServicePayment.objects.get(service_request=self.psr)
        self.assertEqual(payment.status, 'paid')  # unchanged


# ============================================================
# 3. ServiceFeePaymentHandler refund routing
# ============================================================

class ServiceFeePaymentHandlerRefundTestCase(TestCase):
    """Tests for payment method routing in refund_payment()."""

    def setUp(self):
        self.user, _ = create_test_user(
            'handler@test.com', 'testpass!23', 'Handler', 'User', '10', 'male'
        )
        self.product = make_product()
        self.release = make_release(self.product)
        self.psr, self.req = make_psr(self.user, self.release)

    @patch('pop_up_payment.handlers.service_fee_handler.stripe')
    def test_stripe_refund_routes_correctly(self, mock_stripe):
        mock_stripe.Refund.create.return_value = MagicMock(id='re_stripe_test')

        payment = make_service_payment(self.psr, payment_method='stripe',
                                        payment_reference='pi_test_abc')

        from pop_up_payment.handlers.service_fee_handler import ServiceFeePaymentHandler
        handler = ServiceFeePaymentHandler()
        success, refund_id = handler.refund_payment(payment)

        self.assertTrue(success)
        self.assertEqual(refund_id, 're_stripe_test')
        mock_stripe.Refund.create.assert_called_once_with(
            payment_intent='pi_test_abc',
            reason='requested_by_customer'
        )

    @patch('pop_up_payment.handlers.service_fee_handler.stripe')
    def test_stripe_refund_handles_api_error(self, mock_stripe):
        mock_stripe.Refund.create.side_effect = Exception('Card declined')

        payment = make_service_payment(self.psr, payment_method='stripe',
                                        payment_reference='pi_test_fail')

        from pop_up_payment.handlers.service_fee_handler import ServiceFeePaymentHandler
        handler = ServiceFeePaymentHandler()
        success, error = handler.refund_payment(payment)

        self.assertFalse(success)
        self.assertIn('Card declined', error)

    def test_unknown_payment_method_returns_false(self):
        payment = make_service_payment(self.psr, payment_method='stripe')
        payment.payment_method = 'crypto'
        payment.save()

        from pop_up_payment.handlers.service_fee_handler import ServiceFeePaymentHandler
        handler = ServiceFeePaymentHandler()
        success, error = handler.refund_payment(payment)

        self.assertFalse(success)
        self.assertIn('Unknown payment method', error)

    def test_missing_payment_reference_returns_false(self):
        payment = make_service_payment(self.psr)
        payment.payment_reference = None
        payment.save()

        from pop_up_payment.handlers.service_fee_handler import ServiceFeePaymentHandler
        handler = ServiceFeePaymentHandler()
        success, error = handler.refund_payment(payment)

        self.assertFalse(success)


# ============================================================
# 4. ServicePayment creation in CreateOrderAfterPaymentView
# ============================================================

class ServicePaymentCreationInOrderViewTestCase(TestCase):
    """
    Tests that CreateOrderAfterPaymentView creates a ServicePayment
    record when a procurement cart item is present at checkout.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse('pop_up_order:create_after_payment')

        self.user, _ = create_test_user(
            'order@test.com', 'testpass!23', 'Order', 'User', '10', 'male'
        )
        self.client.force_login(self.user)

        self.shipping_address = create_test_address(
            customer=self.user,
            first_name='Order', last_name='User',
            address_line='123 Test St', address_line2='',
            apartment_suite_number='', town_city='Test City',
            state='Florida', postcode='32801',
            delivery_instructions='', default=True,
            is_default_shipping=True, is_default_billing=False
        )
        self.billing_address = create_test_address(
            customer=self.user,
            first_name='Order', last_name='User',
            address_line='456 Bill Ave', address_line2='',
            apartment_suite_number='', town_city='Bill City',
            state='Florida', postcode='32802',
            delivery_instructions='', default=False,
            is_default_shipping=False, is_default_billing=True
        )

        # Create procurement product singleton
        service_type = PopUpProductType.objects.get_or_create(
            slug='service', defaults={'name': 'Service', 'is_active': True}
        )[0]
        service_cat = PopUpCategory.objects.get_or_create(
            slug='service', defaults={'name': 'Service'}
        )[0]
        service_brand = PopUpBrand.objects.get_or_create(
            slug='pop-up-shop', defaults={'name': 'Pop Up Shop'}
        )[0]
        self.procurement_product = PopUpProduct.objects.create(
            product_type=service_type, category=service_cat,
            brand=service_brand,
            product_title='Procurement Service Fee',
            slug='procurement-service-fee',
            retail_price=Decimal('15.00'),
            buy_now_price=Decimal('15.00'),
            inventory_status='in_inventory', is_active=False,
        )

        # Set up procurement request and cart item
        self.product = make_product()
        self.release = make_release(self.product)
        self.psr, self.req = make_psr(self.user, self.release)
        self.cart_item = ProcurementCartItem.objects.create(
            user=self.user,
            procurement_service_request=self.psr,
            fee_amount=Decimal('15.00'),
        )

    def _get_valid_payload(self):
        return {
            'payment_data_id': 'pi_test_servicepayment',
            'payment_method': 'stripe',
            'order_key': f'ORDER-SP-001',
            'user_id': str(self.user.id),
            'total_paid': '15.00',
            'email': 'order@test.com',
            'address1': '123 Test St',
            'address2': '',
            'postal_code': '32801',
            'apartment_suite_number': '',
            'city': 'Test City',
            'state': 'Florida',
            'phone': '407-555-1234',
            'shippingAddressId': str(self.shipping_address.id),
            'billingAddressId': str(self.billing_address.id),
            'discount': 0,
        }

    @patch('pop_up_order.views.get_procurement_service_product')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    @patch('pop_up_order.views.stripe')
    def test_service_payment_created_on_checkout(
        self, mock_stripe, mock_email,
        mock_fees, mock_procurement_product
    ):
        """ServicePayment record is created when procurement cart item checked out."""
        mock_stripe.Customer.create.return_value = MagicMock(id='cus_test')
        mock_stripe.PaymentIntent.retrieve.return_value = MagicMock(
            payment_method='pm_test'
        )
        mock_stripe.PaymentMethod.attach.return_value = MagicMock()
        mock_fees.return_value = Decimal('0.44')
        mock_procurement_product.return_value = self.procurement_product

        self.assertFalse(
            ServicePayment.objects.filter(service_request=self.psr).exists()
        )

        response = self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ServicePayment.objects.filter(service_request=self.psr).exists()
        )

        payment = ServicePayment.objects.get(service_request=self.psr)
        self.assertEqual(payment.status, 'paid')
        self.assertEqual(payment.payment_method, 'stripe')
        self.assertEqual(payment.payment_reference, 'pi_test_servicepayment')
        self.assertEqual(payment.amount, Decimal('15.00'))

    @patch('pop_up_order.views.get_procurement_service_product')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    @patch('pop_up_order.views.stripe')
    def test_procurement_cart_item_deleted_after_checkout(
        self, mock_stripe, mock_email,
        mock_fees, mock_procurement_product
    ):
        """ProcurementCartItem is removed after successful checkout."""
        mock_stripe.Customer.create.return_value = MagicMock(id='cus_test2')
        mock_stripe.PaymentIntent.retrieve.return_value = MagicMock(
            payment_method='pm_test2'
        )
        mock_stripe.PaymentMethod.attach.return_value = MagicMock()
        mock_fees.return_value = Decimal('0.44')
        mock_procurement_product.return_value = self.procurement_product

        self.assertEqual(
            ProcurementCartItem.objects.filter(user=self.user).count(), 1
        )

        self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )

        self.assertEqual(
            ProcurementCartItem.objects.filter(user=self.user).count(), 0
        )

    @patch('pop_up_order.views.get_procurement_service_product')
    @patch('pop_up_order.views.get_fees_by_payment')
    @patch('pop_up_order.views.send_order_confirmation_email')
    @patch('pop_up_order.views.stripe')
    def test_psr_status_updated_to_pending_after_checkout(
        self, mock_stripe, mock_email,
        mock_fees, mock_procurement_product
    ):
        """ProcurementServiceRequest status moves to 'pending' after payment."""
        mock_stripe.Customer.create.return_value = MagicMock(id='cus_test3')
        mock_stripe.PaymentIntent.retrieve.return_value = MagicMock(
            payment_method='pm_test3'
        )
        mock_stripe.PaymentMethod.attach.return_value = MagicMock()
        mock_fees.return_value = Decimal('0.44')
        mock_procurement_product.return_value = self.procurement_product

        self.client.post(
            self.url,
            data=json.dumps(self._get_valid_payload()),
            content_type='application/json'
        )

        self.psr.refresh_from_db()
        self.assertEqual(self.psr.status, 'pending')
        self.assertIsNotNone(self.psr.fee_paid_at)