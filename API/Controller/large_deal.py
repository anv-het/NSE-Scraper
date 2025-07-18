"""
NSE Large Deal Controller
Handles scraping and data management for large deals
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
    HEADERS_URL_LARGE_DEALS
)
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

    def scrap_large_deals(self) -> Dict[str, Any]:
        """Scrapes large deals data from NSE."""
        try:
            url = self.large_deals_api_url
            logger.info(f"Scraping large deals from: {url}")
            response_data = asyncio.run(self._make_request(url))
           
            if not response_data:
                logger.error("No data received from large deals API.")
                return create_error_response(
                    "Failed to fetch large deals data from NSE API."
                )
            
            data = response_data.get("data", [])
            if not data:
                logger.info("No large deals found.")
                return create_success_response(
                    data=[],
                    message="No large deals data available."
                )
            
            return create_success_response(
                data,
                message="Large deals data retrieved successfully."
            )

        except Exception as e:
            logger.error(f"Error while scraping large deals: {str(e)}")
            return create_error_response(
                "An error occurred while scraping large deals data."
            )
        
# if __name__ == "__main__":
#     controller = NSELargeDealsController()
#     result = controller.scrap_large_deals()
    
#     # Print raw result for debugging
#     print("Result:", result)
    
#     if result.get("success"):
#         print("✅ Large Deals data scraped successfully!")
#     else:
#         print("❌ Failed to scrape Large Deals data.")
