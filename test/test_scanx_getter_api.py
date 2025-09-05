"""
Test runner for ScanX Getter API

Usage (Windows example):
1. Activate virtualenv:
   "D:/scraping/scrap_venv/Scripts/activate.bat"
2. Start server in separate terminal: python main.py
3. Run this test: python test/test_scanx_getter_api.py

This script picks one symbol from `company_symbol_list.json` and hits all endpoints sequentially
and then fires several requests concurrently to simulate in-flight scrape handling.
"""

import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE = "http://localhost:1020/scanx/getter"


def pick_symbol():
    p = Path('company_symbol_list.json')
    if not p.exists():
        raise SystemExit('company_symbol_list.json not found')
    data = json.loads(p.read_text())
    # Attempt to pick a symbol from list structure - support both list and dict
    if isinstance(data, dict):
        # If file is a dict with list under 'data' or top-level keys
        candidates = []
        if 'data' in data and isinstance(data['data'], list):
            for item in data['data']:
                if isinstance(item, dict) and item.get('Symbol'):
                    candidates.append(item['Symbol'])
        else:
            # fallback to any 'Symbol' values
            for v in data.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and item.get('Symbol'):
                            candidates.append(item['Symbol'])
    elif isinstance(data, list):
        candidates = [item.get('Symbol') for item in data if isinstance(item, dict) and item.get('Symbol')]
    else:
        candidates = []

    if not candidates:
        raise SystemExit('No symbols found in company_symbol_list.json')
    return candidates[0].upper()


ENDPOINTS = [
    '/company/about_company',
    '/company/analyst_ratings',
    '/company/financials',
    '/company/balance_sheet_consolidated',
    '/company/balance_sheet_standalone',
    '/company/cash_flow_consolidated',
    '/company/cash_flow_standalone',
    '/company/financial_results_quarterly_consolidated',
    '/company/financial_results_annual_consolidated',
    '/company/financial_results_quarterly_standalone',
    '/company/financial_results_annual_standalone',
    '/company/net_profit_standalone',
    '/company/share_holders_equity',
    '/mf/holdings',
    '/mf/transactions',
    '/company/peer_comparison',
    '/company/forecast_Q',
    '/company/forecast_A',
    '/company/corporate_action_data',
    '/company/dividend_data',
    '/company/fundamental_data',
    '/company/latest_news',
    '/company/announcements',
    '/company/company_filings_data',
    '/company/live_news_data',
    '/charts/formatted_last_five_years_chart',
]


def call_endpoint(endpoint, symbol):
    url = f"{BASE}{endpoint}?symbol={symbol}"
    try:
        r = requests.get(url, timeout=60)
        return endpoint, r.status_code, r.json()
    except Exception as e:
        return endpoint, 'ERR', str(e)


def main():
    symbol = pick_symbol()
    print(f"Using symbol: {symbol}")

    # Sequential pass
    print('--- Sequential calls ---')
    for ep in ENDPOINTS:
        ep, status, data = call_endpoint(ep, symbol)
        print(f"{ep} -> {status}")
        time.sleep(0.2)

    # Concurrent pass: fire several calls to test in-flight coordination
    print('\n--- Concurrent calls (simultaneous) ---')
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(call_endpoint, ep, symbol) for ep in ENDPOINTS[:8]]
        for fut in as_completed(futures):
            ep, status, data = fut.result()
            print(f"{ep} -> {status}")

    print('\nTest completed')


if __name__ == '__main__':
    main()
