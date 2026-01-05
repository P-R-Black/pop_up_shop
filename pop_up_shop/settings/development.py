from pathlib import Path
from .base import *
import os
# from dotenv import load_dotenv

env = environ.Env()
environ.Env.read_env()

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
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }