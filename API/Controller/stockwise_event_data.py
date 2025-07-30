# stockwise_event_data.py

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
    HEADERS_URL_EVENT_DATA,
    DATA_RETENTION_DAYS
)
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)

class StockwiseEventDataController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.event_data_headers_url = HEADERS_URL_EVENT_DATA
        self.cookies = None
        self.event_data_api_url = "https://www.nseindia.com/api/top-corp-info?symbol={symbol}&market=equities"

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
            default_headers = load_nse_headers(self.event_data_headers_url)
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

            response = requests.get(url, headers=headers, cookies=cookies)
            if response.status_code == HTTP_STATUS.OK:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None

    def _save_to_database(self, data: Dict[str, Any], symbol: str) -> bool:
        """Save stockwise event data to MongoDB using enhanced save system."""
        try:
            if not data:
                logger.warning(f"No event data to save to database for symbol {symbol}")
                return False
                
            # Use the enhanced save system with data formatting and cleanup
            save_result = self.db.save_data_with_cleanup(
                data, 
                "stock_events", 
                DATA_RETENTION_DAYS['STOCK_EVENTS'],
                symbol=symbol
            )
            
            logger.info(f"Data save result: {'SUCCESS' if save_result else 'FAILED'}")
            return save_result
                
        except Exception as e:
            logger.error(f"Error saving stockwise event data for {symbol} to database: {str(e)}")
            return False

    def get_event_data(self, symbol: str) -> Optional[Dict]:
        """Fetches stockwise event data for a given symbol."""
        try:
            url = self.event_data_api_url.format(symbol=symbol)
            logger.info(f"Fetching event data for {symbol} from {url}")
            response_data = self._make_request(url)
            if not response_data:
                logger.error(f"Failed to fetch event data for {symbol}")
                return create_error_response(f"Failed to fetch event data for {symbol}")

            # Save to MongoDB with enhanced system
            save_result = self._save_to_database(response_data, symbol)
            if not save_result:
                logger.warning(f"Failed to save event data for {symbol} to MongoDB, but returning API data")

            return create_success_response(response_data, message=f"Event data fetched successfully for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching event data for {symbol}: {str(e)}")
            return create_error_response(str(e))

    def scrape_bulk_event_data(self, symbols_list: List[str] = None) -> Dict[str, Any]:
        """Scrape event data for multiple symbols - used by cron jobs."""
        try:
            # Default symbols if none provided
            if not symbols_list:
                symbols_list = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", 
                               "KOTAKBANK", "LT", "ITC", "SBIN", "BHARTIARTL"]
            
            logger.info(f"Scraping event data for {len(symbols_list)} symbols")
            
            all_event_data = []
            successful_count = 0
            
            for symbol in symbols_list:
                try:
                    result = self.get_event_data(symbol)
                    if result and result.get('success'):
                        all_event_data.append(result['data'])
                        successful_count += 1
                except Exception as e:
                    logger.error(f"Error fetching event data for {symbol}: {str(e)}")
                    continue
            
            if successful_count > 0:
                logger.info(f"Successfully scraped event data for {successful_count}/{len(symbols_list)} symbols")
                return create_success_response({
                    'data': all_event_data,
                    'total_symbols': len(symbols_list),
                    'successful_symbols': successful_count,
                    'scraped_at': datetime.now().isoformat()
                }, message=f"Event data scraped for {successful_count} symbols")
            else:
                logger.error("Failed to scrape event data for any symbols")
                return create_error_response("Failed to scrape event data for any symbols")
                
        except Exception as e:
            logger.error(f"Error in bulk event data scraping: {str(e)}")
            return create_error_response(str(e))
    
# if __name__ == "__main__":
#     controller = StockwiseEventDataController()
#     symbol = "IRCTC"
#     event_data = controller.get_event_data(symbol)
#     if event_data:
#         print(event_data)
#     else:
#         print("Failed to fetch event data.")
