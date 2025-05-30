import os
import dj_database_url
from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Allow all Heroku app domains
ALLOWED_HOSTS = ['.herokuapp.com']

# Allow your custom domain if you have one
custom_domain = os.environ.get('CUSTOM_DOMAIN')
if custom_domain:
    ALLOWED_HOSTS.append(custom_domain)

# Add localhost for local testing with heroku_settings
ALLOWED_HOSTS += ['localhost', '127.0.0.1']

# IMPORTANT: This completely replaces the DATABASES setting from settings.py
# Parse database configuration from $DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # Fallback for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Print the actual database configuration for debugging (this will show in Heroku logs)
print(f"Database config: ENGINE={DATABASES['default']['ENGINE']}")

# Static files configuration
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Enable WhiteNoise for serving static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add whitenoise
] + MIDDLEWARE[1:]  # Keep the rest of middleware

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Alpha Vantage API Key from environment variable
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')

# Configure HTTPS settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Set CSRF trusted origins for your Heroku domain
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS if host not in ['localhost', '127.0.0.1']]

# Session timeout settings - 1 day
SESSION_COOKIE_AGE = 86400  # 1 day in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
