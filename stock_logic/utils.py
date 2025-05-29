import yfinance as yf
from datetime import datetime, timedelta, date
import pytz
from .models import Stock, StockPrice, Sector, Industry
from django.db import IntegrityError
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def fetch_stock_data(symbol):
    """
    Fetch today's data for a stock using yfinance with Alpha Vantage as backup
    """
    # First try yfinance
    data = fetch_with_yfinance(symbol)
    
    # If yfinance fails, try Alpha Vantage as backup
    if data is None:
        logger.info(f"yfinance failed for {symbol}, trying Alpha Vantage as backup")
        data = fetch_with_alphavantage(symbol)
    
    return data

def fetch_with_yfinance(symbol):
    """
    Fetch stock data using yfinance library
    """
    try:
        ticker = yf.Ticker(symbol)
        # Get data for today and yesterday to ensure we capture the full trading day
        end_date = datetime.now().date() + timedelta(days=1)  # Include today
        start_date = end_date - timedelta(days=5)  # Go back a few days to ensure we get the latest trading day
        
        data = ticker.history(start=start_date, end=end_date)
        if data.empty:
            logger.warning(f"No data retrieved for {symbol} with yfinance")
            return None
              # Get the most recent trading day
        latest_date = data.index[-1].date()
        
        # Get data for the latest trading day
        latest_data = data.loc[data.index.date == latest_date]
        
        if latest_data.empty:
            logger.warning(f"No data for latest trading day for {symbol} with yfinance")
            return None
            
        return {
            'date': latest_date,
            'open_price': float(latest_data['Open'].iloc[0]),
            'close_price': float(latest_data['Close'].iloc[0]),
            'high_price': float(latest_data['High'].iloc[0]),
            'low_price': float(latest_data['Low'].iloc[0]),
            'volume': int(latest_data['Volume'].iloc[0]) if 'Volume' in latest_data else None,
        }
    except Exception as e:
        logger.error(f"Error fetching data for {symbol} with yfinance: {e}")
        return None

def fetch_with_alphavantage(symbol):
    """
    Fetch stock data using Alpha Vantage API as a backup
    """
    try:
        # Get API key from settings, defaulting to empty string if not set
        api_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', '')
        if not api_key:
            logger.error("Alpha Vantage API key not configured in settings")
            return None
            
        # Prepare API endpoint for daily data
        kek = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo'
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
        
        # Make the request
        response = requests.get(url)
        data = response.json()
        
        # Check if valid data is returned
        if 'Time Series (Daily)' not in data:
            logger.warning(f"No valid data from Alpha Vantage for {symbol}: {data}")
            return None
            
        # Get the most recent date's data
        time_series = data['Time Series (Daily)']
        latest_date_str = max(time_series.keys())
        latest_date_data = time_series[latest_date_str]
        
        # Convert date string to date object
        latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
        
        return {
            'date': latest_date,
            'open_price': float(latest_date_data['1. open']),
            'close_price': float(latest_date_data['4. close']),
            'high_price': float(latest_date_data['2. high']),
            'low_price': float(latest_date_data['3. low']),
            'volume': int(latest_date_data['5. volume']) if '5. volume' in latest_date_data else None,
        }
    except Exception as e:
        logger.error(f"Error fetching data for {symbol} with Alpha Vantage: {e}")
        return None

def update_stock_prices():
    """
    Update prices for all stocks in the database
    """
    stocks = Stock.objects.all()
    updated_count = 0
    
    for stock in stocks:
        data = fetch_stock_data(stock.symbol)
        if data:
            try:
                # Try to update existing record for this date
                price_obj, created = StockPrice.objects.update_or_create(
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
                if created:
                    logger.info(f"Created new price record for {stock.symbol} on {data['date']}")
                else:
                    logger.info(f"Updated price record for {stock.symbol} on {data['date']}")
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating price for {stock.symbol}: {e}")
    
    # After updating stock prices, update all portfolio prices
    from .models import Portfolio
    portfolios = Portfolio.objects.all()
    portfolio_count = 0
    
    for portfolio in portfolios:
        try:
            portfolio.update_prices()
            portfolio_count += 1
            logger.info(f"Updated prices for portfolio: {portfolio.name}")
        except Exception as e:
            logger.error(f"Error updating prices for portfolio {portfolio.name}: {e}")
    
    logger.info(f"Updated prices for {updated_count} stocks and {portfolio_count} portfolios")
    
    return updated_count

def is_nyse_closing_time():
    """
    Check if it's between NYSE close (4:00 PM ET) and 5:00 PM ET
    """
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # NYSE closing time (4:00 PM ET)
    closing_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # 5:00 PM ET
    end_window = now.replace(hour=17, minute=0, second=0, microsecond=0)
    
    # Check if we're within the window between 4:00 PM ET and 5:00 PM ET
    is_in_window = closing_time <= now <= end_window
    
    # Also check if it's a weekday (NYSE is closed on weekends)
    is_weekday = now.weekday() < 5  # 0-4 are Monday to Friday
    
    return is_in_window and is_weekday

def ensure_sector_and_industry(stock, sector_name=None, industry_name=None):
    """
    Ensure a stock has proper sector and industry relationships.
    If sector_name or industry_name are provided, use those.
    Otherwise, keep existing relationships or create defaults.
    """
    if sector_name:
        # Create or get the sector
        sector, _ = Sector.objects.get_or_create(name=sector_name)
        stock.sector = sector
        
        # Create or get a default industry if not provided
        if not industry_name:
            industry_name = f"{sector_name} General"
        
        # Get or create the industry within this sector
        industry, _ = Industry.objects.get_or_create(
            name=industry_name,
            defaults={'sector': sector}
        )
        stock.industry = industry
    
    # Ensure stock is saved with valid relationships
    elif not stock.sector or not stock.industry:
        # Default sector/industry
        default_sector, _ = Sector.objects.get_or_create(name="Uncategorized")
        default_industry, _ = Industry.objects.get_or_create(
            name="Uncategorized", 
            defaults={'sector': default_sector}
        )
        
        if not stock.sector:
            stock.sector = default_sector
        
        if not stock.industry:
            stock.industry = default_industry
    
    stock.save()
    return stock
