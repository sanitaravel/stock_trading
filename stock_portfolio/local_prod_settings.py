from .settings import *

# Use similar settings as production but adapted for local testing
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Static files configuration
STATIC_ROOT = BASE_DIR / 'static_collected'

# Add whitenoise for static files serving
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line
] + MIDDLEWARE[1:]  # Add the rest of your middleware

# Secret key - in production you would use environment variables
SECRET_KEY = 'test-local-production-key-not-for-actual-deployment'
