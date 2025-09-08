#!/usr/bin/env python3
"""
ScanX Stock Data Controller
==========================
Symbol-based stock data scraper following NSE Controller patterns.
Handles comprehensive stock data collection with 24-hour caching and MongoDB storage.

Features:
- NSE Controller pattern implementation
- Symbol-based data scraping (single/multiple symbols)
- 24-hour caching mechanism in MongoDB
- Time-sensitive API updates via cron
- Proper logging and error handling
- MongoDB storage with update-based operations
"""

import json
import time
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, wait_random_exponential, stop_after_attempt

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.config_reader import configure
from Utils.response import create_success_response_n, create_error_response

# Import existing ScanX utilities and functions
from Utils.scanx_utlilits import (
    parallel_format_financial_data, 
    parallel_format_quarterly_data, 
    parallel_format_stock_chart_data, 
    optimize_format_mutual_fund_data
)

logger = get_logger(__name__)


class ScanXStockDataController:
    """
    ScanX Stock Data Controller following NSE Controller pattern
    Handles symbol-based scraping with 24-hour caching and time-sensitive updates
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection_name = 'scanx_stocks_data'
        
        # Load stock data reference
        self.stock_data = self._load_stock_data()
        
        # API endpoints
        self.company_api_url = 'https://scanx-analytics.dhan.co/customscan/fetchdt'
        self.analyst_rating_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/analyst_rating'
        self.announcements_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/lodr'
        self.latest_new_announcement_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/announcements'
        self.live_news_api_url = 'https://news-live.dhan.co/v3/news/getLiveNews'
        self.dividend_data_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/dividenddata'
        self.fundamental_data_api_url = 'https://open-web-scanx.dhan.co/scanx/fundamental'
        self.forecast_data_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/forecast'
        self.corporate_action_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/corporate_action'
        self.company_filings_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/company_filings'
        self.mutual_fund_holdings_api_url = 'https://ow-static-scanx.dhan.co/staticscanx/mfpastholdingsbyisin'
        self.last_five_years_chart_data_api_url = 'https://openweb-ticks.dhan.co/getDataH' 
        self.multi_timeframe_chart_data_api_url = 'https://open-web-scanx.dhan.co/scanx/multirtscrdt'
        self.mutual_fund_transaction_api_url = 'https://static-scanx.dhan.co/staticscanx/mftransaction'
        
        # Headers for requests
        self.headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://scanx.trade',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }    
        
        # Setup requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)
        
        # Unix timestamp for today
        today_dt = datetime.today()
        self.today_dt_unix = int(today_dt.timestamp())

    def _load_stock_data(self) -> Dict:
        """# Load the stock data from the company_symbol_list.json file"""
        try:
            with open('company_symbol_list.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load stock data: {str(e)}")
            return {"data": []}

    def _find_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Find a stock by symbol, matching against Symbol, DispSym or Seosym fields.

        Args:
            symbol (str): The stock symbol to search for (e.g., 'tcs', 'infy', 'hdfc')

        Returns:
            dict: Stock data if found, None otherwise
        """
        symbol_lower = symbol.lower()

        for stock in self.stock_data:
            # Match against Symbol field
            if 'Symbol' in stock:
                symbol_field = stock['Symbol'].lower()
                if symbol_lower in symbol_field or symbol_field in symbol_lower:
                    return stock

            # # Match against DispSym field
            # if 'DispSym' in stock:
            #     dispsym = stock['DispSym'].lower()
            #     if symbol_lower in dispsym:
            #         return stock

            # # Match against Seosym field
            # if 'Seosym' in stock:
            #     seosym = stock['Seosym'].lower()
            #     if symbol_lower in seosym:
            #         return stock

        return None


    def _check_cache_validity(self, symbol: str) -> Optional[Dict]:
        """
        Check if cached data exists and is within 24-hour validity period.
        
        Args:
            symbol (str): Stock symbol to check
            
        Returns:
            dict: Cached document if valid, None otherwise
        """
        try:
            # Query MongoDB for existing document
            query = {"symbol": symbol.upper()}
            document = self.db_manager.mongo_db[self.collection_name].find_one(query)
            
            if not document:
                logger.info(f"No cached data found for symbol: {symbol}")
                return None
            
            # Check if last_updated_at exists and is within 24 hours
            last_updated = document.get('last_updated_at')
            if not last_updated:
                logger.info(f"No last_updated_at timestamp for symbol: {symbol}")
                return None
            
            # Parse the timestamp (assuming ISO format)
            if isinstance(last_updated, str):
                last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            else:
                last_updated_dt = last_updated
            
            # Check if data is less than 24 hours old
            current_time = datetime.now(timezone.utc)
            time_diff = current_time - last_updated_dt.replace(tzinfo=timezone.utc)
            
            if time_diff.total_seconds() < 86400:  # 24 hours = 86400 seconds
                logger.info(f"Valid cached data found for symbol: {symbol} (age: {time_diff})")
                return document
            else:
                logger.info(f"Cached data expired for symbol: {symbol} (age: {time_diff})")
                return None
                
        except Exception as e:
            logger.error(f"Error checking cache for symbol {symbol}: {str(e)}")
            return None

    def _save_or_update_stock_data(self, symbol: str, stock_data: Dict) -> bool:
        """
        Save or update stock data in MongoDB.
        
        Args:
            symbol (str): Stock symbol
            stock_data (dict): Formatted stock data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add metadata timestamps
            current_time = datetime.now(timezone.utc).isoformat()
            stock_data['symbol'] = symbol.upper()
            stock_data['last_updated_at'] = current_time
            
            # If this is a new document, add created_at
            if not stock_data.get('created_at'):
                stock_data['created_at'] = current_time
            
            # Upsert the document
            query = {"symbol": symbol.upper()}
            result = self.db_manager.mongo_db[self.collection_name].replace_one(
                query, stock_data, upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"Successfully saved/updated data for symbol: {symbol}")
                return True
            else:
                logger.error(f"Failed to save/update data for symbol: {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving data for symbol {symbol}: {str(e)}")
            return False

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(3))
    def _make_request(self, url: str, payload: Dict = None, method: str = "POST") -> Optional[Dict]:
        """
        Make HTTP request with retry logic and proper error handling.
        
        Args:
            url (str): API endpoint URL
            payload (dict): Request payload for POST requests
            method (str): HTTP method (GET/POST)
            
        Returns:
            dict: Response data if successful, None otherwise
        """
        try:
            if method.upper() == "POST":
                response = requests.post(
                    url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=configure.getint('SCRAPING', 'TIMEOUT', fallback=30)
                )
            else:
                response = requests.get(
                    url, 
                    headers=self.headers,
                    timeout=configure.getint('SCRAPING', 'TIMEOUT', fallback=30)
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code} for URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Request failed for URL {url}: {str(e)}")
            return None

    def _fetch_company_data(self, seosym: str) -> Optional[Dict]:
        """Fetch company data from the ScanX API"""
        payload = {
            "data": {
                "sorder": "asc",
                "count": 1,
                "fields": ["Isin", "Sid", "Seg", "Pchange", "PPerchange", "Inst", "DispSym", "Sym", "LotSize", "Multiplier", "TickSize", "DayVolPrevCandle", "PricePerchng1week", "DispSym", "Ltp", "Mcap", "Pe", "DivYeild", "Pb", "Roe", "ROCE", "Ind_Pe", "Ind_Pb", "High1Yr", "Low1Yr", "BookValue", "Eps", "YearlyEarningPerShare", "PricePerchng1mon", "PricePerchng2mon", "PricePerchng3mon", "PricePerchng6mon", "PricePerchng9mon", "PricePerchng1week", "PricePerchng2week", "PricePerchng3week", "PricePerchng1year", "PricePerchng2year", "PricePerchng3year", "PricePerchng4year", "PricePerchng5year", "QoQRevenueGrowth", "NetIncome", "YearlyRevenue", "Year1RevenueGrowth", "Year3CAGRRevenueGrowth", "Year5CAGRRevenueGrowth", "QoQNetIncomeGrowth", "Year1NetIncomeGrowth", "Year3NetIncomeGrowth", "Year5NetIncomeGrowth", "OCFGrowthOnYr", "Year3OperatingCashFlow", "Year5OperatingCashFlow", "QoQRoE", "Year1ROE", "Year3ROE", "Year5ROE", "QoQRoCE", "Year1ROCE", "Year3ROCE", "Year5ROCE", "QoQEBITDAMarginGrowth", "Year1CAGREBITDAMarginGrowth", "Year3CAGREBITDAMarginGrowth", "Year5CAGREBITDAMarginGrowth", "YoYLastQtrlyProfitGrowth", "DayRSI14CurrentCandle", "Sector", "SubSector", "Mcap", "DivYeild", "Ind_Eps", "PromoterHolding", "YearlyEarningPerShare", "BookValue", "Sector", "Ind_Debt2Eq", "DIIHolding", "ReturnOnEquity", "Pe", "SubSector", "Ind_Pb", "DIIHLDChagPer", "ROCE", "High1Yr", "Ind_CurrentRto", "FIIHolding", "Pb", "Low1Yr", "Ind_DivYeild", "FIIHLDChagPer", "YearlyEBITDA", "Debt2Eq", "PESecPERatio", "Ind_OperatingMrg", "RetailInvestorHolding", "AboutComp", "Chairman", "Internet", "ListingDate"],
                "params": [{"field": "Seosym.keyword", "op": "", "val": seosym}],
                "logic_op": "AND",
                "pgno": 1
            }
        }
        return self._make_request(self.company_api_url, payload)

    def _fetch_peer_comparison_data(self, subsector: str, sector: str) -> Optional[Dict]:
        """Fetch peer comparison data from the API"""
        payload = {
            "data": {
                "sort": "Mcap",
                "sorder": "desc",
                "count": 50,
                "params": [
                    {"field": "SubSector", "op": "", "val": subsector},
                    {"field": "Sector", "op": "", "val": sector},
                    {"field": "OgInst", "op": "", "val": "ES"}
                ],
                "logic_op": "AND",
                "fields": [
                    "Sym", "Isin", "DispSym", "Ltp", "Mcap", "Pe", "YearlyRevenue",
                    "Year1RevenueGrowth", "NetIncome", "YoYLastQtrlyProfitGrowth", "DayRSI14CurrentCandle"
                ],
                "pgno": 1
            }
        }
        return self._make_request(self.company_api_url, payload)

    def _fetch_analyst_ratings_data(self, isin: str) -> Optional[Dict]:
        """Fetch analyst ratings data from the API"""
        payload = {"data": {"isin": isin}}
        return self._make_request(self.analyst_rating_api_url, payload)

    def _fetch_announcements_data(self, isin: str) -> Optional[Dict]:
        """Fetch announcements data from the API"""
        payload = {
            "data": {
                "isin": isin,
                "pg_no": 1,
                "count": 500
            }
        }
        return self._make_request(self.announcements_api_url, payload)

    def _fetch_latest_announcements_data(self, isin: str) -> Optional[Dict]:
        """Fetch latest announcements data from the API"""
        payload = {
            "data": {
                "isin": isin
            }
        }
        return self._make_request(self.latest_new_announcement_api_url, payload)

    def _fetch_dividend_data(self, isin: str) -> Optional[Dict]:
        """Fetch dividend data from the API"""
        payload = {
            "data": {
                "isin": isin
            }
        }
        return self._make_request(self.dividend_data_api_url, payload)

    def _fetch_fundamental_data(self, isin: str) -> Optional[Dict]:
        """Fetch fundamental data from the API"""
        payload = {
            "data": {
                "isins": [isin]
            }
        }
        return self._make_request(self.fundamental_data_api_url, payload)

    def _fetch_forecast_data_quarterly(self, isin: str, period: str = "Q") -> Optional[Dict]:
        """Fetch forecast data from the API (Quarterly or Annually)"""
        payload = {
            "Data": {
                "isin": isin,
                "period": period
            }
        }
        return self._make_request(self.forecast_data_api_url, payload)
    
    def _fetch_forecast_data_annually(self, isin: str, period: str = "A") -> Optional[Dict]:
        """Fetch forecast data from the API (Quarterly or Annually)"""
        payload = {
            "Data": {
                "isin": isin,
                "period": period
            }
        }
        return self._make_request(self.forecast_data_api_url, payload)

    def _fetch_corporate_action_data(self, isin: str) -> Optional[Dict]:
        """Fetch corporate action data from the API"""
        payload = {
            "data": {
                "isin": isin,
                "time": "ALL",
                "page": 1,
                "pagesize": 250
            }
        }
        return self._make_request(self.corporate_action_api_url, payload)

    def _fetch_company_filings_data(self, isin: str) -> Optional[Dict]:
        """Fetch company filings data from the API"""
        payload = {
            "data": {
                "isin": isin,
                "count": 250
            }
        }
        return self._make_request(self.company_filings_api_url, payload)

    def _fetch_mutual_fund_holdings_data(self, isin: str) -> Optional[Dict]:
        """Fetch mutual fund holdings data from the API"""
        payload = {
            "data": {
                "isin": isin,
                "page": 1,
                "pageSize": 750
            }
        }
        return self._make_request(self.mutual_fund_holdings_api_url, payload)

    def _fetch_chart_data(self, exch: str, sym: str, seg: str, inst: str, sec_id: int, exp_code: str, 
                         interval: str, start: int, end: int, delivery_per: str) -> Optional[Dict]:
        """Fetch last five years chart data from the API"""
        payload = {
            "EXCH": exch,
            "SYM": sym,
            "SEG": seg,
            "INST": inst,
            "SEC_ID": sec_id,
            "EXPCODE": exp_code,
            "INTERVAL": interval,
            "START": 1,
            "END": end,
            "DeliveryPer": delivery_per
        }
        return self._make_request(self.last_five_years_chart_data_api_url, payload)

    def _fetch_last_five_years_chart_data(self, exch: str, sym: str, seg: str, inst: str, sec_id: int, exp_code: str, interval: str, start: int, end: int, delivery_per: str) -> Optional[Dict]:
        """Fetch last five years chart data from the API"""
        payload = {
            "EXCH": exch,
            "SYM": sym,
            "SEG": seg,
            "INST": inst,
            "SEC_ID": sec_id,
            "EXPCODE": exp_code,
            "INTERVAL": interval,
            "START": 1,
            "END": end,
            "DeliveryPer": delivery_per
        }
        return self._make_request(self.last_five_years_chart_data_api_url, payload)
# sym, exch, sym, seg, inst, sec_id, 0, "D", 1, self.today_dt_unix, True

    def _fetch_chart_data_by_symbol(self, sym: str, exch: str, seg: str, inst: str, sec_id: int, exp_code: str, interval: str, start: int, end: int, delivery_per: str) -> Optional[Dict]:
        """Fetch chart data by symbol from the API"""
        chart_data = self._fetch_last_five_years_chart_data(
            exch=exch,
            sym=sym,
            seg=seg,
            inst=inst,
            sec_id=sec_id,
            exp_code=exp_code,
            interval=interval,
            start=start,
            end=end,
            delivery_per=delivery_per
        )
        return {sym.upper(): chart_data}

    def _fetch_multi_timeframe_chart_data(self, sec_id: int) -> Optional[Dict]:
        """Fetch multi-timeframe chart data from the API"""
        payload = {
            "data": {
                "SecId": sec_id
            }
        }
        return self._make_request(self.multi_timeframe_chart_data_api_url, payload)

    def _fetch_live_news_data_advanced(self, symbol: str) -> Optional[Dict]:
        """Fetch advanced live news data from the API"""
        payload = {
            "categories": ["ALL"],
            "page_no": 0,
            "limit": 50,
            "first_news_timeStamp": 0,
            "last_news_timeStamp": 0,
            "news_feed_type": "live",
            "stock_list": [symbol],
            "entity_id": ""
        }
        return self._make_request(self.live_news_api_url, payload)

    def _fetch_mutual_fund_transaction_data(self, isin: str) -> Optional[Dict]:
        """Fetch mutual fund transaction data from the API"""
        payload = {
            "data": {
                "isin": isin,
                "page": 1,
                "pageSize": 750
            }
        }
        return self._make_request(self.mutual_fund_transaction_api_url, payload)


    def scrape_single_symbol(self, symbol: str, max_workers: int = 8) -> Optional[Dict]:
        """
        Scrape data for a single stock symbol with 24-hour caching.
        
        Args:
            symbol (str): Stock symbol to scrape (e.g., 'tcs', 'infy')
            max_workers (int): Number of parallel workers for API calls
        
        Returns:
            dict: Scraped stock data or cached data if valid
        """
        try:
            logger.info(f"Starting scrape for symbol: {symbol}")
            
            # Check cache first
            cached_data = self._check_cache_validity(symbol)
            if cached_data:
                logger.info(f"Returning cached data for symbol: {symbol}")
                return cached_data
            
            # Find stock in reference data
            stock = self._find_stock_by_symbol(symbol)
            if not stock:
                logger.error(f"Stock not found for symbol: {symbol}")
                return None
            
            logger.info(f"Found stock: {symbol} -> {stock.get('DispSym', 'Unknown')}")
            seosym = stock.get('Seosym', '')
            isin = stock.get('Isin', '')
            
            # Fetch company data first
            company_data = self._fetch_company_data(seosym)
            if not company_data or not company_data.get('data'):
                logger.error(f"Failed to fetch company data for {symbol}")
                return None
            
            # Check if data array is empty
            data_list = company_data.get('data', [])
            if not data_list:
                logger.error(f"Empty data list returned for {symbol}")
                return None
            
            # Extract additional data from company_data API response
            company_info = data_list[0]
            subsector = company_info.get('SubSector', '')
            sector = company_info.get('Sector', '')
            sym = company_info.get('Sym', '')
            seg = company_info.get('Seg', '')
            inst = company_info.get('Inst', '')
            isin = company_info.get('Isin', '')
            exch = 'NSE' if 'NSE' in stock.get('Exch', []) else 'BSE'

            sec_id = company_info.get('Sid', '')
            
            # Prepare parallel API calls
            with ThreadPoolExecutor(max_workers=max_workers) as api_executor:
                futures = {
                    "peer_comparison": api_executor.submit(self._fetch_peer_comparison_data, subsector, sector),
                    "analyst_ratings": api_executor.submit(self._fetch_analyst_ratings_data, isin),
                    "announcements": api_executor.submit(self._fetch_announcements_data, isin),
                    "latest_announcements": api_executor.submit(self._fetch_latest_announcements_data, isin),
                    "dividend_data": api_executor.submit(self._fetch_dividend_data, isin),
                    "fundamental_data": api_executor.submit(self._fetch_fundamental_data, isin),
                    "forecast_data_Q": api_executor.submit(self._fetch_forecast_data_quarterly, isin, "Q"),
                    "forecast_data_A": api_executor.submit(self._fetch_forecast_data_annually, isin, "A"),
                    "corporate_action_data": api_executor.submit(self._fetch_corporate_action_data, isin),
                    "company_filings_data": api_executor.submit(self._fetch_company_filings_data, isin),
                    "mutual_fund_holdings_data": api_executor.submit(self._fetch_mutual_fund_holdings_data, isin),
                    "mutual_fund_transaction_data": api_executor.submit(self._fetch_mutual_fund_transaction_data, isin),
                    "live_news_data": api_executor.submit(self._fetch_live_news_data_advanced, stock.get('Sym', '')),
                    
                }

                peer_comparison_data = futures.get("peer_comparison").result()
                analyst_ratings_data = futures.get("analyst_ratings").result()
                announcements_data = futures.get("announcements").result()
                latest_announcements_data = futures.get("latest_announcements").result()
                live_news_data = futures.get("live_news_data").result()
                dividend_data = futures.get("dividend_data").result()
                fundamental_data = futures.get("fundamental_data").result()
                forecast_data_Q = futures.get("forecast_data_Q").result()
                forecast_data_A = futures.get("forecast_data_A").result()
                corporate_action_data = futures.get("corporate_action_data").result()
                company_filings_data = futures.get("company_filings_data").result()
                mutual_fund_holdings_data = futures.get("mutual_fund_holdings_data").result()
                mutual_fund_transaction_data = futures.get("mutual_fund_transaction_data").result()


                # # Fetch chart data for the main stock
                # last_five_years_chart_data = self._fetch_chart_data_by_symbol(sym, exch, seg, inst, sec_id, 0, "D", 1, self.today_dt_unix, True)

                # # Fetch peer comparison data for chart data
                # peer_1_sym = peer_comparison_data.get('data', [{}])[0].get('Sym', '') if peer_comparison_data else ''
                # peer_2_sym = peer_comparison_data.get('data', [{}])[1].get('Sym', '') if peer_comparison_data else ''
                # peer_3_sym = peer_comparison_data.get('data', [{}])[2].get('Sym', '') if peer_comparison_data else ''
                # peer_4_sym = peer_comparison_data.get('data', [{}])[3].get('Sym', '') if peer_comparison_data else ''
                # peer_5_sym = peer_comparison_data.get('data', [{}])[4].get('Sym', '') if peer_comparison_data else ''

                # peer_1_sid = peer_comparison_data.get('data', [{}])[0].get('Sid', '') if peer_comparison_data else ''
                # peer_2_sid = peer_comparison_data.get('data', [{}])[1].get('Sid', '') if peer_comparison_data else ''
                # peer_3_sid = peer_comparison_data.get('data', [{}])[2].get('Sid', '') if peer_comparison_data else ''
                # peer_4_sid = peer_comparison_data.get('data', [{}])[3].get('Sid', '') if peer_comparison_data else ''
                # peer_5_sid = peer_comparison_data.get('data', [{}])[4].get('Sid', '') if peer_comparison_data else ''

                # peer_1_exch = peer_comparison_data.get('data', [{}])[0].get('Exch', '') if peer_comparison_data else ''
                # peer_2_exch = peer_comparison_data.get('data', [{}])[1].get('Exch', '') if peer_comparison_data else ''
                # peer_3_exch = peer_comparison_data.get('data', [{}])[2].get('Exch', '') if peer_comparison_data else ''
                # peer_4_exch = peer_comparison_data.get('data', [{}])[3].get('Exch', '') if peer_comparison_data else ''
                # peer_5_exch = peer_comparison_data.get('data', [{}])[4].get('Exch', '') if peer_comparison_data else ''

                # peer_1_seg = peer_comparison_data.get('data', [{}])[0].get('Seg', '') if peer_comparison_data else ''
                # peer_2_seg = peer_comparison_data.get('data', [{}])[1].get('Seg', '') if peer_comparison_data else ''
                # peer_3_seg = peer_comparison_data.get('data', [{}])[2].get('Seg', '') if peer_comparison_data else ''
                # peer_4_seg = peer_comparison_data.get('data', [{}])[3].get('Seg', '') if peer_comparison_data else ''
                # peer_5_seg = peer_comparison_data.get('data', [{}])[4].get('Seg', '') if peer_comparison_data else ''

                # peer_1_inst = peer_comparison_data.get('data', [{}])[0].get('Inst', '') if peer_comparison_data else ''
                # peer_2_inst = peer_comparison_data.get('data', [{}])[1].get('Inst', '') if peer_comparison_data else ''
                # peer_3_inst = peer_comparison_data.get('data', [{}])[2].get('Inst', '') if peer_comparison_data else ''
                # peer_4_inst = peer_comparison_data.get('data', [{}])[3].get('Inst', '') if peer_comparison_data else ''
                # peer_5_inst = peer_comparison_data.get('data', [{}])[4].get('Inst', '') if peer_comparison_data else ''

                # # Fetch last five years chart data for peer comparison stocks
                # last_five_years_chart_data_peer = {}
                # peer_chart_params = [
                #     (peer_1_exch, peer_1_sym, peer_1_seg, peer_1_inst, peer_1_sid, 0, "D", 1, self.today_dt_unix, True),
                #     (peer_2_exch, peer_2_sym, peer_2_seg, peer_2_inst, peer_2_sid, 0, "D", 1, self.today_dt_unix, True),
                #     (peer_3_exch, peer_3_sym, peer_3_seg, peer_3_inst, peer_3_sid, 0, "D", 1, self.today_dt_unix, True),
                #     (peer_4_exch, peer_4_sym, peer_4_seg, peer_4_inst, peer_4_sid, 0, "D", 1, self.today_dt_unix, True),
                #     (peer_5_exch, peer_5_sym, peer_5_seg, peer_5_inst, peer_5_sid, 0, "D", 1, self.today_dt_unix, True)
                # ]

                # for peer_params in peer_chart_params:
                #     peer_exch, peer_sym, peer_seg, peer_inst, peer_sid, peer_exp_code, peer_interval, peer_start, peer_end, peer_delivery_per = peer_params
                #     if peer_sym:  # Only fetch if symbol exists
                #         last_five_years_chart_data_peer[peer_sym] = self._fetch_last_five_years_chart_data(
                #             peer_exch, peer_sym, peer_seg, peer_inst, peer_sid, peer_exp_code, peer_interval, peer_start, peer_end, peer_delivery_per
                #         )

                # # Fetch chart data for indices (NIFTY 50, NIFTY 500, etc.)
                # index_chart_params = [
                #     ("IDX", "NIFTY", "I", "IDX", 13, 0, "D", 1, self.today_dt_unix, True),  # NIFTY 50
                #     ("IDX", "NIFTY 500", "I", "IDX", 19, 0, "D", 1, self.today_dt_unix, True),  # NIFTY 500
                #     ("IDX", "NIFTY MIDCAP 150", "I", "IDX", 20, 0, "D", 1, self.today_dt_unix, True),  # NIFTY MIDCAP 150
                #     ("IDX", "NIFTY SMALLCAP 250", "I", "IDX", 3, 0, "D", 1, self.today_dt_unix, True),  # NIFTY SMALLCAP 250
                #     ("IDX", "NIFTY TOTAL MKT", "I", "IDX", 443, 0, "D", 1, self.today_dt_unix, True)  # NIFTY TOTAL MARKET
                # ]

                # last_five_years_chart_data_peer_index = {}
                # for index_params in index_chart_params:
                #     idx_exch, idx_sym, idx_seg, idx_inst, idx_sec_id, idx_exp_code, idx_interval, idx_start, idx_end, idx_delivery_per = index_params
                #     last_five_years_chart_data_peer_index[idx_sym] = self._fetch_last_five_years_chart_data(
                #         idx_exch, idx_sym, idx_seg, idx_inst, idx_sec_id, idx_exp_code, idx_interval, idx_start, idx_end, idx_delivery_per
                #     )

                # # Fetch multi-timeframe chart data for indices
                # multi_timeframe_chart_data = self._fetch_multi_timeframe_chart_data([13, 19, 20, 3, 443])  # SecIds for indices

                # Collect results
                api_results = {}
                for key, future in futures.items():
                    try:
                        api_results[key] = future.result()
                    except Exception as e:
                        logger.error(f"Failed to fetch {key} for {symbol}: {str(e)}")
                        api_results[key] = None
            
            
            
            # # Create the complete raw data structure (like single_stock_data.json)
            # raw_data = {
            #     **stock,  # Include all base stock info (DispSym, Exch, High1Yr, etc.)
            #     "symbol": symbol,
            #     "scrape_timestamp": datetime.now(),
            #     "cache_valid_until": datetime.now() + timedelta(hours=24),
            #     "time_sensitive_updated_at": datetime.now(),
            #     "time_sensitive_valid_until": datetime.now() + timedelta(hours=1),
                
            #     # Raw API data sections
            #     "about_company": about_company,
            #     "peer_comparison": api_results.get("peer_comparison"),
            #     "analyst_ratings": api_results.get("analyst_ratings"),
            #     "announcements": api_results.get("announcements"),
            #     "latest_announcements": api_results.get("latest_announcements"),
            #     "live_news_data": api_results.get("live_news_data"),
            #     "dividend_data": api_results.get("dividend_data"),
            #     "fundamental_data": api_results.get("fundamental_data"),
            #     "forecast_data_Q": api_results.get("forecast_data_Q"),
            #     "forecast_data_A": api_results.get("forecast_data_A"),
            #     "corporate_action_data": api_results.get("corporate_action_data"),
            #     "company_filings_data": api_results.get("company_filings_data"),
            #     "mutual_fund_holdings_data": api_results.get("mutual_fund_holdings_data"),
            #     "mutual_fund_transaction_data": api_results.get("mutual_fund_transaction_data")
            # }
            if company_data and peer_comparison_data and analyst_ratings_data:
                    stock_info = stock.copy()
                    # Safe access to company data
                    company_data_list = company_data.get('data', [])
                    stock_info['about_company'] = company_data_list[0] if company_data_list else {}
                    stock_info['peer_comparison'] = peer_comparison_data.get('data', [])
                    stock_info['analyst_ratings'] = analyst_ratings_data.get('data', [])
                    stock_info['announcements'] = announcements_data.get('data', [])
                    stock_info['latest_announcements'] = latest_announcements_data.get('data', [])
                    stock_info['dividend_data'] = dividend_data.get('data', [])
                    stock_info['fundamental_data'] = fundamental_data.get('data', []) if fundamental_data else []
                    stock_info['forecast_data_Q'] = forecast_data_Q.get('data', []) if forecast_data_Q else []
                    stock_info['forecast_data_A'] = forecast_data_A.get('data', []) if forecast_data_A else []
                    stock_info['corporate_action_data'] = corporate_action_data.get('data', []) if corporate_action_data else []
                    stock_info['company_filings_data'] = company_filings_data.get('data', []) if company_filings_data else []
                    # stock_info['mutual_fund_holdings_data'] = mutual_fund_holdings_data.get('data', []) if mutual_fund_holdings_data else []
                    # stock_info['mutual_fund_transaction_data'] = mutual_fund_transaction_data.get('data', []) if mutual_fund_transaction_data else []
                    stock_info['live_news_data'] = live_news_data.get('data', []) if live_news_data else []

                    # Safe access to fundamental_data with proper empty list handling
                    fundamental_data_list = stock_info.get('fundamental_data', [])
                    fundamental_data_item = fundamental_data_list[0] if fundamental_data_list else {}
                    
                    balance_sheet_consolidated = fundamental_data_item.get('bs_c', {})
                    balance_sheet_standalone = fundamental_data_item.get('bs_s', {})
                    cash_flow_consolidated = fundamental_data_item.get('cF_c', {})
                    cash_flow_standalone = fundamental_data_item.get('cF_s', {})
                    financial_results_quarterly_consolidated = fundamental_data_item.get('incomeStat_cq', {})
                    financial_results_annual_consolidated = fundamental_data_item.get('incomeStat_cy', {})
                    financial_results_quarterly_standalone = fundamental_data_item.get('incomeStat_sq', {})
                    financial_results_annual_standalone = fundamental_data_item.get('incomeStat_sy', {})
                    net_profit_standalone = fundamental_data_item.get('rNp_s', {})
                    share_holders_equity = fundamental_data_item.get('sHp', {})

                    stock_info['balance_sheet_consolidated'] = parallel_format_financial_data(balance_sheet_consolidated, report_type="bs_c")
                    stock_info['balance_sheet_standalone'] = parallel_format_financial_data(balance_sheet_standalone, report_type="bs_s")
                    stock_info['cash_flow_consolidated'] = parallel_format_financial_data(cash_flow_consolidated, report_type="cF_c")
                    stock_info['cash_flow_standalone'] = parallel_format_financial_data(cash_flow_standalone, report_type="cF_s")
                    stock_info['financial_results_quarterly_consolidated'] = parallel_format_financial_data(financial_results_quarterly_consolidated, report_type="incomeStat_cq")
                    stock_info['financial_results_annual_consolidated'] = parallel_format_financial_data(financial_results_annual_consolidated, report_type="incomeStat_cy")
                    stock_info['financial_results_quarterly_standalone'] = parallel_format_financial_data(financial_results_quarterly_standalone, report_type="incomeStat_sq")
                    stock_info['financial_results_annual_standalone'] = parallel_format_financial_data(financial_results_annual_standalone, report_type="incomeStat_sy")
                    stock_info['net_profit_standalone'] = parallel_format_financial_data(net_profit_standalone, report_type="rNp_s")
                    stock_info['share_holders_equity'] = parallel_format_financial_data(share_holders_equity, report_type="sHp")
                    stock_info['formatted_mutual_fund_holdings_data'] = optimize_format_mutual_fund_data(mutual_fund_holdings_data)
                    stock_info['formatted_mutual_fund_transaction_data'] = optimize_format_mutual_fund_data(mutual_fund_transaction_data)
                    
                    # # Format chart data
                    # stock_info['formatted_last_five_years_chart'] = parallel_format_stock_chart_data(last_five_years_chart_data)
                    # stock_info['formatted_last_five_years_chart_peer'] = parallel_format_stock_chart_data(last_five_years_chart_data_peer)
                    # stock_info['formatted_last_five_years_chart_peer_index'] = parallel_format_stock_chart_data(last_five_years_chart_data_peer_index)

                
            # Save to MongoDB
            if self._save_or_update_stock_data(symbol, stock_info):
                logger.info(f"Successfully scraped and saved raw data for symbol: {symbol}")
                return stock_info
            else:
                logger.error(f"Failed to save data for symbol: {symbol}")
                return stock_info  # Return data even if save failed
                
        except Exception as e:
            logger.error(f"Error scraping symbol {symbol}: {str(e)}")
            return None

    def scrape_multiple_symbols(self, symbols: List[str], max_workers: int = 4) -> Dict[str, Optional[Dict]]:
        """
        Scrape data for multiple stock symbols with 24-hour caching.
        
        Args:
            symbols (list): List of stock symbols to scrape
            max_workers (int): Number of parallel workers for symbol processing
        
        Returns:
            dict: Dictionary with symbols as keys and their scraped data as values
        """
        try:
            logger.info(f"Starting scrape for {len(symbols)} symbols: {', '.join(symbols)}")
            
            results = {}
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.scrape_single_symbol, symbol): symbol 
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        results[symbol] = result
                        if result:
                            logger.info(f"✅ Successfully scraped: {symbol}")
                        else:
                            logger.error(f"❌ Failed to scrape: {symbol}")
                    except Exception as e:
                        logger.error(f"Exception scraping {symbol}: {str(e)}")
                        results[symbol] = None
            
            successful_count = sum(1 for v in results.values() if v is not None)
            logger.info(f"Scraping completed: {successful_count}/{len(symbols)} symbols successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in scrape_multiple_symbols: {str(e)}")
            return {}

    # def _format_stock_data(self, symbol: str, stock: Dict, about_company: Dict, **api_data) -> Dict:
    #     """
    #     Format the scraped data into the required structure.
        
    #     Args:
    #         symbol (str): Stock symbol
    #         stock (dict): Reference stock data
    #         about_company (dict): Company data from API
    #         **api_data: Various API responses
        
    #     Returns:
    #         dict: Formatted stock data
    #     """
    #     try:
    #         # Base structure from about_company
    #         formatted_data = about_company.copy()

    #         # Add peer comparison data
    #         if api_data.get('peer_comparison') and api_data['peer_comparison'].get('data'):
    #             formatted_data['peer_comparison'] = api_data['peer_comparison']['data']
    #         else:
    #             formatted_data['peer_comparison'] = []
            
    #         # Add analyst ratings
    #         formatted_data['analyst_ratings'] = api_data.get('analyst_ratings', {})
            
    #         # Add announcements
    #         if api_data.get('announcements') and api_data['announcements'].get('data'):
    #             formatted_data['announcements'] = api_data['announcements']['data']
    #         else:
    #             formatted_data['announcements'] = []
            
    #         # Add latest announcements  
    #         formatted_data['latest_announcements'] = api_data.get('latest_announcements')
            
    #         # Add live news data
    #         formatted_data['live_news_data'] = api_data.get('live_news_data', {})
            
    #         # Add additional data fields
    #         formatted_data['dividend_data'] = api_data.get('dividend_data', {})
    #         formatted_data['fundamental_data'] = api_data.get('fundamental_data', {})
    #         formatted_data['forecast_data_Q'] = api_data.get('forecast_data_Q', {})
    #         formatted_data['forecast_data_A'] = api_data.get('forecast_data_A', {})
    #         formatted_data['corporate_action_data'] = api_data.get('corporate_action_data', {})
    #         formatted_data['company_filings_data'] = api_data.get('company_filings_data', {})
    #         formatted_data['mutual_fund_holdings_data'] = api_data.get('mutual_fund_holdings_data', {})
    #         formatted_data['mutual_fund_transaction_data'] = api_data.get('mutual_fund_transaction_data', {})
            
    #         # Add metadata
    #         current_time = datetime.now(timezone.utc).isoformat()
    #         formatted_data['symbol'] = symbol.upper()
    #         formatted_data['seosym'] = stock.get('Seosym', '')
    #         formatted_data['disp_sym'] = about_company.get('DispSym', '')
    #         formatted_data['url'] = stock.get('url', '')
            
    #         # Time-sensitive field timestamps (for cron updates)
    #         formatted_data['announcements_updated_at'] = current_time
    #         formatted_data['latest_announcements_updated_at'] = current_time  
    #         formatted_data['live_news_data_updated_at'] = current_time
            
    #         return formatted_data
            
    #     except Exception as e:
    #         logger.error(f"Error formatting data for {symbol}: {str(e)}")
    #         return {}

    def update_time_sensitive_data(self, symbol: str) -> bool:
        """
        Update only time-sensitive fields (announcements, latest_announcements, live_news_data)
        This method is designed for cron job updates every 60 minutes.
        
        Args:
            symbol (str): Stock symbol to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Updating time-sensitive data for symbol: {symbol}")
            
            # Get existing document
            query = {"symbol": symbol.upper()}
            existing_doc = self.db_manager.mongo_db[self.collection_name].find_one(query)
            
            if not existing_doc:
                logger.error(f"No existing document found for symbol: {symbol}")
                return False
            
            # Get ISIN and symbol for API calls
            isin = existing_doc.get('Isin', '')
            stock_symbol = existing_doc.get('Sym', '')
            
            if not isin:
                logger.error(f"No ISIN found for symbol: {symbol}")
                return False
            
            # Fetch updated time-sensitive data (save raw responses)
            current_time = datetime.now()
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    "announcements": executor.submit(self._fetch_announcements_data, isin),
                    "latest_announcements": executor.submit(self._fetch_latest_announcements_data, isin),
                    "live_news_data": executor.submit(self._fetch_live_news_data_advanced, stock_symbol)
                }
                
                # Collect raw results
                update_data = {
                    "time_sensitive_updated_at": current_time,
                    "time_sensitive_valid_until": current_time + timedelta(hours=1)
                }
                
                for key, future in futures.items():
                    try:
                        result = future.result()
                        # Save raw API response without formatting
                        update_data[key] = result
                        logger.info(f"Updated {key} for {symbol}")
                    except Exception as e:
                        logger.error(f"Failed to fetch {key} for {symbol}: {str(e)}")
                        update_data[key] = None
            
            # Update only the time-sensitive fields
            if update_data:
                result = self.db_manager.mongo_db[self.collection_name].update_one(
                    query, {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(f"Successfully updated time-sensitive data for symbol: {symbol}")
                    return True
                else:
                    logger.error(f"No documents were modified for symbol: {symbol}")
                    return False
            else:
                logger.error(f"No update data collected for symbol: {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating time-sensitive data for {symbol}: {str(e)}")
            return False

    def update_all_time_sensitive_data(self, max_workers: int = 5) -> Dict[str, int]:
        """
        Update time-sensitive data for all symbols in the database.
        This method is designed for cron job execution every 60 minutes.
        
        Args:
            max_workers (int): Number of parallel workers for updates
            
        Returns:
            dict: Summary of update results
        """
        try:
            logger.info("Starting time-sensitive data update for all symbols")
            
            # Get all unique symbols from database
            symbols = self.db_manager.mongo_db[self.collection_name].distinct("symbol")
            
            if not symbols:
                logger.warning("No symbols found in database")
                return {"total": 0, "successful": 0, "failed": 0}
            
            logger.info(f"Found {len(symbols)} symbols to update")
            
            results = {"total": len(symbols), "successful": 0, "failed": 0}
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.update_time_sensitive_data, symbol): symbol 
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        success = future.result()
                        if success:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                    except Exception as e:
                        logger.error(f"Exception updating {symbol}: {str(e)}")
                        results["failed"] += 1
            
            logger.info(f"Time-sensitive update completed: {results['successful']}/{results['total']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error in update_all_time_sensitive_data: {str(e)}")
            return {"total": 0, "successful": 0, "failed": 0}


# Legacy function for backward compatibility
# Legacy function for backward compatibility
def main(symbol):
    """
    Legacy main function for backward compatibility.
    Ensures symbol is uppercase before scraping.
    """
    symbol = symbol.upper()  # Normalize the symbol to uppercase
    
    logger.info("Starting stock data scraping process...")
    start_time = time.time()

    logger.info(f"Scraping data for symbol: {symbol}")
    
    controller = ScanXStockDataController()
    single_stock_data = controller.scrape_single_symbol(symbol)

    end_time = time.time()
    total_time = end_time - start_time

    if single_stock_data:
        # with open('single_stock_data.json', 'w') as f:
        #     json.dump(single_stock_data, f, indent=4, default=str)

        # logger.info(f"Single stock data for '{symbol}' saved to 'single_stock_data.json'.")
        logger.info(f"Total scraping process time: {total_time:.2f} seconds")
        return single_stock_data
    else:
        logger.error(f"Failed to scrape data for symbol '{symbol}'.")
        logger.error(f"Process completed in: {total_time:.2f} seconds (failed)")
        return None


if __name__ == "__main__":
    main(symbol='')  # or any valid NSE symbol

