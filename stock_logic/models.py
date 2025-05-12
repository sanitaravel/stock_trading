from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import pytz

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=25, blank=True, null=True, help_text="A shorter name for display in charts and legends")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    initial_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, 
                                       help_text="Initial portfolio value when created")
    current_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                       help_text="Current portfolio value")
    stored_initial_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                             help_text="Initial value calculated once and stored")
    
    def __str__(self):
        return self.name
    
    def update_prices(self):
        """Update the initial_price and current_price fields"""
        # Calculate and store initial value if not already set
        if self.stored_initial_value is None:
            self.stored_initial_value = self._calculate_initial_value()
        
        self.initial_price = self.initial_value()
        self.current_price = self._calculate_current_value()  # Use internal calculation method
        self.save(update_fields=['stored_initial_value', 'initial_price', 'current_price', 'last_updated'])
    
    def current_value(self):
        """Calculate the current value of the portfolio."""
        # If current_price is set, return it
        if self.current_price is not None:
            return self.current_price
            
        # Otherwise calculate from positions
        return self._calculate_current_value()
    
    def _calculate_current_value(self):
        """Internal method to calculate current value from positions."""
        total = 0
        for position in self.positions.all():
            latest_price = position.stock.get_latest_close_price() if position.stock else 0
            quantity = position.quantity or 0
            total += latest_price * quantity
        return round(total, 2)
    
    def _calculate_initial_value(self):
        """Calculate the initial value of the portfolio from positions."""
        total = 0
        for position in self.positions.all():
            initial_price = position.initial_price or 0
            quantity = position.quantity or 0
            total += initial_price * quantity
        return round(total, 2)
    
    def initial_value(self):
        """Return the stored initial value or calculate it once if not set."""
        # If stored_initial_value is set, return it
        if self.stored_initial_value is not None:
            return self.stored_initial_value
            
        # If initial_price is set, return it
        if self.initial_price is not None:
            return self.initial_price
            
        # Otherwise calculate and store the initial value
        calculated_value = self._calculate_initial_value()
        self.stored_initial_value = calculated_value
        self.save(update_fields=['stored_initial_value', 'last_updated'])
        
        return calculated_value
    
    def gain(self):
        """Calculate the absolute gain/loss of the portfolio in dollars."""
        return round(self.current_value() - self.initial_value(), 2)
    
    def performance(self):
        """Calculate the performance of the portfolio."""
        initial = self.initial_value()
        if initial == 0:
            return 0
        return round((self.current_value() - initial) / initial * 100, 2)

class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='industries')
    
    def __str__(self):
        return f"{self.name} ({self.sector.name})"
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Industries"

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Company description and additional information")
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name='stocks')
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True, related_name='stocks')
    
    def __str__(self):
        return f"{self.symbol} - {self.company_name}"
    
    def get_latest_close_price(self):
        """Get the latest closing price for this stock."""
        latest_price = self.prices.order_by('-date').first()
        if latest_price:
            return latest_price.close_price
        return 0
        
    def get_latest_open_price(self):
        """Get the latest opening price for this stock."""
        latest_price = self.prices.order_by('-date').first()
        if latest_price:
            return latest_price.open_price
        return 0

class PortfolioPosition(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField(default=timezone.now)
    total_investment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                         help_text="Total amount invested (alternative to specifying quantity)")
    
    class Meta:
        unique_together = ('portfolio', 'stock')
    
    def __str__(self):
        return f"{self.portfolio.name} - {self.stock.symbol} ({self.quantity or 'Investment: $' + str(self.total_investment)})"
    
    def clean(self):
        # First check if both fields are empty
        if self.quantity is None and self.total_investment is None:
            raise ValidationError("Either quantity or total investment amount must be provided.")
        
        # If both fields have values, prioritize quantity and clear total_investment
        if self.quantity is not None and self.total_investment is not None:
            self.total_investment = None
        
        # Calculate quantity from total_investment if needed
        if self.total_investment is not None and self.initial_price:
            if self.initial_price <= 0:
                raise ValidationError("Initial price must be greater than zero.")
            
            # Only calculate quantity for new entries or when total_investment has changed
            # Check if this is a new record (no primary key) or if the total investment has changed
            # AND if the existing quantity is None or zero
            if (not self.pk or self._check_if_field_changed('total_investment')) and \
               (self.quantity is None or self.quantity == 0):
                self.quantity = self.total_investment / self.initial_price
    
    def _check_if_field_changed(self, field_name):
        """Check if a field value has changed from the database value"""
        if not self.pk:  # New instance, field is considered changed
            return True
        
        # Get the current value in the database
        old_value = PortfolioPosition.objects.filter(pk=self.pk).values_list(field_name, flat=True).first()
        current_value = getattr(self, field_name)
        
        return old_value != current_value
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def current_value(self):
        """Calculate the current value of this position."""
        if not self.stock or not self.quantity:
            return 0
        return round(self.stock.get_latest_close_price() * self.quantity, 2)
    
    def performance(self):
        """Calculate the performance of this position."""
        if not self.initial_price or not self.quantity:
            return 0
        initial = self.initial_price * self.quantity
        if initial == 0:
            return 0
        current = self.current_value()
        return round((current - initial) / initial * 100, 2)

class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField()
    price_timestamp = models.DateTimeField(auto_now_add=True, help_text="When this price data was recorded")
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Remove unique_together constraint to allow multiple entries per day
        indexes = [
            models.Index(fields=['-date']),  # For efficient date-based lookups
            models.Index(fields=['-price_timestamp']),  # For efficient timestamp-based lookups
        ]
    
    def __str__(self):
        return f"{self.stock.symbol} on {self.date} ({self.price_timestamp.strftime('%H:%M:%S')}): Open ${self.open_price}, Close ${self.close_price}"
