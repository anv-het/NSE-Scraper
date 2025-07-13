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

    def _create_sqlite_tables(self):
        try:
            cursor = self.db_connection.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS top_gainers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    series TEXT,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    ltp REAL,
                    prev_price REAL,
                    net_price REAL,
                    per_change REAL,
                    trade_quantity INTEGER,
                    turnover REAL,
                    category TEXT,
                    market_type TEXT,
                    ca_ex_dt TEXT,
                    ca_purpose TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS top_loosers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    series TEXT,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    ltp REAL,
                    prev_price REAL,
                    net_price REAL,
                    per_change REAL,
                    trade_quantity INTEGER,
                    turnover REAL,
                    category TEXT,
                    market_type TEXT,
                    ca_ex_dt TEXT,
                    ca_purpose TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_indexes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    index_name TEXT NOT NULL,
                    symbol TEXT,
                    series TEXT,
                    last_price REAL,
                    change REAL,
                    percent_change REAL,
                    open_price REAL,
                    high REAL,
                    low REAL,
                    previous_close REAL,
                    total_traded_volume INTEGER,
                    total_traded_value REAL,
                    year_high REAL,
                    year_low REAL,
                    near_wkh REAL,
                    near_wkl REAL,
                    per_change_365d REAL,
                    date_365d_ago TEXT,
                    per_change_30d REAL,
                    date_30d_ago TEXT,
                    chart_today_path TEXT,
                    chart_30d_path TEXT,
                    chart_365d_path TEXT
                )
            ''')


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nse_52_week_low (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    series TEXT,
                    company_name TEXT,
                    new_52_week_low REAL,
                    prev_52_week_low REAL,
                    prev_low_date TEXT,
                    ltp REAL,
                    prev_close REAL,
                    change REAL,
                    p_change REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nse_52_week_high (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    series TEXT,
                    company_name TEXT,
                    new_52_week_high REAL,
                    prev_52_week_high REAL,
                    prev_high_date TEXT,
                    ltp REAL,
                    prev_close REAL,
                    change REAL,
                    p_change REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_health (
                    service_name TEXT PRIMARY KEY,
                    last_hit_time TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            ''')

            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Failed to create SQLite tables: {str(e)}")
            raise

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

    def _delete_old_data_sqlite(self, table_name: str):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(f"DELETE FROM {table_name}")
            self.db_connection.commit()
            logger.info(f"Deleted old data from {table_name}")
        except Exception as e:
            logger.error(f"Failed to delete old data from {table_name}: {str(e)}")
            raise

    def _delete_old_data_mongodb(self, collection_name: str):
        try:
            result = self.mongo_db[collection_name].delete_many({})
            logger.info(f"Deleted {result.deleted_count} old documents from MongoDB collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete old data from MongoDB collection {collection_name}: {str(e)}")
            raise


    def _save_to_sqlite(self, data: Dict, table_name: str):
        try:
            cursor = self.db_connection.cursor()
            records = data.get("stocks", []) if table_name == "all_indexes" else data.get("data", [])
            timestamp = data.get("timestamp")
            scraped_at = data.get("scraped_at") or datetime.now().isoformat()

            # Only proceed if new data is available
            if not records:
                logger.warning(f"No new records to save for {table_name}. Skipping DB update.")
                return

            # Delete old data only if new data exists
            cursor.execute(f"DELETE FROM {table_name}")
            logger.info(f"Old data deleted from table: {table_name}")

            for record in records:
                if table_name in ['top_gainers', 'top_loosers']:
                    cursor.execute(f'''
                        INSERT INTO {table_name} (
                            timestamp, scraped_at, symbol, series, open_price,
                            high_price, low_price, ltp, prev_price, net_price,
                            per_change, trade_quantity, turnover, category,
                            market_type, ca_ex_dt, ca_purpose
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp, scraped_at,
                        record.get("symbol"), record.get("series"),
                        record.get("open_price"), record.get("high_price"),
                        record.get("low_price"), record.get("ltp"),
                        record.get("prev_price"), record.get("net_price"),
                        record.get("per_change"), record.get("trade_quantity"),
                        record.get("turnover"), record.get("category"),
                        record.get("market_type"), record.get("ca_ex_dt"),
                        record.get("ca_purpose")
                    ))

                elif table_name == 'all_indexes':
                    cursor.execute(f'''
                        INSERT INTO {table_name} (
                            timestamp, scraped_at, index_name, symbol, series,
                            last_price, change, percent_change, open_price,
                            high, low, previous_close, total_traded_volume,
                            total_traded_value, year_high, year_low, near_wkh,
                            near_wkl, per_change_365d, date_365d_ago,
                            per_change_30d, date_30d_ago, chart_today_path,
                            chart_30d_path, chart_365d_path
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp, scraped_at,
                        record.get("index_name"), record.get("symbol"), record.get("series"),
                        record.get("last_price"), record.get("change"), record.get("percent_change"),
                        record.get("open_price"), record.get("high"), record.get("low"),
                        record.get("previous_close"), record.get("total_traded_volume"),
                        record.get("total_traded_value"), record.get("year_high"), record.get("year_low"),
                        record.get("near_wkh"), record.get("near_wkl"), record.get("per_change_365d"),
                        record.get("date_365d_ago"), record.get("per_change_30d"), record.get("date_30d_ago"),
                        record.get("chart_today_path"), record.get("chart_30d_path"), record.get("chart_365d_path")
                    ))

                elif table_name == 'nse_52_week_low':
                    cursor.execute(f'''
                        INSERT INTO {table_name} (
                            timestamp, scraped_at, symbol, series, company_name,
                            new_52_week_low, prev_52_week_low, prev_low_date,
                            ltp, prev_close, change, p_change
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp, scraped_at,
                        record.get("symbol"), record.get("series"), record.get("company_name"),
                        record.get("new_52_week_low"), record.get("prev_52_week_low"), record.get("prev_low_date"),
                        record.get("ltp"), record.get("prev_close"), record.get("change"), record.get("p_change")
                    ))
                elif table_name == 'nse_52_week_high':
                    cursor.execute(f'''
                        INSERT INTO {table_name} (
                            timestamp, scraped_at, symbol, series, company_name,
                            new_52_week_high, prev_52_week_high, prev_high_date,
                            ltp, prev_close, change, p_change
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        timestamp, scraped_at,
                        record.get("symbol"), record.get("series"), record.get("company_name"),
                        record.get("new_52_week_high"), record.get("prev_52_week_high"), record.get("prev_high_date"),
                        record.get("ltp"), record.get("prev_close"), record.get("change"), record.get("p_change")
                    ))
                

            self.db_connection.commit()
            logger.info(f"Inserted {len(records)} new records into {table_name}")

        except Exception as e:
            logger.error(f"Failed to upsert SQLite data in {table_name}: {str(e)}")
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

    def get_latest_data(self, table_name: str, limit: int = 50) -> List[Dict]:
        if self.db_type == DB_SQLITE:
            return self._get_from_sqlite(table_name, limit)
        elif self.db_type == DB_MONGODB:
            return self._get_from_mongodb(table_name, limit)

    def _get_from_sqlite(self, table_name: str, limit: int) -> List[Dict]:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(f'''
                SELECT * FROM {table_name} ORDER BY datetime(timestamp) DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get data from SQLite {table_name}: {str(e)}")
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


    def get_latest_data_filtered(self, table: str, field: str, value: str, limit: int = 50):
        query = f"SELECT * FROM {table} WHERE {field} = %s ORDER BY timestamp DESC LIMIT %s"
        self.cursor.execute(query, (value, limit))
        return self.cursor.fetchall()

    def delete_records(self, table_name: str):
        """Clear all data from a specific table."""
        try:
            if self.db_type == DB_SQLITE:
                cursor = self.db_connection.cursor()
                cursor.execute(f"DELETE FROM {table_name}")
                self.db_connection.commit()
                logger.info(f"Cleared table: {table_name}")
            elif self.db_type == DB_MONGODB:
                result = self.mongo_db[table_name].delete_many({})
                logger.info(f"Cleared {result.deleted_count} documents from MongoDB collection: {table_name}")
        except Exception as e:
            logger.error(f"Failed to clear table {table_name}: {str(e)}")
            raise

    def get_data(self, table_name: str, limit: int = 50) -> List[Dict]:
            """Get data from a specific table."""
            try:
                if self.db_type == DB_SQLITE:
                    cursor = self.db_connection.cursor()
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT ?", (limit,))
                    return [dict(row) for row in cursor.fetchall()]
                elif self.db_type == DB_MONGODB:
                    collection = self.mongo_db[table_name]
                    return list(collection.find().sort("timestamp", -1).limit(limit))
            except Exception as e:
                logger.error(f"Failed to get data from {table_name}: {str(e)}")
                raise