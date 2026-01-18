# from pathlib import Path
from .base import *
import os
import environ

env = environ.Env()
# environ.Env.read_env()

DEBUG = True

# ------ Shared Apps Path ------
# for use on VPS
SHARED_APPS_DIR = os.environ.get(
    'SHARED_APPS_DIR',
    '/home/paulb/shared_apps'
)
sys.path.insert(0, SHARED_APPS_DIR)


ALLOWED_HOSTS = [
    'dev.popupshop.paulrblack.com', 
    'www.dev.popupshop.paulrblack.com',
    ]



# Database
# Add VPS Def PostgreSQL config
DATABASES = {
    'default': {
        'ENGINE': env('POP_UP_SHARED_VPS_DEV_DB_ENGINE'),
        'NAME': env('POP_UP_SHARED_VPS_DEV_DB_NAME'),
        'USER':  env('POP_UP_SHARED_VPS_DEV_DB_USER'),
        'PASSWORD': env('POP_UP_SHARED_VPS_DEV_DB_PASSWORD'),
        'HOST': env('POP_UP_SHARED_VPS_DEV_DB_HOST'),
        'PORT': env('POP_UP_SHARED_VPS_DEV_DB_PORT'),
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
print("Loaded VPS DEVELOPMENT settings")
