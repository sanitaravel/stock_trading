"""
WSGI config for stock_portfolio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Add your project directory to the sys.path
path = '/home/sanitaravel/stock_trading'  # Replace with your username and path
if path not in sys.path:
    sys.path.append(path)

# Set environment variable for Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'stock_portfolio.production_settings'

# Serve with WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()