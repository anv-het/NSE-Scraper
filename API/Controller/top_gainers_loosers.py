import requests
import sqlite3
import datetime
import requests
import json
import asyncio
from typing import Dict, Any, List, Optional

from datetime import datetime
from typing import Dict, List, Optional
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_response, create_success_response_n
from Services.get_nse_cookies import get_nse_cookies
from Constant.general import HEADERS_URL_GAINER_LOOSER
from Utils.config_reader import ConfigReader
from Utils.config_reader import configure

from Constant.http import HTTP_STATUS
from Utils.cookie_headers import load_nse_headers
from Utils.data_formatter import NSEDataFormatter


logger = get_logger(__name__)

class NSETopGainersloosersController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.nse_headers_url = HEADERS_URL_GAINER_LOOSER
        self.cookies = None
        self.gainers_api_url = "https://www.nseindia.com/api/live-analysis-variations?index=gainers"
        self.loosers_api_url = "https://www.nseindia.com/api/live-analysis-variations?index=loosers"

    def _get_cookies(self):
        """Get NSE cookies for authenticated requests"""
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None
        
    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Make HTTP request to NSE API"""
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
    

    async def top_gainer_loosers(self) -> Dict:
        """Fetches top gainers and loosers data from NSE"""
        try:
            urls = [
                self.gainers_api_url,
                self.loosers_api_url
            ]

            results = await asyncio.gather(*[asyncio.to_thread(self._make_request, url) for url in urls])

            data_gainer_loosers = {
                "gainers": results[0],
                "loosers": results[1]
            }
                        
            if not data_gainer_loosers["gainers"] or not data_gainer_loosers["loosers"]:
                logger.error("No data found for gainers or loosers.")
                return create_response(HTTP_STATUS.NOT_FOUND, "No data found for gainers or loosers.")
            
            # Format the data
            formatted_data = NSEDataFormatter.format_all_indices_from_list(data_gainer_loosers)

            # Save to MongoDB
            if formatted_data:
                if self.db_manager.save_data(formatted_data, 'nse_gainers_losers'):
                    logger.info("Data saved to MongoDB successfully")
                else:
                    logger.error("Failed to save data to MongoDB")

            return create_success_response_n(formatted_data, HTTP_STATUS.OK)
        
        except Exception as e:
            logger.error(f"Error fetching top gainers and loosers: {str(e)}")
            return create_response(HTTP_STATUS.INTERNAL_SERVER_ERROR, "Error fetching top gainers and loosers.")
            



