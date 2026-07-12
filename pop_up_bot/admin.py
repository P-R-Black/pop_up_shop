# pop_up_bot/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from .models import (
    CookieModel,
    ProcurementRequest,
    ProcurementExecution,
    ExternalProductReference,
    InventoryLock,
    ProcurementEvent,
    BotLog,
    SiteAttempt,
    ScheduledRelease,
    ProcurementServiceRequest
)


from django import forms
from pop_up_bot.models import BotPaymentMethod


@admin.register(CookieModel)
class CookieModelAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'name', 'domain', 'is_expired', 'updated_at')
    list_filter = ('site_name', 'updated_at')
    search_fields = ('site_name', 'name', 'domain')
    readonly_fields = ('saved_at', 'updated_at')
    
    fieldsets = (
        ('Cookie Info', {
            'fields': ('site_name', 'name', 'value', 'domain', 'path')
        }),
        ('Settings', {
            'fields': ('http_only', 'secure', 'same_site')
        }),
        ('Expiration', {
            'fields': ('expires',)
        }),
        ('Timestamps', {
            'fields': ('saved_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScheduledRelease)
class ScheduledReleaseAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'release_date', 'status')
    list_filter = ('status', 'release_date')
    search_fields = ('sku', 'product__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    

@admin.register(ProcurementRequest)
class ProcurementRequestAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'target_size', 'max_price', 'status', 'user', 'created_at')
    list_filter = ('status', 'procurement_type', 'created_at')
    search_fields = ('product_name', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'execution_count', 'execution_success_count')
    
    fieldsets = (
        ('Request Info', {
            'fields': ('id', 'user', 'product', 'brand', 'product_name')
        }),
        ('Search Parameters', {
            'fields': ('target_size', 'target_color', 'max_price', 'price_range')
        }),
        ('Status', {
            'fields': ('status', 'priority_score', 'procurement_type')
        }),
        ('Expiration', {
            'fields': ('expires_at', 'fulfilled_at')
        }),
        ('Statistics', {
            'fields': ('execution_count', 'execution_success_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_range(self, obj):
        """Display price range"""
        return f"${0} - ${obj.max_price}"



@admin.register(ProcurementServiceRequest)
class ProcurementServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'scheduled_release', 'size', 'sex', 'status', 'service_fee', 'fee_paid_at', 'created_at']
    list_filter = ['status', 'strategy']
    search_fields = ['user__email', 'scheduled_release__product__product_title']
    readonly_fields = ['created_at', 'updated_at', 'fee_paid_at']
    ordering = ['-created_at']


@admin.register(ProcurementExecution)
class ProcurementExecutionAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'procurement_request', 'status', 'strategy_used', 'winning_site', 'order_id', 'started_at')
    list_filter = ('status', 'strategy_used', 'winning_site', 'started_at')
    search_fields = ('id', 'order_id', 'procurement_request__product_name')
    readonly_fields = ('id', 'idempotency_key', 'created_at', 'duration_seconds', 'event_count', 'log_count')
    
    fieldsets = (
        ('Execution Info', {
            'fields': ('id', 'procurement_request', 'status')
        }),
        ('Strategy & Result', {
            'fields': ('strategy_used', 'winning_site', 'order_id', 'item_price')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Error Handling', {
            'fields': ('error_message',)
        }),
        ('System', {
            'fields': ('idempotency_key', 'task_id'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('event_count', 'log_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        """Show truncated ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def event_count(self, obj):
        """Count related events"""
        return obj.events.count()
    event_count.short_description = 'Events'
    
    def log_count(self, obj):
        """Count related logs"""
        return obj.logs.count()
    log_count.short_description = 'Logs'


class ProcurementEventInline(admin.TabularInline):
    """Inline events for execution detail"""
    model = ProcurementEvent
    fields = ('event_type', 'site_name', 'timestamp')
    readonly_fields = ('event_type', 'site_name', 'timestamp')
    extra = 0
    can_delete = False


class SiteAttemptInline(admin.TabularInline):
    """Inline site attempts for execution detail"""
    model = SiteAttempt
    fields = ('site_name', 'status', 'failure_reason', 'started_at')
    readonly_fields = ('site_name', 'status', 'failure_reason', 'started_at')
    extra = 0
    can_delete = False


@admin.register(ExternalProductReference)
class ExternalProductReferenceAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'external_sku', 'product', 'last_known_price', 'last_verified_at')
    list_filter = ('site_name', 'last_verified_at')
    search_fields = ('external_sku', 'product__product_title')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Reference Info', {
            'fields': ('id', 'product', 'site_name', 'external_sku')
        }),
        ('Link', {
            'fields': ('external_url',)
        }),
        ('Price Tracking', {
            'fields': ('last_known_price', 'last_price_check')
        }),
        ('Verification', {
            'fields': ('last_verified_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(InventoryLock)
class InventoryLockAdmin(admin.ModelAdmin):
    list_display = ('product_identifier', 'size', 'site_name', 'status', 'execution_link', 'is_active')
    list_filter = ('status', 'site_name', 'acquired_at')
    search_fields = ('product_identifier', 'execution__id')
    readonly_fields = ('id', 'acquired_at', 'execution_link', 'is_active', 'is_expired')
    
    fieldsets = (
        ('Lock Info', {
            'fields': ('id', 'product_identifier', 'size', 'site_name')
        }),
        ('Execution', {
            'fields': ('execution', 'execution_link')
        }),
        ('Status', {
            'fields': ('status', 'locked_until', 'is_active', 'is_expired')
        }),
        ('Lifecycle', {
            'fields': ('acquired_at', 'released_at'),
            'classes': ('collapse',)
        }),
    )
    
    def execution_link(self, obj):
        """Link to execution"""
        url = reverse('admin:pop_up_bot_procurementexecution_change', args=[obj.execution.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.execution.id)[:8])
    execution_link.short_description = 'Execution'


@admin.register(ProcurementEvent)
class ProcurementEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'site_name', 'execution_link', 'timestamp')
    list_filter = ('event_type', 'site_name', 'timestamp')
    search_fields = ('bot_execution__id',)
    readonly_fields = ('id', 'bot_execution', 'timestamp', 'metadata_display')
    
    fieldsets = (
        ('Event Info', {
            'fields': ('id', 'event_type', 'site_name', 'bot_execution')
        }),
        ('Metadata', {
            'fields': ('metadata_display',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def execution_link(self, obj):
        """Link to execution"""
        url = reverse('admin:pop_up_bot_procurementexecution_change', args=[obj.bot_execution.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.bot_execution.id)[:8])
    execution_link.short_description = 'Execution'
    
    def metadata_display(self, obj):
        """Pretty display of metadata JSON"""
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
    metadata_display.short_description = 'Metadata'


@admin.register(BotLog)
class BotLogAdmin(admin.ModelAdmin):
    list_display = ('level', 'message_truncated', 'bot_execution', 'timestamp')
    list_filter = ('level', 'timestamp')
    search_fields = ('message', 'bot_execution__id')
    readonly_fields = ('id', 'bot_execution', 'timestamp', 'context_display')
    
    fieldsets = (
        ('Log Info', {
            'fields': ('id', 'level', 'message', 'bot_execution')
        }),
        ('Context', {
            'fields': ('context_display',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def message_truncated(self, obj):
        """Truncate long messages"""
        return obj.message[:75] + '...' if len(obj.message) > 75 else obj.message
    message_truncated.short_description = 'Message'
    
    def context_display(self, obj):
        """Pretty display of context JSON"""
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.context, indent=2))
    context_display.short_description = 'Context'


@admin.register(SiteAttempt)
class SiteAttemptAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'status', 'failure_reason', 'execution_link', 'duration_seconds', 'started_at')
    list_filter = ('site_name', 'status', 'failure_reason', 'started_at')
    search_fields = ('site_name', 'execution__id', 'external_sku')
    readonly_fields = ('id', 'started_at', 'duration_seconds', 'execution_link')
    
    fieldsets = (
        ('Attempt Info', {
            'fields': ('id', 'site_name', 'execution', 'execution_link')
        }),
        ('Status', {
            'fields': ('status', 'failure_reason')
        }),
        ('Product Info', {
            'fields': ('product_url', 'external_sku')
        }),
        ('Errors', {
            'fields': ('error_message',)
        }),
        ('Retry', {
            'fields': ('retry_count',)
        }),
        ('Debugging', {
            'fields': ('screenshot',),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
    )
    
    def execution_link(self, obj):
        """Link to execution"""
        url = reverse('admin:pop_up_bot_procurementexecution_change', args=[obj.execution.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.execution.id)[:8])
    execution_link.short_description = 'Execution'




class BotPaymentMethodAdminForm(forms.ModelForm):
    """
    Custom form for adding/editing payment methods in Django admin.

    Accepts plaintext card details and encrypts them on save.
    Plain fields are write-only — they never display existing values
    to avoid accidentally exposing decrypted data.
    """

    # Write-only plaintext fields — not model fields
    card_number_plain = forms.CharField(
        label='Card / Gift Card Number',
        required=True,
        widget=forms.PasswordInput(render_value=False),
        help_text='Enter full card number. Will be encrypted on save.'
    )
    cvv_plain = forms.CharField(
        label='CVV',
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Credit cards only. Leave blank for gift cards.'
    )
    expiry_plain = forms.CharField(
        label='Expiry (MM/YY)',
        required=False,
        max_length=5,
        help_text='Credit cards only e.g. 09/27. Leave blank for gift cards.'
    )
    pin_plain = forms.CharField(
        label='PIN',
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Gift cards only. Leave blank for credit cards.'
    )

    class Meta:
        model = BotPaymentMethod
        fields = [
            'label', 'method_type', 'last_four',
            'available_balance', 'billing_address',
            'is_active',
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Encrypt card number
        number = self.cleaned_data.get('card_number_plain', '').strip()
        if number:
            instance.encrypted_number = BotPaymentMethod.encrypt(number)
            instance.last_four = number[-4:]

        # Encrypt CVV
        cvv = self.cleaned_data.get('cvv_plain', '').strip()
        if cvv:
            instance.encrypted_cvv = BotPaymentMethod.encrypt(cvv)

        # Encrypt expiry
        expiry = self.cleaned_data.get('expiry_plain', '').strip()
        if expiry:
            instance.encrypted_expiry = BotPaymentMethod.encrypt(expiry)

        # Encrypt PIN
        pin = self.cleaned_data.get('pin_plain', '').strip()
        if pin:
            instance.encrypted_pin = BotPaymentMethod.encrypt(pin)

        if commit:
            instance.save()
        return instance


@admin.register(BotPaymentMethod)
class BotPaymentMethodAdmin(admin.ModelAdmin):
    form = BotPaymentMethodAdminForm

    list_display = [
        'label', 'method_type', 'last_four',
        'available_balance', 'is_active', 'is_locked',
        'locked_by_execution', 'updated_at',
    ]
    list_filter  = ['method_type', 'is_active', 'is_locked']
    search_fields = ['label', 'last_four']
    readonly_fields = [
        'is_locked', 'locked_by_execution', 'locked_at',
        'created_at', 'updated_at',
    ]

    fieldsets = (
        ('Card Details', {
            'fields': (
                'label', 'method_type',
                'card_number_plain', 'cvv_plain',
                'expiry_plain', 'pin_plain',
                'last_four',
            ),
            'description': (
                'Card number and sensitive fields are encrypted on save. '
                'Leave a field blank to keep the existing encrypted value.'
            ),
        }),
        ('Balance & Address', {
            'fields': ('available_balance', 'billing_address'),
        }),
        ('Status', {
            'fields': ('is_active', 'is_locked', 'locked_by_execution', 'locked_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['force_release_lock', 'deactivate_cards', 'activate_cards']

    def force_release_lock(self, request, queryset):
        """Admin action to force-release stuck card locks."""
        released = 0
        for card in queryset.filter(is_locked=True):
            card.release_lock()
            released += 1
        self.message_user(request, f"Released {released} card lock(s).")
    force_release_lock.short_description = "Force release lock on selected cards"

    def deactivate_cards(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} card(s).")
    deactivate_cards.short_description = "Deactivate selected cards"

    def activate_cards(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} card(s).")
    activate_cards.short_description = "Activate selected cards"