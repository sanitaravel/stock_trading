from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Portfolio, Stock, PortfolioPosition, StockPrice
from .serializers import (
    PortfolioSerializer, StockSerializer, 
    PortfolioPositionSerializer, StockPriceSerializer
)
from .utils import update_stock_prices, fetch_stock_data
import logging

logger = logging.getLogger(__name__)

class StockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for stock management.
    Provides CRUD operations for stocks and additional actions
    for price updates and history retrieval.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['symbol', 'company_name', 'sector']
    ordering_fields = ['symbol', 'company_name', 'sector']
    
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
        """Get price history for a specific stock"""
        stock = self.get_object()
        prices = stock.prices.order_by('-date')
        
        # Optional date range filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            prices = prices.filter(date__gte=start_date)
        if end_date:
            prices = prices.filter(date__lte=end_date)
            
        page = self.paginate_queryset(prices)
        if page is not None:
            serializer = StockPriceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = StockPriceSerializer(prices, many=True)
        return Response(serializer.data)

class PortfolioViewSet(viewsets.ModelViewSet):
    """
    API endpoint for portfolio management.
    Provides CRUD operations for portfolios and additional actions
    for managing positions within a portfolio.
    """
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only portfolios owned by the current user"""
        return Portfolio.objects.all()
    
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

class PortfolioPositionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for portfolio position management.
    Provides CRUD operations for portfolio positions.
    """
    queryset = PortfolioPosition.objects.all()
    serializer_class = PortfolioPositionSerializer
    permission_classes = [IsAuthenticated]
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
    Provides CRUD operations for stock prices and additional actions
    for fetching the latest price for a specific stock symbol.
    """
    queryset = StockPrice.objects.all()
    serializer_class = StockPriceSerializer
    permission_classes = [IsAuthenticated]
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
