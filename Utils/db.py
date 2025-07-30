import pymongo
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from Utils.logger import get_logger
from Utils.config_reader import configure
from Utils.data_formatter import NSEDataFormatter

logger = get_logger(__name__)

class DatabaseManager:
    """MongoDB-only Database Manager for NSE Data Storage"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.database_name = None
        self._initialize_mongodb()
    
    @property
    def client(self):
        """Property to access mongo_client for backward compatibility"""
        return self.mongo_client
    
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
            self.database_name = database_name
            
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
                'nse_advances_declines': [
                    ('timestamp', DESCENDING),
                    ('market_type', 1),
                ],
                'nse_large_deals': [
                    ('timestamp', DESCENDING),
                    ('deal_type', 1),
                    ('symbol', 1),
                ],
                'nse_forthcoming_listings': [
                    ('timestamp', DESCENDING),
                    ('symbol', 1),
                    ('effective_date', DESCENDING),
                ],
                'nse_most_active_contracts': [
                    ('timestamp', DESCENDING),
                    ('instrument', 1),
                    ('symbol', 1),
                ],
                'nse_most_active_equities': [
                    ('timestamp', DESCENDING),
                    ('index_type', 1),
                    ('symbol', 1),
                ],
                'nse_most_active_underlying': [
                    ('timestamp', DESCENDING),
                    ('underlying', 1),
                ],
                'nse_new_listings': [
                    ('timestamp', DESCENDING),
                    ('listing_type', 1),
                    ('symbol', 1),
                ],
                'nse_week_52_data': [
                    ('timestamp', DESCENDING),
                    ('data_type', 1),
                    ('symbol', 1),
                ],
                'nse_indices_data': [
                    ('timestamp', DESCENDING),
                    ('index_name', 1),
                    ('symbol', 1),
                ],
                'nse_price_band_hitters': [
                    ('timestamp', DESCENDING),
                    ('band_type', 1),
                    ('symbol', 1),
                ],
                'nse_stock_events': [
                    ('timestamp', DESCENDING),
                    ('symbol', 1),
                    ('event_type', 1),
                ],
                'nse_gainers_losers': [
                    ('timestamp', DESCENDING),
                    ('data_type', 1),
                    ('category', 1),
                    ('symbol', 1),
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
    


    def save_data(self, data: List[Dict[str, Any]], collection_name: str) -> bool:
        """Saves data to the specified MongoDB collection."""
        if self.mongo_db is None:
            logger.error("MongoDB connection is not initialized.")
            return False

        try:
            collection = self.mongo_db[collection_name]
            if isinstance(data, dict):
                data = [data]

            # Clean old data before saving new data also we can't get data from the API so we need to clean the old data frist we check data is not empty
            if data and isinstance(data, list) and len(data) > 0:
                # Clean old data only if we successfully get data from the API
                collection.delete_many({})
                # Delete old data from the collection
                logger.info(f"Cleaning old data from {collection_name} collection {len(data)} records to delete old data.")
            else:
                logger.warning(f"No data provided for {collection_name}. Skipping deletion of old data.")
                return False
            
            # Insert data into the collection
            if not isinstance(data, list):
                logger.error(f"Data for {collection_name} must be a list of dictionaries.")
                return False
            
            result = collection.insert_many(data)
            logger.info(f"Inserted {len(result.inserted_ids)} documents into {collection_name}.")
            return True

        except OperationFailure as e:
            logger.error(f"Failed to insert data into {collection_name}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error saving data to {collection_name}: {str(e)}")
            return False



        



