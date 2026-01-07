from .base import *

DEBUG = False
SECRET_KEY = "ci-not-secret"
ALLOWED_HOSTS = ['localhost']

INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app != "django_recaptcha"
]

# PostgreSQL — single DB, two aliases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ci_db",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    },
    "shared_auth": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ci_db",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    },
}

# Ensure routers are active
DATABASE_ROUTERS = [
    'accounts.routers.SharedAuthRouter',
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


# Static files (no collectstatic in CI)
STATIC_URL = "/static/"

# Speed up tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher"
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True