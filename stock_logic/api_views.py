from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUserOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Portfolio, Stock, PortfolioPosition, StockPrice, Sector, Industry
from .serializers import (
    PortfolioSerializer, StockSerializer, 
    PortfolioPositionSerializer, StockPriceSerializer,
    SectorSerializer, IndustrySerializer
)
from .utils import update_stock_prices, fetch_stock_data
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SectorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for sector management.
    Only admin users can modify sectors.
    """
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    search_fields = ['name', 'description']
    
    @swagger_auto_schema(
        operation_description="Get industries for a specific sector",
        responses={200: IndustrySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def industries(self, request, pk=None):
        """Get all industries for a specific sector"""
        sector = self.get_object()
        industries = sector.industries.all()
        serializer = IndustrySerializer(industries, many=True)
        return Response(serializer.data)

class IndustryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for industry management.
    Only admin users can modify industries.
    """
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'sector__name']
    filterset_fields = ['sector']
    
    @swagger_auto_schema(
        operation_description="Get stocks for a specific industry",
        responses={200: StockSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def stocks(self, request, pk=None):
        """Get all stocks for a specific industry"""
        industry = self.get_object()
        stocks = industry.stocks.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

# Update StockViewSet to include sector/industry filtering
class StockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for stock management.
    Only admin users can modify stocks.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['symbol', 'company_name', 'description']
    ordering_fields = ['symbol', 'company_name']
    filterset_fields = ['sector', 'industry']
    
    @swagger_auto_schema(
        operation_description="Update prices for all stocks in the database",
        responses={200: openapi.Response("Success", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING),
                'updated_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ))}
    )
    @action(detail=False, methods=['post'])
    def update_prices(self, request):
        """Update prices for all stocks"""
        updated_count = update_stock_prices()
        return Response({
            'status': 'success',
            'updated_count': updated_count,
            'message': f'Updated prices for {updated_count} stocks'
        })
    
    @swagger_auto_schema(
        operation_description="Get historical price data for a specific stock",
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Filter by start date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="Filter by end date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        responses={200: StockPriceSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def price_history(self, request, pk=None):
        """Get price history for a specific stock with optional date filtering"""
        stock = self.get_object()
        
        # Get date parameters from request, or use defaults
        end_date_str = request.query_params.get('end_date')
        start_date_str = request.query_params.get('start_date')
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = datetime.now().date()
        else:
            end_date = datetime.now().date()
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date - timedelta(days=90)  # Default to 90 days
        else:
            start_date = end_date - timedelta(days=90)  # Default to 90 days
        
        # Query price history with date filters
        queryset = StockPrice.objects.filter(
            stock=stock,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        serializer = StockPriceSerializer(queryset, many=True)
        return Response(serializer.data)

class PortfolioViewSet(viewsets.ModelViewSet):
    """
    API endpoint for portfolio management.
    Only admin users can modify portfolios.
    """
    serializer_class = PortfolioSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
    def get_queryset(self):
        """Return only portfolios owned by the current user"""
        return Portfolio.objects.all()
    
    @action(detail=True, methods=['post'])
    def update_prices(self, request, pk=None):
        """Update the initial_price and current_price fields for a portfolio"""
        portfolio = self.get_object()
        portfolio.update_prices()
        serializer = self.get_serializer(portfolio)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_all_prices(self, request):
        """Update the initial_price and current_price fields for all portfolios"""
        portfolios = self.get_queryset()
        updated_count = 0
        
        for portfolio in portfolios:
            portfolio.update_prices()
            updated_count += 1
            
        return Response({
            'status': 'success',
            'updated_count': updated_count,
            'message': f'Updated prices for {updated_count} portfolios'
        })
    
    @swagger_auto_schema(
        operation_description="Get all positions for a specific portfolio",
        responses={200: PortfolioPositionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def positions(self, request, pk=None):
        """Get all positions for a specific portfolio"""
        portfolio = self.get_object()
        positions = portfolio.positions.all()
        serializer = PortfolioPositionSerializer(positions, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Add a new position to the portfolio",
        request_body=PortfolioPositionSerializer,
        responses={201: PortfolioPositionSerializer, 400: "Bad Request"}
    )
    @action(detail=True, methods=['post'])
    def add_position(self, request, pk=None):
        """Add a new position to the portfolio"""
        portfolio = self.get_object()
        
        # Include the portfolio in the data
        data = request.data.copy()
        data['portfolio'] = portfolio.id
        
        serializer = PortfolioPositionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Get historical value data for a specific portfolio",
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Filter by start date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="Filter by end date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        responses={200: openapi.Response("Success", schema=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                    'value': openapi.Schema(type=openapi.TYPE_NUMBER),
                }
            )
        ))}
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get historical value data for a specific portfolio with optional date filtering"""
        portfolio = self.get_object()
        
        # Get date parameters from request, or use defaults
        end_date_str = request.query_params.get('end_date')
        start_date_str = request.query_params.get('start_date')
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = datetime.now().date()
        else:
            end_date = datetime.now().date()
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date - timedelta(days=90)  # Default to 90 days
        else:
            start_date = end_date - timedelta(days=90)  # Default to 90 days
        
        # Get all positions in the portfolio
        positions = portfolio.positions.all()
        
        # Initialize result list to store historical values
        historical_values = []
        
        # Get all dates between start_date and end_date
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        for date in date_range:
            daily_value = 0
            
            # Calculate the portfolio value for each date
            for position in positions:
                # Check if the position was purchased before or on the current date
                if position.purchase_date <= date:
                    # Get the stock price for this date (or closest previous date)
                    price = StockPrice.objects.filter(
                        stock=position.stock,
                        date__lte=date
                    ).order_by('-date').first()
                    
                    if price:
                        # Add the position value to the daily total
                        daily_value += position.quantity * price.close_price
            
            # Add the date and value to the results
            historical_values.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(daily_value, 2)
            })
        
        return Response(historical_values)

class PortfolioPositionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for portfolio position management.
    Only admin users can modify positions.
    """
    queryset = PortfolioPosition.objects.all()
    serializer_class = PortfolioPositionSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['purchase_date', 'stock__symbol']
    
    def get_queryset(self):
        """Optionally filter by portfolio"""
        queryset = PortfolioPosition.objects.all()
        portfolio_id = self.request.query_params.get('portfolio_id')
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        return queryset

class StockPriceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for stock price management.
    Only admin users can modify stock prices.
    """
    queryset = StockPrice.objects.all()
    serializer_class = StockPriceSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'price_timestamp']
    
    def get_queryset(self):
        """Optionally filter by stock"""
        queryset = StockPrice.objects.all()
        stock_id = self.request.query_params.get('stock_id')
        if stock_id:
            queryset = queryset.filter(stock_id=stock_id)
        return queryset
    
    @swagger_auto_schema(
        operation_description="Fetch the latest price for a specific stock symbol",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'symbol': openapi.Schema(type=openapi.TYPE_STRING, description="Stock symbol")
            }
        ),
        responses={200: StockPriceSerializer, 400: "Bad Request", 404: "Not Found"}
    )
    @action(detail=False, methods=['post'])
    def fetch_latest(self, request):
        """Fetch latest price for a specific stock symbol"""
        symbol = request.data.get('symbol')
        if not symbol:
            return Response({'error': 'Symbol is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # First try to find the stock in the database
            stock = get_object_or_404(Stock, symbol=symbol)
            
            # Fetch the latest data
            data = fetch_stock_data(symbol)
            if not data:
                return Response({'error': 'Could not fetch data for this symbol'}, 
                                status=status.HTTP_404_NOT_FOUND)
            
            # Create or update price record
            price, created = StockPrice.objects.update_or_create(
                stock=stock,
                date=data['date'],
                defaults={
                    'open_price': data['open_price'],
                    'close_price': data['close_price'],
                    'high_price': data['high_price'],
                    'low_price': data['low_price'],
                    'volume': data['volume'],
                }
            )
            
            serializer = StockPriceSerializer(price)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
