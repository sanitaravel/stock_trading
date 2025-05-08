from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate


class StockLogicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_logic'

    def ready(self):
        from django.core.management import call_command
        post_migrate.connect(self._load_initial_data, sender=self)

    def _load_initial_data(self, **kwargs):
        # Only load data if no sectors exist already
        from .models import Sector, Portfolio
        if Sector.objects.count() == 0:
            call_command('loaddata', 'initial_sector_industry_data.json')