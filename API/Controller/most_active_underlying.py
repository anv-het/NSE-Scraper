"""
NSE Most Active underlying Controller
Handles scraping and data management for NSE most active underlying data
"""

import asyncio
from typing import Optional, Dict, Any
import requests

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response_n, create_error_response
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import HEADERS_URL_MOST_ACTIVE_UNDERLYING
from Services.get_nse_cookies import get_nse_cookies

logger = get_logger(__name__)


class NSEMostActiveUnderlyingController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.cookies = None
        self.most_active_underlying_api_url = "https://www.nseindia.com/api/live-analysis-most-active-underlying"

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
            default_headers = load_nse_headers(HEADERS_URL_MOST_ACTIVE_UNDERLYING)
            if not default_headers:
                logger.error("Failed to load default headers.")
                return None

            if headers is None:
                headers = {}
            headers.update(default_headers)

            cookies = self.get_cookies()
            if not cookies:
                logger.error("Failed to retrieve NSE cookies.")
                return None

            response = requests.get(url, headers=headers, cookies=cookies)
            if response.status_code != HTTP_STATUS.OK:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None
        

    async def scrap_most_active_underlying(self) -> Dict[str, Any]:
        """Scrapes the most active underlying data from NSE."""
        try:
            data_underlying = self._make_request(self.most_active_underlying_api_url)
            if not data_underlying:
                return create_error_response("Failed to fetch most active underlying data.")

            return create_success_response_n("Most active underlying data fetched successfully.", data_underlying)

        except Exception as e:
            logger.error(f"Error while scraping most active underlying: {str(e)}")
            return create_error_response(f"Error while scraping most active underlying: {str(e)}")
        
# if __name__ == "__main__":
#     controller = NSEMostActiveUnderlyingController()
#     result = asyncio.run(controller.scrap_most_active_underlying())
#     print(result)
