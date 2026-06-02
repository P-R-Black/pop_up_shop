# pop_up_bot/tasks.py
"""
Celery tasks for automated procurement scheduling.

The scheduler:
1. Runs every minute (configurable)
2. Finds ScheduledRelease instances that are active
3. For each active release, gets all pending ProcurementServiceRequest
4. Creates ProcurementRequest for each user
5. Runs BotOrchestrator with NikeSiteHandler in parallel
6. Groups results in ReleaseExecutionBatch
7. Updates user statuses (success/failed)
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import asyncio
import logging

from pop_up_bot.models import (
    ScheduledRelease,
    ProcurementServiceRequest,
    ProcurementRequest,
    ReleaseExecutionBatch,
)
from pop_up_bot.orchestrator import BotOrchestrator
# from pop_up_bot.handlers.nike_handler import NikeSiteHandler
from pop_up_bot.engines.scraper_engine import PlaywrightScraperEngine
from pop_up_bot.managers.session_manager import SessionManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_scheduled_releases(self):
    """
    Main scheduler task - runs every minute to check for active releases.
    
    This is called by Celery Beat periodically (see celerybeat_schedule).
    
    Process:
    1. Find all ScheduledRelease with status='active' (within release window)
    2. For each release:
       a. Get all ProcurementServiceRequest with status='pending'
       b. Create ProcurementRequest for each user
       c. Run BotOrchestrator in parallel
       d. Update request statuses
       e. Create ReleaseExecutionBatch for reporting
    3. Send notifications to users
    """
    try:
        logger.info("Starting scheduled release processor")
        
        # Find all active releases
        active_releases = ScheduledRelease.objects.filter(
            status='scheduled'
        ).filter(
            release_date__lte=timezone.now(),
            release_date__gte=timezone.now() - timezone.timedelta(minutes=31)
        )
        
        if not active_releases.exists():
            logger.info("No active releases to process")
            return {
                'status': 'ok',
                'releases_processed': 0,
                'message': 'No active releases'
            }
        
        logger.info(f"Found {active_releases.count()} active releases")
        
        results = {
            'releases_processed': 0,
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
        }
        
        for release in active_releases:
            try:
                logger.info(f"Processing release: {release.product.product_title}")
                release_results = process_release(release)
                
                results['releases_processed'] += 1
                results['total_attempts'] += release_results['total_attempts']
                results['successful'] += release_results['successful']
                results['failed'] += release_results['failed']
                
                if release_results['errors']:
                    results['errors'].extend(release_results['errors'])
            
            except Exception as e:
                error_msg = f"Error processing release {release.sku}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results['errors'].append(error_msg)
                
                # Retry with exponential backoff
                try:
                    self.retry(exc=e, countdown=2 ** self.request.retries)
                except Exception:
                    logger.error(f"Max retries exceeded for {release.sku}")
        
        logger.info(f"Scheduler results: {results}")
        return results
    
    except Exception as e:
        logger.error(f"Scheduler task failed: {str(e)}", exc_info=True)
        raise


def process_release(release: ScheduledRelease) -> dict:
    """
    Process a single ScheduledRelease.
    
    Args:
        release: ScheduledRelease instance
    
    Returns:
        dict with results: {
            'total_attempts': int,
            'successful': int,
            'failed': int,
            'errors': [str],
        }
    """
    logger.info(f"Processing release: {release.sku}")
    
    results = {
        'total_attempts': 0,
        'successful': 0,
        'failed': 0,
        'errors': [],
    }
    
    # Get all pending service requests for this release
    pending_requests = ProcurementServiceRequest.objects.filter(
        scheduled_release=release,
        status='pending'
    )
    
    if not pending_requests.exists():
        logger.info(f"No pending requests for release {release.sku}")
        return results
    
    logger.info(f"Found {pending_requests.count()} pending requests for {release.sku}")
    results['total_attempts'] = pending_requests.count()
    
    # Create batch to group all executions
    batch = ReleaseExecutionBatch.objects.create(
        scheduled_release=release,
        total_attempts=pending_requests.count(),
        started_at=timezone.now(),
    )
    
    # Process each service request
    execution_tasks = []
    
    for service_request in pending_requests:
        try:
            with transaction.atomic():

                # Create ProcurementRequest
                proc_request = service_request.create_procurement_request()
                
                logger.info(
                    f"Created ProcurementRequest {proc_request.id} "
                    f"for user {service_request.user.email}"
                )
                
                # Queue the actual execution (can be async)
                task = execute_procurement_request.delay(
                    proc_request.id,
                    service_request.id,
                    batch.id,
                )
                
                execution_tasks.append({
                    'task_id': task.id,
                    'service_request_id': service_request.id,
                    'proc_request_id': proc_request.id,
                })
        
        except Exception as e:
            error_msg = f"Error creating request for {service_request.user.email}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            results['failed'] += 1
            
            ProcurementServiceRequest.objects.filter(id=service_request.id).update(
                status='failed'
            )

            # Update service request status
            # service_request.status = 'failed'
            # service_request.save()
    
    # Log the batch
    logger.info(
        f"Created batch {batch.id} with {len(execution_tasks)} execution tasks "
        f"for release {release.sku}"
    )
    
    # Update release status
    release.status = 'active'
    release.save()
    
    results['successful'] = len(execution_tasks)
    
    return results


@shared_task(bind=True, max_retries=2)
def execute_procurement_request(self, proc_request_id: str, service_request_id: str, batch_id: str):
    """
    Execute a single procurement request.
    
    This runs the bot for one user. Can be run in parallel.
    
    Args:
        proc_request_id: UUID of ProcurementRequest
        service_request_id: UUID of ProcurementServiceRequest
        batch_id: UUID of ReleaseExecutionBatch
    """
    logger.info(f"Starting execution for request {proc_request_id}")
    
    try:
        # Fetch objects
        proc_request = ProcurementRequest.objects.get(id=proc_request_id)
        service_request = ProcurementServiceRequest.objects.get(id=service_request_id)
        batch = ReleaseExecutionBatch.objects.get(id=batch_id)
        
        # Initialize bot components
        session_manager = SessionManager()
        scraper_engine = PlaywrightScraperEngine(
            headless=True,
            disable_images=True,
            user_agent='Nike Bot'
        )
        
        orchestrator = BotOrchestrator(
            session_manager=session_manager,
            event_logger=None,  # TODO: Add event logger
        )
        
        # Run procurement
        result = asyncio.run(
            orchestrator.run(
                product_name=proc_request.product_name,
                size=proc_request.target_size,
                color=proc_request.target_color,
                strategy_name=service_request.strategy,
                price_range=(0, service_request.max_price or 10000),
                site_name='nike',
            )
        )
        
        # Handle results
        execution = result.get('execution')
        
        if result.get('status') == 'success' and execution:
            logger.info(f"Success! Order {execution.order_id} for {service_request.user.email}")
            
            # Update service request
            service_request.procurement_execution = execution
            service_request.status = 'success'
            service_request.save()
            
            # Update request
            proc_request.status = 'fulfilled'
            proc_request.fulfilled_at = timezone.now()
            proc_request.save()
            
            # Update batch
            batch.successful_count += 1
            batch.executions.add(execution)
            batch.save()
            
            # Send success email
            send_success_notification(service_request, execution)
        
        else:
            logger.warning(f"Failed to secure item for {service_request.user.email}")
            
            # Update service request
            service_request.status = 'failed'
            service_request.save()
            
            # Update request
            proc_request.status = 'cancelled'
            proc_request.save()
            
            # Update batch
            batch.failed_count += 1
            batch.save()
            
            # Send failure email
            send_failure_notification(service_request, result.get('error'))
        
        # Update batch completion
        batch.completed_at = timezone.now()
        batch.save()
        
        logger.info(f"Execution complete for request {proc_request_id}")
        return {
            'status': 'success' if result.get('status') == 'success' else 'failed',
            'order_id': execution.order_id if execution else None,
        }
    
    except Exception as e:
        error_msg = f"Execution failed for {proc_request_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Retry
        try:
            self.retry(exc=e, countdown=60)
        except Exception:
            # Max retries exceeded
            service_request = ProcurementServiceRequest.objects.get(id=service_request_id)
            service_request.status = 'failed'
            service_request.save()
            
            batch = ReleaseExecutionBatch.objects.get(id=batch_id)
            batch.failed_count += 1
            batch.save()
            
            send_failure_notification(service_request, error_msg)
        
        raise


def send_success_notification(service_request: ProcurementServiceRequest, execution):
    """Send email when bot successfully secures item"""
    user = service_request.user
    product = service_request.scheduled_release.product
    
    subject = f"✅ We secured {product.product_title}!"
    message = f"""
    Hi {user.first_name},
    
    Great news! We successfully secured the {product.product_title} in size {service_request.size}.
    
    Order ID: {execution.order_id}
    Price: ${execution.item_price}
    
    The item is in your cart and reserved for 48 hours. 
    Please complete your purchase at: {settings.SITE_URL}/cart
    
    Best,
    Pop Up Shop Bot
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Success notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send success email to {user.email}: {str(e)}")


def send_failure_notification(service_request: ProcurementServiceRequest, error: str):
    """Send email when bot fails to secure item"""
    user = service_request.user
    product = service_request.scheduled_release.product
    
    subject = f"❌ We couldn't secure {product.product_title}"
    message = f"""
    Hi {user.first_name},
    
    Unfortunately, we were unable to secure the {product.product_title} in size {service_request.size}.
    
    Reason: {error or 'Item went out of stock'}
    
    Your ${service_request.service_fee} fee has been refunded to your account.
    
    Better luck next time!
    
    Pop Up Shop Bot
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Failure notification sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send failure email to {user.email}: {str(e)}")


# ============================================================================
# CELERY BEAT SCHEDULE
# ============================================================================

"""
Add this to your settings.py to enable the scheduler:

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'process-scheduled-releases': {
        'task': 'pop_up_bot.tasks.process_scheduled_releases',
        'schedule': crontab(minute='*/1'),  # Every minute
        # OR:
        # 'schedule': 60.0,  # Every 60 seconds
    },
}

CELERY_TIMEZONE = 'US/Eastern'  # Or your timezone

Then start Celery Beat:
    celery -A pop_up_shop beat -l info

And start Celery worker:
    celery -A pop_up_shop worker -l info
"""