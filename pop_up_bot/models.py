# pop_up_bot/models.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from pop_up_auction.models import PopUpProduct, PopUpBrand, PopUpCategory
import uuid
from django.utils.timezone import now
from django.utils import timezone as django_timezone
from datetime import timezone as dt_timezone, datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

from cryptography.fernet import Fernet
import uuid

"""
All Models
 1. CookieModel
 2. ProcurementRequest
 3. ProcurementExecution
 4. ExternalProductReference
 5. InventoryLock
 6. ProcurementEvent
 7. BotLog
 8. SiteAttempt
 9. ScheduledRelease
10. ProcurementServiceRequest
11. ReleaseExecutionBatch
12. DailyHealthCheck
13. HealthCheckStep
14. HealthCheckNotification
15. BotPaymentMethod
"""

class CookieModel(models.Model):
    """
    Django model to store cookies persistently in the database.
    
    Allows bots to maintain logged-in state, shopping cart state, etc.
    across multiple executions.
    """
    
    id = models.BigAutoField(primary_key=True)
    site_name = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Site identifier (e.g., 'nike', 'footlocker')"
    )
    name = models.CharField(
        max_length=255,
        help_text="Cookie name"
    )
    value = models.TextField(
        help_text="Cookie value"
    )
    domain = models.CharField(
        max_length=255,
        help_text="Cookie domain (e.g., '.nike.com')"
    )
    path = models.CharField(
        max_length=255,
        default='/',
        help_text="Cookie path"
    )
    expires = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cookie expiration time"
    )
    http_only = models.BooleanField(
        default=False,
        help_text="Cookie httpOnly flag"
    )
    secure = models.BooleanField(
        default=False,
        help_text="Cookie secure flag (HTTPS only)"
    )
    same_site = models.CharField(
        max_length=10,
        choices=[
            ('Lax', 'Lax'),
            ('Strict', 'Strict'),
            ('None', 'None'),
        ],
        default='Lax',
        help_text="Cookie SameSite flag"
    )
    saved_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this cookie was saved"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this cookie was last updated"
    )
    
    class Meta:
        db_table = 'pop_up_bot_cookies'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['site_name', 'name']),
            models.Index(fields=['site_name', '-updated_at']),
            models.Index(fields=['expires']),
        ]
        verbose_name = 'Bot Cookie'
        verbose_name_plural = 'Bot Cookies'
        constraints = [
            models.UniqueConstraint(
                fields=['site_name', 'domain', 'name'],
                name='unique_site_domain_cookie_name'
            )
        ]
    
    def __str__(self):
        return f"{self.site_name} - {self.name} ({self.domain})"
    
    @property
    def is_expired(self) -> bool:
        """Check if cookie is expired"""
        if self.expires is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires
    
    def to_playwright_dict(self) -> Dict:
        """Convert to Playwright cookie format"""
        cookie_dict = {
            'name': self.name,
            'value': self.value,
            'domain': self.domain,
            'path': self.path,
            'httpOnly': self.http_only,
            'secure': self.secure,
            'sameSite': self.same_site,
        }
        
        if self.expires:
            # Playwright expects Unix timestamp
            cookie_dict['expires'] = self.expires.timestamp()
        
        return cookie_dict


class ProcurementRequest(models.Model):
    """
    User request to procure an item from external sites.
    
    Represents a procurement task (find this shoe in this size).
    Can have multiple ProcurementExecution attempts if first ones fail.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    PROCUREMENT_TYPE_CHOICES = [
        ('inventory', 'Inventory Procurement'),
        ('concierge', 'Concierge Procurement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='procurement_requests'
    )

    product = models.ForeignKey(
        PopUpProduct,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    brand = models.ForeignKey(
        PopUpBrand,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    product_name = models.CharField(
        max_length=255,
        help_text="Name of product to find (e.g., 'Air Jordan 1')"
    )

    target_size = models.CharField(
        max_length=50,
        help_text="Size to find (e.g., 'US 10')"
    )

    target_sex = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Gender sizing (Mens/Womens) — for shoes only"
    )

    target_color = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Optional color preference"
    )

    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum price willing to pay"
    )

    procurement_type = models.CharField(
        max_length=20,
        choices=PROCUREMENT_TYPE_CHOICES,
        default='inventory'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    priority_score = models.IntegerField(
        default=0,
        help_text="Higher = more urgent"
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Procurement request expires at this time"
    )

    fulfilled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the item was successfully procured"
    )

    created_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = 'Procurement Request'
        verbose_name_plural = 'Procurement Requests'

    def __str__(self):
        return f"{self.product_name} (Size: {self.target_size}) - {self.status}"

    @property
    def is_expired(self):
        """Check if request has expired"""
        if self.expires_at:
            return now() > self.expires_at
        return False

    @property
    def execution_count(self):
        """How many execution attempts?"""
        return self.executions.count()

    @property
    def execution_success_count(self):
        """How many successful executions?"""
        return self.executions.filter(status='success').count()


class ProcurementExecution(models.Model):
    """
    Single execution attempt to procure an item.
    
    One ProcurementRequest can have multiple ProcurementExecutions if the first
    ones fail. Tracks which strategy was used, which site won, order ID, etc.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
        ('cancelled', 'Cancelled'),
    ]

    STRATEGY_CHOICES = [
        ('sequential', 'Sequential'),
        ('parallel', 'Parallel'),
        ('priority', 'Priority'),
        ('fastest', 'Fastest'),
        ('cheapest', 'Cheapest'),
        ('retail_only', 'Retail Only'),
    ]

    ERROR_TYPE_CHOICES = [
        # Refundable (CODE/BOT issues - we refund)
        ('bot_crash', 'Bot Crashed'),
        ('rate_limited', 'Rate Limited'),
        ('site_structure_changed', 'Site Structure Changed'),
        ('exception', 'Unhandled Exception'),
        ('unknown_error', 'Unknown Error'),
        
        # Non-refundable (USER/MARKET issues - we keep fee)
        ('out_of_stock', 'Out of Stock'),
        ('lost_to_bots', 'Lost to Other Bots'),
        ('item_not_found', 'Item Not Found'),
        ('sold_out', 'Sold Out'),
        ('coming_soon', 'Coming Soon'),
        ('payment_already_exists', 'Payment Already Exists'),
        ('success', 'Success'),
    ]

    error_type = models.CharField(
        max_length=30,
        choices=ERROR_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Type of error - determines if refund should be issued"
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    procurement_request = models.ForeignKey(
        ProcurementRequest,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text="The request this execution is fulfilling"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )

    strategy_used = models.CharField(
        max_length=20,
        choices=STRATEGY_CHOICES,
        default='sequential',
        help_text="Which procurement strategy was used"
    )

    winning_site = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Which site successfully procured the item"
    )

    order_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="Order ID from the site"
    )

    item_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price paid for the item"
    )

    idempotency_key = models.UUIDField(
        default=uuid.uuid4,
        help_text="Prevents duplicate execution"
    )

    started_at = models.DateTimeField(
        help_text="When execution started"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When execution completed (success or failure)"
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if execution failed"
    )

    task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Celery task ID if running asynchronously"
    )

    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['procurement_request', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['winning_site']),
            models.Index(fields=['order_id']),
        ]
        verbose_name = 'Procurement Execution'
        verbose_name_plural = 'Procurement Executions'

    def __str__(self):
        return f"{self.procurement_request.product_name} - {self.status}"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def was_successful(self) -> bool:
        """Quick check if execution succeeded"""
        return self.status == 'success' and self.order_id is not None

    @property
    def is_running(self) -> bool:
        """Check if execution is still running"""
        return self.status == 'running'


class ExternalProductReference(models.Model):
    """
    Map between our PopUpProduct and external site SKUs.
    
    Helps identify products on external sites and track pricing.
    """

    SITE_CHOICES = [
        ('nike', 'Nike'),
        ('footlocker', 'Footlocker'),
        ('adidas', 'Adidas'),
        ('new_balance', 'New Balance'),
        ('supreme', 'Supreme'),
        ('grailed', 'Grailed'),
        ('stockx', 'StockX'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        PopUpProduct,
        on_delete=models.CASCADE,
        related_name='external_references'
    )

    site_name = models.CharField(
        max_length=50,
        choices=SITE_CHOICES,
        db_index=True,
    )

    external_sku = models.CharField(
        max_length=255,
        help_text="SKU on the external site"
    )

    external_url = models.URLField(
        help_text="Direct link to product on external site"
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time we verified this product exists"
    )

    last_price_check = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_known_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(default=django_timezone.now)

    class Meta:
        indexes = [
        models.Index(fields=['site_name', 'external_sku']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['site_name', 'external_sku'],
                name='unique_site_external_sku'
            )
        ]

    def __str__(self):
        return f"{self.site_name} - {self.external_sku}"


class InventoryLock(models.Model):
    """
    Distributed lock to prevent race conditions and duplicate purchases.
    
    Prevents:
    - Two executions buying the same item simultaneously
    - Race conditions in parallel procurement strategies
    - Double-charging users
    """

    LOCK_STATUS_CHOICES = [
        ('acquired', 'Acquired'),
        ('released', 'Released'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # What are we locking?
    product_identifier = models.CharField(
        max_length=255,
        db_index=True,
        help_text="External SKU or product identifier (e.g., Nike: 'DA1971-104')"
    )
    size = models.CharField(max_length=20, db_index=True)
    
    # Who holds the lock?
    execution = models.ForeignKey(
        ProcurementExecution,
        on_delete=models.CASCADE,
        related_name='inventory_locks',
        null=True,
        blank=True,
        help_text="Which execution this attempt is part of"
    )
    
    # execution = models.ForeignKey(
    #     ProcurementExecution,
    #     on_delete=models.CASCADE,
    #     related_name='inventory_locks'
    # )
    
    site_name = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Which site this lock is for (e.g., 'nike', 'footlocker')"
    )
    
    # Lock lifecycle
    status = models.CharField(
        max_length=20,
        choices=LOCK_STATUS_CHOICES,
        default='acquired',
        db_index=True,
    )
    locked_until = models.DateTimeField(
        help_text="Lock automatically expires at this time (prevents deadlocks)"
    )
    acquired_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-acquired_at']
        indexes = [
            models.Index(fields=['product_identifier', 'size', 'status']),
            models.Index(fields=['execution']),
            models.Index(fields=['locked_until']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['product_identifier', 'size'],
                condition=models.Q(status='acquired'),
                name='unique_active_lock_per_product_size'
            )
        ]
    
    def __str__(self):
        return f"{self.product_identifier} (Size {self.size}) - {self.status}"
    
    @property
    def is_active(self):
        """Check if lock is still active"""
        if self.status != 'acquired':
            return False
        return now() < self.locked_until
    
    @property
    def is_expired(self):
        """Check if lock has expired (prevents deadlocks)"""
        return self.status == 'acquired' and now() > self.locked_until
    
    @classmethod
    def try_acquire_lock(cls, product_identifier, size, site_name, execution, ttl_seconds=60):
        """
        Attempt to acquire a lock for a product.
        
        Args:
            product_identifier: External SKU
            size: Product size
            site_name: Which site
            execution: ProcurementExecution instance
            ttl_seconds: Lock timeout (default 60 seconds)
        
        Returns:
            (lock_instance, acquired: bool)
            
        Example:
            lock, acquired = InventoryLock.try_acquire_lock(
                product_identifier='DA1971-104',
                size='10',
                site_name='nike',
                execution=execution,
                ttl_seconds=60
            )
            
            if acquired:
                # Proceed to checkout
                proceed_to_checkout()
                lock.release()
            else:
                # Another execution won the race
                abort_execution()
        """
        from django.db import IntegrityError
        
        try:
            lock = cls.objects.create(
                product_identifier=product_identifier,
                size=size,
                site_name=site_name,
                execution=execution,
                locked_until=now() + timedelta(seconds=ttl_seconds),
                status='acquired'
            )
            return lock, True
        except IntegrityError:
            # Another execution already has the lock
            return None, False
    
    def release(self):
        """Release the lock after successful purchase"""
        self.status = 'released'
        self.released_at = now()
        self.save()
    
    def mark_failed(self):
        """Mark lock as failed if something went wrong"""
        self.status = 'failed'
        self.released_at = now()
        self.save()
    
    def mark_expired(self):
        """Mark lock as expired (TTL exceeded)"""
        self.status = 'expired'
        self.released_at = now()
        self.save()


class ProcurementEvent(models.Model):
    """
    Event log for complete auditability and debugging.
    
    Enables:
    - Full event replay/debugging
    - Analytics on where bots fail most
    - Complete audit trail
    - State machine reconstruction
    """
    EVENT_CHOICES = [
        ('INITIALIZED', 'Initialized'),
        ('STRATEGY_SELECTED', 'Strategy Selected'),
        ('SITE_SELECTED', 'Site Selected'),
        ('PRODUCT_FOUND', 'Product Found'),
        ('SIZE_SELECTED', 'Size Selected'),
        ('CART_SUCCESS', 'Added to Cart'),
        ('LOCK_ACQUIRED', 'Lock Acquired'),
        ('LOCK_FAILED', 'Lock Failed'),
        ('CHECKOUT_STARTED', 'Checkout Started'),
        ('PAYMENT_SUBMITTED', 'Payment Submitted'),
        ('ORDER_CONFIRMED', 'Order Confirmed'),
        ('FAILED', 'Failed'),
        ('ABANDONED', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    bot_execution = models.ForeignKey(
        ProcurementExecution,
        on_delete=models.CASCADE,
        related_name='events'
    )
    
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_CHOICES,
        db_index=True,
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    site_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Which site this event relates to (if applicable)"
    )
    
    metadata = models.JSONField(
        default=dict,
        help_text="Additional event data (JSON)"
    )
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['bot_execution', 'timestamp']),
            models.Index(fields=['event_type']),
        ]
        verbose_name = 'Procurement Event'
        verbose_name_plural = 'Procurement Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class BotLog(models.Model):
    """
    Detailed logging of bot operations.
    
    Different from ProcurementEvent (which are state transitions).
    BotLog captures operational messages and warnings.
    """
    LOG_LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    bot_execution = models.ForeignKey(
        ProcurementExecution,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    level = models.CharField(
        max_length=20,
        choices=LOG_LEVEL_CHOICES,
        db_index=True,
    )
    
    message = models.TextField()
    
    context = models.JSONField(
        default=dict,
        help_text="Additional context (JSON)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['bot_execution', 'timestamp']),
            models.Index(fields=['level']),
        ]
        verbose_name = 'Bot Log'
        verbose_name_plural = 'Bot Logs'
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.message[:50]}"


class SiteAttempt(models.Model):
    """
    Detailed record of a single site procurement attempt.
    
    Tracks what happened on a specific site during execution.
    Helps debug and understand bot failures.
    """

    STATUS_CHOICES = [
        ('started', 'Started'),
        ('product_found', 'Product Found'),
        ('carted', 'Carted'),
        ('checkout_started', 'Checkout Started'),
        ('payment_submitted', 'Payment Submitted'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('oos', 'Out Of Stock'),
        ('blocked', 'Blocked'),
    ]

    FAILURE_CHOICES = [
        ('oos', 'Out Of Stock'),
        ('payment_declined', 'Payment Declined'),
        ('captcha', 'Captcha'),
        ('site_timeout', 'Site Timeout'),
        ('blocked', 'Blocked'),
        ('selector_failure', 'Selector Failure'),
        ('network_error', 'Network Error'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    execution = models.ForeignKey(
        ProcurementExecution,
        on_delete=models.CASCADE,
        related_name='site_attempts',
        help_text="Which execution this attempt is part of"
    )

    site_name = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Which site this attempt targeted"
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='started',
        db_index=True,
    )

    failure_reason = models.CharField(
        max_length=50,
        choices=FAILURE_CHOICES,
        null=True,
        blank=True,
        help_text="Reason for failure (if failed)"
    )

    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="How many times was this attempt retried"
    )

    product_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL of product found on site"
    )

    external_sku = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="SKU from the site"
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if attempt failed"
    )

    screenshot = models.ImageField(
        upload_to='bot_failures/',
        null=True,
        blank=True,
        help_text="Screenshot for debugging"
    )

    started_at = models.DateTimeField(
        help_text="When this site attempt started"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this site attempt completed"
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['execution', 'site_name']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'Site Attempt'
        verbose_name_plural = 'Site Attempts'

    def __str__(self):
        return f"{self.site_name} - {self.status}"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate attempt duration"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def was_successful(self) -> bool:
        """Quick check if site attempt succeeded"""
        return self.status == 'success'



class ScheduledRelease(models.Model):
    """
    Represents a scheduled Nike release.
    
    Admin creates this when they've decided to attempt procurement for a product.
    
    Example:
    - Product: LeBron NXXT Gen By JuJu "Silver Lining"
    - SKU: IQ8495-002
    - Release: June 2, 2026 at 10:00 AM EST
    - Direct URL: https://www.nike.com/t/lebron-nxxt-gen-by-juju.../IQ8495-002
    
    Admin checks:
    - product.interested_users.count() = 15 users interested
    - Decides: "Worth attempting to secure"
    - Creates ScheduledRelease
    """
    
    SEARCH_METHOD_CHOICES = [
        ('direct_url', 'Direct URL - Go straight to product page'),
        ('sku_search', 'SKU Search - Search Nike by SKU'),
        ('product_name', 'Product Name - Search by name'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled - Waiting for release time'),
        ('active', 'Active - Release time has arrived, bot running'),
        ('completed', 'Completed - Release window closed'),
        ('cancelled', 'Cancelled - Admin cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # What product?
    product = models.ForeignKey(
        PopUpProduct,
        on_delete=models.CASCADE,
        related_name='scheduled_releases',
        help_text="The PopUpProduct being released"
    )
    
    # Nike identifiers
    sku = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Nike SKU (e.g., IQ8495-002)"
    )
    
    # When does it release?
    release_date = models.DateTimeField(
        db_index=True,
        help_text="Exact time product becomes available on Nike"
    )
    
    # How long to keep trying after release?
    procurement_window_minutes = models.PositiveIntegerField(
        default=30,
        help_text="How many minutes after release time to keep attempting to buy (default 30)"
    )
    
    # How to find it on Nike?
    search_method = models.CharField(
        max_length=20,
        choices=SEARCH_METHOD_CHOICES,
        default='direct_url',
        help_text="How the bot should find this product on Nike"
    )
    
    # Direct URL (preferred method)
    product_url = models.URLField(
        null=True,
        blank=True,
        help_text="Direct Nike product URL (e.g., https://www.nike.com/t/...)"
    )
    
    # Search fallback (if URL doesn't work)
    search_query = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Product name to search for if direct URL fails"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        db_index=True,
    )
    
    # Celery task tracking
    celery_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Celery task ID for scheduled release"
    )
    
    # Metadata
    nike_product_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Exact product name from Nike (if already ran once)"
    )
    
    retail_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected retail price"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['release_date']
        indexes = [
            models.Index(fields=['sku', 'release_date']),
            models.Index(fields=['status', 'release_date']),
        ]
        verbose_name = 'Scheduled Release'
        verbose_name_plural = 'Scheduled Releases'
    
    def __str__(self):
        return f"{self.product.product_title} - {self.sku} ({self.release_date.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_upcoming(self) -> bool:
        """Release hasn't happened yet"""
        return django_timezone.now() < self.release_date
    
    @property
    def is_active(self) -> bool:
        """We're currently within the procurement window"""
        now = django_timezone.now()
        window_end = self.release_date + timedelta(minutes=self.procurement_window_minutes)
        return self.release_date <= now <= window_end
    
    @property
    def minutes_until_release(self) -> int:
        """How many minutes until release?"""
        delta = self.release_date - django_timezone.now()
        return int(delta.total_seconds() / 60)
    
    @property
    def interested_user_count(self) -> int:
        """How many users are interested in this product? (from PopUpCustomerProfile)"""
        return self.product.interested_users.count()
    
    @property
    def paid_user_count(self) -> int:
        """How many users have paid for procurement service?"""
        return self.procurement_service_requests.filter(
            status__in=['pending', 'active', 'success']
        ).count()
    
    def get_search_params(self) -> dict:
        """Get search parameters for bot"""
        return {
            'method': self.search_method,
            'query': self.search_query or self.product_url,
            'sku': self.sku,
        }


class ProcurementServiceRequest(models.Model):
    """
    User PAYS Pop Up Shop to attempt procurement (PAID SERVICE).
    
    When user is interested in a product and it becomes available for procurement,
    they pay a fee and this record is created.
    
    At release_date, the bot runs for this user.
    
    Example:
    1. User marked "interested" in LeBron NXXT via PopUpCustomerProfile
    2. Item is scheduled for release (ScheduledRelease created)
    3. Pop Up Shop notifies user: "Pay $15 and we'll secure it for you"
    4. User pays → ProcurementServiceRequest created
    5. June 2, 10:00 AM → Bot runs
    6. If success: Item in user's cart with 48-hour hold
    7. If failure: User refunded
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending - User paid, waiting for release'),
        ('pending_payment', 'Pending Payment - Awaiting service fee payment'),
        ('active', 'Active - Release time has arrived, bot running'),
        ('success', 'Success - Bot secured item'),
        ('failed', 'Failed - Bot could not secure'),
        ('abandoned', 'Abandoned - User cancelled before release'),
        ('expired', 'Expired - Release window closed without success'),
    ]
    
    STRATEGY_CHOICES = [
        ('fastest', 'Fastest - Use fastest strategy available'),
        ('cheapest', 'Cheapest - Try to find lowest price'),
        ('standard', 'Standard - Sequential attempts'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who and what release?
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='procurement_service_requests'
    )
    
    scheduled_release = models.ForeignKey(
        ScheduledRelease,
        on_delete=models.CASCADE,
        related_name='procurement_service_requests',
        help_text="The release this user paid for"
    )
    
    # Size and color preferences
    size = models.CharField(
        max_length=50,
        help_text="Size they want (e.g., US 10)"
    )
    
    sex = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Gender sizing (Mens/Womens) - applicable for shoes or sneakers only"
    )
    
    color = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Preferred color if available"
    )
    
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Max price they'll pay (optional)"
    )
    
    # Procurement settings
    strategy = models.CharField(
        max_length=20,
        choices=STRATEGY_CHOICES,
        default='fastest',
        help_text="Which strategy to use"
    )
    
    # Payment tracking
    service_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount user paid for this service"
    )
    
    fee_paid_at = models.DateTimeField(
        help_text="When user paid the fee"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    
    # Links to actual procurement
    procurement_request = models.OneToOneField(
        ProcurementRequest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='service_request',
        help_text="The ProcurementRequest created at release time"
    )
    
    procurement_execution = models.OneToOneField(
        ProcurementExecution,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='service_request',
        help_text="The execution result (if successful)"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    procurement_request_created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When ProcurementRequest was created (at release time)"
    )
    
    class Meta:
        # A user can have one request per product/size/sex combination.
        # Mens 10 and Womens 10 are different requests.
        unique_together = ('user', 'scheduled_release', 'size', 'sex')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_release', 'status']),
        ]
        verbose_name = 'Procurement Service Request'
        verbose_name_plural = 'Procurement Service Requests'
 
    
    def __str__(self):
        return f"{self.user.email} → {self.scheduled_release.product.product_title} (Size {self.size})"
    
    @property
    def was_successful(self) -> bool:
        """Did bot succeed?"""
        return self.status == 'success' and self.procurement_execution is not None
    
    @property
    def time_until_release(self) -> timedelta:
        """Time remaining until release"""
        return self.scheduled_release.release_date - django_timezone.now()
    
    def create_procurement_request(self) -> 'ProcurementRequest':
        """
        Create a ProcurementRequest at release time.
        Called by Celery task when release_date arrives.
        """
        from pop_up_bot.models import ProcurementRequest
    
        max_price = (
            self.max_price
            or self.scheduled_release.retail_price
            or Decimal('9999.99')
        )
    
        request = ProcurementRequest.objects.create(
            user=self.user,
            product=self.scheduled_release.product,
            product_name=self.scheduled_release.product.product_title,
            target_size=self.size,
            target_sex=self.sex,          # ← NEW: pass sex through
            target_color=self.color or '',
            max_price=max_price,
            procurement_type='inventory',
            status='pending',
        )
    
        self.procurement_request = request
        self.procurement_request_created_at = django_timezone.now()
        self.status = 'active'
        self.save()
    
        return request
 
 
 
class ReleaseExecutionBatch(models.Model):
    """
    Groups all executions that ran for a single ScheduledRelease.
    
    Example:
    - Release: LeBron NXXT at 10:00 AM
    - 5 users paid for service
    - Bot ran 5 times
    - This model groups all 5 together for reporting
    
    Used for:
    - Analytics: "How many releases have we attempted?"
    - Reporting: "5 paid, 3 succeeded, 2 failed"
    - Debugging: "What happened on release day?"
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    scheduled_release = models.ForeignKey(
        ScheduledRelease,
        on_delete=models.CASCADE,
        related_name='execution_batches',
        help_text="The release this batch was for"
    )
    
    # Stats
    total_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Total executions attempted"
    )
    
    successful_count = models.PositiveIntegerField(
        default=0,
        help_text="How many succeeded"
    )
    
    failed_count = models.PositiveIntegerField(
        default=0,
        help_text="How many failed"
    )
    
    # Timing
    started_at = models.DateTimeField(
        help_text="When we started executing"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When all executions finished"
    )
    
    # All executions in this batch
    executions = models.ManyToManyField(
        ProcurementExecution,
        related_name='release_batch',
        help_text="All executions in this batch"
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Any notes about this release (e.g., 'Nike was slow')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Release Execution Batch'
        verbose_name_plural = 'Release Execution Batches'
    
    def __str__(self):
        return f"{self.scheduled_release} - {self.successful_count}/{self.total_attempts} succeeded"
    
    @property
    def success_rate(self) -> float:
        """Success percentage"""
        if self.total_attempts == 0:
            return 0
        return (self.successful_count / self.total_attempts) * 100
    
    @property
    def duration_seconds(self) -> int:
        """How long did batch take?"""
        if not self.completed_at:
            return 0
        return int((self.completed_at - self.started_at).total_seconds())
 
 
# ============================================================================
# USAGE WORKFLOW
# ============================================================================
 
"""
STEP-BY-STEP:
 
1. INTEREST TRACKING (Existing in PopUpCustomerProfile)
   - User clicks "Interested" on LeBron NXXT
   - Stored in: product.interested_users (ManyToMany)
   - Admin can see: product.interested_users.count() = 15
 
2. ADMIN DECISION
   - Admin checks: "LeBron has 15 interested users"
   - Admin checks Nike SNKR: "Releases June 2 at 10:00 AM EST"
   - Admin decides: "Worth it, let's create ScheduledRelease"
   - Creates ScheduledRelease:
     * product = LeBron NXXT
     * sku = IQ8495-002
     * release_date = 2026-06-02 10:00:00 EST
     * product_url = https://www.nike.com/t/...
     * search_method = 'direct_url'
 
3. USER PAYS FOR SERVICE
   - Pop Up Shop notifies interested users
   - User sees: "Secure this shoe for $15"
   - User pays → ProcurementServiceRequest created:
     * user = john
     * scheduled_release = LeBron NXXT release
     * size = US 10
     * service_fee = 15.00
     * status = 'pending'
 
4. RELEASE TIME ARRIVES
   - June 2, 10:00 AM
   - Celery task finds ScheduledRelease with is_active=True
   - Gets all ProcurementServiceRequest with status='pending'
   - For each request:
     a. Calls request.create_procurement_request()
     b. Runs BotOrchestrator with NikeSiteHandler
     c. Updates status: 'success' or 'failed'
   - Creates ReleaseExecutionBatch to group all executions
 
5. REPORTING
   - Admin dashboard shows:
     * "LeBron NXXT release: 5 users paid"
     * "Results: 3 succeeded, 2 failed"
     * "Success rate: 60%"
     * "Execution batch details: times, errors, etc"
 
6. USER FULFILLMENT
   - Success: Item in user's cart with 48-hour hold
   - Failed: User gets refund + notification
   - User has 48 hours to complete purchase
   - If not purchased: Item becomes "buy now" listing
"""


class DailyHealthCheck(models.Model):
    """
    Daily health check run for a specific site.
    
    Tests bot functionality: navigate → search → add to cart → remove from cart
    """
    
    SITE_CHOICES = [
        ('nike', 'Nike'),
        ('footlocker', 'Footlocker'),
        ('adidas', 'Adidas'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    site = models.CharField(
        max_length=20,
        choices=SITE_CHOICES,
        help_text="Which site to test"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Health check status"
    )
    
    # Test product (fixed SKU for consistent testing)
    product_sku = models.CharField(
        max_length=100,
        help_text="Test product SKU (e.g., DJ0646-610 for Nike)"
    )
    
    product_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of test product"
    )
    
    # Results
    steps_completed = models.JSONField(
        default=list,
        help_text="List of completed steps: ['navigate', 'search', 'add_to_cart', 'remove_from_cart']"
    )
    
    error_step = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Which step failed (if any)"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if health check failed"
    )
    
    # Timing
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When health check started"
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When health check completed"
    )
    
    duration_seconds = models.IntegerField(
        blank=True,
        null=True,
        help_text="How long the health check took"
    )
    
    # Notifications
    admin_notified = models.BooleanField(
        default=False,
        help_text="Whether admin was notified of failure"
    )
    
    admin_notification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When notification was sent"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = "Daily Health Check"
        verbose_name_plural = "Daily Health Checks"
        indexes = [
            models.Index(fields=['site', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"HealthCheck {self.site.upper()} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_success(self):
        return self.status == 'success'
    
    @property
    def is_failed(self):
        return self.status == 'failed'
    
    @property
    def all_steps_completed(self):
        """Check if all required steps were completed"""
        required_steps = ['navigate', 'search', 'add_to_cart', 'remove_from_cart']
        return all(step in self.steps_completed for step in required_steps)
    
    def mark_running(self):
        """Mark health check as running"""
        self.status = 'running'
        self.started_at = django_timezone.now()
        self.save()
    
    def mark_success(self):
        """Mark health check as successful"""
        self.status = 'success'
        self.completed_at = django_timezone.now()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
        self.save()
    
    def mark_failed(self, error_step: str, error_message: str):
        """Mark health check as failed"""
        self.status = 'failed'
        self.error_step = error_step
        self.error_message = error_message
        self.completed_at = django_timezone.now()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
        self.save()
    
    def mark_admin_notified(self):
        """Mark that admin was notified"""
        self.admin_notified = True
        self.admin_notification_sent_at = django_timezone.now()
        self.save()
    
    def add_step(self, step_name: str):
        """Record a completed step"""
        if step_name not in self.steps_completed:
            self.steps_completed.append(step_name)
            self.save()
 
 
class HealthCheckStep(models.Model):
    """
    Detailed log of each step in a health check.
    
    Helps debug which exact step failed and why.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    health_check = models.ForeignKey(
        DailyHealthCheck,
        on_delete=models.CASCADE,
        related_name='steps',
        help_text="Parent health check"
    )
    
    step_number = models.IntegerField(
        help_text="Order of execution (1, 2, 3, etc)"
    )
    
    step_name = models.CharField(
        max_length=100,
        help_text="Step description (navigate, search, add_to_cart, etc)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    description = models.TextField(
        blank=True,
        help_text="What this step does"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error if step failed"
    )
    
    # Timing
    started_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    
    duration_ms = models.IntegerField(
        blank=True,
        null=True,
        help_text="Duration in milliseconds"
    )
    
    # Details
    url = models.URLField(
        blank=True,
        help_text="URL being tested"
    )
    
    selector_used = models.CharField(
        max_length=255,
        blank=True,
        help_text="CSS selector that was used"
    )
    
    element_found = models.BooleanField(
        default=False,
        help_text="Whether element was found"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about step"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('step_number',)
        verbose_name = "Health Check Step"
        verbose_name_plural = "Health Check Steps"
    
    def __str__(self):
        return f"Step {self.step_number}: {self.step_name} ({self.status})"
    
    def mark_running(self):
        """Mark step as running"""
        self.status = 'running'
        self.started_at = django_timezone.now()
        self.save()
    
    def mark_success(self, duration_ms: int = None):
        """Mark step as successful"""
        self.status = 'success'
        self.completed_at = django_timezone.now()
        self.duration_ms = duration_ms
        self.save()
    
    def mark_failed(self, error_message: str, duration_ms: int = None):
        """Mark step as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = django_timezone.now()
        self.duration_ms = duration_ms
        self.save()
 
 
class HealthCheckNotification(models.Model):
    """
    Track notifications sent to admins about health check failures.
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('slack', 'Slack'),
        ('sms', 'SMS'),
        ('in_app', 'In App'),
    ]
    
    health_check = models.ForeignKey(
        DailyHealthCheck,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
    )
    
    recipient = models.CharField(
        max_length=255,
        help_text="Email, phone, Slack ID, etc"
    )
    
    subject = models.CharField(max_length=255)
    
    message = models.TextField()
    
    sent_at = models.DateTimeField(auto_now_add=True)
    
    success = models.BooleanField(
        default=False,
        help_text="Whether notification was successfully sent"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Error if notification failed to send"
    )
    
    class Meta:
        ordering = ('-sent_at',)
        verbose_name = "Health Check Notification"
        verbose_name_plural = "Health Check Notifications"
    
    def __str__(self):
        return f"{self.notification_type.upper()} to {self.recipient} - {self.sent_at}"
    



# ============================================================
# Add ENCRYPTION_KEY to settings.py and .env:
#   ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')  # Fernet key
#
# Generate a key once:
#   from cryptography.fernet import Fernet
#   print(Fernet.generate_key().decode())
# ============================================================


class BotPaymentMethod(models.Model):
    """
    Encrypted payment method for bot use at retailers.

    Stores credit cards and gift cards used by the bot to pay
    retailers (Nike, Shoe Palace, etc.) during procurement.

    Security:
    - Card numbers, CVV, expiry encrypted with AES-256 (Fernet)
    - Only last four digits stored in plaintext (for display)
    - Decrypted in memory only during checkout, never persisted
    - One card locked to one active procurement at a time
    """

    METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('gift_card',   'Gift Card'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    label = models.CharField(
        max_length=100,
        help_text="Human-readable label e.g. 'Nike Visa ending 4242' or 'Nike Gift Card #3'"
    )

    method_type = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default='credit_card',
    )

    # ------------------------------------------------------------------
    # Encrypted fields (stored as base64 Fernet tokens)
    # ------------------------------------------------------------------
    encrypted_number = models.TextField(
        help_text="Encrypted card number or gift card number"
    )
    encrypted_cvv = models.TextField(
        null=True, blank=True,
        help_text="Encrypted CVV (credit cards only)"
    )
    encrypted_expiry = models.TextField(
        null=True, blank=True,
        help_text="Encrypted expiry MM/YY (credit cards only)"
    )
    encrypted_pin = models.TextField(
        null=True, blank=True,
        help_text="Encrypted PIN (gift cards only)"
    )

    # ------------------------------------------------------------------
    # Plaintext metadata (safe to store)
    # ------------------------------------------------------------------
    last_four = models.CharField(
        max_length=4,
        help_text="Last 4 digits — for display only"
    )

    # Balance tracking — updated manually or after each purchase
    available_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Known available balance. Null = unknown (credit cards). Required for gift cards."
    )

    # Billing address — linked to admin's existing address
    billing_address = models.ForeignKey(
        'pop_accounts.PopUpCustomerAddress',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Billing address on file for this card"
    )

    # Locking — prevents two bots using the same card simultaneously
    is_locked = models.BooleanField(
        default=False,
        help_text="True while a bot is actively using this card"
    )
    locked_by_execution = models.ForeignKey(
        'ProcurementExecution',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='locked_payment_method',
        help_text="Which execution currently holds this card"
    )
    locked_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the lock was acquired"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive cards are never selected by the bot"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bot Payment Method'
        verbose_name_plural = 'Bot Payment Methods'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.label} (···{self.last_four})"

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cipher():
        key = settings.ENCRYPTION_KEY
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in settings")
        return Fernet(key.encode() if isinstance(key, str) else key)

    @classmethod
    def encrypt(cls, value: str) -> str:
        """Encrypt a plaintext string, return base64 token."""
        return cls._cipher().encrypt(value.encode()).decode()

    @classmethod
    def decrypt(cls, token: str) -> str:
        """Decrypt a Fernet token, return plaintext string."""
        return cls._cipher().decrypt(token.encode()).decode()

    # ------------------------------------------------------------------
    # Convenience accessors (decrypt on demand, never stored)
    # ------------------------------------------------------------------

    @property
    def card_number(self) -> str:
        return self.decrypt(self.encrypted_number)

    @property
    def cvv(self) -> str:
        return self.decrypt(self.encrypted_cvv) if self.encrypted_cvv else ''

    @property
    def expiry(self) -> str:
        return self.decrypt(self.encrypted_expiry) if self.encrypted_expiry else ''

    @property
    def pin(self) -> str:
        return self.decrypt(self.encrypted_pin) if self.encrypted_pin else ''

    # ------------------------------------------------------------------
    # Balance check
    # ------------------------------------------------------------------

    def has_sufficient_balance(self, amount) -> bool:
        """
        Returns True if the card can cover the purchase amount.
        Credit cards with no balance set are assumed sufficient.
        Gift cards must have a known balance.
        """
        from decimal import Decimal
        if self.available_balance is None:
            # Credit card with unknown balance — assume OK
            return self.method_type == 'credit_card'
        return self.available_balance >= Decimal(str(amount))

    def deduct_balance(self, amount):
        """Subtract purchase amount from known balance and save."""
        from decimal import Decimal
        if self.available_balance is not None:
            self.available_balance = max(
                Decimal('0.00'),
                self.available_balance - Decimal(str(amount))
            )
            self.save(update_fields=['available_balance', 'updated_at'])

    # ------------------------------------------------------------------
    # Locking
    # ------------------------------------------------------------------

    def acquire_lock(self, execution) -> bool:
        """
        Atomically acquire the lock for an execution.
        Returns True if lock was acquired, False if already locked.
        """
        from django.db import transaction
        from django.utils import timezone

        with transaction.atomic():
            # Re-fetch with SELECT FOR UPDATE to prevent race conditions
            refreshed = BotPaymentMethod.objects.select_for_update().get(
                pk=self.pk
            )
            if refreshed.is_locked:
                return False

            refreshed.is_locked = True
            refreshed.locked_by_execution = execution
            refreshed.locked_at = timezone.now()
            refreshed.save(update_fields=[
                'is_locked', 'locked_by_execution', 'locked_at', 'updated_at'
            ])
            return True

    def release_lock(self):
        """Release the lock after procurement completes or fails."""
        self.is_locked = False
        self.locked_by_execution = None
        self.locked_at = None
        self.save(update_fields=[
            'is_locked', 'locked_by_execution', 'locked_at', 'updated_at'
        ])

    # ------------------------------------------------------------------
    # Class-level card selection
    # ------------------------------------------------------------------

    @classmethod
    def get_available_card(cls, required_amount=None):
        """
        Find an unlocked, active card with sufficient balance.

        Args:
            required_amount: Decimal purchase amount. If None, skips balance check.

        Returns:
            BotPaymentMethod instance or None if none available.
        """
        from decimal import Decimal

        candidates = cls.objects.filter(
            is_active=True,
            is_locked=False,
        ).select_related('billing_address')

        for card in candidates:
            if required_amount is None or card.has_sufficient_balance(required_amount):
                return card

        return None
    

    

# class Procurement
# tRequest(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('active', 'Active'),
#         ('fulfilled', 'Fulfilled'),
#         ('cancelled', 'Cancelled'),
#         ('expired', 'Expired'),
#     ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='procurement_requests'
#     )

#     product = models.ForeignKey(
#         PopUpProduct,
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL
#     )

#     product_name = models.CharField(max_length=255)

#     target_size = models.CharField(max_length=50)

#     max_price = models.DecimalField(
#         max_digits=10,
#         decimal_places=2
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='pending'
#     )

#     expires_at = models.DateTimeField(null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     updated_at = models.DateTimeField(auto_now=True)

# class BotExecution(models.Model):
#     """
#     Track each bot run attempt
#     """
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('running', 'Running'),
#         ('success', 'Success'),
#         ('failed', 'Failed'),
#         ('abandoned', 'Abandoned'),
#     ]
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='bot_executions')
    
#     # Link to product (optional - for tracking which product was procured)
#     product = models.ForeignKey(PopUpProduct, null=True, blank=True, on_delete=models.SET_NULL, related_name='bot_executions')
#     brand = models.ForeignKey(PopUpBrand, null=True, blank=True, on_delete=models.SET_NULL, related_name='bot_executions')
    
#     # Search parameters
#     product_name = models.CharField(max_length=255)
#     target_size = models.CharField(max_length=50)
#     target_color = models.CharField(max_length=100, null=True, blank=True)
#     price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    
#     # Execution details
#     strategy_used = models.CharField(max_length=50, default='sequential')
#     sites_attempted = models.JSONField(default=list)  # ["nike", "footlocker"]
#     winning_site = models.CharField(max_length=50, null=True, blank=True)
    
#     # Order details
#     order_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
#     item_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     reservation_fee_paid = models.BooleanField(default=False)

#     # added by gpt
#     procurement_request = models.ForeignKey(
#         ProcurementRequest,
#         null=True,
#         blank=True,
#         on_delete=models.CASCADE,
#         related_name='executions'
#     )

    # added by gpt
    # reservation_fee_transaction = models.ForeignKey(
    #     'pop_up_payments.PaymentTransaction',
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name='reservation_fee_executions'
    # )

    # added by gpt
    # final_payment_transaction = models.ForeignKey(
    #     'pop_up_payments.PaymentTransaction',
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name='final_payment_executions'
    # )

    # payment_method_type = models.CharField(
    #     max_length=50, 
    #     null=True, 
    #     blank=True,
    #     choices=[
    #         ('credit_card', 'Credit Card'),
    #         ('gift_card', 'Gift Card'),
    #     ]
    # )
    
    # # Status
    # status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # error_message = models.TextField(null=True, blank=True)
    
    # # Concierge mode
    # concierge_mode = models.BooleanField(default=False)
    
    # # Timestamps
    # started_at = models.DateTimeField()
    # completed_at = models.DateTimeField(null=True, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    
    # class Meta:
    #     ordering = ['-created_at']
    #     indexes = [
    #         models.Index(fields=['user', '-created_at']),
    #         models.Index(fields=['status']),
    #         models.Index(fields=['winning_site']),
    #         models.Index(fields=['order_id']),
    #     ]
    
    # def __str__(self):
    #     return f"{self.product_name} - {self.status} ({self.id})"
    
    # @property
    # def duration_seconds(self):
    #     """Calculate execution duration"""
    #     if self.completed_at and self.started_at:
    #         return (self.completed_at - self.started_at).total_seconds()
    #     return None
    
    # @property
    # def was_successful(self):
    #     """Quick check if bot succeeded"""
    #     return self.status == 'success' and self.order_id is not None





# class SiteAttempt(models.Model):
#     """
#     Track individual site attempt within a bot execution
#     """
#     ATTEMPT_STATUS_CHOICES = [
#         ('in_progress', 'In Progress'),
#         ('item_found', 'Item Found'),
#         ('added_to_cart', 'Added to Cart'),
#         ('checkout_started', 'Checkout Started'),
#         ('payment_failed', 'Payment Failed'),
#         ('order_confirmed', 'Order Confirmed'),
#         ('stock_out', 'Out of Stock'),
#         ('not_available', 'Not Available'),
#         ('error', 'Error'),
#     ]
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     bot_execution = models.ForeignKey(BotExecution, on_delete=models.CASCADE, related_name='site_attempts')
#     site_name = models.CharField(max_length=50)
#     attempt_number = models.PositiveIntegerField()
#     status = models.CharField(max_length=50, choices=ATTEMPT_STATUS_CHOICES)
#     product_url = models.URLField(null=True, blank=True)
#     product_sku = models.CharField(max_length=100, null=True, blank=True, help_text="Site's product SKU/ID")
#     error_message = models.TextField(null=True, blank=True)
#     screenshot = models.FileField(null=True, blank=True)
#     started_at = models.DateTimeField()
#     completed_at = models.DateTimeField(null=True, blank=True)
    
#     class Meta:
#         ordering = ['started_at']
#         indexes = [
#             models.Index(fields=['bot_execution', 'site_name']),
#             models.Index(fields=['status']),
#         ]
    
#     def __str__(self):
#         return f"{self.bot_execution.id} - {self.site_name}"
    
#     @property
#     def duration_seconds(self):
#         """Calculate attempt duration"""
#         if self.completed_at and self.started_at:
#             return (self.completed_at - self.started_at).total_seconds()
#         return None


# class PaymentMethod(models.Model):
#     """
#     Store encrypted payment credentials
#     Associated with user (for future concierge mode)
#     """
#     PAYMENT_CHOICES = [
#         ('credit_card', 'Credit Card'),
#         ('gift_card', 'Gift Card'),
#     ]
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='payment_methods')
#     method_type = models.CharField(max_length=50, choices=PAYMENT_CHOICES)
    
#     # Encrypted fields (never display unencrypted)
#     encrypted_number = models.BinaryField(help_text="AES-256 encrypted card/gift card number")
#     encrypted_csv = models.BinaryField(help_text="AES-256 encrypted CVV/CSV")
#     encrypted_expiry = models.BinaryField(help_text="AES-256 encrypted expiration date")
#     encrypted_pin = models.BinaryField(null=True, blank=True, help_text="AES-256 encrypted PIN (gift cards only)")
    
#     # Metadata (safe to display)
#     last_four = models.CharField(max_length=4, help_text="Last 4 digits for display")
#     card_holder_name = models.CharField(max_length=255, null=True, blank=True)
#     is_active = models.BooleanField(default=True)
    
#     # Tracking
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     last_used_at = models.DateTimeField(null=True, blank=True)
    
#     class Meta:
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['user', 'is_active']),
#         ]
    
#     def __str__(self):
#         return f"{self.get_method_type_display()} ending in {self.last_four}"


