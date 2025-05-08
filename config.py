import os
import dj_database_url

# Database configuration
if os.environ.get('DATABASE_URL'):
    # Use Heroku's DATABASE_URL
    DATABASE_CONFIG = dj_database_url.config(conn_max_age=600)
else:
    # Local SQLite database
    DATABASE_CONFIG = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'your_database_name.db',
    }
