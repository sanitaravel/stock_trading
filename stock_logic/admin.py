from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import TruncDay
from .models import Portfolio, Stock, PortfolioPosition, StockPrice, Sector, Industry
from .utils import update_stock_prices, ensure_sector_and_industry

class PortfolioPositionInline(admin.TabularInline):
    model = PortfolioPosition
    extra = 1
    fields = ('stock', 'quantity', 'total_investment', 'initial_price', 'purchase_date', 'current_value', 'performance')
    readonly_fields = ('current_value', 'performance')
    autocomplete_fields = ['stock']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        form.base_fields['quantity'].help_text = "Leave blank if using total investment"
        form.base_fields['total_investment'].help_text = "Leave blank if using quantity"
        return formset

class StockPriceInline(admin.TabularInline):
    model = StockPrice
    extra = 0
    fields = ('date', 'open_price', 'close_price', 'high_price', 'low_price', 'volume')
    readonly_fields = ('date', 'open_price', 'close_price', 'high_price', 'low_price', 'volume')
    max_num = 30  # Show more historical prices
    ordering = ('-date', '-price_timestamp')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'formatted_current_value', 'formatted_initial_value', 
                    'formatted_gain', 'formatted_performance', 'positions_count', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    inlines = [PortfolioPositionInline]
    readonly_fields = ('created_at', 'last_updated', 'current_value', 'initial_value', 
                       'gain', 'performance')
    fieldsets = (
        ('Portfolio Information', {
            'fields': ('name', 'description', 'created_at', 'last_updated')
        }),
        ('Performance Metrics', {
            'fields': ('current_value', 'initial_value', 'gain', 'performance'),
            'classes': ('wide',)
        }),
    )
    
    def positions_count(self, obj):
        return obj.positions.count()
    positions_count.short_description = 'Stock Positions'
    
    def formatted_performance(self, obj):
        perf = obj.performance()
        color = 'green' if perf > 0 else 'red' if perf < 0 else 'gray'
        return format_html('<span style="color: {};">{}%</span>', color, perf)
    formatted_performance.short_description = 'Performance'
    
    def formatted_current_value(self, obj):
        value = obj.current_value()
        formatted_value = '{:,.2f}'.format(value)
        return format_html('${}', formatted_value)
    formatted_current_value.short_description = 'Current Value'
    
    def formatted_initial_value(self, obj):
        value = obj.initial_value()
        formatted_value = '{:,.2f}'.format(value)
        return format_html('${}', formatted_value)
    formatted_initial_value.short_description = 'Initial Value'
    
    def formatted_gain(self, obj):
        gain = obj.gain()
        color = 'green' if gain > 0 else 'red' if gain < 0 else 'gray'
        prefix = '+' if gain > 0 else ''
        formatted_value = '{:,.2f}'.format(gain)
        return format_html('<span style="color: {};">${}{}</span>', color, prefix, formatted_value)
    formatted_gain.short_description = 'Total Gain/Loss'

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'industries_count', 'stocks_count')
    search_fields = ('name', 'description')
    
    def industries_count(self, obj):
        return obj.industries.count()
    industries_count.short_description = 'Industries'
    
    def stocks_count(self, obj):
        return obj.stocks.count()
    stocks_count.short_description = 'Stocks'

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'description', 'stocks_count')
    list_filter = ('sector',)
    search_fields = ('name', 'description', 'sector__name')
    autocomplete_fields = ['sector']
    
    def stocks_count(self, obj):
        return obj.stocks.count()
    stocks_count.short_description = 'Stocks'

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'company_name', 'sector_display', 'industry_display', 'formatted_latest_open', 'formatted_latest_close', 'daily_change', 'has_price_data')
    search_fields = ('symbol', 'company_name', 'description')
    list_filter = ('sector', 'industry')
    readonly_fields = ('get_latest_open_price', 'get_latest_close_price', 'price_change', 'sector')
    autocomplete_fields = ['industry']
    inlines = [StockPriceInline]
    fieldsets = (
        ('Stock Information', {
            'fields': ('symbol', 'company_name', 'description', 'industry')
        }),
        ('Latest Pricing Data', {
            'fields': ('get_latest_open_price', 'get_latest_close_price', 'price_change'),
            'classes': ('wide',)
        }),
    )
    
    def sector_display(self, obj):
        if obj.sector:
            return obj.sector.name
        return '-'
    sector_display.short_description = 'Sector'
    
    def industry_display(self, obj):
        if obj.industry:
            return obj.industry.name
        return '-'
    industry_display.short_description = 'Industry'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update_prices/', self.admin_site.admin_view(self.update_prices_view), name='update-stock-prices'),
        ]
        return custom_urls + urls
    
    def update_prices_view(self, request):
        updated_count = update_stock_prices()
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Stock Price Update Results',
            'updated_count': updated_count,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, "admin/stock_logic/stock/price_update_results.html", context)
    
    def formatted_latest_open(self, obj):
        price = obj.get_latest_open_price()
        if price:
            formatted_price = '{:,.2f}'.format(price)
            return format_html('${}', formatted_price)
        return '-'
    formatted_latest_open.short_description = 'Latest Open'
    
    def get_latest_price(self, obj):
        """Return both the latest price and the one before that for comparison"""
        prices = obj.prices.order_by('-date', '-price_timestamp')[:2]
        if not prices:
            return None, None
        
        latest = prices[0]
        previous = prices[1] if len(prices) > 1 else None
        return latest, previous
    
    def formatted_latest_close(self, obj):
        latest, previous = self.get_latest_price(obj)
        if not latest:
            return '-'
            
        formatted_price = '{:,.2f}'.format(latest.close_price)
        
        # Add trend indicator if we have a previous price
        if previous:
            if latest.close_price > previous.close_price:
                trend = '<span style="color:green">↑</span>'
            elif latest.close_price < previous.close_price:
                trend = '<span style="color:red">↓</span>'
            else:
                trend = '<span style="color:gray">→</span>'
            
            return format_html('${} {}', formatted_price, trend)
        
        return format_html('${}', formatted_price)
    formatted_latest_close.short_description = 'Latest Close'
    
    def daily_change(self, obj):
        open_price = obj.get_latest_open_price()
        close_price = obj.get_latest_close_price()
        if open_price and close_price:
            change = (close_price - open_price) / open_price * 100
            color = 'green' if change > 0 else 'red' if change < 0 else 'gray'
            formatted_change = '{:.2f}'.format(round(change, 2))
            return format_html('<span style="color: {};">{}%</span>', color, formatted_change)
        return '-'
    daily_change.short_description = 'Daily Change'
    
    def has_price_data(self, obj):
        return obj.prices.exists()
    has_price_data.boolean = True
    has_price_data.short_description = 'Has Price Data'
    
    def price_change(self, obj):
        open_price = obj.get_latest_open_price()
        close_price = obj.get_latest_close_price()
        if open_price and close_price:
            change = close_price - open_price
            percent = (change / open_price) * 100 if open_price else 0
            color = 'green' if change > 0 else 'red' if change < 0 else 'gray'
            formatted_change = '{:,.2f}'.format(change)
            formatted_percent = '{:,.2f}'.format(percent)
            return format_html(
                '<span style="color: {};">${} ({}%)</span>', 
                color, formatted_change, formatted_percent
            )
        return '-'

    def save_model(self, request, obj, form, change):
        # Set sector automatically based on the selected industry
        if obj.industry and obj.industry.sector:
            obj.sector = obj.industry.sector
        
        super().save_model(request, obj, form, change)
        ensure_sector_and_industry(obj)

@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'stock', 'quantity', 'formatted_total_investment', 'formatted_initial_price', 'formatted_current_value', 'formatted_performance', 'purchase_date')
    list_filter = ('portfolio', 'purchase_date')
    search_fields = ('portfolio__name', 'stock__symbol', 'stock__company_name')
    readonly_fields = ('current_value', 'performance')
    autocomplete_fields = ['stock', 'portfolio']
    date_hierarchy = 'purchase_date'
    
    fieldsets = (
        ('Position Information', {
            'fields': ('portfolio', 'stock', 'initial_price', 'purchase_date')
        }),
        ('Investment Details', {
            'fields': ('quantity', 'total_investment'),
            'description': 'Enter either quantity OR total investment amount, not both.',
        }),
        ('Performance Metrics', {
            'fields': ('current_value', 'performance'),
            'classes': ('wide',)
        }),
    )
    
    def formatted_total_investment(self, obj):
        if not obj.total_investment:
            if obj.quantity and obj.initial_price:
                # Calculate what the investment would have been
                calculated = obj.quantity * obj.initial_price
                return format_html('${} (calculated)', '{:,.2f}'.format(calculated))
            return '-'
        formatted_value = '{:,.2f}'.format(obj.total_investment)
        return format_html('${}', formatted_value)
    formatted_total_investment.short_description = 'Total Investment'
    
    def formatted_initial_price(self, obj):
        formatted_price = '{:,.2f}'.format(obj.initial_price)
        return format_html('${}', formatted_price)
    formatted_initial_price.short_description = 'Initial Price'
    
    def formatted_current_value(self, obj):
        value = obj.current_value()
        formatted_value = '{:,.2f}'.format(value)
        return format_html('${}', formatted_value)
    formatted_current_value.short_description = 'Current Value'
    
    def formatted_performance(self, obj):
        perf = obj.performance()
        color = 'green' if perf > 0 else 'red' if perf < 0 else 'gray'
        return format_html('<span style="color: {};">{}%</span>', color, perf)
    formatted_performance.short_description = 'Performance'

@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'formatted_timestamp', 'formatted_open_price', 'formatted_close_price', 'daily_change', 'formatted_volume', 'last_updated')
    list_filter = ('stock', 'date', 'price_timestamp')
    search_fields = ('stock__symbol', 'stock__company_name')
    readonly_fields = ('price_timestamp', 'last_updated', 'daily_change_value')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Stock Information', {
            'fields': ('stock', 'date')
        }),
        ('Price Data', {
            'fields': ('open_price', 'close_price', 'high_price', 'low_price', 'daily_change_value', 'volume'),
            'classes': ('wide',)
        }),
    )
    
    def formatted_timestamp(self, obj):
        return obj.price_timestamp.strftime('%H:%M:%S') if obj.price_timestamp else '-'
    formatted_timestamp.short_description = 'Time'
    
    def formatted_open_price(self, obj):
        formatted_price = '{:,.2f}'.format(obj.open_price)
        return format_html('${}', formatted_price)
    formatted_open_price.short_description = 'Open Price'
    
    def formatted_close_price(self, obj):
        formatted_price = '{:,.2f}'.format(obj.close_price)
        return format_html('${}', formatted_price)
    formatted_close_price.short_description = 'Close Price'
    
    def daily_change(self, obj):
        if obj.open_price and obj.close_price:
            change = (obj.close_price - obj.open_price) / obj.open_price * 100
            color = 'green' if change > 0 else 'red' if change < 0 else 'gray'
            formatted_change = '{:.2f}'.format(round(change, 2))
            return format_html('<span style="color: {};">{}%</span>', color, formatted_change)
        return '-'
    daily_change.short_description = 'Daily Change'
    
    def daily_change_value(self, obj):
        if obj.open_price and obj.close_price:
            change = obj.close_price - obj.open_price
            percent = (change / obj.open_price) * 100
            color = 'green' if change > 0 else 'red' if change < 0 else 'gray'
            formatted_change = '{:.2f}'.format(change)
            formatted_percent = '{:.2f}'.format(percent)
            return format_html(
                '<span style="color: {};">${} ({}%)</span>', 
                color, formatted_change, formatted_percent
            )
        return '-'
    daily_change_value.short_description = "Price Change"
    
    def formatted_volume(self, obj):
        if obj.volume:
            formatted_vol = '{:,}'.format(obj.volume)
            return format_html('{}', formatted_vol)
        return '-'
    formatted_volume.short_description = 'Volume'
