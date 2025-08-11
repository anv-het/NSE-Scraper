import pymongo
import pyodbc
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from Utils.logger import get_logger
from Utils.config_reader import configure

logger = get_logger(__name__)

# Global MongoDB connection for GETMASTERDATA
mongo_db1 = None

def initialize_masterdata_connection():
    """Initialize global MongoDB connection for GETMASTERDATA"""
    global mongo_db1
    try:
        # Use DATABASE section instead of MONGODB
        mongo_uri = configure.get('DATABASE', 'MONGO_URI')
        db_name = configure.get('DATABASE', 'DB_NAME1')
        client = MongoClient(mongo_uri)
        mongo_db1 = client[db_name]
        logger.info(f"Global GETMASTERDATA MongoDB connection initialized: {db_name}")
    except Exception as e:
        logger.error(f"Failed to initialize global GETMASTERDATA MongoDB connection: {str(e)}")
        raise

# Initialize the connection when module is loaded
initialize_masterdata_connection()

class DatabaseManager:
    """Dual Database Manager for NSE Data Storage: MongoDB for NSE data, SQL Server for IPO data"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.database_name = None
        # Additional MongoDB connection for GETMASTERDATA
        self.mongo_client1 = None
        self.mongo_db1 = None
        # SQL Server connection properties
        self.sql_connection = None
        self.sql_server_config = {}
        self._initialize_mongodb()
        self._initialize_masterdata_mongodb()
        self._initialize_sql_server_config()
    
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
    
    def _initialize_masterdata_mongodb(self):
        """Initialize MongoDB connection for GETMASTERDATA database"""
        try:
            # Use DATABASE section instead of MONGODB
            mongo_uri = configure.get('DATABASE', 'MONGO_URI')
            db_name = configure.get('DATABASE', 'DB_NAME1')
            
            self.mongo_client1 = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.mongo_client1.admin.command('ping')
            self.mongo_db1 = self.mongo_client1[db_name]
            
            logger.info(f"Connected to GETMASTERDATA MongoDB: {mongo_uri}, Database: {db_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to GETMASTERDATA MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error initializing GETMASTERDATA MongoDB: {str(e)}")
            raise
    
    def _initialize_sql_server_config(self):
        """Initialize SQL Server connection configuration"""
        try:
            self.sql_server_config = {
                'host': configure.get('DATABASE', 'SQL_SERVER_HOST'),
                'driver': configure.get('DATABASE', 'SQL_SERVER_DRIVER'),
                'port': configure.get('DATABASE', 'SQL_SERVER_PORT'),
                'username': configure.get('DATABASE', 'SQL_SERVER_USERNAME'),
                'password': configure.get('DATABASE', 'SQL_SERVER_PASSWORD'),
                'database': configure.get('DATABASE', 'SQL_SERVER_DATABASE_NAME'),
                'table': configure.get('DATABASE', 'SQL_SERVER_TABLE_NAME')
            }
            
            logger.info(f"SQL Server configuration loaded for host: {self.sql_server_config['host']}")
            
        except Exception as e:
            logger.error(f"Error loading SQL Server configuration: {str(e)}")
            # Don't raise exception here as SQL Server is optional for other operations
    
    def _create_sql_server_connection(self):
        """Create SQL Server connection"""
        try:
            connection_string = (
                f"DRIVER={{{self.sql_server_config['driver']}}};"
                f"SERVER={self.sql_server_config['host']},{self.sql_server_config['port']};"
                f"DATABASE={self.sql_server_config['database']};"
                f"UID={self.sql_server_config['username']};"
                f"PWD={self.sql_server_config['password']};"
                f"TrustServerCertificate=yes;"
            )
            
            self.sql_connection = pyodbc.connect(connection_string)
            logger.info(f"Connected to SQL Server: {self.sql_server_config['host']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {str(e)}")
            return False
    
    def _ensure_ipo_table_exists(self):
        """Create IPO table if it doesn't exist"""
        try:
            if not self.sql_connection:
                if not self._create_sql_server_connection():
                    return False
            
            cursor = self.sql_connection.cursor()
            
            # Check if table exists
            check_table_query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_SCHEMA = 'dbo'
            """
            
            cursor.execute(check_table_query, (self.sql_server_config['table'],))
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                logger.info(f"Creating table {self.sql_server_config['table']} in SQL Server...")
                
                create_table_query = f"""
                CREATE TABLE {self.sql_server_config['table']} (
                    ipoId INT PRIMARY KEY,
                    apiCompanyName VARCHAR(255),
                    apiIpoCategory VARCHAR(255),
                    apiIssueSize FLOAT,
                    apiIssueOpenDate DATE,
                    apiIssueEndDate DATE,
                    apiListingAt VARCHAR(255),
                    apiIpoStatus VARCHAR(255),
                    apiIpoStatusFormatted VARCHAR(255),
                    
                    -- Scraping Information
                    scrapingDate DATETIME2,
                    detailUrl VARCHAR(255),
                    scrapedCompanyName VARCHAR(255),
                    companyLogoUrl VARCHAR(255),
                    localLogoPath VARCHAR(255),
                    companyFullNameScraped VARCHAR(255),
                    aboutCompanyText TEXT,

                    -- IPO Details
                    minOrderQuantityScraped INT,
                    sharesPerLotScraped INT,
                    ipoSummaryText TEXT,

                    -- Date Status and Parsing
                    ipoIssueOpeningDateStatus VARCHAR(255),
                    ipoIssueOpeningDateParsed DATE,
                    ipoIssueClosingDateStatus VARCHAR(255),
                    ipoIssueClosingDateParsed DATE,
                    ipoOpenDate DATE,
                    ipoCloseDate DATE,

                    -- Timeline Information
                    basisOfAllotment TEXT,
                    initiationOfRefunds DATE,
                    creditOfSharesToDemat DATE,
                    listingDate DATE,
                    
                    -- Additional Date Status Fields
                    ipoOpenDateStatus VARCHAR(255),
                    ipoOpenDateParsed DATE,
                    ipoCloseDateStatus VARCHAR(255),
                    ipoCloseDateParsed DATE,
                    listingDateStatus VARCHAR(255),
                    listingDateParsed DATE,
                    basisOfAllotmentStatus VARCHAR(255),
                    basisOfAllotmentParsed DATE,
                    initiationOfRefundsStatus VARCHAR(255),
                    initiationOfRefundsParsed DATE,
                    creditOfSharesToDematStatus VARCHAR(255),
                    creditOfSharesToDematParsed DATE,
                    
                    -- Lot Information
                    lotIssuePrice FLOAT,
                    lotMarketLot INT,
                    lotIndividualInvestor INT,
                    lotMinHniLots INT,
                    lotMinSmallHniLots210Lakh INT,
                    lotMinBigHniLots10PlusLakh INT,
                    
                    -- GMP (Grey Market Premium) Data
                    seq INT,
                    idGmpData INT,
                    ipoIdGmpData INT,
                    gmpDate DATE,
                    currentGmp FLOAT,
                    gmpComments TEXT,
                    gmpCompareDesc TEXT,
                    subjectToSauda VARCHAR(255),
                    gmpCity VARCHAR(255),
                    gmpVariation FLOAT,
                    maxIpoPrice FLOAT,
                    estimatedListingPrice FLOAT,
                    gmpPercentCalc FLOAT,
                    gmpDescOther TEXT,
                    upDownStatus VARCHAR(255),
                    gmpActiveRecordFlag BIT,
                    sub2SaudaRate FLOAT,
                    estProfit FLOAT,
                    createDate DATETIME2,
                    createDateGmp DATETIME2,
                    lastUpdatedGmp DATETIME2,
                    lastUpdated DATETIME2,
                    
                    -- Table Data Fields
                    ipoIssueOpeningDateTable DATE,
                    ipoIssueClosingDateTable DATE,
                    ipoIssuePriceTable FLOAT,
                    drhpLinkTable VARCHAR(255),
                    rhpLinkTable VARCHAR(255),
                    listingAtTable VARCHAR(255),
                    retailQuotaTable FLOAT,
                    ipoIssueTypeTable VARCHAR(255),
                    ipoIssueSizeTable FLOAT,
                    freshIssueTable FLOAT,
                    faceValueTable FLOAT,
                    promoterHoldingPreIpoTable FLOAT,
                    promoterHoldingPostIpoTable FLOAT,
                    anchorListLinkTable VARCHAR(255),
                    minOrderQuantityTable INT,
                    lotSizeTable INT,
                    allotmentStatusTable VARCHAR(255),
                    
                    -- Metadata
                    lastUpdatedTimestamp DATETIME2,
                    metaTitle VARCHAR(255),
                    pageTitle VARCHAR(255),
                    metaDesc TEXT,
                    cacheKey VARCHAR(255),
                    currentTime DATETIME2,
                    scrapedAt DATETIME2,
                    
                    -- Array Fields (stored as JSON)
                    ipoShareAllocation NVARCHAR(MAX),
                    ipoDaywiseSubscriptionTable NVARCHAR(MAX),
                    ipoSharesBidAmountTable NVARCHAR(MAX),
                    ipoBiddingHistoryJson NVARCHAR(MAX),
                    gmpTrendHistoryTable NVARCHAR(MAX),
                    strengths NVARCHAR(MAX),
                    objectives NVARCHAR(MAX),
                    companyFinancialInformationRestatedConsolidated NVARCHAR(MAX),
                    peerComparison NVARCHAR(MAX),
                    
                    -- Object Fields (stored as JSON)
                    companyAddress NVARCHAR(MAX),
                    ipoRegistrar NVARCHAR(MAX),
                    ipoLeadManager NVARCHAR(MAX),
                    companySectorInfo NVARCHAR(MAX),

                    -- System timestamp for tracking
                    timestamp DATETIME2 DEFAULT GETDATE()
                )
                """
                
                cursor.execute(create_table_query)
                self.sql_connection.commit()
                logger.info(f"Table {self.sql_server_config['table']} created successfully")
            else:
                logger.info(f"Table {self.sql_server_config['table']} already exists")
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring IPO table exists: {str(e)}")
            return False
    
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
                'nse_stockwise_event': [
                    ('timestamp', DESCENDING),
                    ('symbol', 1),
                    ('event_type', 1),
                ],
                'nse_gainers_losers': [
                    ('timestamp', DESCENDING),
                    ('data_type', 1),
                    ('category', 1),
                    ('symbol', 1),
                ],
                'nse_special_preopen_listings': [
                    ('timestamp', DESCENDING),
                    ('symbol', 1),
                    ('listing_type', 1),
                ],
                'nse_recent_listings': [
                    ('timestamp', DESCENDING),
                    ('symbol', 1),
                    ('listing_type', 1),
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
        

    def save_stockwise_event_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Save data to 'nse_stockwise_event' collection.
        Delete only old data for the symbols in the incoming data.
        """
        if self.mongo_db is None:
            logger.error("MongoDB connection is not initialized.")
            return False

        if not data or not isinstance(data, list):
            logger.warning("No valid data provided for stockwise event save.")
            return False
        
        try:
            collection = self.mongo_db['nse_stockwise_event']

            # Extract all symbols from the data
            symbols = set()
            for item in data:
                symbol = item.get('symbol')
                if symbol:
                    symbols.add(symbol)

            if symbols:
                # Delete old data for these symbols only
                delete_result = collection.delete_many({'symbol': {'$in': list(symbols)}})
                logger.info(f"Deleted {delete_result.deleted_count} old records for symbols {symbols} in nse_stockwise_event.")

            # Insert new data
            result = collection.insert_many(data)
            logger.info(f"Inserted {len(result.inserted_ids)} new documents into nse_stockwise_event.")
            return True
        
        except Exception as e:
            logger.error(f"Error saving stockwise event data: {str(e)}")
            return False

    def upsert_record(self, collection_name: str, filter_criteria: Dict[str, Any], update_data: Dict[str, Any]):
        """
        Upserts a single record in the specified MongoDB collection.
        Updates the record if it exists, inserts if it doesn't.
        
        Args:
            collection_name (str): Name of the MongoDB collection
            filter_criteria (dict): Criteria to find the existing record
            update_data (dict): Data to update/insert
            
        Returns:
            pymongo.results.UpdateResult: Result of the upsert operation
        """
        if self.mongo_db is None:
            logger.error("MongoDB connection is not initialized.")
            return None

        try:
            collection = self.mongo_db[collection_name]
            
            # Add timestamp for tracking
            update_data['updated_at'] = datetime.now(timezone.utc)
            if 'created_at' not in update_data:
                update_data['created_at'] = datetime.now(timezone.utc)
            
            # Perform upsert operation
            result = collection.replace_one(
                filter_criteria, 
                update_data, 
                upsert=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error upserting record in {collection_name}: {str(e)}")
            return None

    def save_investorgain_ipo_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Saves InvestorGain IPO data to MongoDB using upsert operations.
        Updates existing records based on ipo_id rather than delete-replace.
        
        Args:
            data (list): List of IPO data dictionaries
            
        Returns:
            dict: Result summary with counts
        """
        collection_name = "investorgain_ipo_data_v1"
        
        if self.mongo_db is None:
            logger.error("MongoDB connection is not initialized.")
            return {"success": False, "message": "MongoDB connection not initialized"}

        if not data or not isinstance(data, list):
            logger.warning("No valid data provided for InvestorGain IPO save.")
            return {"success": False, "message": "No valid data provided"}
        
        try:
            updated_count = 0
            inserted_count = 0
            
            # Process each record individually for update-based saving
            for record in data:
                ipo_id = record.get('ipoId')  # Changed from 'ipo_id' to 'ipoId' to match formatter output
                if not ipo_id:
                    logger.warning("Record missing ipoId, skipping")
                    continue
                
                # Use upsert operation
                result = self.upsert_record(
                    collection_name=collection_name,
                    filter_criteria={"ipoId": ipo_id},  # Changed from "ipo_id" to "ipoId"
                    update_data=record
                )
                
                if result:
                    if result.upserted_id:
                        inserted_count += 1
                    elif result.modified_count > 0:
                        updated_count += 1
            
            logger.info(f"InvestorGain IPO data operation completed: {inserted_count} inserted, {updated_count} updated")
            
            return {
                "success": True,
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "total_processed": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error saving InvestorGain IPO data: {str(e)}")
            return {
                "success": False,
                "message": f"Database error: {str(e)}"
            }

    def save_investorgain_ipo_data_to_sql(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Saves InvestorGain IPO data to SQL Server using upsert operations.
        
        Args:
            data (list): List of IPO data dictionaries
            
        Returns:
            dict: Result summary with counts
        """
        if not data or not isinstance(data, list):
            logger.warning("No valid data provided for InvestorGain IPO SQL save.")
            return {"success": False, "message": "No valid data provided"}
        
        try:
            # Ensure SQL Server connection and table
            if not self._create_sql_server_connection():
                return {"success": False, "message": "Failed to connect to SQL Server"}
            
            if not self._ensure_ipo_table_exists():
                return {"success": False, "message": "Failed to create/verify IPO table"}
            
            cursor = self.sql_connection.cursor()
            inserted_count = 0
            updated_count = 0
            
            for record in data:
                ipo_id = record.get('ipoId')  # Changed from 'ipo_id' to 'ipoId' to match formatter output
                if not ipo_id:
                    logger.warning("Record missing ipoId, skipping SQL insert")
                    continue
                
                try:
                    # Check if record exists
                    check_query = f"SELECT COUNT(*) FROM {self.sql_server_config['table']} WHERE ipoId = ?"
                    cursor.execute(check_query, (ipo_id,))
                    exists = cursor.fetchone()[0] > 0
                    
                    # Enhanced helper function to safely convert values for SQL Server
                    def safe_sql_value(value, data_type='string'):
                        import re
                        from datetime import datetime
                        
                        if value is None or value == 'N/A' or value == '' or (isinstance(value, str) and value.strip() == ''):
                            return None
                            
                        if data_type == 'json' and (isinstance(value, (dict, list))):
                            return json.dumps(value, ensure_ascii=False)
                            
                        if data_type == 'date':
                            if isinstance(value, str):
                                try:
                                    if value and value.strip():
                                        # Handle various date formats including ISO format and text dates
                                        date_formats = [
                                            '%Y-%m-%d', 
                                            '%d-%m-%Y', 
                                            '%Y-%m-%d %H:%M:%S', 
                                            '%d/%m/%Y',
                                            '%Y-%m-%dT%H:%M:%S.%fZ',
                                            '%Y-%m-%dT%H:%M:%S'
                                        ]
                                        
                                        for fmt in date_formats:
                                            try:
                                                parsed_date = datetime.strptime(value.strip(), fmt)
                                                return parsed_date.date()
                                            except ValueError:
                                                continue
                                        
                                        # Handle text dates like "7th Aug 2025", "12th Aug 2025"
                                        text_date_match = re.search(r'(\d{1,2})[^\d]*(\w{3})[^\d]*(\d{4})', value)
                                        if text_date_match:
                                            day, month_abbr, year = text_date_match.groups()
                                            month_map = {
                                                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                                            }
                                            if month_abbr in month_map:
                                                try:
                                                    date_str = f"{year}-{month_map[month_abbr]}-{day.zfill(2)}"
                                                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                                                except:
                                                    pass
                                                    
                                    return None
                                except:
                                    return None
                            return None
                            
                        if data_type == 'datetime':
                            if isinstance(value, str):
                                try:
                                    if value and value.strip():
                                        datetime_formats = [
                                            '%Y-%m-%d %H:%M:%S', 
                                            '%Y-%m-%dT%H:%M:%S', 
                                            '%Y-%m-%d',
                                            '%Y-%m-%dT%H:%M:%S.%fZ',
                                            '%Y-%m-%dT%H:%M:%S.%f'
                                        ]
                                        
                                        for fmt in datetime_formats:
                                            try:
                                                return datetime.strptime(value.strip(), fmt)
                                            except ValueError:
                                                continue
                                                
                                        # Handle date-time strings like "Aug 5th 2025 10:35 AM"
                                        datetime_match = re.search(r'(\w{3})\s+(\d{1,2})[^\d]*(\d{4})\s+(\d{1,2}):(\d{2})', value)
                                        if datetime_match:
                                            month_abbr, day, year, hour, minute = datetime_match.groups()
                                            month_map = {
                                                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                                                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                                                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                                            }
                                            if month_abbr in month_map:
                                                try:
                                                    datetime_str = f"{year}-{month_map[month_abbr]}-{day.zfill(2)} {hour.zfill(2)}:{minute}:00"
                                                    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                                                except:
                                                    pass
                                    return None
                                except:
                                    return None
                            return None
                            
                        if data_type == 'int':
                            try:
                                if isinstance(value, str):
                                    # Extract numbers from strings like "54Shares", "1 lot", "102"
                                    number_match = re.search(r'(\d+)', value.replace(',', ''))
                                    if number_match:
                                        return int(number_match.group(1))
                                return int(float(str(value).replace(',', ''))) if value is not None else None
                            except:
                                return None
                                
                        if data_type == 'float':
                            try:
                                if isinstance(value, str):
                                    # Handle various formats like "400.60 Cr", "₹139.00-147.00", "12.93", "1500/21000"
                                    if '/' in value:  # Handle ratios like "1500/21000"
                                        parts = value.split('/')
                                        if len(parts) >= 2 and parts[0].strip().replace('.', '').replace('-', '').isdigit():
                                            return float(parts[0].strip())
                                    
                                    # Extract first number from strings
                                    number_match = re.search(r'(\d+(?:\.\d+)?)', value.replace(',', '').replace('₹', ''))
                                    if number_match:
                                        return float(number_match.group(1))
                                
                                return float(str(value).replace(',', '').replace('₹', '')) if value is not None else None
                            except:
                                return None
                                
                        if data_type == 'bool':
                            if isinstance(value, bool):
                                return value
                            if isinstance(value, str):
                                return value.lower() in ['true', '1', 'yes', 'on']
                            if isinstance(value, (int, float)):
                                return bool(value)
                            return bool(value) if value is not None else None
                            
                        # Default string handling
                        if value is None:
                            return None
                        return str(value)[:500] if len(str(value)) > 500 else str(value)  # Truncate long strings
                    
                    # Prepare values for SQL insertion based on actual formatter output
                    sql_values = (
                        safe_sql_value(record.get('ipoId'), 'string'),  # ID from formatter
                        safe_sql_value(record.get('companyName')),  # Company name
                        safe_sql_value(record.get('logoUrl')),  # Logo URL
                        safe_sql_value(record.get('issueType')),  # Issue type
                        safe_sql_value(record.get('listingSegment')),  # Listing segment
                        safe_sql_value(record.get('sector')),  # Sector
                        safe_sql_value(record.get('industry')),  # Industry
                        safe_sql_value(record.get('businessDescription')),  # Business description
                        safe_sql_value(record.get('marketCapCategory')),  # Market cap category
                        safe_sql_value(record.get('website')),  # Website
                        
                        # API Details from formatter
                        safe_sql_value(record.get('apiIssueSize')),  # "400.60 Cr"
                        safe_sql_value(record.get('apiFreshIssueSize')),  # Fresh issue size
                        safe_sql_value(record.get('apiOfferForSaleSize')),  # OFS size
                        safe_sql_value(record.get('apiIssueOpenDate'), 'date'),  # Issue open date
                        safe_sql_value(record.get('apiIssueCloseDate'), 'date'),  # Issue close date
                        safe_sql_value(record.get('apiListingDate'), 'date'),  # Listing date
                        safe_sql_value(record.get('apiAllotmentFinalizationDate'), 'date'),  # Allotment date
                        safe_sql_value(record.get('apiRefundInitiationDate'), 'date'),  # Refund date
                        safe_sql_value(record.get('apiDemandCollectionDate'), 'date'),  # Demand collection
                        safe_sql_value(record.get('apiMinimumOrderQuantity')),  # "54Shares"
                        safe_sql_value(record.get('apiPrice')),  # Price range
                        safe_sql_value(record.get('apiPriceRange')),  # Price range formatted
                        safe_sql_value(record.get('apiMinBidQuantity')),  # Min bid quantity
                        safe_sql_value(record.get('apiMaxBidQuantity')),  # Max bid quantity
                        safe_sql_value(record.get('apiMinApplicationAmount')),  # Min application amount
                        safe_sql_value(record.get('apiCutOffPrice')),  # Cut off price
                        safe_sql_value(record.get('apiLotSize')),  # Lot size
                        
                        # Status fields
                        safe_sql_value(record.get('status')),  # Status
                        safe_sql_value(record.get('ipoGrade')),  # IPO grade
                        safe_sql_value(record.get('isOpenForSubscription'), 'bool'),  # Is open
                        safe_sql_value(record.get('isListingToday'), 'bool'),  # Is listing today
                        safe_sql_value(record.get('isMainboard')),  # Is mainboard
                        safe_sql_value(record.get('isMainlineIpo')),  # Is mainline IPO
                        safe_sql_value(record.get('isSmeIpo')),  # Is SME IPO
                        safe_sql_value(record.get('isExpectedListing')),  # Is expected listing
                        
                        # Company details
                        safe_sql_value(record.get('registrar')),  # Registrar
                        safe_sql_value(record.get('leadManagers')),  # Lead managers
                        safe_sql_value(record.get('latestNews')),  # Latest news
                        safe_sql_value(record.get('aboutCompanyDescription')),  # About company
                        
                        # Market lot and order quantities
                        safe_sql_value(record.get('marketLot')),  # Market lot
                        safe_sql_value(record.get('minOrderQuantityScraped')),  # Min order qty scraped
                        safe_sql_value(record.get('maxOrderQuantityScraped')),  # Max order qty scraped
                        safe_sql_value(record.get('lotSizeScraped')),  # Lot size scraped
                        
                        # Date fields from scraper
                        safe_sql_value(record.get('issueDateOpen'), 'date'),  # Issue open date
                        safe_sql_value(record.get('issueDateClose'), 'date'),  # Issue close date
                        safe_sql_value(record.get('allotmentDate'), 'date'),  # Allotment date
                        safe_sql_value(record.get('listingDate'), 'date'),  # Listing date
                        safe_sql_value(record.get('refundDate'), 'date'),  # Refund date
                        safe_sql_value(record.get('expectedListingDate'), 'date'),  # Expected listing
                        
                        # Additional status and flags
                        safe_sql_value(record.get('hasExpectedListing'), 'bool'),  # Has expected listing
                        safe_sql_value(record.get('hasSubscriptionData'), 'bool'),  # Has subscription data
                        safe_sql_value(record.get('hasAllotmentInfo'), 'bool'),  # Has allotment info
                        safe_sql_value(record.get('hasFinancialInfo'), 'bool'),  # Has financial info
                        safe_sql_value(record.get('hasGmpData'), 'bool'),  # Has GMP data
                        safe_sql_value(record.get('hasLotInfo'), 'bool'),  # Has lot info
                        safe_sql_value(record.get('hasOfferDetails'), 'bool'),  # Has offer details
                        safe_sql_value(record.get('hasCompanyDetails'), 'bool'),  # Has company details
                        safe_sql_value(record.get('hasPromResults'), 'bool'),  # Has prom results
                        safe_sql_value(record.get('hasKeyDates'), 'bool'),  # Has key dates
                        safe_sql_value(record.get('hasReservationDetails'), 'bool'),  # Has reservation details
                        safe_sql_value(record.get('hasDocuments'), 'bool'),  # Has documents
                        safe_sql_value(record.get('hasReviews'), 'bool'),  # Has reviews
                        safe_sql_value(record.get('isClosed'), 'bool'),  # Is closed
                        safe_sql_value(record.get('isListed'), 'bool'),  # Is listed
                        safe_sql_value(record.get('isUpcoming'), 'bool'),  # Is upcoming
                        safe_sql_value(record.get('isActive'), 'bool'),  # Is active
                        safe_sql_value(record.get('isWithdrawn'), 'bool'),  # Is withdrawn
                        safe_sql_value(record.get('isPending'), 'bool'),  # Is pending
                        
                        # Subscription data
                        safe_sql_value(record.get('subscriptionStatus')),  # Subscription status
                        safe_sql_value(record.get('overallSubscription')),  # Overall subscription
                        safe_sql_value(record.get('qibSubscription')),  # QIB subscription
                        safe_sql_value(record.get('niiSubscription')),  # NII subscription
                        safe_sql_value(record.get('retailSubscription')),  # Retail subscription
                        safe_sql_value(record.get('employeeSubscription')),  # Employee subscription
                        safe_sql_value(record.get('othersSubscription')),  # Others subscription
                        safe_sql_value(record.get('totalApplications')),  # Total applications
                        safe_sql_value(record.get('totalAmount')),  # Total amount
                        
                        # Allotment information
                        safe_sql_value(record.get('allotmentStatus')),  # Allotment status
                        safe_sql_value(record.get('allotmentPercentage')),  # Allotment percentage
                        safe_sql_value(record.get('totalSharesAllotted')),  # Total shares allotted
                        safe_sql_value(record.get('listingGains')),  # Listing gains
                        safe_sql_value(record.get('listingPrice')),  # Listing price
                        safe_sql_value(record.get('currentPrice')),  # Current price
                        safe_sql_value(record.get('marketValue')),  # Market value
                        safe_sql_value(record.get('listing_gain_percentage')),  # Listing gain %
                        
                        # GMP data
                        safe_sql_value(record.get('gmpValue')),  # GMP value
                        safe_sql_value(record.get('gmpPercentage')),  # GMP percentage
                        safe_sql_value(record.get('gmpPrice')),  # GMP price
                        safe_sql_value(record.get('estimatedListing')),  # Estimated listing
                        safe_sql_value(record.get('lastGmpUpdate'), 'datetime'),  # Last GMP update
                        safe_sql_value(record.get('gmpTrend')),  # GMP trend
                        safe_sql_value(record.get('kostakRate')),  # KOSTAK rate
                        safe_sql_value(record.get('subjectToSauda')),  # Subject to sauda
                        
                        # URLs
                        safe_sql_value(record.get('ipoUrl')),  # IPO URL
                        safe_sql_value(record.get('prospectusUrl')),  # Prospectus URL
                        safe_sql_value(record.get('rhpUrl')),  # RHP URL
                        safe_sql_value(record.get('drhpUrl')),  # DRHP URL
                        safe_sql_value(record.get('addendumUrl')),  # Addendum URL
                        safe_sql_value(record.get('bseUrl')),  # BSE URL
                        safe_sql_value(record.get('nseUrl')),  # NSE URL
                        
                        # Review data
                        safe_sql_value(record.get('reviewRating')),  # Review rating
                        safe_sql_value(record.get('reviewRecommendation')),  # Review recommendation
                        safe_sql_value(record.get('analystRecommendation')),  # Analyst recommendation
                        safe_sql_value(record.get('riskLevel')),  # Risk level
                        safe_sql_value(record.get('investmentHorizon')),  # Investment horizon
                        
                        # JSON fields
                        safe_sql_value(record.get('financialInformation'), 'json'),  # Financial information
                        safe_sql_value(record.get('keyMetrics'), 'json'),  # Key metrics
                        safe_sql_value(record.get('promoterDetails'), 'json'),  # Promoter details
                        safe_sql_value(record.get('companyDetails'), 'json'),  # Company details
                        safe_sql_value(record.get('issueDetails'), 'json'),  # Issue details
                        safe_sql_value(record.get('sharesDetails'), 'json'),  # Shares details
                        safe_sql_value(record.get('reservationDetails'), 'json'),  # Reservation details
                        safe_sql_value(record.get('subscriptionData'), 'json'),  # Subscription data
                        safe_sql_value(record.get('allotmentDetails'), 'json'),  # Allotment details
                        safe_sql_value(record.get('gmpData'), 'json'),  # GMP data
                        safe_sql_value(record.get('timeline'), 'json'),  # Timeline
                        safe_sql_value(record.get('lotDetails'), 'json'),  # Lot details
                        safe_sql_value(record.get('offerDetails'), 'json'),  # Offer details
                        safe_sql_value(record.get('exchangeUrls'), 'json'),  # Exchange URLs
                        safe_sql_value(record.get('sourceUrls'), 'json'),  # Source URLs
                        safe_sql_value(record.get('reviewData'), 'json'),  # Review data
                        safe_sql_value(record.get('rawDataFromSource'), 'json'),  # Raw data from source
                        safe_sql_value(record.get('processingErrors'), 'json'),  # Processing errors
                        safe_sql_value(record.get('validationErrors'), 'json'),  # Validation errors
                        safe_sql_value(record.get('tags'), 'json'),  # Tags
                        safe_sql_value(record.get('categories'), 'json'),  # Categories
                        safe_sql_value(record.get('metadata'), 'json'),  # Metadata
                        
                        # Metadata fields
                        safe_sql_value(record.get('dataSource')),  # Data source
                        safe_sql_value(record.get('scrapeVersion')),  # Scrape version
                        safe_sql_value(record.get('isDataComplete'), 'bool'),  # Is data complete
                        safe_sql_value(record.get('dataQualityScore'), 'float'),  # Data quality score
                        safe_sql_value(record.get('notes')),  # Notes
                        safe_sql_value(record.get('lastUpdated'), 'datetime'),  # Last updated
                        safe_sql_value(record.get('scrapedAt'), 'datetime'),  # Scraped at
                    )
                    
                    if exists:
                        # Update existing record - **MAJOR ISSUE FIXED**
                        # The original query had completely different column names than the sql_values tuple
                        update_query = f"""
                        UPDATE {self.sql_server_config['table']} SET
                            companyName=?, logoUrl=?, issueType=?, listingSegment=?, sector=?,
                            industry=?, businessDescription=?, marketCapCategory=?, website=?, apiIssueSize=?,
                            apiFreshIssueSize=?, apiOfferForSaleSize=?, apiIssueOpenDate=?, apiIssueCloseDate=?, apiListingDate=?,
                            apiAllotmentFinalizationDate=?, apiRefundInitiationDate=?, apiDemandCollectionDate=?, apiMinimumOrderQuantity=?, apiPrice=?,
                            apiPriceRange=?, apiMinBidQuantity=?, apiMaxBidQuantity=?, apiMinApplicationAmount=?, apiCutOffPrice=?,
                            apiLotSize=?, status=?, ipoGrade=?, isOpenForSubscription=?, isListingToday=?,
                            isMainboard=?, isMainlineIpo=?, isSmeIpo=?, isExpectedListing=?, registrar=?,
                            leadManagers=?, latestNews=?, aboutCompanyDescription=?, marketLot=?, minOrderQuantityScraped=?,
                            maxOrderQuantityScraped=?, lotSizeScraped=?, issueDateOpen=?, issueDateClose=?, allotmentDate=?,
                            listingDate=?, refundDate=?, expectedListingDate=?, hasExpectedListing=?, hasSubscriptionData=?,
                            hasAllotmentInfo=?, hasFinancialInfo=?, hasGmpData=?, hasLotInfo=?, hasOfferDetails=?,
                            hasCompanyDetails=?, hasPromResults=?, hasKeyDates=?, hasReservationDetails=?, hasDocuments=?,
                            hasReviews=?, isClosed=?, isListed=?, isUpcoming=?, isActive=?,
                            isWithdrawn=?, isPending=?, subscriptionStatus=?, overallSubscription=?, qibSubscription=?,
                            niiSubscription=?, retailSubscription=?, employeeSubscription=?, othersSubscription=?, totalApplications=?,
                            totalAmount=?, allotmentStatus=?, allotmentPercentage=?, totalSharesAllotted=?, listingGains=?,
                            listingPrice=?, currentPrice=?, marketValue=?, listing_gain_percentage=?, gmpValue=?,
                            gmpPercentage=?, gmpPrice=?, estimatedListing=?, lastGmpUpdate=?, gmpTrend=?,
                            kostakRate=?, subjectToSauda=?, ipoUrl=?, prospectusUrl=?, rhpUrl=?,
                            drhpUrl=?, addendumUrl=?, bseUrl=?, nseUrl=?, reviewRating=?,
                            reviewRecommendation=?, analystRecommendation=?, riskLevel=?, investmentHorizon=?, financialInformation=?,
                            keyMetrics=?, promoterDetails=?, companyDetails=?, issueDetails=?, sharesDetails=?,
                            reservationDetails=?, subscriptionData=?, allotmentDetails=?, gmpData=?, timeline=?,
                            lotDetails=?, offerDetails=?, exchangeUrls=?, sourceUrls=?, reviewData=?,
                            rawDataFromSource=?, processingErrors=?, validationErrors=?, tags=?, categories=?,
                            metadata=?, dataSource=?, scrapeVersion=?, isDataComplete=?, dataQualityScore=?,
                            notes=?, lastUpdated=?, scrapedAt=?, timestamp=GETDATE()
                        WHERE ipoId=?
                        """
                        cursor.execute(update_query, sql_values[1:] + (ipo_id,))
                        updated_count += 1
                    else:
                        # Insert new record
                        insert_query = f"""
                        INSERT INTO {self.sql_server_config['table']} (
                            ipoId, companyName, logoUrl, issueType, listingSegment, sector,
                            industry, businessDescription, marketCapCategory, website, apiIssueSize,
                            apiFreshIssueSize, apiOfferForSaleSize, apiIssueOpenDate, apiIssueCloseDate, apiListingDate,
                            apiAllotmentFinalizationDate, apiRefundInitiationDate, apiDemandCollectionDate, apiMinimumOrderQuantity, apiPrice,
                            apiPriceRange, apiMinBidQuantity, apiMaxBidQuantity, apiMinApplicationAmount, apiCutOffPrice,
                            apiLotSize, status, ipoGrade, isOpenForSubscription, isListingToday,
                            isMainboard, isMainlineIpo, isSmeIpo, isExpectedListing, registrar,
                            leadManagers, latestNews, aboutCompanyDescription, marketLot, minOrderQuantityScraped,
                            maxOrderQuantityScraped, lotSizeScraped, issueDateOpen, issueDateClose, allotmentDate,
                            listingDate, refundDate, expectedListingDate, hasExpectedListing, hasSubscriptionData,
                            hasAllotmentInfo, hasFinancialInfo, hasGmpData, hasLotInfo, hasOfferDetails,
                            hasCompanyDetails, hasPromResults, hasKeyDates, hasReservationDetails, hasDocuments,
                            hasReviews, isClosed, isListed, isUpcoming, isActive,
                            isWithdrawn, isPending, subscriptionStatus, overallSubscription, qibSubscription,
                            niiSubscription, retailSubscription, employeeSubscription, othersSubscription, totalApplications,
                            totalAmount, allotmentStatus, allotmentPercentage, totalSharesAllotted, listingGains,
                            listingPrice, currentPrice, marketValue, listing_gain_percentage, gmpValue,
                            gmpPercentage, gmpPrice, estimatedListing, lastGmpUpdate, gmpTrend,
                            kostakRate, subjectToSauda, ipoUrl, prospectusUrl, rhpUrl,
                            drhpUrl, addendumUrl, bseUrl, nseUrl, reviewRating,
                            reviewRecommendation, analystRecommendation, riskLevel, investmentHorizon, financialInformation,
                            keyMetrics, promoterDetails, companyDetails, issueDetails, sharesDetails,
                            reservationDetails, subscriptionData, allotmentDetails, gmpData, timeline,
                            lotDetails, offerDetails, exchangeUrls, sourceUrls, reviewData,
                            rawDataFromSource, processingErrors, validationErrors, tags, categories,
                            metadata, dataSource, scrapeVersion, isDataComplete, dataQualityScore,
                            notes, lastUpdated, scrapedAt, timestamp
                        ) VALUES ({','.join(['?' for _ in sql_values])}, GETDATE())
                        """
                        cursor.execute(insert_query, sql_values)
                        inserted_count += 1
                    
                except Exception as record_error:
                    logger.error(f"Error processing IPO record {ipo_id}: {str(record_error)}")
                    continue
            
            self.sql_connection.commit()
            cursor.close()
            
            # Close connection after operation
            if self.sql_connection:
                self.sql_connection.close()
                self.sql_connection = None
            
            logger.info(f"SQL Server IPO data operation completed: {inserted_count} inserted, {updated_count} updated")
            
            return {
                "success": True,
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "total_processed": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error saving InvestorGain IPO data to SQL Server: {str(e)}")
            # Close connection on error
            if self.sql_connection:
                try:
                    self.sql_connection.close()
                except:
                    pass
                self.sql_connection = None
            return {
                "success": False,
                "message": f"SQL Server error: {str(e)}"
            }




