web: gunicorn stock_portfolio.wsgi --log-file -
worker: python manage.py run_scheduler --loop
release: python manage.py migrate
