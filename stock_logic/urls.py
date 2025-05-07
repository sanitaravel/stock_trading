from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    StockViewSet, PortfolioViewSet, 
    PortfolioPositionViewSet, StockPriceViewSet
)
from .views import get_current_stock_price

# Initialize the router
router = DefaultRouter()

# Stock resources
router.register('stocks', StockViewSet, basename='stock')
router.register('stock-prices', StockPriceViewSet, basename='stock-price')

# Portfolio resources
router.register('portfolios', PortfolioViewSet, basename='portfolio')
router.register('positions', PortfolioPositionViewSet, basename='position')

# URL patterns
urlpatterns = [
    # Router generated URLs
    path('', include(router.urls)),
    
    # Custom action URLs
    path('stocks/update-all/', StockViewSet.as_view({'post': 'update_prices'}), name='update-all-stocks'),
    path('stocks/<int:pk>/history/', StockViewSet.as_view({'get': 'price_history'}), name='stock-price-history'),
    path('portfolios/<int:pk>/positions/', PortfolioViewSet.as_view({'get': 'positions', 'post': 'add_position'}), name='portfolio-positions'),
    path('stock-prices/fetch-latest/', StockPriceViewSet.as_view({'post': 'fetch_latest'}), name='fetch-latest-price'),
    
    # Legacy admin view
    path('admin/get-stock-price/', get_current_stock_price, name='admin-get-stock-price'),
]
