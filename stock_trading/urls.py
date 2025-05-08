from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stock-logic/', include('stock_logic.urls')),
    path('stock-visualization/', include('stock_visualization.urls')),
]
