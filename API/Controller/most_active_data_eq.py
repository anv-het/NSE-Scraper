"""
NSE Most Active Equities Controller
Handles scraping and data management for most active equities
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
from Constant.general import (
    HEADERS_URL_MOST_ACTIVE_EQUITIES
)
from Services.get_nse_cookies import get_nse_cookies



logger = get_logger(__name__)


class NSEMostActiveEquitiesController:
    def __init__(self):
        self.db = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.most_active_headers_url = HEADERS_URL_MOST_ACTIVE_EQUITIES
        self.cookies = None
        self.most_active_api_url_by_value = "https://www.nseindia.com/api/live-analysis-most-active-securities?index=value"
        self.most_active_api_url_by_volume = "https://www.nseindia.com/api/live-analysis-most-active-securities?index=volume"
        self.most_active_sme_api_url_by_value = "https://www.nseindia.com/api/live-analysis-most-active-sme?index=value"
        self.most_active_sme_api_url_by_volume = "https://www.nseindia.com/api/live-analysis-most-active-sme?index=volume"
        self.most_active_etf_api_url_by_value = "https://www.nseindia.com/api/live-analysis-most-active-etf?index=value"
        self.most_active_etf_api_url_by_volume = "https://www.nseindia.com/api/live-analysis-most-active-etf?index=volume"
        self.most_active_variations_api_url_by_lower = "https://www.nseindia.com/api/live-analysis-variations?index=gainers&key=SecLwr20"
        self.most_active_variations_api_url_by_greater = "https://www.nseindia.com/api/live-analysis-variations?index=gainers&key=SecGtr20"
        self.most_active_volume_gainers_api_url = "https://www.nseindia.com/api/live-analysis-volume-gainers"


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
            default_headers = load_nse_headers(self.most_active_headers_url)
            if headers:
                default_headers.update(headers)
                
            cookies = self.get_cookies()
            
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
        

    def scrape_most_active_equities(self) -> Dict[str, Any]:
        try:
            logger.info("Scraping most active equities data")
            data_value = self.make_request(self.most_active_api_url_by_value)
            data_volume = self.make_request(self.most_active_api_url_by_volume)

            if not data_value and not data_volume:
                return create_error_response("Failed to fetch most active equities data", HTTP_STATUS.INTERNAL_SERVER_ERROR)

            return create_success_response({
                "by_value": data_value,
                "by_volume": data_volume
            }, "Most active equities fetched successfully")

        except Exception as e:
            logger.error(f"Error scraping most active equities: {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)

    def scrape_most_active_sme_equities(self) -> Dict[str, Any]:
        try:
            logger.info("Scraping most active SME equities data")
            data_value = self.make_request(self.most_active_sme_api_url_by_value)
            data_volume = self.make_request(self.most_active_sme_api_url_by_volume)

            if not data_value and not data_volume:
                return create_error_response("Failed to fetch most active SME equities data", HTTP_STATUS.INTERNAL_SERVER_ERROR)

            return create_success_response({
                "by_value": data_value,
                "by_volume": data_volume
            }, "Most active SME equities fetched successfully")

        except Exception as e:
            logger.error(f"Error scraping most active SME equities: {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)

    def scrape_most_active_etf_equities(self) -> Dict[str, Any]:
        try:
            logger.info("Scraping most active ETF equities data")
            data_value = self.make_request(self.most_active_etf_api_url_by_value)
            data_volume = self.make_request(self.most_active_etf_api_url_by_volume)

            if not data_value and not data_volume:
                return create_error_response("Failed to fetch most active ETF equities data", HTTP_STATUS.INTERNAL_SERVER_ERROR)

            return create_success_response({
                "by_value": data_value,
                "by_volume": data_volume
            }, "Most active ETF equities fetched successfully")

        except Exception as e:
            logger.error(f"Error scraping most active ETF equities: {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)

    def scrape_most_active_variations(self, variation_type: str) -> Dict[str, Any]:
        try:
            if variation_type == "lower":
                url = self.most_active_variations_api_url_by_lower
            elif variation_type == "greater":
                url = self.most_active_variations_api_url_by_greater
            else:
                return create_error_response("Invalid variation type", HTTP_STATUS.BAD_REQUEST)

            logger.info(f"Scraping most active variations ({variation_type}) data")
            data = self.make_request(url)

            if not data:
                return create_error_response(f"Failed to fetch most active variations ({variation_type}) data", HTTP_STATUS.INTERNAL_SERVER_ERROR)

            return create_success_response(data, f"Most active variations ({variation_type}) fetched successfully")

        except Exception as e:
            logger.error(f"Error scraping most active variations ({variation_type}): {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)
        
    def scrape_most_active_volume_gainers(self) -> Dict[str, Any]:
        try:
            logger.info("Scraping most active volume gainers data")
            data = self.make_request(self.most_active_volume_gainers_api_url)

            if not data:
                return create_error_response("Failed to fetch most active volume gainers data", HTTP_STATUS.INTERNAL_SERVER_ERROR)

            return create_success_response(data, "Most active volume gainers fetched successfully")

        except Exception as e:
            logger.error(f"Error scraping most active volume gainers: {str(e)}")
            return create_error_response(str(e), HTTP_STATUS.INTERNAL_SERVER_ERROR)
        

# if __name__ == "__main__":
#     controller = NSEMostActiveEquitiesController()
#     most_active_eq = controller.scrape_most_active_equities()
#     print("Most Active Equities:", most_active_eq)

#     most_active_sme = controller.scrape_most_active_sme_equities()
#     print("Most Active SME Equities:", most_active_sme)

#     most_active_etf = controller.scrape_most_active_etf_equities()
#     print("Most Active ETF Equities:", most_active_etf)

#     most_active_variations_lower = controller.scrape_most_active_variations("lower")
#     print("Most Active Variations (Lower):", most_active_variations_lower)

#     most_active_variations_greater = controller.scrape_most_active_variations("greater")
#     print("Most Active Variations (Greater):", most_active_variations_greater)
