import requests
import sqlite3
import datetime
import requests
import json

from datetime import datetime
from typing import Dict, List, Optional
from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_response
from Services.get_nse_cookies import get_nse_cookies
from Constant.general import HEADERS_URL_GAINER_LOOSER
from Utils.config_reader import ConfigReader
from Utils.config_reader import configure

from Constant.http import HTTP_STATUS
from Utils.cookie_headers import load_nse_headers


logger = get_logger(__name__)

class NSETopGainersloosersController:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.nse_headers_url = HEADERS_URL_GAINER_LOOSER
        self.cookies = None

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
    
    def scrape_top_gainers(self) -> Dict:
        """Scrape top gainers data from NSE"""
        try:
            url = f"{self.base_url}/api/live-analysis-variations?index=gainers"
            logger.info(f"Scraping top gainers from: {url}")
            
            data = self._make_request(url)
            if data:
                # Process and clean the data
                processed_data = self._process_gainers_loosers_data(data, "gainers")
                
                # Save to database
                self._save_to_database(processed_data, "top_gainers")
                
                logger.info(f"Successfully scraped {len(processed_data.get('data', []))} top gainers")
                return create_response(
                    success=True,
                    data=processed_data,
                    message="Top gainers data retrieved successfully"
                )
            else:
                return create_response(
                    success=False,
                    message="Failed to retrieve top gainers data",
                    status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error scraping top gainers: {str(e)}")
            return create_response(
                success=False,
                message=f"Error scraping top gainers: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def scrape_top_loosers(self) -> Dict:
        """Scrape top loosers data from NSE"""
        try:
            url = f"{self.base_url}/api/live-analysis-variations?index=loosers"
            logger.info(f"Scraping top loosers from: {url}")
            
            data = self._make_request(url)
            if data:
                # Process and clean the data
                processed_data = self._process_gainers_loosers_data(data, "loosers")
                
                # Save to database
                self._save_to_database(processed_data, "top_loosers")
                
                logger.info(f"Successfully scraped {len(processed_data.get('data', []))} top loosers")
                return create_response(
                    success=True,
                    data=processed_data,
                    message="Top loosers data retrieved successfully"
                )
            else:
                return create_response(
                    success=False,
                    message="Failed to retrieve top loosers data",
                    status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error scraping top loosers: {str(e)}")
            return create_response(
                success=False,
                message=f"Error scraping top loosers: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )
    
    def _process_gainers_loosers_data(self, raw_data: Dict, data_type: str) -> Dict:
        """Process and clean gainers/loosers data"""
        try:
            processed_data = {
                "timestamp": datetime.now().isoformat(),
                "data_type": data_type,
                "legends": raw_data.get("legends", []),
                "data": []
            }
            
            # Process each category (NIFTY, BANKNIFTY, etc.)
            for category, category_data in raw_data.items():
                if category == "legends":
                    continue
                    
                if isinstance(category_data, dict) and "data" in category_data:
                    for stock in category_data["data"]:
                        processed_stock = {
                            "category": category,
                            "symbol": stock.get("symbol"),
                            "series": stock.get("series"),
                            "open_price": stock.get("open_price"),
                            "high_price": stock.get("high_price"),
                            "low_price": stock.get("low_price"),
                            "ltp": stock.get("ltp"),
                            "prev_price": stock.get("prev_price"),
                            "net_price": stock.get("net_price"),
                            "per_change": stock.get("perChange"),
                            "trade_quantity": stock.get("trade_quantity"),
                            "turnover": stock.get("turnover"),
                            "market_type": stock.get("market_type"),
                            "ca_ex_dt": stock.get("ca_ex_dt"),
                            "ca_purpose": stock.get("ca_purpose")
                        }
                        processed_data["data"].append(processed_stock)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing {data_type} data: {str(e)}")
            return {"timestamp": datetime.now().isoformat(), "data_type": data_type, "data": []}

    def _save_to_database(self, data: Dict, table_name: str):
        """Save processed data to database"""
        try:
            self.db_manager.save_data(data, table_name)
            logger.info(f"Data saved to database table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to save data to database: {str(e)}")

    def get_top_gainers_from_db(self, limit: int = 50) -> Dict:
        """Get top gainers data from database"""
        try:
            data = self.db_manager.get_latest_data("top_gainers", limit)
            return create_response(
                success=True,
                data=data,
                message="Top gainers data retrieved from database"
            )
        except Exception as e:
            logger.error(f"Error retrieving top gainers from database: {str(e)}")
            return create_response(
                success=False,
                message=f"Error retrieving data: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def get_top_loosers_from_db(self, limit: int = 50) -> Dict:
        """Get top loosers data from database"""
        try:
            data = self.db_manager.get_latest_data("top_loosers", limit)
            return create_response(
                success=True,
                data=data,
                message="Top loosers data retrieved from database"
            )
        except Exception as e:
            logger.error(f"Error retrieving top loosers from database: {str(e)}")
            return create_response(
                success=False,
                message=f"Error retrieving data: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

    def get_top_gainers_and_loosers(self, limit: int = 50) -> Dict:
        """Get both top gainers and loosers data from database"""
        try:
            gainers = self.get_top_gainers_from_db(limit)
            loosers = self.get_top_loosers_from_db(limit)

            return create_response(
                success=True,
                data={
                    "gainers": gainers.get("data", []),
                    "loosers": loosers.get("data", [])
                },
                message="Top gainers and loosers data retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving gainers/loosers data: {str(e)}")
            return create_response(
                success=False,
                message=f"Error retrieving data: {str(e)}",
                status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR
            )

