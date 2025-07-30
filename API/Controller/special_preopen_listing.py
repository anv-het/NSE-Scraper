"""
# special_preopen_listing.py
Handles scraping and data management for special pre-open stock listings
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests

from Utils.data_formatter import NSEDataFormatter
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_success_response_n, create_error_response
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import (
    HEADERS_URL_NEW_LISTINGS
)
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)


class NSESpecialPreopenListingsController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.new_listing_headers_url = HEADERS_URL_NEW_LISTINGS
        self.cookies = None
        self.special_preopen_api_url = "https://www.nseindia.com/api/special-preopen-listing"

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

    async def scrap_special_preopen_listings(self) -> Dict[str, Any]:
        """Scrapes special pre-open listings."""
        try:
            preopen_data = self._make_request(self.special_preopen_api_url)

            # format data
            formatted_data = NSEDataFormatter.format_special_preopen_data(preopen_data)

            # Save to MongoDB
            self.db.save_data(formatted_data, "nse_special_preopen_listings")

            return create_success_response(formatted_data, "Special pre-open listings fetched successfully.")
        
        except Exception as e:
            logger.error(f"Error while scraping special pre-open listings: {str(e)}")
            return create_error_response(f"Error while scraping special pre-open listings: {str(e)}")





