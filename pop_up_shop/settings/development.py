# from pathlib import Path
from .base import *
import os
import environ

env = environ.Env()
# environ.Env.read_env()

DEBUG = True

# ------ Shared Apps Path ------
# For local dev use
SHARED_APPS_DIR = os.environ.get(
    "SHARED_APPS_DIR",
    "/Users/paulblack/PycharmProjects/Projects/shared_apps"
)
sys.path.insert(0, SHARED_APPS_DIR)


ALLOWED_HOSTS = [
    'mysite.com', 
    "localhost:8000",  
    "localhost", 
    "b537-2600-1700-1580-da40-95ee-f24c-ab30-f44f.ngrok-free.app", 
    "https://*.ngrok.io",
    "162.243.128",
    ]


# Use in-memory database for tests
# if 'test' in sys.argv:
#     DATABASES = {
#         'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': ':memory:',  # In-memory database - no cleanup needed
#         'ATOMIC_REQUESTS': True,  # Ensure test isolation
#         }
#     }

# else:
# Database
# Add PostgreSQL config
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'shared_auth_db',  # Same database as accounts_master
        'USER': 'paulblack',
        'PASSWORD': '',  # Blank since using trust auth
        # 'HOST': 'localhost',
        'PORT': '5432',
    }
}




# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql', # env('POP_UP_SHARED_DB_ENGINE'),
#         'NAME': 'pop_up_shop_dev_db',  # env('POP_UP_SHARED_DEFAULT_DEV_DB_NAME'),
#         'USER': "paulblack",
#         'PASSWORD': "", #env('POP_UP_SHARED_DEV_DB_PASSWORD'),
#         # 'HOST': "localhost",
#         'PORT': 5432, #  env('POP_UP_SHARED_DEV_DB_PORT')
#     },
#     'shared_auth': {
#         'ENGINE': 'django.db.backends.postgresql', # env('POP_UP_SHARED_DB_ENGINE'),
#         'NAME': 'shared_auth_db_dev', # env('POP_UP_SHARED_DEV_DB_NAME'),
#         'USER': "paulblack",
#         'PASSWORD': "", #env('POP_UP_SHARED_DEV_DB_PASSWORD'),
#         # 'HOST': "localhost",
#         'PORT': 5432 #  env('POP_UP_SHARED_DEV_DB_PORT'),

#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2', # env('POP_UP_SHARED_DB_ENGINE'),
#         'NAME': 'pop_up_shop_dev_db',  # env('POP_UP_SHARED_DEFAULT_DEV_DB_NAME'),
#         'USER': env('POP_UP_SHARED_DEV_DB_USER'),
#         'PASSWORD': env('POP_UP_SHARED_DEV_DB_PASSWORD'),
#         'HOST': env('POP_UP_SHARED_DEV_DB_HOST'),
#         'PORT': '25060', #  env('POP_UP_SHARED_DEV_DB_PORT')
#     },
#     'shared_auth': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2', # env('POP_UP_SHARED_DB_ENGINE'),
#         'NAME': 'shared_auth_db_dev', # env('POP_UP_SHARED_DEV_DB_NAME'),
#         'USER': env('POP_UP_SHARED_DEV_DB_USER'),
#         'PASSWORD': env('POP_UP_SHARED_DEV_DB_PASSWORD'),
#         'HOST': env('POP_UP_SHARED_DEV_DB_HOST'),
#         'PORT': '25060' #  env('POP_UP_SHARED_DEV_DB_PORT'),

#     }
# }

# print('Databases Config', DATABASES)
print("Loaded LOCAL DEVELOPMENT settings")
