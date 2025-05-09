from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
import time

from scheduler.scheduler import update_stock_prices_job

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the scheduled stock price update job immediately'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run in a continuous loop (for Heroku worker)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,
            help='Interval between checks in seconds when using --loop (default: 1 hour)',
        )

    def handle(self, *args, **options):
        if options['loop']:
            self.stdout.write(self.style.SUCCESS('Starting scheduler loop...'))
            interval = options['interval']

            try:
                while True:
                    self.stdout.write(f"Running scheduled jobs at {timezone.now()}")
                    update_stock_prices_job()
                    self.stdout.write(f"Sleeping for {interval} seconds...")
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nStopping scheduler loop...'))
        else:
            self.stdout.write(self.style.SUCCESS('Running stock price update job...'))
            update_stock_prices_job()
            self.stdout.write(self.style.SUCCESS('Job completed!'))
