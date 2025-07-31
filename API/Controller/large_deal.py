"""
NSE Large Deal Controller
Handles scraping and data management for large deals
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import HEADERS_URL_LARGE_DEALS
from Utils.data_formatter import NSEDataFormatter
from Services.get_nse_cookies import get_nse_cookies

logger = get_logger(__name__)

class NSELargeDealsController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.large_deals_headers_url = HEADERS_URL_LARGE_DEALS
        self.cookies = None
        self.large_deals_api_url = "https://www.nseindia.com/api/snapshot-capital-market-largedeal"

    def get_cookies(self) -> Optional[Dict[str, str]]:
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None
        
    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        try:
            default_headers = load_nse_headers(self.large_deals_headers_url)
            if not default_headers:
                logger.error("Failed to load default headers.")
                return None

            if headers is None:
                headers = {}
            headers.update(default_headers)

            cookies = self.get_cookies()
            if not cookies:
                logger.error("Failed to retrieve cookies.")
                return None

            response = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=configure.getint('SCRAPING', 'TIMEOUT')
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None

    async def scrap_large_deals(self) -> Dict[str, Any]:
        try:
            data = self._make_request(self.large_deals_api_url)
            if not data:
                return create_error_response("Failed to fetch large deals data", HTTP_STATUS.INTERNAL_SERVER_ERROR)

            # ✅ Format raw data using formatter
            formatted_data = NSEDataFormatter.format_large_deals(data)

            if not formatted_data:
                return create_success_response([], "No large deals available to format")

            # ✅ Optional: Save to MongoDB
            self.db.save_data(formatted_data, "nse_large_deals")

            return create_success_response(formatted_data, "Large deals data fetched and formatted successfully")

        except Exception as e:
            logger.error(f"Error in scrap_large_deals: {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)


        
     
