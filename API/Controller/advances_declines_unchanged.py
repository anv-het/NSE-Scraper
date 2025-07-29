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
from Utils.response import create_success_response_n, create_error_response
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
        """Scrapes and formats advance, decline, and unchanged data from NSE."""
        try:
            advance_data = self.make_request(self.advance_api_url)
            decline_data = self.make_request(self.decline_api_url)
            unchanged_data = self.make_request(self.unchanged_api_url)

            if not advance_data or not decline_data or not unchanged_data:
                return create_error_response(HTTP_STATUS.INTERNAL_SERVER_ERROR, "Failed to fetch data")

            formatted_data = self.format_nse_data(advance_data, decline_data, unchanged_data)

            # Optional: Save to MongoDB
            # self.db.save_data(formatted_data, "nse_adv_decl_unch")

            return create_success_response_n(
                data=formatted_data,
                message="Advance Decline and Unchanged data retrieved successfully"
            )

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return create_error_response(HTTP_STATUS.INTERNAL_SERVER_ERROR, str(e))

    def format_nse_data(
        self,
        advance_data: Dict[str, Any],
        decline_data: Dict[str, Any],
        unchanged_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format raw NSE advance, decline, and unchanged data into unified MongoDB-ready structure."""
        try:
            timestamp = advance_data.get("timestamp") or datetime.now().isoformat()

            # Optional: Extract individual counts from unchanged_data
            total_count = advance_data.get("advance", {}).get("count", {})

            def extract_data(data: Dict[str, Any], key: str) -> Dict[str, Any]:
                items = data.get(key, {}).get("data", [])
                return {
                    "data": [
                        {
                            "identifier": item.get("identifier"),
                            "symbol": item.get("symbol"),
                            "series": item.get("series"),
                            "marketType": item.get("marketType"),
                            "pchange": item.get("pchange"),
                            "change": item.get("change"),
                            "basePrice": item.get("basePrice"),
                            "previousClose": item.get("previousClose"),
                            "lastPrice": item.get("lastPrice"),
                            "totalTradedVolume": item.get("totalTradedVolume"),
                            "issuedCap": item.get("issuedCap"),
                            "totalTradedValue": item.get("totalTradedValue"),
                            "totalMarketCap": item.get("totalMarketCap")
                        }
                        for item in items
                    ]
                }

            return {
                "count": total_count,
                "Advances": extract_data(advance_data, "advance"),
                "Declines": extract_data(decline_data, "decline"),
                "Unchange": extract_data(unchanged_data, "Unchange")
            }

        except Exception as e:
            logger.error(f"Error formatting NSE data: {str(e)}")
            return {}

        
if __name__ == "__main__":
    controller = NSEAdvancesDeclinesUnchangedController()
    result = asyncio.run(controller.scrap_advance_decline_unchanged())
    print(result)
