import logging
import sys
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone
from pytz import timezone as pytz_timezone

from stock_logic.utils import update_stock_prices, is_nyse_closing_time

logger = logging.getLogger(__name__)

def update_stock_prices_job():
    """Job to update stock prices"""
    try:
        # Check if it's the right time (around NYSE closing)
        if is_nyse_closing_time():
            logger.info(f"Running scheduled stock price update at {timezone.now()}")
            updated_count = update_stock_prices()
            logger.info(f"Updated prices for {updated_count} stocks")
        else:
            logger.info("Skipping scheduled update - not within NYSE closing window")
    except Exception as e:
        logger.error(f"Error in scheduled stock price update: {e}")


def delete_old_job_executions(max_age=604_800):  # 7 days in seconds
    """Delete job execution entries older than `max_age`."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start():
    """Start the APScheduler."""
    # Don't start the scheduler when running management commands (except runserver)
    if len(sys.argv) > 1 and sys.argv[1] != 'runserver' and 'test' not in sys.argv[1:]:
        return

    # Don't start if settings say not to
    if not getattr(settings, 'SCHEDULER_AUTOSTART', True):
        return

    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Add scheduled job for stock price updates - default to NYSE closing time (4:10 PM ET)
    scheduler.add_job(
        update_stock_prices_job,
        trigger=CronTrigger(hour=16, minute=10, timezone=pytz_timezone('US/Eastern')),
        id="update_stock_prices",
        name="Update stock prices after market close",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added job: 'update_stock_prices'")

    # Add a job to delete old job executions weekly
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="mon", hour=0, minute=0),
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Added weekly job: 'delete_old_job_executions'")

    try:
        logger.info("Starting scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully!")
