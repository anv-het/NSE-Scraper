import requests
import concurrent.futures
import json

# Base host
BASE_URL = 'http://192.168.119.183:1020'

# API endpoints (paths only)
endpoints = [
    '/scanx/getter/company/about_company?symbol=itc&include_outer=false',
    '/scanx/getter/company/analyst_ratings?symbol=itc',
    '/scanx/getter/company/financials?symbol=itc',
    '/scanx/getter/company/balance_sheet_consolidated?symbol=itc',
    '/scanx/getter/company/balance_sheet_standalone?symbol=itc',
    '/scanx/getter/company/cash_flow_consolidated?symbol=itc',
    '/scanx/getter/company/cash_flow_standalone?symbol=itc',
    '/scanx/getter/company/financial_results_quarterly_consolidated?symbol=itc',
    '/scanx/getter/company/financial_results_annual_consolidated?symbol=itc',
    '/scanx/getter/company/financial_results_quarterly_standalone?symbol=itc',
    '/scanx/getter/company/financial_results_annual_standalone?symbol=itc',
    '/scanx/getter/company/net_profit_standalone?symbol=itc',
    '/scanx/getter/company/share_holders_equity?symbol=itc',
    '/scanx/getter/mf/holdings?symbol=itc',
    '/scanx/getter/mf/transactions?symbol=itc',
    '/scanx/getter/company/peer_comparison?symbol=itc',
    '/scanx/getter/company/forecast_Q?symbol=itc',
    '/scanx/getter/company/forecast_A?symbol=itc',
    '/scanx/getter/company/corporate_action_data?symbol=itc',
    '/scanx/getter/company/dividend_data?symbol=itc',
    '/scanx/getter/company/fundamental_data?symbol=itc',
    '/scanx/getter/company/latest_news?symbol=itc',
    '/scanx/getter/charts/formatted_last_five_years_chart?symbol=itc',
    '/scanx/getter/company/announcements?symbol=itc',
    '/scanx/getter/company/company_filings_data?symbol=itc',
    '/scanx/getter/company/live_news_data?symbol=itc'
]

# Headers
headers = {
    'accept': 'application/json'
}

# Function to fetch one API
def fetch_api(endpoint):
    url = BASE_URL + endpoint
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return (endpoint, response.json())
    except requests.RequestException as e:
        return (endpoint, {'error': str(e)})

# Main
def main():
    result = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map each endpoint to the fetch_api function
        futures = executor.map(fetch_api, endpoints)

        for endpoint, data in futures:
            result[endpoint] = data

    # Save all responses to a JSON file
    with open('itc_all_api_responses.json', 'w') as f:
        json.dump(result, f, indent=2)

    print("✅ All APIs fetched and saved to 'itc_all_api_responses.json'.")

if __name__ == '__main__':
    main()
