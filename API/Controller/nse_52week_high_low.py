"""
NSE 52-Week High/Low Controller
Handles scraping and data management for 52-week high/low stocks
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
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)


class NSE52WeekHighLowController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.high_headers_url = configure.get('NSE', 'HEADERS_URL_52_WEEK_HIGH')
        self.low_headers_url = configure.get('NSE', 'HEADERS_URL_52_WEEK_LOW')
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

    def scrape_52_week_high(self) -> Dict[str, Any]:
        """Scrape 52-week high stocks and store in the database."""
        try:
            url = self.high_api_url
            logger.info(f"Scraping 52-week high stocks from: {url}")

            data = self._make_request(url)
            if data:
                processed_data = self._process_52_week_data(data, "high")
                if processed_data:
                    self._save_52_week_data_to_db(processed_data, "high")
                    return create_success_response(processed_data, "52-week high data scraped successfully")
                else:
                    return create_error_response("No valid data found for 52-week high stocks")

        except Exception as e:
            logger.error(f"Error scraping 52-week high: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )
    
    def scrape_52_week_low(self) -> Dict[str, Any]:
        """Scrape 52-week low stocks and store in the database."""
        try:
            url = self.low_api_url
            logger.info(f"Scraping 52-week low stocks from: {url}")

            data = self._make_request(url)
            if data:
                processed_data = self._process_52_week_data(data, "low")
                if processed_data:
                    self._save_52_week_data_to_db(processed_data, "low")
                    return create_success_response(processed_data, "52-week low data scraped successfully")
                else:
                    return create_error_response("No valid data found for 52-week low stocks")

        except Exception as e:
            logger.error(f"Error scraping 52-week low: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )
    
    def scrape_52_week_high_low(self) -> Dict[str, Any]:
        """Scrape both 52-week high and low stocks."""
        try:
            logger.info("Starting to scrape 52-week high and low stocks...")

            high_result = self.scrape_52_week_high()
            low_result = self.scrape_52_week_low()

            if high_result.get('success') and low_result.get('success'):
                return create_success_response(
                    data={
                        "high": high_result.get("data"),
                        "low": low_result.get("data")
                    },
                    message="52-week high and low data scraped successfully"
                )
            else:
                return create_error_response(
                    message="Failed to scrape 52-week high or low data",
                    status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error scraping 52-week high and low: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def _process_52_week_data(self, data: Dict[str, Any], week_type: str) -> Optional[Dict[str, Any]]:
        """Process the raw data for 52-week high/low stocks."""
        try:
            if not data or 'data' not in data:
                logger.warning("No data found for processing")
                return None

            processed_data = {
                "timestamp": data.get("timestamp") or datetime.now().isoformat(),
                "week_type": week_type,
                "scraped_at": datetime.now().isoformat(),
                "data": []
            }

            for item in data['data']:
                processed_item = {
                    "symbol": item.get("symbol"),
                    "series": item.get("series"),
                    "companyName": item.get("comapnyName"),
                    "new52WHL": clean_numeric_value(item.get("new52WHL")),
                    "prev52WHL": clean_numeric_value(item.get("prev52WHL")),
                    "prevHLDate": item.get("prevHLDate"),
                    "ltp": clean_numeric_value(item.get("ltp")),
                    "prevClose": clean_numeric_value(item.get("prevClose")),
                    "change": clean_numeric_value(item.get("change")),
                    "pChange": clean_numeric_value(item.get("pChange"))
                }
                processed_data["data"].append(processed_item)

            return processed_data
        except Exception as e:
            logger.error(f"Error processing 52-week {week_type} data: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "week_type": week_type,
                "data": []
            }

    def _save_52_week_data_to_db(self, data: Dict[str, Any], week_type: str) -> int:
        """Save processed 52-week high/low data to the database."""
        try:
            table_name = f"nse_52_week_{week_type}"

            #clear the table before saving new data but also chek the the data is not empty
            if data and data.get("data"):
                self.db.delete_records(table_name)
                self.db.save_data(data, table_name)
                logger.info(f"Data saved to database table: {table_name}")
            return 1
        except Exception as e:
            logger.error(f"Error saving 52-week {week_type} data to database: {str(e)}")
            return 0
    
    def get_52_week_high_from_db(self, limit: int = 50) -> Dict[str, Any]:
        """Get 52-week high stocks from the database."""
        try:
            data = self.db.get_data("nse_52_week_high", limit=limit)
            if data:
                return create_success_response(data, "52-week high data retrieved successfully")
            else:
                return create_error_response("No 52-week high data found in the database")
        except Exception as e:
            logger.error(f"Error retrieving 52-week high data from database: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def get_52_week_low_from_db(self, limit: int = 50) -> Dict[str, Any]:
        """Get 52-week low stocks from the database."""
        try:
            data = self.db.get_data("nse_52_week_low", limit=limit)
            if data:
                return create_success_response(data, "52-week low data retrieved successfully")
            else:
                return create_error_response("No 52-week low data found in the database")
        except Exception as e:
            logger.error(f"Error retrieving 52-week low data from database: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def get_52_week_high_low_data_from_db(self, week_type: str, limit: int = 50) -> Dict[str, Any]:
        """Get 52-week high or low data based on week_type."""
        try:
            if week_type == "high":
                return self.get_52_week_high_from_db(limit)
            elif week_type == "low":
                return self.get_52_week_low_from_db(limit)
            else:
                return create_error_response("Invalid week type specified", status_code=HTTP_STATUS.BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error retrieving 52-week {week_type} data: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )
        
    def refresh_52week_data(self):
        """Refresh 52-week high and low data by scraping and saving to the database."""
        try:
            logger.info("Refreshing 52-week high and low data...")

            # Scrape 52-week high data and scrap 52-week low data
            high_result = self.scrape_52_week_high()
            low_result = self.scrape_52_week_low()

           # Check results
            high_success = high_result.get('status') == 'success'
            low_success = low_result.get('status') == 'success'

            if high_success and low_success:
                logger.info("52-week high and low data refreshed successfully")
                return create_success_response(
                    data={
                        "high": high_result.get("data"),
                        "low": low_result.get("data")
                    },
                    message="52-week high and low data refreshed successfully"
                )
            elif high_success and not low_success:
                logger.warning("52-week high data refreshed successfully, but low data refresh failed")
                return create_success_response(
                    data={
                        "high": high_result.get("data"),
                        "low": None
                    },
                    message="52-week high data refreshed successfully, but low data refresh failed"
                )
            elif not high_success and low_success:
                logger.warning("52-week low data refreshed successfully, but high data refresh failed")
                return create_success_response(
                    data={
                        "high": None,
                        "low": low_result.get("data")
                    },
                    message="52-week low data refreshed successfully, but high data refresh failed"
                )
            else:
                logger.error("Failed to refresh both 52-week high and low data")
                return create_error_response(
                    message="Failed to refresh both 52-week high and low data",
                    status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error refreshing 52-week high and low data: {str(e)}")
            return create_error_response(
                success=False,
                message=str(e),
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

