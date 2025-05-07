import yfinance as yf
from datetime import datetime, timedelta, date
import pytz
from .models import Stock, StockPrice
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

def fetch_stock_data(symbol):
    """
    Fetch today's data for a stock using yfinance
    """
    try:
        ticker = yf.Ticker(symbol)
        # Get data for today and yesterday to ensure we capture the full trading day
        end_date = datetime.now().date() + timedelta(days=1)  # Include today
        start_date = end_date - timedelta(days=5)  # Go back a few days to ensure we get the latest trading day
        
        data = ticker.history(start=start_date, end=end_date)
        if data.empty:
            logger.warning(f"No data retrieved for {symbol}")
            return None
            
        # Get the most recent trading day
        latest_date = data.index[-1].date()
        
        # Get data for the latest trading day
        latest_data = data.loc[data.index.date == latest_date]
        
        if latest_data.empty:
            logger.warning(f"No data for latest trading day for {symbol}")
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
        logger.error(f"Error fetching data for {symbol}: {e}")
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
    
    return updated_count

def is_nyse_closing_time():
    """
    Check if it's exactly 10 minutes after NYSE close (4:10 PM ET)
    """
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # NYSE closing time (4:00 PM ET)
    closing_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # 10 minutes after closing
    ten_min_after = closing_time + timedelta(minutes=10)
    
    # Check if we're within a 2-minute window of 4:10 PM ET (to account for scheduling delays)
    start_window = ten_min_after - timedelta(minutes=1)
    end_window = ten_min_after + timedelta(minutes=1)
    
    # Also check if it's a weekday (NYSE is closed on weekends)
    is_weekday = now.weekday() < 5  # 0-4 are Monday to Friday
    
    return start_window <= now <= end_window and is_weekday
