from .base import *
import os
import environ

env = environ.Env()
# environ.Env.read_env()

DEBUG = False

ALLOWED_HOSTS = [
    'popupshop.paulrblack.com', 
    'www.popupshop.paulrblack.com'
    ]


# Prod Database
DATABASES = {
    'default': {
        'ENGINE': env('POP_UP_SHARED_PROD_DB_ENGINE'), # 'django.db.backends.postgresql_psycopg2',
        'NAME': env('POP_UP_SHARED_DEFAULT_PROD_DB_NAME'), # 'pop_up_shop_prod_db',
        'USER': env('POP_UP_SHARED_PROD_DB_USER'), # doadmin
        'PASSWORD': env('POP_UP_SHARED_PROD_DB_PASSWORD'),
        'HOST': env('POP_UP_SHARED_PROD_DB_HOST'),
        'PORT': env('POP_UP_SHARED_PROD_DB_PORT'),
    },
    'shared_auth': {
        'ENGINE': env('POP_UP_SHARED_PROD_DB_ENGINE'),
        'NAME': env('POP_UP_SHARED_PROD_DB_NAME'), # 'shared_auth_db',
        'USER': env('POP_UP_SHARED_PROD_DB_USER'),
        'PASSWORD': env('POP_UP_SHARED_PROD_DB_PASSWORD'),
        'HOST': env('POP_UP_SHARED_PROD_DB_HOST'),
        'PORT': env('POP_UP_SHARED_PROD_DB_PORT'),
    }
}



# Once domain name secured, uncomment
# Production security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# AWS_S3_OBJECT_PARAMETERS = {
# 'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
# 'CacheControl': 'max-age=94608000',
# }

# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = 'us-east-1'
# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')


# AWS_S3_CUSTOM_DOMAIN =  f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# STATICFILES_STORAGE = 'custom_storage.StaticStorage'
# STATICFILES_LOCATION = 'static'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/'

# DEFAULT_FILE_STORAGE = 'custom_storage.MediaStorage'
# MEDIAFILES_LOCATION = 'media'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'

# AWS_DEFAULT_ACL = 'public-read'

# AWS_S3_FILE_OVERWRITE = False
# AWS_QUERYSTRING_AUTH = False
# AWS_S3_SIGNATURE_VERSION = "s3v4"


# # Stripe Configuration
# STRIPE_PUBLIC_KEY = env('STRIPE_PUBLIC_KEY')
# STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
# STRIPE_WEBHOOK_SECRET = ""
# STRIPE_ENDPOINT_SECRET = env('STRIPE_ENDPOINT_SECRET')


# #SMTP Configuratoin
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# EMAIL_PORT = env('EMAIL_PORT')
# EMAIL_USE_TLS = True

print("Loaded PRODUCTION settings")