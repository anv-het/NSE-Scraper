import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

import urllib
from Utils.data_formatter import NSEDataFormatter
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_error_response, create_response, create_success_response_n
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

    async def scrape_all_indices_from_list(self) -> Dict:
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
                    if raw_data.get("data"):
                        all_processed_data.append(raw_data["data"])
                        logger.info(f"Successfully scraped {index_name}")
                    else:
                        logger.warning(f"No processed data for {index_name}")
                        failed_indices.append(index_name)
                else:
                    logger.warning(f"Failed to fetch data for index: {index_name}")
                    failed_indices.append(index_name)

            # format the data 
            formatted_data = NSEDataFormatter.format_all_indices(all_processed_data)

            # Save to MongoDB
            if formatted_data:
                if self.db_manager.save_data(formatted_data, 'nse_all_indexes'):
                    logger.info("Data saved to MongoDB successfully")
                else:
                    logger.error("Failed to save data to MongoDB")

            return create_success_response_n(formatted_data, HTTP_STATUS.OK)

        except Exception as e:
            logger.error(f"Error scraping all indices: {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)



