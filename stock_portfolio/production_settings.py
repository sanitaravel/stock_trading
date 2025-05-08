from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secure-secret-key'  # Change this!

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['sanitaravel.pythonanywhere.com']  # Replace with your actual domain

# Database
# You can continue using SQLite or configure MySQL (available on PythonAnywhere)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_ROOT = BASE_DIR / 'static'

# Add whitenoise for static files serving
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this line
    # ...existing middleware...
]

# Configure CSRF for your domain
CSRF_TRUSTED_ORIGINS = ['https://sanitaravel.pythonanywhere.com']  # Replace with your domain
