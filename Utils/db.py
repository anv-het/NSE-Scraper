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
        try:
            db_path = configure.get('DB', 'DATABASE_PATH', fallback='nse_data.db')
            self.db_connection = sqlite3.connect(db_path, check_same_thread=False)
            self.db_connection.row_factory = sqlite3.Row
            self._create_sqlite_tables()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {str(e)}")
            raise
    
    def _initialize_mongodb(self):
        try:
            mongo_url = configure.get('MONGODB', 'URL')
            db_name = configure.get('MONGODB', 'DB_NAME')
            self.mongo_client = pymongo.MongoClient(mongo_url)
            self.mongo_db = self.mongo_client[db_name]
            self.mongo_client.admin.command('ping')  # Test connection
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB database: {str(e)}")
            raise
    
    def _create_sqlite_tables(self):
        try:
            cursor = self.db_connection.cursor()
            # Top gainers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS top_gainers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    category TEXT,
                    symbol TEXT,
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
                    market_type TEXT,
                    ca_ex_dt TEXT,
                    ca_purpose TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Top loosers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS top_loosers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    category TEXT,
                    symbol TEXT,
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
                    market_type TEXT,
                    ca_ex_dt TEXT,
                    ca_purpose TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # New listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS new_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    symbol TEXT,
                    company_name TEXT,
                    series TEXT,
                    listing_date TEXT,
                    face_value REAL,
                    issue_price REAL,
                    listing_price REAL,
                    listing_gains REAL,
                    listing_gains_percent REAL,
                    current_price REAL,
                    current_gains REAL,
                    current_gains_percent REAL,
                    market_cap REAL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # IPO data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ipo_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    company_name TEXT,
                    symbol TEXT,
                    series TEXT,
                    issue_start_date TEXT,
                    issue_end_date TEXT,
                    listing_date TEXT,
                    issue_price REAL,
                    issue_size REAL,
                    lot_size INTEGER,
                    issue_type TEXT,
                    category TEXT,
                    grade TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # All indexes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_indexes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    index_name TEXT,
                    index_symbol TEXT,
                    last_price REAL,
                    variation REAL,
                    percent_change REAL,
                    open_price REAL,
                    high REAL,
                    low REAL,
                    previous_close REAL,
                    year_high REAL,
                    year_low REAL,
                    pe REAL,
                    pb REAL,
                    div_yield REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db_connection.commit()
            logger.info("SQLite tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create SQLite tables: {str(e)}")
            raise
    
    def save_data(self, data: Dict, table_name: str):
        try:
            if self.db_type == DB_SQLITE:
                self._save_to_sqlite(data, table_name)
            elif self.db_type == DB_MONGODB:
                self._save_to_mongodb(data, table_name)
            logger.info(f"Data saved to {table_name} table")
        except Exception as e:
            logger.error(f"Failed to save data to {table_name}: {str(e)}")
            raise
    
    def _save_to_sqlite(self, data: Dict, table_name: str):
        try:
            cursor = self.db_connection.cursor()
            for record in data.get('data', []):
                if table_name in ['top_gainers', 'top_loosers']:
                    cursor.execute(f'''
                        INSERT INTO {table_name} (
                            timestamp, data_type, category, symbol, series,
                            open_price, high_price, low_price, ltp, prev_price,
                            net_price, per_change, trade_quantity, turnover,
                            market_type, ca_ex_dt, ca_purpose
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('timestamp'), data.get('data_type'),
                        record.get('category'), record.get('symbol'),
                        record.get('series'), record.get('open_price'),
                        record.get('high_price'), record.get('low_price'),
                        record.get('ltp'), record.get('prev_price'),
                        record.get('net_price'), record.get('per_change'),
                        record.get('trade_quantity'), record.get('turnover'),
                        record.get('market_type'), record.get('ca_ex_dt'),
                        record.get('ca_purpose')
                    ))
                elif table_name == 'new_listings':
                    cursor.execute('''
                        INSERT INTO new_listings (
                            timestamp, data_type, symbol, company_name, series,
                            listing_date, face_value, issue_price, listing_price,
                            listing_gains, listing_gains_percent, current_price,
                            current_gains, current_gains_percent, market_cap, category
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('timestamp'), data.get('data_type'),
                        record.get('symbol'), record.get('company_name'),
                        record.get('series'), record.get('listing_date'),
                        record.get('face_value'), record.get('issue_price'),
                        record.get('listing_price'), record.get('listing_gains'),
                        record.get('listing_gains_percent'), record.get('current_price'),
                        record.get('current_gains'), record.get('current_gains_percent'),
                        record.get('market_cap'), record.get('category')
                    ))
                elif table_name == 'ipo_data':
                    cursor.execute('''
                        INSERT INTO ipo_data (
                            timestamp, data_type, company_name, symbol, series,
                            issue_start_date, issue_end_date, listing_date,
                            issue_price, issue_size, lot_size, issue_type,
                            category, grade, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('timestamp'), data.get('data_type'),
                        record.get('company_name'), record.get('symbol'),
                        record.get('series'), record.get('issue_start_date'),
                        record.get('issue_end_date'), record.get('listing_date'),
                        record.get('issue_price'), record.get('issue_size'),
                        record.get('lot_size'), record.get('issue_type'),
                        record.get('category'), record.get('grade'),
                        record.get('status')
                    ))
                elif table_name == 'all_indexes':
                    cursor.execute('''
                        INSERT INTO all_indexes (
                            timestamp, data_type, index_name, index_symbol,
                            last_price, variation, percent_change, open_price,
                            high, low, previous_close, year_high, year_low,
                            pe, pb, div_yield
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.get('timestamp'), data.get('data_type'),
                        record.get('index_name'), record.get('index_symbol'),
                        record.get('last_price'), record.get('variation'),
                        record.get('percent_change'), record.get('open'),
                        record.get('high'), record.get('low'),
                        record.get('previous_close'), record.get('year_high'),
                        record.get('year_low'), record.get('pe'),
                        record.get('pb'), record.get('div_yield')
                    ))
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Failed to save data to SQLite: {str(e)}")
            raise
    
    def _save_to_mongodb(self, data: Dict, collection_name: str):
        try:
            collection = self.mongo_db[collection_name]
            document = {
                'timestamp': data.get('timestamp'),
                'data_type': data.get('data_type'),
                'data': data.get('data', []),
                'created_at': datetime.now().isoformat()
            }
            collection.insert_one(document)
        except Exception as e:
            logger.error(f"Failed to save data to MongoDB: {str(e)}")
            raise
    
    def get_latest_data(self, table_name: str, limit: int = 50) -> List[Dict]:
        try:
            if self.db_type == DB_SQLITE:
                return self._get_from_sqlite(table_name, limit)
            elif self.db_type == DB_MONGODB:
                return self._get_from_mongodb(table_name, limit)
        except Exception as e:
            logger.error(f"Failed to get data from {table_name}: {str(e)}")
            raise
    

    def _get_from_sqlite(self, table_name: str, limit: int) -> List[Dict]:
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(f'''
                SELECT * FROM {table_name} 
                ORDER BY datetime(created_at) DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get data from SQLite: {str(e)}")
            raise


    def _get_from_mongodb(self, collection_name: str, limit: int) -> List[Dict]:
        try:
            collection = self.mongo_db[collection_name]
            documents = collection.find().sort('created_at', -1).limit(limit)
            return list(documents)
        except Exception as e:
            logger.error(f"Failed to get data from MongoDB: {str(e)}")
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
