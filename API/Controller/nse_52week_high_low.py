"""
NSE 52-Week High/Low Controller
Handles scraping and data management for 52-week high/low stocks
"""

import asyncio
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
    HEADERS_URL_52_WEEK_HIGH,
    HEADERS_URL_52_WEEK_LOW
)
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)


class NSE52WeekHighLowController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.high_headers_url = HEADERS_URL_52_WEEK_HIGH
        self.low_headers_url = HEADERS_URL_52_WEEK_LOW
        self.cookies = None
        self.high_api_url = "https://www.nseindia.com/api/live-analysis-data-52weekhighstock"
        self.low_api_url = "https://www.nseindia.com/api/live-analysis-data-52weeklowstock"

    def _get_cookies(self) -> Optional[Dict[str, str]]:
        """Get NSE cookies for authenticated requests."""
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None

    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        try:
            """Make a GET request to the specified URL with headers and cookies."""
            if url == self.high_api_url:
                default_headers = load_nse_headers(self.high_headers_url)
            elif url == self.low_api_url:
                default_headers = load_nse_headers(self.low_headers_url)
            else:
                default_headers = {}

            if headers:
                default_headers.update(headers)

            cookies = self._get_cookies()
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

    async def scrape_52_week_high_low(self) -> Dict[str, Any]:
        """Scrape both 52-week high and low stocks."""
        try:
            logger.info("Starting to scrape 52-week high and low stocks...")

            # Use asyncio.gather to fetch both high and low data concurrently
            urls = [
                self.high_api_url, 
                self.low_api_url
            ]
            
            
            # Await the results of the tasks
            results = await asyncio.gather(*[asyncio.to_thread(self._make_request, url) for url in urls])

            #unpack results
            high_data = results[0]
            low_data = results[1]

            if not high_data or not low_data:
                logger.error("Failed to fetch data for 52-week high or low stocks.")
                return create_error_response("Failed to fetch data", HTTP_STATUS.INTERNAL_SERVER_ERROR)
            
            data = {
                "52-week-high": high_data.get("data", []),
                "52-week-low": low_data.get("data", [])
            }

            # Optional: Print out the data for debugging
            # print("Data:", data)

            # Format the data before saving (ensure data is in expected format)
            formatted_data = NSEDataFormatter.format_52_week_high_low(data)

            # Save the formatted data to the database
            self.db.save_data(formatted_data, "nse_week_52_data")

            return create_success_response_n(data, "52-week high and low stocks data scraped successfully.")

        except Exception as e:
            logger.error(f"Error scraping 52-week high and low stocks: {str(e)}")
            return create_error_response("Error scraping data", HTTP_STATUS.INTERNAL_SERVER_ERROR)



if __name__ == "__main__":
    controller = NSE52WeekHighLowController()
    asyncio.run(controller.scrape_52_week_high_low())
    print("52-week high and low data refreshed successfully.")
