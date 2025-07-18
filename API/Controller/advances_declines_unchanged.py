"""
NSE Advance Decline Unchanged Data Controller
Handles scraping and data management for NSE advance, decline, and unchanged stock data
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import requests

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import HEADERS_URL_ADVANCE, HEADERS_URL_DECLINE, HEADERS_URL_UNCHANGED
from Services.get_nse_cookies import get_nse_cookies

logger = get_logger(__name__)



class NSEAdvancesDeclinesUnchangedController:

    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.cookies = None
        self.advance_api_url = "https://www.nseindia.com/api/live-analysis-advance"
        self.decline_api_url = "https://www.nseindia.com/api/live-analysis-decline"
        self.unchanged_api_url = "https://www.nseindia.com/api/live-analysis-unchanged"

    def get_cookies(self) -> Optional[Dict[str, str]]:
        """Fetches NSE cookies for session management."""
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None

    def make_request(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Makes an HTTP GET request to the specified URL."""
        try:

            if url == self.advance_api_url:
                default_headers = load_nse_headers(HEADERS_URL_ADVANCE)
            elif url == self.decline_api_url:
                default_headers = load_nse_headers(HEADERS_URL_DECLINE)
            elif url == self.unchanged_api_url:
                default_headers = load_nse_headers(HEADERS_URL_UNCHANGED)

            cookies = self.get_cookies()
            
            if not cookies:
                logger.error("Failed to retrieve NSE cookies.")
                return None
            
            response = requests.get(
                url,
                headers=default_headers,
                cookies=cookies,
                timeout=configure.getint('SCRAPING', 'TIMEOUT')
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None
        
    def scrap_advance_decline_unchanged(self) -> Dict[str, Any]:
        """Scrapes advance, decline, and unchanged data from NSE."""
        try:
            advance_data = self.make_request(self.advance_api_url)
            decline_data = self.make_request(self.decline_api_url)
            unchanged_data = self.make_request(self.unchanged_api_url)

            if not advance_data or not decline_data or not unchanged_data:
                return create_error_response(HTTP_STATUS.INTERNAL_SERVER_ERROR, "Failed to fetch data")

            return create_success_response({
                "advance": advance_data,
                "decline": decline_data,
                "unchanged": unchanged_data
            })

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return create_error_response(HTTP_STATUS.INTERNAL_SERVER_ERROR, str(e))
        

    async def async_scrap_advance_decline_unchanged(self) -> Dict[str, Any]:
        """Asynchronously scrapes advance, decline, and unchanged data from NSE."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.scrap_advance_decline_unchanged)
            return result
        except Exception as e:
            logger.error(f"Async scraping error: {str(e)}")
            return create_error_response(HTTP_STATUS.INTERNAL_SERVER_ERROR, str(e))
        
# if __name__ == "__main__":
#     controller = NSEAdvancesDeclinesUnchangedController()
#     result = asyncio.run(controller.async_scrap_advance_decline_unchanged())
#     print(result)