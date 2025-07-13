import requests
from datetime import datetime
from typing import Dict, Optional
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_response
from Services.get_nse_cookies import get_nse_cookies

from Constant.general import ALL_INDICES_LIST
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers
from Constant.http import HTTP_STATUS

logger = get_logger(__name__)


class NSEAllIndexesController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.nse_headers_url = configure.get('NSE', 'HEADERS_URL_ALL_INDEXES')
        self.cookies = None

    def _get_cookies(self):
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None

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
        """Scrape all NSE indices and store in one table: all_indexes"""
        try:
            all_processed_data = []

            for index_name in ALL_INDICES_LIST:
                logger.info(f"Scraping data for index: {index_name}")
                url = f"{self.base_url}/api/equity-stockIndices?index={index_name.replace(' ', '%20')}"
                raw_data = self._make_request(url)

                if raw_data:
                    processed = self._process_generic_index_data(raw_data, index_name)
                    if processed:
                        all_processed_data.append(processed)
                        self._save_to_database(processed)
                    else:
                        logger.warning(f"No processed data for {index_name}")
                else:
                    logger.warning(f"Failed to fetch data for index: {index_name}")

            return create_response(
                success=True,
                data={"total_indices_scraped": len(all_processed_data)},
                message="All indices data scraped successfully"
            )

        except Exception as e:
            logger.error(f"Error scraping all indices: {str(e)}")
            return create_response(
                success=False,
                message=f"Failed to scrape all indices: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

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
            processed = {
                "timestamp": datetime.now().isoformat(),
                "index_name": index_name,
                "index_info": {
                    "index_name": raw_data.get("indexName"),
                    "last_price": raw_data.get("last"),
                    "variation": raw_data.get("variation"),
                    "percent_change": raw_data.get("percentChange"),
                    "open": raw_data.get("open"),
                    "high": raw_data.get("dayHigh"),
                    "low": raw_data.get("dayLow"),
                    "previous_close": raw_data.get("previousClose"),
                    "year_high": raw_data.get("yearHigh"),
                    "year_low": raw_data.get("yearLow")
                },
                "stocks": []
            }

            for stock in raw_data.get("data", []):
                processed["stocks"].append({
                    "symbol": stock.get("symbol"),
                    "series": stock.get("series"),
                    "open": stock.get("open"),
                    "high": stock.get("dayHigh"),
                    "low": stock.get("dayLow"),
                    "last_price": stock.get("lastPrice"),
                    "previous_close": stock.get("previousClose"),
                    "change": stock.get("change"),
                    "percent_change": stock.get("pChange"),
                    "total_traded_volume": stock.get("totalTradedVolume"),
                    "total_traded_value": stock.get("totalTradedValue"),
                    "last_update_time": stock.get("lastUpdateTime"),
                    "year_high": stock.get("yearHigh"),
                    "year_low": stock.get("yearLow"),
                    "near_week_high": stock.get("nearWkH"),
                    "near_week_low": stock.get("nearWkL"),
                    "per_change_365d": stock.get("perChange365d"),
                    "per_change_30d": stock.get("perChange30d")
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
