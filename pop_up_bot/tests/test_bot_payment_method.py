# ============================================================
# pop_up_bot/tests/test_bot_payment_method.py
# ============================================================

from decimal import Decimal
from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import MagicMock, patch
import uuid

from pop_up_bot.models import BotPaymentMethod, ProcurementExecution, ProcurementRequest
from pop_up_bot.vault.credential_vault import CredentialVault
from pop_up_auction.models import PopUpProduct, PopUpProductType, PopUpCategory, PopUpBrand
from pop_up_auction.tests.conftest import create_test_user

# Stable test encryption key — safe to commit, test-only
TEST_ENCRYPTION_KEY = 'GNZaHk-XPb__Nkmfs0QTMJmZuF6wlBmrzyqHgdhtzk8='


def make_product():
    pt = PopUpProductType.objects.get_or_create(name='Sneakers', slug='sneakers')[0]
    cat = PopUpCategory.objects.get_or_create(name='Basketball', slug='basketball')[0]
    brand = PopUpBrand.objects.get_or_create(name='Nike', slug='nike')[0]
    return PopUpProduct.objects.create(
        product_type=pt, category=cat, brand=brand,
        product_title='Air Jordan 1', slug=f'aj1-{uuid.uuid4().hex[:6]}',
        retail_price=Decimal('180.00'), is_active=True,
    )


def make_execution(user, product):
    req = ProcurementRequest.objects.create(
        user=user, product=product,
        product_name='Air Jordan 1', target_size='10',
        max_price=Decimal('200.00'), procurement_type='inventory',
    )
    return ProcurementExecution.objects.create(
        procurement_request=req,
        status='running',
        strategy_used='fastest',
        started_at=timezone.now(),
    )


@override_settings(ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BotPaymentMethodEncryptionTestCase(TestCase):
    """Tests for encryption/decryption of card details."""

    def test_encrypt_and_decrypt_card_number(self):
        token = BotPaymentMethod.encrypt('4111111111111111')
        self.assertNotEqual(token, '4111111111111111')
        self.assertEqual(BotPaymentMethod.decrypt(token), '4111111111111111')

    def test_encrypt_and_decrypt_cvv(self):
        token = BotPaymentMethod.encrypt('123')
        self.assertEqual(BotPaymentMethod.decrypt(token), '123')

    def test_encrypt_and_decrypt_expiry(self):
        token = BotPaymentMethod.encrypt('09/27')
        self.assertEqual(BotPaymentMethod.decrypt(token), '09/27')

    def test_encrypt_and_decrypt_pin(self):
        token = BotPaymentMethod.encrypt('7890')
        self.assertEqual(BotPaymentMethod.decrypt(token), '7890')

    def test_encrypted_value_differs_from_plaintext(self):
        token = BotPaymentMethod.encrypt('4111111111111111')
        self.assertNotIn('4111111111111111', token)

    def test_missing_encryption_key_raises(self):
        with override_settings(ENCRYPTION_KEY=None):
            with self.assertRaises(ValueError):
                BotPaymentMethod.encrypt('test')


@override_settings(ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BotPaymentMethodModelTestCase(TestCase):
    """Tests for BotPaymentMethod model fields and properties."""

    def _make_credit_card(self, **kwargs):
        defaults = dict(
            label='Test Visa ···4242',
            method_type='credit_card',
            encrypted_number=BotPaymentMethod.encrypt('4242424242424242'),
            encrypted_cvv=BotPaymentMethod.encrypt('123'),
            encrypted_expiry=BotPaymentMethod.encrypt('12/28'),
            last_four='4242',
            available_balance=None,
            is_active=True,
        )
        defaults.update(kwargs)
        return BotPaymentMethod.objects.create(**defaults)

    def _make_gift_card(self, balance=Decimal('100.00'), **kwargs):
        defaults = dict(
            label='Nike Gift Card ···0001',
            method_type='gift_card',
            encrypted_number=BotPaymentMethod.encrypt('1234567890120001'),
            encrypted_pin=BotPaymentMethod.encrypt('1234'),
            last_four='0001',
            available_balance=balance,
            is_active=True,
        )
        defaults.update(kwargs)
        return BotPaymentMethod.objects.create(**defaults)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def test_card_number_property_decrypts(self):
        card = self._make_credit_card()
        self.assertEqual(card.card_number, '4242424242424242')

    def test_cvv_property_decrypts(self):
        card = self._make_credit_card()
        self.assertEqual(card.cvv, '123')

    def test_expiry_property_decrypts(self):
        card = self._make_credit_card()
        self.assertEqual(card.expiry, '12/28')

    def test_pin_property_decrypts(self):
        card = self._make_gift_card()
        self.assertEqual(card.pin, '1234')

    def test_cvv_returns_empty_string_when_null(self):
        card = self._make_gift_card()
        self.assertEqual(card.cvv, '')

    def test_str_shows_last_four(self):
        card = self._make_credit_card()
        self.assertIn('4242', str(card))

    # ------------------------------------------------------------------
    # Balance checks
    # ------------------------------------------------------------------

    def test_credit_card_with_no_balance_is_sufficient(self):
        """Credit cards with unknown balance assumed OK."""
        card = self._make_credit_card(available_balance=None)
        self.assertTrue(card.has_sufficient_balance(Decimal('500.00')))

    def test_gift_card_sufficient_balance(self):
        card = self._make_gift_card(balance=Decimal('200.00'))
        self.assertTrue(card.has_sufficient_balance(Decimal('180.00')))

    def test_gift_card_insufficient_balance(self):
        card = self._make_gift_card(balance=Decimal('50.00'))
        self.assertFalse(card.has_sufficient_balance(Decimal('180.00')))

    def test_gift_card_exact_balance_is_sufficient(self):
        card = self._make_gift_card(balance=Decimal('180.00'))
        self.assertTrue(card.has_sufficient_balance(Decimal('180.00')))

    def test_deduct_balance_reduces_amount(self):
        card = self._make_gift_card(balance=Decimal('200.00'))
        card.deduct_balance(Decimal('180.00'))
        card.refresh_from_db()
        self.assertEqual(card.available_balance, Decimal('20.00'))

    def test_deduct_balance_does_not_go_negative(self):
        card = self._make_gift_card(balance=Decimal('10.00'))
        card.deduct_balance(Decimal('50.00'))
        card.refresh_from_db()
        self.assertEqual(card.available_balance, Decimal('0.00'))

    def test_deduct_balance_no_op_when_balance_is_null(self):
        card = self._make_credit_card(available_balance=None)
        card.deduct_balance(Decimal('180.00'))
        card.refresh_from_db()
        self.assertIsNone(card.available_balance)

    # ------------------------------------------------------------------
    # Locking
    # ------------------------------------------------------------------

    def test_acquire_lock_succeeds_on_unlocked_card(self):
        user, _ = create_test_user('lock@test.com', 'pass!23', 'A', 'B', '10', 'male')
        product = make_product()
        execution = make_execution(user, product)
        card = self._make_credit_card()

        result = card.acquire_lock(execution)

        self.assertTrue(result)
        card.refresh_from_db()
        self.assertTrue(card.is_locked)
        self.assertEqual(card.locked_by_execution, execution)
        self.assertIsNotNone(card.locked_at)

    def test_acquire_lock_fails_on_already_locked_card(self):
        user, _ = create_test_user('lock2@test.com', 'pass!23', 'A', 'B', '10', 'male')
        product = make_product()
        execution1 = make_execution(user, product)
        execution2 = make_execution(user, product)
        card = self._make_credit_card()

        card.acquire_lock(execution1)
        result = card.acquire_lock(execution2)

        self.assertFalse(result)
        card.refresh_from_db()
        self.assertEqual(card.locked_by_execution, execution1)

    def test_release_lock_clears_lock_fields(self):
        user, _ = create_test_user('lock3@test.com', 'pass!23', 'A', 'B', '10', 'male')
        product = make_product()
        execution = make_execution(user, product)
        card = self._make_credit_card()

        card.acquire_lock(execution)
        card.release_lock()

        card.refresh_from_db()
        self.assertFalse(card.is_locked)
        self.assertIsNone(card.locked_by_execution)
        self.assertIsNone(card.locked_at)

    # ------------------------------------------------------------------
    # get_available_card
    # ------------------------------------------------------------------

    def test_get_available_card_returns_unlocked_active_card(self):
        card = self._make_credit_card()
        result = BotPaymentMethod.get_available_card()
        self.assertEqual(result, card)

    def test_get_available_card_skips_locked_card(self):
        user, _ = create_test_user('avail@test.com', 'pass!23', 'A', 'B', '10', 'male')
        product = make_product()
        execution = make_execution(user, product)

        card1 = self._make_credit_card(label='Card 1 ···1111', last_four='1111')
        card2 = self._make_credit_card(label='Card 2 ···2222', last_four='2222')

        card1.acquire_lock(execution)

        result = BotPaymentMethod.get_available_card()
        self.assertEqual(result, card2)

    def test_get_available_card_skips_inactive_card(self):
        self._make_credit_card(is_active=False)
        result = BotPaymentMethod.get_available_card()
        self.assertIsNone(result)

    def test_get_available_card_checks_balance(self):
        self._make_gift_card(balance=Decimal('50.00'))
        result = BotPaymentMethod.get_available_card(
            required_amount=Decimal('180.00')
        )
        self.assertIsNone(result)

    def test_get_available_card_returns_none_when_none_available(self):
        result = BotPaymentMethod.get_available_card()
        self.assertIsNone(result)


@override_settings(ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class CredentialVaultTestCase(TestCase):
    """Tests for CredentialVault."""

    def setUp(self):
        self.vault = CredentialVault()
        self.user, _ = create_test_user(
            'vault@test.com', 'pass!23', 'Vault', 'User', '10', 'male'
        )
        self.product = make_product()
        self.execution = make_execution(self.user, self.product)

        self.card = BotPaymentMethod.objects.create(
            label='Vault Test Card ···9999',
            method_type='credit_card',
            encrypted_number=BotPaymentMethod.encrypt('4111111111111111'),
            encrypted_cvv=BotPaymentMethod.encrypt('321'),
            encrypted_expiry=BotPaymentMethod.encrypt('06/26'),
            last_four='9999',
            available_balance=None,
            is_active=True,
        )

    # ------------------------------------------------------------------
    # acquire_card
    # ------------------------------------------------------------------

    def test_acquire_card_returns_locked_card(self):
        result = self.vault.acquire_card(self.execution)
        self.assertIsNotNone(result)
        self.card.refresh_from_db()
        self.assertTrue(self.card.is_locked)

    def test_acquire_card_returns_none_when_no_cards(self):
        self.card.is_active = False
        self.card.save()
        result = self.vault.acquire_card(self.execution)
        self.assertIsNone(result)

    def test_acquire_card_checks_balance(self):
        gift = BotPaymentMethod.objects.create(
            label='Low Balance Gift Card ···0000',
            method_type='gift_card',
            encrypted_number=BotPaymentMethod.encrypt('0000111122223333'),
            encrypted_pin=BotPaymentMethod.encrypt('0000'),
            last_four='0000',
            available_balance=Decimal('10.00'),
            is_active=True,
        )
        # Deactivate credit card so only gift card is available
        self.card.is_active = False
        self.card.save()

        result = self.vault.acquire_card(
            self.execution,
            required_amount=Decimal('180.00')
        )
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # release_card — success
    # ------------------------------------------------------------------

    def test_release_card_success_deducts_balance(self):
        gift = BotPaymentMethod.objects.create(
            label='Gift Card ···5555',
            method_type='gift_card',
            encrypted_number=BotPaymentMethod.encrypt('5555555555555555'),
            encrypted_pin=BotPaymentMethod.encrypt('5555'),
            last_four='5555',
            available_balance=Decimal('200.00'),
            is_active=True,
        )
        gift.acquire_lock(self.execution)

        self.vault.release_card(
            gift,
            amount_spent=Decimal('180.00'),
            success=True
        )

        gift.refresh_from_db()
        self.assertFalse(gift.is_locked)
        self.assertEqual(gift.available_balance, Decimal('20.00'))

    def test_release_card_success_unlocks_card(self):
        self.card.acquire_lock(self.execution)
        self.vault.release_card(self.card, amount_spent=None, success=True)
        self.card.refresh_from_db()
        self.assertFalse(self.card.is_locked)

    # ------------------------------------------------------------------
    # release_card — failure
    # ------------------------------------------------------------------

    def test_release_card_failure_does_not_deduct_balance(self):
        gift = BotPaymentMethod.objects.create(
            label='Gift Card ···6666',
            method_type='gift_card',
            encrypted_number=BotPaymentMethod.encrypt('6666666666666666'),
            encrypted_pin=BotPaymentMethod.encrypt('6666'),
            last_four='6666',
            available_balance=Decimal('200.00'),
            is_active=True,
        )
        gift.acquire_lock(self.execution)

        self.vault.release_card(gift, amount_spent=None, success=False)

        gift.refresh_from_db()
        self.assertFalse(gift.is_locked)
        self.assertEqual(gift.available_balance, Decimal('200.00'))

    # ------------------------------------------------------------------
    # get_card_for_checkout
    # ------------------------------------------------------------------

    def test_get_card_for_checkout_returns_decrypted_details(self):
        details = self.vault.get_card_for_checkout(self.card)

        self.assertEqual(details['number'], '4111111111111111')
        self.assertEqual(details['cvv'], '321')
        self.assertEqual(details['expiry'], '06/26')
        self.assertEqual(details['last_four'], '9999')
        self.assertEqual(details['method_type'], 'credit_card')

    def test_get_card_for_checkout_gift_card_has_pin(self):
        gift = BotPaymentMethod.objects.create(
            label='Checkout Gift Card ···7777',
            method_type='gift_card',
            encrypted_number=BotPaymentMethod.encrypt('7777777777777777'),
            encrypted_pin=BotPaymentMethod.encrypt('9876'),
            last_four='7777',
            available_balance=Decimal('100.00'),
            is_active=True,
        )
        details = self.vault.get_card_for_checkout(gift)

        self.assertEqual(details['number'], '7777777777777777')
        self.assertEqual(details['pin'], '9876')
        self.assertEqual(details['method_type'], 'gift_card')
        self.assertEqual(details['cvv'], '')