from django.urls import path
from . import views

app_name = 'stock_visualization'

urlpatterns = [
    path('', views.index, name='index'),
    path('portfolio/<int:portfolio_id>/', views.portfolio_detail, name='portfolio_detail'),
    path('api/portfolio/<int:portfolio_id>/history/', views.portfolio_history_data, name='portfolio_history_data'),
    path('api/portfolios/history/', views.all_portfolios_history_data, name='all_portfolios_history_data'),
    path('stock/<int:stock_id>/', views.stock_detail, name='stock_detail'),
]
