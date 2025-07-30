"""
NSE Most Active Contracts Controller
Handles scraping and data management for NSE most active contracts data
"""


import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import requests

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response, create_success_response_n
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers
from Constant.http import HTTP_STATUS
from Constant.general import HEADERS_URL_MOST_ACTIVE_CONTRACTS
from Services.get_nse_cookies import get_nse_cookies
from Utils.data_formatter import NSEDataFormatter


logger = get_logger(__name__)


class NSEMostActiveContractsController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.nse_headers = load_nse_headers()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.cookies = None
        self.most_active_contracts_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=contracts&limit=50"
        self.most_active_futures_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=futures"
        self.most_active_options_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=options&limit=50"
        self.most_active_options_api_url_20 = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=options&limit=20"
        self.most_active_puts_index_vol_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=puts-index-vol"
        self.most_active_calls_stocks_vol_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=calls-stocks-vol"
        self.most_active_puts_stocks_vol_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=puts-stocks-vol"
        self.most_active_oi_api_url = "https://www.nseindia.com/api/snapshot-derivatives-equity?index=oi"


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
        """Makes a GET request to the specified URL with the given headers."""
        try:
            default_headers = load_nse_headers(HEADERS_URL_MOST_ACTIVE_CONTRACTS)
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
                cookies=cookies
            )

            if response.status_code == HTTP_STATUS.OK:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None
        
    async def scrap_most_active_contracts(self) -> Dict[str, Any]:
        """Scrapes the most active contracts data from NSE."""
        try:
            urls = [
                self.most_active_contracts_api_url,
                self.most_active_futures_api_url,
                self.most_active_options_api_url,
                self.most_active_options_api_url_20,
                self.most_active_puts_index_vol_api_url,
                self.most_active_calls_stocks_vol_api_url,
                self.most_active_puts_stocks_vol_api_url,
                self.most_active_oi_api_url
            ]

            results = await asyncio.gather(*[asyncio.to_thread(self._make_request, url) for url in urls])
            
            data = {
                "most_active_contract": results[0],
                "most_active_futures": results[1],
                "most_active_options": results[2],
                "most_active_options_20": results[3],
                "most_active_puts_index_vol": results[4],
                "most_active_calls_stocks_vol": results[5],
                "most_active_puts_stocks_vol": results[6],
                "most_active_oi": results[7],
            }
            
            # ✅ Format raw data using formatter
            formatted_data = NSEDataFormatter.format_most_active_contracts(data)
            
            # ✅ Optional: Save to MongoDB
            self.db_manager.save_data(formatted_data, "nse_most_active_contracts")
            
            return create_success_response_n(formatted_data, "Most active contracts data scraped successfully")

        except Exception as e:
            logger.error(f"Error occurred while scraping most active contracts: {str(e)}")
            return create_error_response("Error occurred while scraping most active contracts.")


# if __name__ == "__main__":
#     controller = NSEMostActiveContractsController()
#     result = asyncio.run(controller.scrap_most_active_contracts())
#     print(result)