"""
NSE Scraper - Forthcoming Listings Controller
Handles scraping and data management for forthcoming stock listings
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import (
    HEADERS_URL_FORTHCOMING_LISTINGS
)
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)


class NSEForthcomingListingsController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.forthcoming_listings_headers_url = HEADERS_URL_FORTHCOMING_LISTINGS
        self.cookies = None
        self.forthcoming_listings_api_url = "https://www.nseindia.com/api/new-listing-today?index=ForthListing"

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
            default_headers = load_nse_headers(self.forthcoming_listings_headers_url)
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
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        
    async def scrap_forthcoming_listings(self) -> Dict[str, Any]:
        """Scrapes forthcoming stock listings data from the NSE API."""
        try:
            url = self.forthcoming_listings_api_url
            logger.info(f"Fetching data from {url}")
            response_data = await asyncio.to_thread(self._make_request, url)

            if not response_data or 'data' not in response_data:
                logger.error("Failed to fetch forthcoming listings data.")
                return create_error_response("Failed to fetch forthcoming listings data.")

            data = response_data.get("data", [])
            if not data:
                logger.info("No forthcoming listings found.")
                return create_success_response("No forthcoming listings found.", data)

            return create_success_response("Forthcoming listings fetched successfully.", data)

        except Exception as e:
            logger.error(f"Error while scraping forthcoming listings: {str(e)}")
            return create_error_response(f"Error while scraping forthcoming listings: {str(e)}")
    
# if __name__ == "__main__":
#     controller = NSEForthcomingListingsController()
#     result = asyncio.run(controller.scrap_forthcoming_listings())
#     print(result)
