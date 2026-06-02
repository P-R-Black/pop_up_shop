# CELERY SCHEDULER SETUP GUIDE

## Step 1: Copy the Scheduler Task File

```bash
cp tasks.py pop_up_bot/tasks.py
cp test_scheduler.py pop_up_bot/tests/test_scheduler.py
```

## Step 2: Update Your Django Settings

Add to `pop_up_shop/settings.py`:

```python
# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

import os
from celery.schedules import crontab

# Celery broker (Redis or RabbitMQ)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Celery configuration
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'US/Eastern'  # Change to your timezone
CELERY_ENABLE_UTC = True

# Task time limit (3 hours)
CELERY_TASK_TIME_LIMIT = 3 * 60 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 2.5 * 60 * 60

# Celery Beat Schedule - Scheduler runs every minute
CELERY_BEAT_SCHEDULE = {
    'process-scheduled-releases': {
        'task': 'pop_up_bot.tasks.process_scheduled_releases',
        'schedule': crontab(minute='*'),  # Every minute
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/celery.log',
        },
    },
    'loggers': {
        'pop_up_bot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

## Step 3: Create Celery App Configuration

Create `pop_up_shop/celery.py`:

```python
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pop_up_shop.settings')

app = Celery('pop_up_shop')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

Then update `pop_up_shop/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## Step 4: Install Redis (if not already installed)

### Mac (Homebrew):
```bash
brew install redis
brew services start redis
```

### Linux (Ubuntu):
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

## Step 5: Start Celery Workers

In separate terminal windows:

### Terminal 1 - Celery Worker
```bash
celery -A pop_up_shop worker -l info
```

### Terminal 2 - Celery Beat Scheduler
```bash
celery -A pop_up_shop beat -l info
```

### (Optional) Terminal 3 - Monitor Tasks
```bash
celery -A pop_up_shop events
```

## Step 6: Run Tests

```bash
pytest pop_up_bot/tests/test_scheduler.py -v
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                      EVERY MINUTE                           │
├─────────────────────────────────────────────────────────────┤
│  1. Celery Beat runs process_scheduled_releases()           │
│     ↓                                                         │
│  2. Finds all ScheduledRelease with is_active=True          │
│     ↓                                                         │
│  3. For each release:                                       │
│     - Gets all pending ProcurementServiceRequest            │
│     - Creates ProcurementRequest for each user              │
│     - Queues execute_procurement_request task               │
│     - Creates ReleaseExecutionBatch                         │
│     ↓                                                         │
│  4. Worker runs execute_procurement_request tasks in parallel│
│     - Initializes NikeSiteHandler                           │
│     - Runs BotOrchestrator                                  │
│     - Updates service_request status (success/failed)       │
│     - Sends email notifications                            │
│     ↓                                                         │
│  5. Batch completes when all tasks finish                   │
└─────────────────────────────────────────────────────────────┘
```

## Admin Dashboard Workflow

### Admin Actions:
1. Views PopUpCustomerProfile.prods_interested_in
2. Sees "15 users interested in Air Jordan 1"
3. Creates ScheduledRelease (release_date, SKU, URL)
4. Runs scheduler (or waits for scheduled time)

### Scheduler Actions:
1. At release_date, finds ScheduledRelease with is_active=True
2. Gets all pending ProcurementServiceRequest
3. Creates ProcurementRequest for each user
4. Runs bot in parallel
5. Updates statuses and sends emails

### Result:
- 5 users paid for service
- 3 succeeded (items in carts)
- 2 failed (refunds processed)
- Admin sees batch stats: "3/5 succeeded"

## Troubleshooting

### Redis connection error
```
Error: [Errno 61] Connection refused
```
**Fix:** Start Redis:
```bash
redis-server
```

### Tasks not running
```
celery -A pop_up_shop worker -l debug
```
Check for errors. Look for 'autodiscover_tasks' in logs.

### Scheduler not firing
```
celery -A pop_up_shop beat -l debug
```
Check that beat is scheduling tasks. Look for "Scheduler: Scheduler started".

### Check Celery Flower UI (Optional)

```bash
pip install flower
celery -A pop_up_shop flower
# Visit http://localhost:5555
```

## Production Notes

For production, use:

### Supervisor for Celery Worker
```ini
[program:celery_worker]
command=celery -A pop_up_shop worker -l info
directory=/path/to/pop_up_shop
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
```

### Supervisor for Celery Beat
```ini
[program:celery_beat]
command=celery -A pop_up_shop beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/pop_up_shop
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
```

### Or Use Docker

```dockerfile
FROM python:3.13

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Worker
CMD celery -A pop_up_shop worker -l info

# Beat (separate container)
# CMD celery -A pop_up_shop beat -l info
```

## Monitoring & Alerts

Add to settings.py for production:

```python
# Alert on task failure
CELERY_TASK_TRACK_STARTED = True

# Retry failed tasks
CELERY_TASK_MAX_RETRIES = 3

# Send alerts (optional Sentry integration)
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[CeleryIntegration()]
)
```

## Database Migrations (if needed)

If using `django_celery_beat`:

```bash
pip install django-celery-beat
```

Add to INSTALLED_APPS:
```python
INSTALLED_APPS = [
    ...
    'django_celery_beat',
]
```

Then:
```bash
python manage.py migrate
```

This allows managing schedules via Django admin instead of settings.py.

## Testing Without Running Celery

```python
# In tests, call tasks directly:
from pop_up_bot.tasks import process_scheduled_releases

result = process_scheduled_releases()
assert result['releases_processed'] == 1
```

Or with eager mode for tests:

```python
# settings.py
CELERY_TASK_ALWAYS_EAGER = True  # Execute synchronously in tests
```

---

**Ready? Run the tests:**
```bash
pytest pop_up_bot/tests/test_scheduler.py -v
```

**Questions? Check the task comments in pop_up_bot/tasks.py**
