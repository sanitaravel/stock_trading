"""
WSGI config for stock_portfolio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Change to heroku_settings for Heroku deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_portfolio.heroku_settings')

application = get_wsgi_application()