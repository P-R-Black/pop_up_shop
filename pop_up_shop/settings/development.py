from pathlib import Path
from .base import *
import os
from dotenv import load_dotenv

DEBUG = True

ALLOWED_HOSTS = [
    'dev.popupshop.paulrblack.com', 
    'www.dev.popupshop.paulrblack.com', 'mysite.com', "localhost:8000",  "localhost", "38c0db4405f5.ngrok-free.app","https://*.ngrok.io","162.243.128"]


env = environ.Env()
environ.Env.read_env()

# Database
# Add PostgreSQL config
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'shared_auth_db',  # Same database as accounts_master
#         'USER': 'paulblack',
#         'PASSWORD': '',  # Blank since using trust auth
#         # 'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }



# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2', # env('POP_UP_SHARED_DB_ENGINE'),
#         'NAME': 'pop_up_shop_dev_db',  # env('POP_UP_SHARED_DEFAULT_DEV_DB_NAME'),
#         'USER': "paulblack",
#         'PASSWORD': "",
#         'HOST': "localhost",
#         'PORT': 5432, #  env('POP_UP_SHARED_DEV_DB_PORT')
#     },
#     'shared_auth': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2', # env('POP_UP_SHARED_DB_ENGINE'),
#         'NAME': 'shared_auth_db_dev', # env('POP_UP_SHARED_DEV_DB_NAME'),
#         'USER': "paulblack",
#         'PASSWORD': "",
#         'HOST': "localhost",
#         'PORT': 5432 #  env('POP_UP_SHARED_DEV_DB_PORT'),

#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # env('POP_UP_SHARED_DB_ENGINE'),
        'NAME': 'pop_up_shop_dev_db',  # env('POP_UP_SHARED_DEFAULT_DEV_DB_NAME'),
        'USER': env('POP_UP_SHARED_DEV_DB_USER'),
        'PASSWORD': env('POP_UP_SHARED_DEV_DB_PASSWORD'),
        'HOST': env('POP_UP_SHARED_DEV_DB_HOST'),
        'PORT': '25060', #  env('POP_UP_SHARED_DEV_DB_PORT')
    },
    'shared_auth': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # env('POP_UP_SHARED_DB_ENGINE'),
        'NAME': 'shared_auth_db_dev', # env('POP_UP_SHARED_DEV_DB_NAME'),
        'USER': env('POP_UP_SHARED_DEV_DB_USER'),
        'PASSWORD': env('POP_UP_SHARED_DEV_DB_PASSWORD'),
        'HOST': env('POP_UP_SHARED_DEV_DB_HOST'),
        'PORT': '25060' #  env('POP_UP_SHARED_DEV_DB_PORT'),

    }
}

# print('Databases Config', DATABASES)
