from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import pytz

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def current_value(self):
        """Calculate the current value of the portfolio."""
        total = 0
        for position in self.positions.all():
            latest_price = position.stock.get_latest_close_price() if position.stock else 0
            quantity = position.quantity or 0
            total += latest_price * quantity
        return round(total, 2)
    
    def initial_value(self):
        """Calculate the initial value of the portfolio."""
        total = 0
        for position in self.positions.all():
            initial_price = position.initial_price or 0
            quantity = position.quantity or 0
            total += initial_price * quantity
        return round(total, 2)
    
    def performance(self):
        """Calculate the performance of the portfolio."""
        initial = self.initial_value()
        if initial == 0:
            return 0
        return round((self.current_value() - initial) / initial * 100, 2)

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True)
    
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
            self.quantity = self.total_investment / self.initial_price
    
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
