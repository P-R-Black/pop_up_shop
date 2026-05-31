# pop_up_bot/tests/test_integration_smoke.py
import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
import uuid

from pop_up_bot.models import (
    CookieModel,
    ProcurementRequest,
    ProcurementExecution,
    ExternalProductReference,
    InventoryLock,
    ProcurementEvent,
    BotLog,
    SiteAttempt,
)

from pop_up_auction.models import (
    PopUpProductType,
    PopUpCategory,
    PopUpBrand,)

from pop_up_auction.tests.conftest import (create_test_user)

from django.contrib.auth import get_user_model
User = get_user_model()



class TestProcurementFlow(TestCase):
    """Basic smoke test of full flow"""
    
    def test_basic_flow(self):
        """Can we create request -> execution -> event?"""
        # user = User.objects.create_user('test')
        # Create test user
        user, user_profile = create_test_user(
            "test@example.com", "testpass!23", "Test", "User", "9", "male"
        )
        request = ProcurementRequest.objects.create(
            user=user,
            product_name='Test',
            target_size='US 10',
            max_price=200,
        )
        
        execution = ProcurementExecution.objects.create(
            procurement_request=request,
            status='success',
            strategy_used='sequential',
            order_id='ORD-123',
            started_at=timezone.now(),
        )
        
        event = ProcurementEvent.objects.create(
            bot_execution=execution,
            event_type='ORDER_CONFIRMED',
            metadata={'test': True},
        )
        
        # Verify relationships work
        assert execution.events.count() == 1
        assert request.executions.count() == 1
        assert event.bot_execution == execution