import os
from celery import Celery


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pop_up_shop.settings.base')
app = Celery('pop_up_shop')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Add this line to use Celery Beat as the periodic task scheduler
app.conf.beat_scheduler = "django_celery_beat.schedulers.DatabaseScheduler"


app.autodiscover_tasks()
