import requests
from datetime import datetime
from typing import Dict, List, Optional

import urllib
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_response
from Services.get_nse_cookies import get_nse_cookies

from Constant.general import (
    ALL_INDICES_LIST,
    HEADERS_URL_ALL_INDEXES
)
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers
from Constant.http import HTTP_STATUS

logger = get_logger(__name__)


class NSEAllIndexesController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.nse_headers_url = HEADERS_URL_ALL_INDEXES
        self.cookies = None

    def _get_cookies(self):
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None

    def _encode_index_name(self, index_name: str) -> str:
        """URL encode the index name to handle special characters."""
        return urllib.parse.quote(index_name)

    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        try:
            default_headers = load_nse_headers(self.nse_headers_url)
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

    def scrape_all_indices_from_list(self) -> Dict:
        """Scrape all NSE indices and return structured data"""
        try:
            all_processed_data = []
            failed_indices = []

            for index_name in ALL_INDICES_LIST:
                logger.info(f"Scraping data for index: {index_name}")
                encoded_index_name = self._encode_index_name(index_name)
                url = f"{self.base_url}/api/equity-stockIndices?index={encoded_index_name}"
                raw_data = self._make_request(url)

                if raw_data:
                    processed = self._process_generic_index_data(raw_data, index_name)
                    if processed:
                        all_processed_data.append(processed)
                        logger.info(f"Successfully scraped {index_name}")
                    else:
                        logger.warning(f"No processed data for {index_name}")
                        failed_indices.append(index_name)
                else:
                    logger.warning(f"Failed to fetch data for index: {index_name}")
                    failed_indices.append(index_name)

            # Save all data at once
            if all_processed_data:
                self._save_all_to_database(all_processed_data)
                logger.info(f"Saved {len(all_processed_data)} indices to database")
            else:
                logger.warning("No index data scraped")

            return {
                "total_scraped": len(all_processed_data),
                "failed_indices": failed_indices,
                "records": all_processed_data
            }

        except Exception as e:
            logger.error(f"Error scraping all indices: {str(e)}")
            raise  # Let the router handle this with a clean error response

    def scrape_index_data(self, index_name: str) -> Dict:
        """Scrape a single index and store in one table: all_indexes"""
        try:
            formatted_name = index_name.replace(" ", "%20")
            url = f"{self.base_url}/api/equity-stockIndices?index={formatted_name}"
            logger.info(f"Scraping data for index: {index_name} from URL: {url}")

            raw_data = self._make_request(url)
            if raw_data:
                processed = self._process_generic_index_data(raw_data, index_name)
                self._save_to_database(processed)
                return create_response(
                    success=True,
                    data=processed,
                    message=f"Index data for '{index_name}' retrieved successfully"
                )
            else:
                return create_response(
                    success=False,
                    message=f"Failed to retrieve data for index '{index_name}'",
                    status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error scraping index '{index_name}': {str(e)}")
            return create_response(
                success=False,
                message=f"Error scraping index '{index_name}': {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def _process_generic_index_data(self, raw_data: Dict, index_name: str) -> Optional[Dict]:
        """Process data for saving to all_indexes"""
        try:
            # Get the main index data (usually first in the list, priority = 1)
            main_index_data = raw_data.get("data", [])[0] if raw_data.get("data") else {}

            processed = {
                "timestamp": datetime.now().isoformat(),
                "index_name": index_name,
                "index_info": {
                    "priority": main_index_data.get("priority", 1),
                    "full_name": raw_data.get("name", index_name),
                    "decline_stocks": int(raw_data.get("advance", {}).get("declines", 0)),
                    "advance_stocks": int(raw_data.get("advance", {}).get("advances", 0)),
                    "unchanged_stocks": int(raw_data.get("advance", {}).get("unchanged", 0)),
                    "last_update_time": main_index_data.get("lastUpdateTime"),
                    "last_price": main_index_data.get("lastPrice"),
                    "previous_close": main_index_data.get("previousClose"),
                    "open": main_index_data.get("open"),
                    "day_high": main_index_data.get("dayHigh"),
                    "day_low": main_index_data.get("dayLow"),
                    "change": main_index_data.get("change"),
                    "percent_change": main_index_data.get("pChange"),
                    "year_high": main_index_data.get("yearHigh"),
                    "year_low": main_index_data.get("yearLow"),
                    "total_traded_volume": main_index_data.get("totalTradedVolume"),
                    "total_traded_value": main_index_data.get("totalTradedValue"),
                    "near_52w_high_percent": main_index_data.get("nearWKH"),
                    "near_52w_low_percent": main_index_data.get("nearWKL"),
                    "1y_percent_change": main_index_data.get("perChange365d"),
                    "30d_percent_change": main_index_data.get("perChange30d"),
                    "chart_today_url": main_index_data.get("chartTodayPath"),
                    "chart_30d_url": main_index_data.get("chart30dPath"),
                    "chart_365d_url": main_index_data.get("chart365dPath")
                },
                "stocks": []
            }

            # Add stock-level data (including index itself and other components)
            for stock in raw_data.get("data", []):
                processed["stocks"].append({
                    "symbol": stock.get("symbol"),
                    "series": stock.get("series"),
                    "last_price": stock.get("lastPrice"),
                    "change": stock.get("change"),
                    "percent_change": stock.get("pChange"),
                    "open_price": stock.get("open"),  # Fix key name
                    "high": stock.get("dayHigh"),
                    "low": stock.get("dayLow"),
                    "previous_close": stock.get("previousClose"),
                    "total_traded_volume": stock.get("totalTradedVolume"),
                    "total_traded_value": stock.get("totalTradedValue"),
                    "year_high": stock.get("yearHigh"),
                    "year_low": stock.get("yearLow"),
                    "near_wkh": stock.get("nearWKH"),  # Fix key name
                    "near_wkl": stock.get("nearWKL"),  # Fix key name
                    "per_change_365d": stock.get("perChange365d"),
                    "date_365d_ago": stock.get("date365dAgo"),
                    "per_change_30d": stock.get("perChange30d"),
                    "date_30d_ago": stock.get("date30dAgo"),
                    "chart_today_path": stock.get("chartTodayPath"),
                    "chart_30d_path": stock.get("chart30dPath"),
                    "chart_365d_path": stock.get("chart365dPath")
                })


            return processed

        except Exception as e:
            logger.error(f"Error processing index {index_name}: {str(e)}")
            return None

    def _save_to_database(self, data: Dict):
        """Save to shared all_indexes table"""
        try:
            self.db_manager.save_data(data, "all_indexes")
            logger.info("Data saved to database table: all_indexes")
        except Exception as e:
            logger.error(f"Failed to save data for {data.get('index_name')}: {str(e)}")

    def get_index_data_from_db(self, index_name: str, limit: int = 50) -> Dict:
        """Fetch data for a specific index from all_indexes table"""
        try:
            data = self.db_manager.get_latest_data_filtered("all_indexes", "index_name", index_name, limit)
            return create_response(
                success=True,
                data=data,
                message=f"{index_name} data retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving {index_name} data: {str(e)}")
            return create_response(
                success=False,
                message=f"Error retrieving data: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def get_all_indexes_from_db(self, limit: int = 50) -> Dict:
        """Fetch recent entries from all indexes"""
        try:
            data = self.db_manager.get_latest_data("all_indexes", limit)
            return create_response(
                success=True,
                data=data,
                message="All indexes data retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving all indexes: {str(e)}")
            return create_response(
                success=False,
                message=f"Error retrieving data: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def _save_all_to_database(self, all_data: List[Dict]):
        """Save all indices data at once"""
        try:
            self.db_manager.save_all_data(all_data, "all_indexes")
            logger.info("All data saved to database table: all_indexes")
        except Exception as e:
            logger.error(f"Failed to save all data: {str(e)}")
            raise
