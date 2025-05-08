from django.core.management.base import BaseCommand
from stock_logic.utils import update_stock_prices, is_nyse_closing_time
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update stock prices, runs at 4:10 PM ET (10 minutes after NYSE closes)'

    def handle(self, *args, **options):
        # Check if it's the right time to update prices
        should_update = is_nyse_closing_time()
        
        # Allow forcing update with --force
        force_update = options.get('force', False)
        
        if should_update or force_update:
            self.stdout.write(self.style.SUCCESS('Starting daily price update...'))
            updated_count = update_stock_prices()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} stock prices'))
            
            # Log the update
            logger.info(f"Daily stock price update completed at {timezone.now()}, updated {updated_count} stocks")
        else:
            self.stdout.write(self.style.WARNING('Not updating prices - not within the 10-minute window after NYSE closing'))
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update regardless of time',
        )
