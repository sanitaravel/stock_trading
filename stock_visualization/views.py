from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from stock_logic.models import Portfolio, PortfolioPosition, Stock, StockPrice, Sector, Industry
import json
from django.db.models import Max, Case, When
from datetime import datetime, timedelta

def index(request):
    """Home page with portfolio leaderboard and comparison charts"""
    portfolios = Portfolio.objects.all()
    
    # Get performance data for leaderboard
    portfolio_data = [{
        'id': p.id,
        'name': p.name,
        'current_value': float(p.current_value()),
        'initial_value': float(p.initial_value()),
        'performance': float(p.performance()),
        'gain': float(p.gain()),  # Add gain
    } for p in portfolios]
    
    # Sort portfolios by performance (descending)
    portfolio_data.sort(key=lambda x: x['performance'], reverse=True)
    
    # Create a sorted list of portfolio objects based on the sorted portfolio_data
    portfolio_ids = [item['id'] for item in portfolio_data]
    # Use the Case/When to preserve the sort order when querying
    preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(portfolio_ids)])
    sorted_portfolios = Portfolio.objects.filter(id__in=portfolio_ids).order_by(preserved_order)
    
    context = {
        'portfolios': sorted_portfolios,
        'portfolio_data_json': json.dumps(portfolio_data),
    }
    return render(request, 'stock_visualization/dashboard/index.html', context)

def portfolio_detail(request, portfolio_id):
    """Individual portfolio detail page"""
    portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
    
    # Get positions and sort them by performance (descending)
    positions = sorted(
        portfolio.positions.select_related('stock').all(),
        key=lambda pos: pos.performance(),
        reverse=True
    )
    
    # Get position data for charts with better number formatting
    position_data = [{
        'id': pos.id,
        'stock_symbol': pos.stock.symbol,
        'stock_name': pos.stock.company_name,
        'quantity': float(pos.quantity) if pos.quantity else 0,
        'initial_price': float(pos.initial_price),
        'current_value': float(pos.current_value()),
        'performance': float(pos.performance()),
        # Add formatted values for display
        'formatted_current_value': "${:,.2f}".format(pos.current_value()),
        'formatted_initial_price': "${:,.2f}".format(pos.initial_price),
    } for pos in positions]
    
    context = {
        'portfolio': portfolio,
        'positions': positions,
        'position_data_json': json.dumps(position_data),
        'portfolio_value': portfolio.current_value(),
        'portfolio_initial': portfolio.initial_value(),
        'portfolio_performance': portfolio.performance(),
        'portfolio_gain': portfolio.gain(),  # Add gain
        # Add formatted values for display
        'portfolio_value_formatted': "${:,.2f}".format(portfolio.current_value()),
        'portfolio_initial_formatted': "${:,.2f}".format(portfolio.initial_value()),
        'portfolio_gain_formatted': "${:,.2f}".format(portfolio.gain()),  # Format gain
    }
    return render(request, 'stock_visualization/portfolios/detail.html', context)

def portfolio_history_data(request, portfolio_id):
    """API endpoint to get portfolio history data for charts"""
    portfolio = get_object_or_404(Portfolio, pk=portfolio_id)
    positions = portfolio.positions.select_related('stock').all()
    
    # Get date parameters from request, or use defaults
    end_date_str = request.GET.get('end_date')
    start_date_str = request.GET.get('start_date')
    
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
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get all dates in the period where we have price data
    dates = StockPrice.objects.filter(
        stock__in=[pos.stock for pos in positions],
        date__gte=start_date, 
        date__lte=end_date
    ).values('date').distinct().order_by('date')
    
    history_data = {
        'labels': [],
        'values': [],
        'initial_value': float(portfolio.initial_value())  # This now uses the stored value
    }
    
    # For each date, calculate portfolio value based on positions and stock prices
    for date_obj in dates:
        date = date_obj['date']
        history_data['labels'].append(date.strftime('%Y-%m-%d'))
        
        total_value = 0
        for pos in positions:
            # Get the stock price on this date if available
            price = StockPrice.objects.filter(
                stock=pos.stock, 
                date__lte=date
            ).order_by('-date').first()
            
            if price and pos.quantity:
                total_value += float(price.close_price) * float(pos.quantity)
                
        history_data['values'].append(round(total_value, 2))
    
    # If we have no historical data, create some placeholder data
    if not history_data['labels']:
        days_range = min(30, (end_date - start_date).days)
        initial_value = float(portfolio.initial_value())
        current_value = float(portfolio.current_value())
        history_data = {
            'labels': [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days_range, 0, -1)],
            'values': [current_value for _ in range(days_range)],
            'initial_value': initial_value
        }
    
    return JsonResponse(history_data)

def all_portfolios_history_data(request):
    """API endpoint to get history data for all portfolios"""
    portfolios = Portfolio.objects.all()
    
    # Get date parameters from request, or use defaults
    end_date_str = request.GET.get('end_date')
    start_date_str = request.GET.get('start_date')
    
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
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get all dates in the period where we have price data
    dates = StockPrice.objects.filter(
        date__gte=start_date, 
        date__lte=end_date
    ).values('date').distinct().order_by('date')
    
    data = {
        'labels': [],
        'datasets': []
    }
    
    date_list = []
    for date_obj in dates:
        date = date_obj['date']
        date_list.append(date)
        data['labels'].append(date.strftime('%Y-%m-%d'))
    
    colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#6f42c1', '#5a5c69', '#858796', '#3498db', '#e67e22'
    ]
    
    # First, ensure all portfolios have updated prices
    for portfolio in portfolios:
        if portfolio.initial_price is None or portfolio.current_price is None:
            portfolio.update_prices()
    
    # For each portfolio, calculate values over time
    for i, portfolio in enumerate(portfolios):
        positions = portfolio.positions.select_related('stock').all()
        color_index = i % len(colors)
        
        values = []
        for date in date_list:
            total_value = 0
            for pos in positions:
                # Get the stock price on this date if available
                price = StockPrice.objects.filter(
                    stock=pos.stock, 
                    date__lte=date
                ).order_by('-date').first()
                
                if price and pos.quantity:
                    total_value += float(price.close_price) * float(pos.quantity)
            
            values.append(round(total_value, 2))
        
        # If we have no values (no historical data), use current value
        if not values and not date_list:
            # Create placeholder data
            days_range = min(30, (end_date - start_date).days)
            data['labels'] = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days_range, 0, -1)]
            values = [float(portfolio.current_price or portfolio.current_value()) for _ in range(days_range)]
        
        dataset = {
            'label': portfolio.short_name if portfolio.short_name else portfolio.name,
            'data': values,
            'backgroundColor': 'transparent',
            'borderColor': colors[color_index],
            'pointBackgroundColor': colors[color_index],
            'borderWidth': 2,
            'pointRadius': 3,
            'lineTension': 0.3,
        }
        data['datasets'].append(dataset)
    
    return JsonResponse(data)

def stock_detail(request, stock_id):
    """Individual stock detail page"""
    stock = get_object_or_404(Stock, pk=stock_id)
    
    # Get price history
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)  # Last 90 days
    
    price_history = StockPrice.objects.filter(
        stock=stock,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Get portfolios that include this stock
    portfolio_positions = []
    portfolios_with_stock = Portfolio.objects.filter(positions__stock=stock).distinct()
    
    # Prepare portfolio position data for each portfolio containing this stock
    for portfolio in portfolios_with_stock:
        try:
            position = PortfolioPosition.objects.get(portfolio=portfolio, stock=stock)
            portfolio_positions.append({
                'portfolio': portfolio,
                'position': position
            })
        except PortfolioPosition.DoesNotExist:
            continue
    
    # Get latest price and change
    latest_price = stock.prices.order_by('-date').first()
    previous_price = stock.prices.filter(date__lt=latest_price.date).order_by('-date').first() if latest_price else None
    
    price_change = 0
    price_change_percent = 0
    
    if latest_price and previous_price:
        price_change = latest_price.close_price - previous_price.close_price
        price_change_percent = (price_change / previous_price.close_price) * 100
    
    # Prepare data for chart
    labels = [price.date.strftime('%Y-%m-%d') for price in price_history]
    values = [float(price.close_price) for price in price_history]
    
    chart_data = json.dumps({
        'labels': labels,
        'values': values
    })
    
    # Ensure proper API url for the frontend to use
    api_price_history_url = f"/api/v1/stocks/{stock.id}/history/"
    
    context = {
        'stock': stock,
        'price_history': price_history,
        'portfolio_positions': portfolio_positions,
        'chart_data': chart_data,
        'latest_price': latest_price,
        'price_change': price_change,
        'price_change_percent': price_change_percent,
        'api_price_history_url': api_price_history_url
    }
    return render(request, 'stock_visualization/stocks/detail.html', context)

# New views for sectors
def sector_list(request):
    sectors = Sector.objects.all()
    context = {
        'sectors': sectors,
    }
    return render(request, 'stock_visualization/stocks/sector_list.html', context)

def sector_detail(request, sector_id):
    sector = get_object_or_404(Sector, id=sector_id)
    stocks = Stock.objects.filter(sector=sector)
    
    # Sort stocks by daily change percentage (descending)
    stocks_list = list(stocks)
    stocks_list.sort(key=lambda stock: stock.get_daily_change().get('percent', 0) if stock.get_daily_change() else 0, reverse=True)
    
    context = {
        'sector': sector,
        'stocks': stocks_list,
    }
    return render(request, 'stock_visualization/stocks/sector_detail.html', context)

# New views for industries
def industry_list(request):
    industries = Industry.objects.all()
    context = {
        'industries': industries,
    }
    return render(request, 'stock_visualization/stocks/industry_list.html', context)

def industry_detail(request, industry_id):
    industry = get_object_or_404(Industry, id=industry_id)
    stocks = Stock.objects.filter(industry=industry)
    context = {
        'industry': industry,
        'stocks': stocks,
    }
    return render(request, 'stock_visualization/stocks/industry_detail.html', context)

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'stock_visualization/legal/privacy_policy.html')

def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'stock_visualization/legal/terms_of_service.html')
