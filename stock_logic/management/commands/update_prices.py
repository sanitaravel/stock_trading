from django.core.management.base import BaseCommand
from stock_logic.utils import update_stock_prices, is_nyse_closing_time
from stock_logic.models import Portfolio
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update stock prices, runs between 4:00 PM ET and 5:00 PM ET (after NYSE closes)'

    def handle(self, *args, **options):
        # Check if it's the right time to update prices
        should_update = is_nyse_closing_time()
        
        # Allow forcing update with --force
        force_update = options.get('force', False)
        
        if should_update or force_update:
            self.stdout.write(self.style.SUCCESS('Starting daily price update...'))
            
            # Count portfolios before update
            portfolio_count = Portfolio.objects.count()
            
            # Update stock prices (which now also updates portfolio prices)
            updated_count = update_stock_prices()
            
            # Count portfolios with current_price set   
            portfolios_updated = Portfolio.objects.exclude(current_price=None).count()
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully updated {updated_count} stock prices and {portfolios_updated}/{portfolio_count} portfolios'
            ))
            
            # Log the update
            logger.info(f"Daily stock price update completed at {timezone.now()}, "
                      f"updated {updated_count} stocks and {portfolios_updated} portfolios")
        else:
            self.stdout.write(self.style.WARNING('Not updating prices - not within the 10-minute window after NYSE closing'))
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update regardless of time',
        )
