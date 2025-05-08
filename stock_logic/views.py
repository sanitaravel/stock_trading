from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Stock

# Create your views here.

@staff_member_required
def get_current_stock_price(request):
    """API endpoint to get the current price of a stock by ID"""
    stock_id = request.GET.get('stock_id')
    if not stock_id:
        return JsonResponse({'error': 'No stock ID provided'}, status=400)
    
    try:
        stock = Stock.objects.get(id=stock_id)
        price = stock.get_latest_close_price()
        return JsonResponse({
            'price': price,
            'formatted_price': '{:.2f}'.format(price),
            'stock_name': stock.company_name,
            'stock_symbol': stock.symbol
        })
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Stock not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
