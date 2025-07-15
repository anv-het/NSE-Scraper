"""
NSE Price Band Hitters Controller
Handles scraping and data management for stocks hitting price bands
"""
import requests
from typing import Optional, Dict, Any
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers
from Constant.general import (
    HEADERS_URL_UPPER_BAND_HITTERS,
    HEADERS_URL_LOWER_BAND_HITTERS,
    HEADERS_URL_BOTH_BAND_HITTERS
)

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response
from Utils.utilities_functions import clean_numeric_value

logger = get_logger(__name__)

class NSEPriceBandHittersController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.upper_band_headers_url = HEADERS_URL_UPPER_BAND_HITTERS
        self.cookies = None
        self.band_hitter_api_url = "https://www.nseindia.com/api/live-analysis-price-band-hitter"
        
    def get_cookies(self) -> Optional[Dict[str, str]]:
        """Fetches NSE cookies for session management."""
        if not self.cookies:
            self.cookies = load_nse_headers()
            if not self.cookies:
                logger.error("Failed to load NSE cookies.")
                return None
        return self.cookies
    
    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Makes a GET request to the specified URL with the provided headers."""
        try:
            default_headers = load_nse_headers(self.upper_band_headers_url)
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
                timeout=configure.getint("NSE", "timeout")
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None

    def scrap_price_band_hitters(self) -> Dict[str, Any]:
        """Scrapes price band hitters data from the NSE API."""
        try:
            url = self.band_hitter_api_url
            logger.info(f"Fetching data from {url}")

            data = self._make_request(url)

            if data is None:
                return create_error_response("Failed to fetch data from the API.")
            
            if "upper" not in data or "lower" not in data or "count" not in data or "both" not in data:
                logger.error("Invalid data structure received from the API.")
                return create_error_response("Invalid data structure received from the API.")

            upper_band_data = data.get("upper", {})
            lower_band_data = data.get("lower", {})
            both_band_data = data.get("both", {})
            count_data = data.get("count", {})

            print(f"Upper Band Hitters: =============== {upper_band_data}")
            print(f"Lower Band Hitters: =============== {lower_band_data}")
            print(f"Both Band Hitters: =============== {both_band_data}")
            print(f"Count Data: =============== {count_data}")

            if not upper_band_data and not lower_band_data and not both_band_data:
                logger.info("No price band hitters found.")
                return create_success_response("No price band hitters found.", data={})

            # ✅ Return proper success response
            return create_success_response(
                message="Fetched price band hitters successfully.",
                data={
                    "upper": upper_band_data,
                    "lower": lower_band_data,
                    "both": both_band_data,
                    "count": count_data
                }
            )

        except Exception as e:
            logger.error(f"Error while scraping price band hitters: {str(e)}")
            return create_error_response(f"Error while scraping price band hitters: {str(e)}")

if __name__ == "__main__":
    controller = NSEPriceBandHittersController()
    result = controller.scrap_price_band_hitters()
    print(result)
