"""
NSE New LISTINGS Controller
Handles scraping and data management for new stock listings
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
    HEADERS_URL_NEW_LISTINGS
)
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)


class NSEPriceBandHittersController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.new_listing_headers_url = HEADERS_URL_NEW_LISTINGS
        self.cookies = None
        self.new_listing_api_url = "https://www.nseindia.com/api/new-listing-today-ipo?index=NewListing"
        self.special_preopen_api_url = "https://www.nseindia.com/api/special-preopen-listing"
        self.recent_listing_api_url = "https://www.nseindia.com/api/new-listing-today?index=RecentListing"

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
            default_headers = load_nse_headers(self.new_listing_headers_url)
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
        
    def scrap_new_listings(self) -> Dict[str, Any]:
        """Scrapes new stock listings data from the NSE API."""
        try:
            url = self.new_listing_api_url
            logger.info(f"Fetching data from {url}")

            response_data = self._make_request(url)
            if not response_data:
                return create_error_response("Failed to fetch new listings data.")

            data = response_data.get("data", [])
            if not data:
                logger.info("No new listings found.")
                return create_success_response("No new listings found.", data={})

            return create_success_response("New listings fetched successfully.", data=data)

        except Exception as e:
            logger.error(f"Error while scraping new listings: {str(e)}")
            return create_error_response(f"Error while scraping new listings: {str(e)}")

    def scrap_special_preopen_listings(self) -> Dict[str, Any]:
        """Scrapes special pre-open listings data from the NSE API."""
        try:
            url = self.special_preopen_api_url
            logger.info(f"Fetching data from {url}")

            response_data = self._make_request(url)
            if not response_data:
                return create_error_response("Failed to fetch special pre-open listings data.")

            data = response_data.get("data", [])
            print(f"Special Pre-Open Listings Data: {data}")
            if not data:
                logger.info("No special pre-open listings found.")
                return create_success_response("No special pre-open listings found.", data={})

            return create_success_response("Special pre-open listings fetched successfully.", data=data)

        except Exception as e:
            logger.error(f"Error while scraping special pre-open listings: {str(e)}")
            return create_error_response(f"Error while scraping special pre-open listings: {str(e)}")

    def scrap_recent_listings(self) -> Dict[str, Any]:
        """Scrapes recent stock listings data from the NSE API."""
        try:
            url = self.recent_listing_api_url
            logger.info(f"Fetching data from {url}")

            response_data = self._make_request(url)
            if not response_data:
                return create_error_response("Failed to fetch recent listings data.")

            data = response_data.get("data", [])
            if not data:
                logger.info("No recent listings found.")
                return create_success_response("No recent listings found.", data={})

            return create_success_response("Recent listings fetched successfully.", data)

        except Exception as e:
            logger.error(f"Error while scraping recent listings: {str(e)}")
            return create_error_response(f"Error while scraping recent listings: {str(e)}")


# if __name__ == "__main__":
#     controller = NSEPriceBandHittersController()
#     new_listings_result = controller.scrap_new_listings()
#     print(new_listings_result)

#     special_preopen_result = controller.scrap_special_preopen_listings()
#     print(special_preopen_result)

#     recent_listings_result = controller.scrap_recent_listings()
#     print(recent_listings_result)
