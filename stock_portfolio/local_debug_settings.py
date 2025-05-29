# Local settings for debugging with PostgreSQL database
import os
import environ
from .settings import *

# Initialize environment variables
env = environ.Env()

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Override database configuration to use local PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='stock_trading_backup'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Debug settings
DEBUG = env.bool('DEBUG_LOCAL', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS_LOCAL', default=['localhost', '127.0.0.1'])

# Print database info for debugging
print(f"Using local PostgreSQL database: {DATABASES['default']['NAME']}")
print(f"Database engine: {DATABASES['default']['ENGINE']}")
