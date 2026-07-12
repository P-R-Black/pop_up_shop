# ============================================================
# pop_up_bot/vault/credential_vault.py
# ============================================================

import logging
from decimal import Decimal
from typing import Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class CredentialVault:
    """
    Manages bot payment method selection, locking, and post-purchase
    balance updates.

    Usage in BotOrchestrator / site handlers:

        vault = CredentialVault()
        card = vault.acquire_card(execution, required_amount=Decimal('180.00'))
        if not card:
            # No card available — abort
            ...

        # Use card.card_number, card.cvv, card.expiry in checkout form
        # After successful purchase:
        vault.release_card(card, amount_spent=Decimal('180.00'), success=True)

        # After failed purchase (no order confirmation):
        vault.release_card(card, amount_spent=None, success=False)
    """

    def acquire_card(
        self,
        execution,
        required_amount: Optional[Decimal] = None,
    ):
        """
        Find and lock an available payment card for this execution.

        Args:
            execution: ProcurementExecution instance
            required_amount: Amount needed — gift cards must have this balance

        Returns:
            Locked BotPaymentMethod or None if none available
        """
        from pop_up_bot.models import BotPaymentMethod

        card = BotPaymentMethod.get_available_card(required_amount)

        if not card:
            logger.warning(
                f"No available payment card for execution {execution.id} "
                f"(required: ${required_amount})"
            )
            return None

        locked = card.acquire_lock(execution)

        if not locked:
            # Race condition — another execution grabbed it first, try again
            logger.info(f"Card {card.last_four} grabbed by another execution — retrying")
            card = BotPaymentMethod.get_available_card(required_amount)
            if card:
                locked = card.acquire_lock(execution)

        if not locked or not card:
            logger.warning(f"Could not acquire card lock for execution {execution.id}")
            return None

        logger.info(
            f"Card ···{card.last_four} ({card.method_type}) locked "
            f"for execution {execution.id}"
        )
        return card

    def release_card(
        self,
        card,
        amount_spent: Optional[Decimal] = None,
        success: bool = True,
    ) -> None:
        """
        Release card lock after procurement attempt.

        Args:
            card: BotPaymentMethod instance
            amount_spent: Actual amount charged (deducted from balance if known)
            success: Whether purchase succeeded
        """
        try:
            if success and amount_spent is not None:
                card.deduct_balance(amount_spent)
                logger.info(
                    f"Card ···{card.last_four} balance reduced by ${amount_spent}"
                )
            elif not success:
                logger.info(
                    f"Card ···{card.last_four} released after failed attempt "
                    f"(balance unchanged)"
                )

            card.release_lock()
            logger.info(f"Card ···{card.last_four} unlocked")

        except Exception as e:
            logger.error(f"Error releasing card lock: {e}", exc_info=True)
            # Force-release the lock even if balance update failed
            try:
                card.release_lock()
            except Exception:
                pass

    def get_card_for_checkout(self, card) -> dict:
        """
        Return decrypted card details for filling checkout forms.
        Details are decrypted in memory and never persisted.

        Returns dict with keys: number, cvv, expiry, pin, last_four,
        method_type, billing_address
        """
        return {
            'number':          card.card_number,
            'cvv':             card.cvv,
            'expiry':          card.expiry,
            'pin':             card.pin,
            'last_four':       card.last_four,
            'method_type':     card.method_type,
            'billing_address': card.billing_address,
        }