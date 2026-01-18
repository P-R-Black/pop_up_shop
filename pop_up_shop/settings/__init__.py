"""
Automatically load the correct settings based on DJANGO_ENVIRONMENT variable.
"""
import os
from pathlib import Path
import environ

# ✅ Load .env file FIRST before checking environment
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# Get environment from environment variable
environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')

print(f"Loading settings for: {environment}")

if environment == 'production':
    from .production import *
elif environment == 'ci':
    from .ci import *
# elif environment == 'test':
#     from .test import *
else:
    from .development import *

print(f"Settings loaded successfully for {environment}")