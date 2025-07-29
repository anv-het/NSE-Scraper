import pymongo
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from Utils.logger import get_logger
from Utils.config_reader import configure

logger = get_logger(__name__)

class DatabaseManager:
    """MongoDB-only Database Manager for NSE Data Storage"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self._initialize_mongodb()
    
    def _initialize_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            mongo_uri = configure.get('DATABASE', 'MONGO_URI')
            database_name = configure.get('DATABASE', 'DATABASE_NAME')
            
            # Get optional authentication details
            username = configure.get('DATABASE', 'MONGO_USERNAME', fallback=None)
            password = configure.get('DATABASE', 'MONGO_PASSWORD', fallback=None)
            
            # Build connection URI with auth if provided
            if username and password:
                # Parse the URI to add authentication
                if '://' in mongo_uri:
                    protocol, rest = mongo_uri.split('://', 1)
                    mongo_uri = f"{protocol}://{username}:{password}@{rest}"
                logger.info("Connecting to MongoDB with authentication")
            else:
                logger.info("Connecting to MongoDB without authentication")
            
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[database_name]
            
            # Create indexes for better performance
            self._create_mongodb_indexes()
            
            logger.info(f"Connected to MongoDB: {mongo_uri.replace(password or '', '***') if password else mongo_uri}, Database: {database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {str(e)}")
            raise
    
    def _create_mongodb_indexes(self):
        """Create indexes for MongoDB collections for better performance"""
        try:
            collections_indexes = {
                'gainers_losers': [
                    ('timestamp', DESCENDING),
                    ('data_type', 1),
                    ('category', 1),
                    ('symbol', 1),
                ],
                'indices_data': [
                    ('timestamp', DESCENDING),
                    ('index_name', 1),
                    ('symbol', 1),
                ],
                'most_active_securities': [
                    ('timestamp', DESCENDING),
                    ('index_type', 1),
                    ('symbol', 1),
                ],
                'price_band_hitters': [
                    ('timestamp', DESCENDING),
                    ('band_type', 1),
                    ('symbol', 1),
                ],
                'week_52_data': [
                    ('timestamp', DESCENDING),
                    ('data_type', 1),
                    ('symbol', 1),
                ],
                'large_deals': [
                    ('timestamp', DESCENDING),
                    ('deal_type', 1),
                    ('symbol', 1),
                ],
                'advances_declines': [
                    ('timestamp', DESCENDING),
                    ('market_type', 1),
                ],
                'new_listings': [
                    ('timestamp', DESCENDING),
                    ('listing_type', 1),
                    ('symbol', 1),
                ],
                'most_active_contracts': [
                    ('timestamp', DESCENDING),
                    ('instrument', 1),
                    ('symbol', 1),
                ],
                'most_active_underlying': [
                    ('timestamp', DESCENDING),
                    ('underlying', 1),
                ],
                'stock_events': [
                    ('timestamp', DESCENDING),
                    ('symbol', 1),
                    ('event_type', 1),
                ]
            }
            
            for collection_name, indexes in collections_indexes.items():
                collection = self.mongo_db[collection_name]
                for index in indexes:
                    try:
                        if isinstance(index, tuple):
                            # Handle tuple format (field, direction)
                            collection.create_index([index])
                        else:
                            # Handle other formats
                            collection.create_index(index)
                    except Exception as e:
                        logger.warning(f"Could not create index {index} for {collection_name}: {e}")
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {str(e)}")
    
    # ======================== DATA FORMATTING METHODS ========================
    
    def _format_gainers_losers_data(self, raw_data: Dict, data_type: str) -> List[Dict]:
        """Format gainers/losers data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Process each category in the response
            for category, category_data in raw_data.items():
                if category == "legends" or not isinstance(category_data, dict):
                    continue
                    
                if "data" in category_data and isinstance(category_data["data"], list):
                    for stock in category_data["data"]:
                        formatted_record = {
                            "timestamp": timestamp,
                            "data_type": data_type,  # "gainers" or "losers"
                            "category": category,
                            "symbol": stock.get("symbol"),
                            "series": stock.get("series"),
                            "open_price": self._safe_float(stock.get("open_price")),
                            "high_price": self._safe_float(stock.get("high_price")),
                            "low_price": self._safe_float(stock.get("low_price")),
                            "ltp": self._safe_float(stock.get("ltp")),
                            "prev_price": self._safe_float(stock.get("prev_price")),
                            "net_price": self._safe_float(stock.get("net_price")),
                            "per_change": self._safe_float(stock.get("perChange")),
                            "trade_quantity": self._safe_int(stock.get("trade_quantity")),
                            "turnover": self._safe_float(stock.get("turnover")),
                            "market_type": stock.get("market_type"),
                            "ca_ex_dt": stock.get("ca_ex_dt"),
                            "ca_purpose": stock.get("ca_purpose"),
                            "raw_data": stock
                        }
                        formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} {data_type} records")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting {data_type} data: {str(e)}")
            return []
    
    def _format_indices_data(self, raw_data: Dict, index_name: str) -> List[Dict]:
        """Format indices data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for stock in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "index_name": index_name,
                        "symbol": stock.get("symbol"),
                        "series": stock.get("series"),
                        "open": self._safe_float(stock.get("open")),
                        "dayHigh": self._safe_float(stock.get("dayHigh")),
                        "dayLow": self._safe_float(stock.get("dayLow")),
                        "lastPrice": self._safe_float(stock.get("lastPrice")),
                        "previousClose": self._safe_float(stock.get("previousClose")),
                        "change": self._safe_float(stock.get("change")),
                        "pChange": self._safe_float(stock.get("pChange")),
                        "totalTradedVolume": self._safe_int(stock.get("totalTradedVolume")),
                        "totalTradedValue": self._safe_float(stock.get("totalTradedValue")),
                        "priority": self._safe_int(stock.get("priority")),
                        "yearHigh": self._safe_float(stock.get("yearHigh")),
                        "yearLow": self._safe_float(stock.get("yearLow")),
                        "nearWKH": self._safe_float(stock.get("nearWKH")),
                        "nearWKL": self._safe_float(stock.get("nearWKL")),
                        "perChange365d": self._safe_float(stock.get("perChange365d")),
                        "perChange30d": self._safe_float(stock.get("perChange30d")),
                        "raw_data": stock
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} index records for {index_name}")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting index data for {index_name}: {str(e)}")
            return []
    
    def _format_most_active_data(self, raw_data: Dict, index_type: str) -> List[Dict]:
        """Format most active securities data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for stock in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "index_type": index_type,
                        "symbol": stock.get("symbol"),
                        "series": stock.get("series"),
                        "open": self._safe_float(stock.get("open")),
                        "high": self._safe_float(stock.get("high")),
                        "low": self._safe_float(stock.get("low")),
                        "ltp": self._safe_float(stock.get("ltp")),
                        "ptsC": self._safe_float(stock.get("ptsC")),
                        "per": self._safe_float(stock.get("per")),
                        "trdVol": self._safe_int(stock.get("trdVol")),
                        "trdVolM": self._safe_float(stock.get("trdVolM")),
                        "ntP": self._safe_float(stock.get("ntP")),
                        "date30d": stock.get("date30d"),
                        "chart30dPath": stock.get("chart30dPath"),
                        "chartTodayPath": stock.get("chartTodayPath"),
                        "raw_data": stock
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} most active records for {index_type}")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting most active data for {index_type}: {str(e)}")
            return []
    
    def _format_price_band_data(self, raw_data: Dict, band_type: str) -> List[Dict]:
        """Format price band hitters data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for stock in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "band_type": band_type,
                        "symbol": stock.get("symbol"),
                        "series": stock.get("series"),
                        "high": self._safe_float(stock.get("high")),
                        "low": self._safe_float(stock.get("low")),
                        "ltp": self._safe_float(stock.get("ltp")),
                        "ptsC": self._safe_float(stock.get("ptsC")),
                        "per": self._safe_float(stock.get("per")),
                        "date30d": stock.get("date30d"),
                        "raw_data": stock
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} price band records for {band_type}")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting price band data for {band_type}: {str(e)}")
            return []
    
    def _format_52week_data(self, raw_data: Dict, data_type: str) -> List[Dict]:
        """Format 52-week high/low data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for stock in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "data_type": data_type,  # "high" or "low"
                        "symbol": stock.get("symbol"),
                        "dt": stock.get("dt"),
                        "series": stock.get("series"),
                        "ltp": self._safe_float(stock.get("ltp")),
                        "prev": self._safe_float(stock.get("prev")),
                        "ch": self._safe_float(stock.get("ch")),
                        "per": self._safe_float(stock.get("per")),
                        "hi_52w": self._safe_float(stock.get("hi_52w")),
                        "lo_52w": self._safe_float(stock.get("lo_52w")),
                        "raw_data": stock
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} 52-week {data_type} records")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting 52-week {data_type} data: {str(e)}")
            return []
    
    def _format_large_deals_data(self, raw_data: Dict, deal_type: str) -> List[Dict]:
        """Format large deals data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for deal in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "deal_type": deal_type,
                        "symbol": deal.get("symbol"),
                        "series": deal.get("series"),
                        "secType": deal.get("secType"),
                        "secVar": deal.get("secVar"),
                        "tdQty": self._safe_int(deal.get("tdQty")),
                        "value": self._safe_float(deal.get("value")),
                        "mktType": deal.get("mktType"),
                        "raw_data": deal
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} large deals records for {deal_type}")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting large deals data for {deal_type}: {str(e)}")
            return []
    
    def _format_advances_declines_data(self, raw_data: Dict, market_type: str) -> List[Dict]:
        """Format advances/declines data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for stock in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "market_type": market_type,
                        "symbol": stock.get("symbol"),
                        "series": stock.get("series"),
                        "high": self._safe_float(stock.get("high")),
                        "low": self._safe_float(stock.get("low")),
                        "ltp": self._safe_float(stock.get("ltp")),
                        "ptsC": self._safe_float(stock.get("ptsC")),
                        "per": self._safe_float(stock.get("per")),
                        "raw_data": stock
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} {market_type} records")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting {market_type} data: {str(e)}")
            return []
    
    def _format_new_listings_data(self, raw_data: Dict, listing_type: str) -> List[Dict]:
        """Format new listings data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for listing in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "listing_type": listing_type,
                        "symbol": listing.get("symbol"),
                        "series": listing.get("series"),
                        "listingDate": listing.get("listingDate"),
                        "industry": listing.get("industry"),
                        "raw_data": listing
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} new listings records for {listing_type}")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting new listings data for {listing_type}: {str(e)}")
            return []
    
    def _format_most_active_contracts_data(self, raw_data: Dict) -> List[Dict]:
        """Format most active contracts data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for contract in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "instrument": contract.get("instrument"),
                        "symbol": contract.get("symbol"),
                        "expiryDate": contract.get("expiryDate"),
                        "optionType": contract.get("optionType"),
                        "strikePrice": self._safe_float(contract.get("strikePrice")),
                        "openPrice": self._safe_float(contract.get("openPrice")),
                        "highPrice": self._safe_float(contract.get("highPrice")),
                        "lowPrice": self._safe_float(contract.get("lowPrice")),
                        "ltp": self._safe_float(contract.get("ltp")),
                        "netChange": self._safe_float(contract.get("netChange")),
                        "percentChange": self._safe_float(contract.get("percentChange")),
                        "volume": self._safe_int(contract.get("volume")),
                        "value": self._safe_float(contract.get("value")),
                        "premiumTurnover": self._safe_float(contract.get("premiumTurnover")),
                        "raw_data": contract
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} most active contracts records")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting most active contracts data: {str(e)}")
            return []
    
    def _format_most_active_underlying_data(self, raw_data: Dict) -> List[Dict]:
        """Format most active underlying data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if "data" in raw_data and isinstance(raw_data["data"], list):
                for underlying in raw_data["data"]:
                    formatted_record = {
                        "timestamp": timestamp,
                        "underlying": underlying.get("underlying"),
                        "noOfContracts": self._safe_int(underlying.get("noOfContracts")),
                        "turnover": self._safe_float(underlying.get("turnover")),
                        "raw_data": underlying
                    }
                    formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} most active underlying records")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting most active underlying data: {str(e)}")
            return []
    
    def _format_stock_events_data(self, raw_data: Dict, symbol: str) -> List[Dict]:
        """Format stock events data for MongoDB storage"""
        formatted_records = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Handle different event types in the response
            if isinstance(raw_data, dict):
                formatted_record = {
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "event_type": "corporate_info",
                    "data": raw_data,
                    "raw_data": raw_data
                }
                formatted_records.append(formatted_record)
            
            logger.info(f"Formatted {len(formatted_records)} stock events records for {symbol}")
            return formatted_records
            
        except Exception as e:
            logger.error(f"Error formatting stock events data for {symbol}: {str(e)}")
            return []
    
    # ======================== UTILITY METHODS ========================
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == "" or value == "-":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None or value == "" or value == "-":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    # ======================== MAIN SAVE METHODS ========================
    
    def save_gainers_losers_data(self, raw_data: Dict, data_type: str) -> bool:
        """Save gainers/losers data to MongoDB"""
        try:
            formatted_data = self._format_gainers_losers_data(raw_data, data_type)
            if formatted_data:
                collection = self.mongo_db['gainers_losers']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} {data_type} records to gainers_losers collection")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving {data_type} data: {str(e)}")
            return False
    
    def save_indices_data(self, raw_data: Dict, index_name: str) -> bool:
        """Save indices data to MongoDB"""
        try:
            formatted_data = self._format_indices_data(raw_data, index_name)
            if formatted_data:
                collection = self.mongo_db['indices_data']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to indices_data collection for {index_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving indices data for {index_name}: {str(e)}")
            return False
    
    def save_most_active_data(self, raw_data: Dict, index_type: str) -> bool:
        """Save most active securities data to MongoDB"""
        try:
            formatted_data = self._format_most_active_data(raw_data, index_type)
            if formatted_data:
                collection = self.mongo_db['most_active_securities']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to most_active_securities collection for {index_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving most active data for {index_type}: {str(e)}")
            return False
    
    def save_price_band_data(self, raw_data: Dict, band_type: str) -> bool:
        """Save price band hitters data to MongoDB"""
        try:
            formatted_data = self._format_price_band_data(raw_data, band_type)
            if formatted_data:
                collection = self.mongo_db['price_band_hitters']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to price_band_hitters collection for {band_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving price band data for {band_type}: {str(e)}")
            return False
    
    def save_52week_data(self, raw_data: Dict, data_type: str) -> bool:
        """Save 52-week high/low data to MongoDB"""
        try:
            formatted_data = self._format_52week_data(raw_data, data_type)
            if formatted_data:
                collection = self.mongo_db['week_52_data']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to week_52_data collection for {data_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving 52-week {data_type} data: {str(e)}")
            return False
    
    def save_large_deals_data(self, raw_data: Dict, deal_type: str) -> bool:
        """Save large deals data to MongoDB"""
        try:
            formatted_data = self._format_large_deals_data(raw_data, deal_type)
            if formatted_data:
                collection = self.mongo_db['large_deals']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to large_deals collection for {deal_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving large deals data for {deal_type}: {str(e)}")
            return False
    
    def save_advances_declines_data(self, raw_data: Dict, market_type: str) -> bool:
        """Save advances/declines data to MongoDB"""
        try:
            formatted_data = self._format_advances_declines_data(raw_data, market_type)
            if formatted_data:
                collection = self.mongo_db['advances_declines']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to advances_declines collection for {market_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving {market_type} data: {str(e)}")
            return False
    
    def save_new_listings_data(self, raw_data: Dict, listing_type: str) -> bool:
        """Save new listings data to MongoDB"""
        try:
            formatted_data = self._format_new_listings_data(raw_data, listing_type)
            if formatted_data:
                collection = self.mongo_db['new_listings']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to new_listings collection for {listing_type}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving new listings data for {listing_type}: {str(e)}")
            return False
    
    def save_most_active_contracts_data(self, raw_data: Dict) -> bool:
        """Save most active contracts data to MongoDB"""
        try:
            formatted_data = self._format_most_active_contracts_data(raw_data)
            if formatted_data:
                collection = self.mongo_db['most_active_contracts']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to most_active_contracts collection")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving most active contracts data: {str(e)}")
            return False
    
    def save_most_active_underlying_data(self, raw_data: Dict) -> bool:
        """Save most active underlying data to MongoDB"""
        try:
            formatted_data = self._format_most_active_underlying_data(raw_data)
            if formatted_data:
                collection = self.mongo_db['most_active_underlying']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to most_active_underlying collection")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving most active underlying data: {str(e)}")
            return False
    
    def save_stock_events_data(self, raw_data: Dict, symbol: str) -> bool:
        """Save stock events data to MongoDB"""
        try:
            formatted_data = self._format_stock_events_data(raw_data, symbol)
            if formatted_data:
                collection = self.mongo_db['stock_events']
                result = collection.insert_many(formatted_data)
                logger.info(f"Saved {len(result.inserted_ids)} records to stock_events collection for {symbol}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving stock events data for {symbol}: {str(e)}")
            return False
    
    # ======================== GENERIC SAVE METHOD ========================
    
    def save_data(self, raw_data: Dict, data_type: str, **kwargs) -> bool:
        """Generic save method that routes to specific formatters based on data type"""
        try:
            if data_type == "gainers":
                return self.save_gainers_losers_data(raw_data, "gainers")
            elif data_type == "losers":
                return self.save_gainers_losers_data(raw_data, "losers")
            elif data_type == "indices":
                index_name = kwargs.get("index_name", "unknown")
                return self.save_indices_data(raw_data, index_name)
            elif data_type == "most_active":
                index_type = kwargs.get("index_type", "unknown")
                return self.save_most_active_data(raw_data, index_type)
            elif data_type == "price_band":
                band_type = kwargs.get("band_type", "unknown")
                return self.save_price_band_data(raw_data, band_type)
            elif data_type == "52week_high":
                return self.save_52week_data(raw_data, "high")
            elif data_type == "52week_low":
                return self.save_52week_data(raw_data, "low")
            elif data_type == "large_deals":
                deal_type = kwargs.get("deal_type", "unknown")
                return self.save_large_deals_data(raw_data, deal_type)
            elif data_type == "advances":
                return self.save_advances_declines_data(raw_data, "advances")
            elif data_type == "declines":
                return self.save_advances_declines_data(raw_data, "declines")
            elif data_type == "unchanged":
                return self.save_advances_declines_data(raw_data, "unchanged")
            elif data_type == "new_listings":
                listing_type = kwargs.get("listing_type", "unknown")
                return self.save_new_listings_data(raw_data, listing_type)
            elif data_type == "most_active_contracts":
                return self.save_most_active_contracts_data(raw_data)
            elif data_type == "most_active_underlying":
                return self.save_most_active_underlying_data(raw_data)
            elif data_type == "stock_events":
                symbol = kwargs.get("symbol", "unknown")
                return self.save_stock_events_data(raw_data, symbol)
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error in generic save method for {data_type}: {str(e)}")
            return False
    
    # ======================== DATA RETRIEVAL METHODS ========================
    
    def get_latest_data(self, collection_name: str, limit: int = 50, filter_criteria: Dict = None) -> List[Dict]:
        """Get latest data from specified collection"""
        try:
            collection = self.mongo_db[collection_name]
            query = filter_criteria or {}
            cursor = collection.find(query).sort("timestamp", DESCENDING).limit(limit)
            
            results = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                results.append(doc)
            
            logger.info(f"Retrieved {len(results)} records from {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving data from {collection_name}: {str(e)}")
            return []
    
    def get_data_by_symbol(self, collection_name: str, symbol: str, limit: int = 50) -> List[Dict]:
        """Get data for a specific symbol from collection"""
        filter_criteria = {"symbol": symbol}
        return self.get_latest_data(collection_name, limit, filter_criteria)
    
    def get_data_by_date_range(self, collection_name: str, start_date: datetime, end_date: datetime, limit: int = 1000) -> List[Dict]:
        """Get data within a date range"""
        filter_criteria = {
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        return self.get_latest_data(collection_name, limit, filter_criteria)
    
    def get_gainers_losers(self, data_type: str = None, limit: int = 50) -> List[Dict]:
        """Get gainers/losers data"""
        filter_criteria = {"data_type": data_type} if data_type else {}
        return self.get_latest_data("gainers_losers", limit, filter_criteria)
    
    def get_indices_data(self, index_name: str = None, limit: int = 50) -> List[Dict]:
        """Get indices data"""
        filter_criteria = {"index_name": index_name} if index_name else {}
        return self.get_latest_data("indices_data", limit, filter_criteria)
    
    def get_most_active_securities(self, index_type: str = None, limit: int = 50) -> List[Dict]:
        """Get most active securities data"""
        filter_criteria = {"index_type": index_type} if index_type else {}
        return self.get_latest_data("most_active_securities", limit, filter_criteria)
    
    def get_price_band_hitters(self, band_type: str = None, limit: int = 50) -> List[Dict]:
        """Get price band hitters data"""
        filter_criteria = {"band_type": band_type} if band_type else {}
        return self.get_latest_data("price_band_hitters", limit, filter_criteria)
    
    def get_52week_data(self, data_type: str = None, limit: int = 50) -> List[Dict]:
        """Get 52-week high/low data"""
        filter_criteria = {"data_type": data_type} if data_type else {}
        return self.get_latest_data("week_52_data", limit, filter_criteria)
    
    def get_large_deals(self, deal_type: str = None, limit: int = 50) -> List[Dict]:
        """Get large deals data"""
        filter_criteria = {"deal_type": deal_type} if deal_type else {}
        return self.get_latest_data("large_deals", limit, filter_criteria)
    
    def get_advances_declines(self, market_type: str = None, limit: int = 50) -> List[Dict]:
        """Get advances/declines data"""
        filter_criteria = {"market_type": market_type} if market_type else {}
        return self.get_latest_data("advances_declines", limit, filter_criteria)
    
    def get_new_listings(self, listing_type: str = None, limit: int = 50) -> List[Dict]:
        """Get new listings data"""
        filter_criteria = {"listing_type": listing_type} if listing_type else {}
        return self.get_latest_data("new_listings", limit, filter_criteria)
    
    def get_most_active_contracts(self, limit: int = 50) -> List[Dict]:
        """Get most active contracts data"""
        return self.get_latest_data("most_active_contracts", limit)
    
    def get_most_active_underlying(self, limit: int = 50) -> List[Dict]:
        """Get most active underlying data"""
        return self.get_latest_data("most_active_underlying", limit)
    
    def get_stock_events(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get stock events data"""
        filter_criteria = {"symbol": symbol} if symbol else {}
        return self.get_latest_data("stock_events", limit, filter_criteria)
    
    # ======================== DATABASE MANAGEMENT ========================
    
    def get_collection_stats(self, collection_name: str) -> Dict:
        """Get statistics for a collection"""
        try:
            collection = self.mongo_db[collection_name]
            stats = self.mongo_db.command("collStats", collection_name)
            
            # Get latest timestamp
            latest_doc = collection.find().sort("timestamp", DESCENDING).limit(1)
            latest_timestamp = None
            for doc in latest_doc:
                latest_timestamp = doc.get("timestamp")
                break
            
            return {
                "count": stats.get("count", 0),
                "size": stats.get("size", 0),
                "avgObjSize": stats.get("avgObjSize", 0),
                "storageSize": stats.get("storageSize", 0),
                "latest_timestamp": latest_timestamp,
                "indexes": len(stats.get("indexSizes", {}))
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {str(e)}")
            return {}
    
    def get_all_collections_info(self) -> Dict:
        """Get information about all collections"""
        try:
            collections = self.mongo_db.list_collection_names()
            info = {}
            
            for collection_name in collections:
                info[collection_name] = self.get_collection_stats(collection_name)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting collections info: {str(e)}")
            return {}
    
    def cleanup_old_data(self, collection_name: str, days_to_keep: int = 30) -> int:
        """Clean up old data from collection"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            collection = self.mongo_db[collection_name]
            
            result = collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            deleted_count = result.deleted_count
            
            logger.info(f"Cleaned up {deleted_count} old records from {collection_name}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up {collection_name}: {str(e)}")
            return 0
    
    def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            self.mongo_client.admin.command('ping')
            logger.info("MongoDB connection test successful")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {str(e)}")
            return False
    
    def close_connection(self):
        """Close MongoDB connection"""
        try:
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()

# ======================== HELPER FUNCTIONS ========================

def get_database_manager() -> DatabaseManager:
    """Get a database manager instance"""
    return DatabaseManager()

def test_database_connection() -> bool:
    """Test database connection"""
    try:
        with get_database_manager() as db:
            return db.test_connection()
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False