import requests
import json
from pprint import pprint

BASE_URL = 'http://localhost:8000/api/v1'  # For local production testing

TOKEN = None  # You'll need to set this after authentication

def authenticate(username, password):
    global TOKEN
    response = requests.post(
        'http://localhost:8000/api/auth/token/',  # Updated auth endpoint
        data={'username': username, 'password': password}
    )
    if response.status_code == 200:
        TOKEN = response.json()['token']
        print(f"Authentication successful. Token: {TOKEN}")
        return True
    else:
        print(f"Authentication failed: {response.json()}")
        return False

def get_headers():
    return {'Authorization': f'Token {TOKEN}'} if TOKEN else {}

def get_stocks():
    response = requests.get(f'{BASE_URL}/stocks/', headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_portfolios():
    response = requests.get(f'{BASE_URL}/portfolios/', headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def get_portfolio_positions(portfolio_id):
    response = requests.get(
        f'{BASE_URL}/portfolios/{portfolio_id}/positions/', 
        headers=get_headers()
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def update_stock_prices():
    response = requests.post(
        f'{BASE_URL}/stocks/update_prices/', 
        headers=get_headers()
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def add_position(portfolio_id, stock_id, quantity, initial_price, purchase_date):
    data = {
        'portfolio': portfolio_id,
        'stock': stock_id,
        'quantity': quantity,
        'initial_price': initial_price,
        'purchase_date': purchase_date
    }
    response = requests.post(
        f'{BASE_URL}/portfolios/{portfolio_id}/add_position/', 
        headers=get_headers(),
        json=data
    )
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    # Replace with your actual username and password
    if not authenticate('admin', 'password'):
        return
    
    # Example API usage
    print("\n== Stock List ==")
    stocks = get_stocks()
    if stocks:
        for stock in stocks['results']:
            print(f"{stock['symbol']} - {stock['company_name']}: ${stock.get('latest_price', 'N/A')}")
    
    print("\n== Update Stock Prices ==")
    update_result = update_stock_prices()
    if update_result:
        pprint(update_result)
    
    print("\n== Portfolios ==")
    portfolios = get_portfolios()
    if portfolios:
        for portfolio in portfolios['results']:
            print(f"{portfolio['name']} - Value: ${portfolio['current_value']}")
            
            print(f"\n== Positions for {portfolio['name']} ==")
            positions = get_portfolio_positions(portfolio['id'])
            if positions:
                for position in positions:
                    print(f"{position['stock_symbol']} - {position['quantity']} shares, "
                          f"Value: ${position['current_value']}, "
                          f"Performance: {position['performance']}%")

if __name__ == "__main__":
    main()
