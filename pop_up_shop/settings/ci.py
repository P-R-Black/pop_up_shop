from .base import *

DEBUG = False
SECRET_KEY = "ci-not-secret"
ALLOWED_HOSTS = ['localhost']
USE_RECAPTCHA = False
RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = ""
print("CI USE_RECAPTCHA =", USE_RECAPTCHA)
print('sys', sys)

# ------ Shared Apps Path ------
# for use on VPS
SHARED_APPS_DIR = os.environ.get(
    'SHARED_APPS_DIR',
    '/home/paulb/shared_apps'
)
sys.path.insert(0, SHARED_APPS_DIR)

print('SHARED_APPS_DIR', SHARED_APPS_DIR)

INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app != "django_recaptcha"
]



# PostgreSQL — single DB, two aliases
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME":"ci_db", # os.environ.get("POSTGRES_DB", "postgres"),
#         "USER": os.environ.get("POSTGRES_USER", "postgres"),
#         "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
#         "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
#         "PORT": os.environ.get("POSTGRES_PORT", "5432"),
#     }
# }


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ci_db",
        "USER": "postgres",
        "PASSWORD":"postgres", # env('POP_UP_SHARED_DEV_DB_PASSWORD'), #"postgres",
        "HOST": "localhost",
        "PORT": 5432,
    },
    "shared_auth": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ci_db",
        "USER": "postgres",
        "PASSWORD": "postgres", # env('POP_UP_SHARED_DEV_DB_PASSWORD'), #"postgres",
        "HOST": "localhost",
        "PORT": 5432,
    },
}

# Ensure routers are active
DATABASE_ROUTERS = [
  
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




print("✅ Loaded CI settings")
print("USE_RECAPTCHA =", USE_RECAPTCHA)