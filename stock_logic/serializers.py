from rest_framework import serializers
from .models import Portfolio, Stock, PortfolioPosition, StockPrice, Sector, Industry
from django.db.models import Sum
from decimal import Decimal

class StockPriceSerializer(serializers.ModelSerializer):
    """
    Serializer for stock price data, including open, close, high, and low prices.
    """
    class Meta:
        model = StockPrice
        fields = ['id', 'date', 'price_timestamp', 'open_price', 'close_price', 
                 'high_price', 'low_price', 'volume', 'last_updated']

class SectorSerializer(serializers.ModelSerializer):
    """
    Serializer for sector data.
    """
    industries_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sector
        fields = ['id', 'name', 'description', 'industries_count']
    
    def get_industries_count(self, obj):
        return obj.industries.count()

class IndustrySerializer(serializers.ModelSerializer):
    """
    Serializer for industry data, including sector information.
    """
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    
    class Meta:
        model = Industry
        fields = ['id', 'name', 'description', 'sector', 'sector_name']

class StockSerializer(serializers.ModelSerializer):
    """
    Serializer for stock data, including the latest price and price change.
    """
    latest_price = serializers.SerializerMethodField()
    price_change = serializers.SerializerMethodField()
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'company_name', 'description', 'sector', 'sector_name', 
                  'industry', 'industry_name', 'latest_price', 'price_change']
    
    def get_latest_price(self, obj):
        price = obj.get_latest_close_price()
        return float(price) if price else None
    
    def get_price_change(self, obj):
        open_price = obj.get_latest_open_price()
        close_price = obj.get_latest_close_price()
        if open_price and close_price:
            change = float(close_price) - float(open_price)
            percent = (change / float(open_price)) * 100 if float(open_price) > 0 else 0
            return {
                'change': round(change, 2),
                'percent': round(percent, 2)
            }
        return None

class PortfolioPositionSerializer(serializers.ModelSerializer):
    """
    Serializer for portfolio positions, including stock symbol, name, current value, and performance.
    """
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.company_name', read_only=True)
    current_value = serializers.SerializerMethodField()
    performance = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioPosition
        fields = ['id', 'portfolio', 'stock', 'stock_symbol', 'stock_name', 'quantity', 
                 'initial_price', 'total_investment', 'purchase_date', 'current_value', 'performance']
    
    def get_current_value(self, obj):
        return float(obj.current_value())
    
    def get_performance(self, obj):
        return float(obj.performance())
    
    def validate(self, data):
        """
        Validate the portfolio position data, ensuring either quantity or total investment is provided.
        """
        # Check if both quantity and total_investment are provided
        if data.get('quantity') is not None and data.get('total_investment') is not None:
            # If both are provided, prioritize quantity and remove total_investment
            data.pop('total_investment')
        
        # Check if neither is provided
        if data.get('quantity') is None and data.get('total_investment') is None:
            raise serializers.ValidationError(
                "Either quantity or total investment amount must be provided.")
        
        # Calculate quantity from total_investment if needed
        if data.get('total_investment') is not None and data.get('initial_price'):
            if data['initial_price'] <= 0:
                raise serializers.ValidationError("Initial price must be greater than zero.")
            data['quantity'] = data['total_investment'] / data['initial_price']
        
        return data

class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for portfolio data, including positions, current value, initial value, performance, and positions count.
    """
    positions = PortfolioPositionSerializer(many=True, read_only=True)
    current_value = serializers.SerializerMethodField()
    initial_value = serializers.SerializerMethodField()
    performance = serializers.SerializerMethodField()
    positions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'description', 'created_at', 'last_updated', 
                 'positions', 'positions_count', 'current_value', 'initial_value', 'performance']
    
    def get_current_value(self, obj):
        return float(obj.current_value())
    
    def get_initial_value(self, obj):
        return float(obj.initial_value())
    
    def get_performance(self, obj):
        return float(obj.performance())
    
    def get_positions_count(self, obj):
        return obj.positions.count()
