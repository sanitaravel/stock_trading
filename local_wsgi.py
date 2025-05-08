import os
import sys

# Use local paths
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Set environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_portfolio.local_prod_settings')

# Import the application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == '__main__':
    # Run with Waitress (a production WSGI server)
    from waitress import serve
    print("Starting server on http://localhost:8000")
    serve(application, host='localhost', port=8000)
