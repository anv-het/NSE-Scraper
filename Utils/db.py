import sqlite3
import pymongo
from datetime import datetime
from typing import Dict, List
from Utils.logger import get_logger
from Utils.config_reader import configure
from Constant.general import DB_SQLITE, DB_MONGODB

logger = get_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_type = configure.get('DB', 'TYPE', fallback=DB_SQLITE).lower()
        self.db_connection = None
        self.mongo_client = None
        self.mongo_db = None
        self._initialize_database()

    def _initialize_database(self):
        try:
            if self.db_type == DB_SQLITE:
                self._initialize_sqlite()
            elif self.db_type == DB_MONGODB:
                self._initialize_mongodb()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
            logger.info(f"Database ({self.db_type}) initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def _initialize_sqlite(self):
        db_path = configure.get('DB', 'DATABASE_PATH', fallback='nse_data.db')
        self.db_connection = sqlite3.connect(db_path, check_same_thread=False)
        self.db_connection.row_factory = sqlite3.Row
        self._create_sqlite_tables()

    def _initialize_mongodb(self):
        mongo_url = configure.get('MONGODB', 'URL')
        db_name = configure.get('MONGODB', 'DB_NAME')
        self.mongo_client = pymongo.MongoClient(mongo_url)
        self.mongo_db = self.mongo_client[db_name]
        self.mongo_client.admin.command('ping')  # Test connection

    

    def save_data(self, data: Dict, table_name: str):
        if self.db_type == DB_SQLITE:
            if self._is_data_valid(data, table_name):
                self._delete_old_data_sqlite(table_name)
                self._save_to_sqlite(data, table_name)
            else:
                logger.warning(f"Skipped saving to {table_name}: Scraped data is empty or invalid")

        elif self.db_type == DB_MONGODB:
            if self._is_data_valid(data, table_name):
                self._delete_old_data_mongodb(table_name)
                self._save_to_mongodb(data, table_name)
            else:
                logger.warning(f"Skipped saving to MongoDB collection {table_name}: Scraped data is empty or invalid")

    def _is_data_valid(self, data: Dict, table_name: str) -> bool:
        key = "stocks" if table_name == "all_indexes" else "data"
        return data.get(key) and len(data.get(key)) > 0


    def _delete_old_data_mongodb(self, collection_name: str):
        try:
            result = self.mongo_db[collection_name].delete_many({})
            logger.info(f"Deleted {result.deleted_count} old documents from MongoDB collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete old data from MongoDB collection {collection_name}: {str(e)}")
            raise


    def _save_to_mongodb(self, data: Dict, collection_name: str):
        try:
            collection = self.mongo_db[collection_name]
            for record in data.get("data", []):
                query = {"timestamp": data.get("timestamp")}
                if "symbol" in record:
                    query["symbol"] = record["symbol"]
                elif "index_name" in record:
                    query["index_name"] = record["index_name"]

                collection.update_one(
                    filter=query,
                    update={"$set": {**record, "timestamp": data.get("timestamp"), "updated_at": datetime.utcnow()}},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Failed to upsert MongoDB data in {collection_name}: {str(e)}")
            raise


    def _get_from_mongodb(self, collection_name: str, limit: int) -> List[Dict]:
        try:
            collection = self.mongo_db[collection_name]
            return list(collection.find().sort("timestamp", -1).limit(limit))
        except Exception as e:
            logger.error(f"Failed to get data from MongoDB {collection_name}: {str(e)}")
            raise

    def close_connection(self):
        try:
            if self.db_type == DB_SQLITE and self.db_connection:
                self.db_connection.close()
            elif self.db_type == DB_MONGODB and self.mongo_client:
                self.mongo_client.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")


    
    def save_all_data(self, all_data: List[Dict], table_name: str):
        """Save all data at once - delete once, then insert all"""
        if self.db_type == DB_MONGODB:
            self._save_all_to_mongodb(all_data, table_name)


    def _save_all_to_mongodb(self, all_data: List[Dict], collection_name: str):
        """Save all indices data to MongoDB at once"""
        try:
            # Step 1: Delete all old data once
            result = self.mongo_db[collection_name].delete_many({})
            logger.info(f"Deleted {result.deleted_count} old documents from MongoDB collection {collection_name}")
            
            # Step 2: Prepare all documents for insertion
            documents = []
            for data in all_data:
                timestamp = data.get("timestamp")
                scraped_at = data.get("scraped_at") or datetime.now().isoformat()
                index_name = data.get("index_name")
                
                for record in data.get("stocks", []):
                    doc = {
                        "timestamp": timestamp,
                        "scraped_at": scraped_at,
                        "index_name": index_name,
                        **record
                    }
                    documents.append(doc)
            
            # Step 3: Insert all documents at once
            if documents:
                result = self.mongo_db[collection_name].insert_many(documents)
                logger.info(f"Successfully inserted {len(result.inserted_ids)} documents from {len(all_data)} indices into MongoDB collection {collection_name}")
            else:
                logger.warning("No documents to insert into MongoDB")
                
        except Exception as e:
            logger.error(f"Failed to save all data to MongoDB collection {collection_name}: {str(e)}")
            raise
