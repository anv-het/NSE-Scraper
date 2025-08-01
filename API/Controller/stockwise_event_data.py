# stockwise_event_data.py

import asyncio
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests

from Utils.data_formatter import NSEDataFormatter
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response, create_success_response_n
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import (
    HEADERS_URL_EVENT_DATA
    )
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)

class StockwiseEventDataController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.event_data_headers_url = HEADERS_URL_EVENT_DATA
        self.cookies = None
        self.event_data_api_url = "https://www.nseindia.com/api/top-corp-info?symbol={symbol}&market=equities"

    def get_cookies(self) -> Optional[Dict[str, str]]:
        """Fetches NSE cookies for session management."""
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None
        
    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Makes a GET request to the specified URL with the provided headers."""
        try:
            default_headers = load_nse_headers(self.event_data_headers_url)
            if not default_headers:
                logger.error("Failed to load default headers.")
                return None

            if headers is None:
                headers = {}
            headers.update(default_headers)

            cookies = self.get_cookies()
            if not cookies:
                logger.error("No cookies available for request.")
                return None

            response = requests.get(url, headers=headers, cookies=cookies)
            if response.status_code == HTTP_STATUS.OK:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None
    
    #for the current implementation, we are ussing static symbol as a TCS

    # symbol = "TCS"

    async def scrape_stockwise_event_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Scrapes stockwise event data from the NSE API."""
        try:
            symbol = symbol.upper()
            url = self.event_data_api_url.format(symbol=symbol)
            data = self._make_request(url)

            if not data:
                logger.error(f"No data found for symbol: {symbol}")
                return None 

            # ✅ Wrap in list since formatter expects a list of dicts
            stock_data_list = [data]

            # Format data
            formated_data = NSEDataFormatter.format_stocks_wise_market_event(stock_data_list)

            if not formated_data:
                logger.error(f"No formatted data found for symbol: {symbol}")
                return None

            # Save to MongoDB
            if not self.db.save_stockwise_event_data(formated_data):
                logger.error(f"Failed to save data for symbol: {symbol}")
                return None

            logger.info(f"Data for {symbol} saved successfully.")
            return formated_data

        except Exception as e:
            logger.error(f"Error scraping stockwise event data for {symbol}: {str(e)}")
            return None



