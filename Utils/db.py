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
        """Create IPO table with new schema if it doesn't exist"""
        try:
            if not self.sql_connection:
                if not self._create_sql_server_connection():
                    return False
            
            cursor = self.sql_connection.cursor()
            
            # Use new table name for the updated schema
            table_name = self.sql_server_config['table']
            
            # Check if table exists
            check_table_query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_SCHEMA = 'dbo'
            """
            
            cursor.execute(check_table_query, (table_name,))
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                logger.info(f"Creating table {table_name} in SQL Server with new schema...")
                
                create_table_query = f"""
                CREATE TABLE {table_name} (
                    -- Primary identifiers
                    ipoId VARCHAR(50) PRIMARY KEY,
                    
                    -- API Company Information
                    apiCompanyName NVARCHAR(255),
                    apiIpoStatus NVARCHAR(100),
                    apiIpoStatusFormatted NVARCHAR(100),
                    apiListedPrice DECIMAL(18,4),
                    apiListingGain DECIMAL(18,4),
                    apiGmpValue DECIMAL(18,4),
                    apiGmpPercent DECIMAL(18,4),
                    apiFireRating NVARCHAR(50),
                    apiFireRatingCount INT,
                    apiSubscription NVARCHAR(100),
                    apiPrice DECIMAL(18,4),
                    apiEstimatedListingPrice DECIMAL(18,4),
                    apiEstimatedListingPercent DECIMAL(18,4),
                    apiIssueSize NVARCHAR(100),
                    apiLot NVARCHAR(50),
                    apiPe DECIMAL(18,4),
                    apiIssueOpenDate DATE,
                    apiIssueCloseDate DATE,
                    apiBoaDate DATE,
                    apiListingAt DATE,
                    apiUrl NVARCHAR(500),
                    apiIpoCategory NVARCHAR(100),
                    apiIpoYear INT,

                    -- Scraping Information
                    scrapingDate DATETIME2,
                    detailUrl NVARCHAR(500),
                    scrapedCompanyName NVARCHAR(255),
                    companyLogoUrl NVARCHAR(500),
                    localLogoPath NVARCHAR(500),
                    companyFullNameScraped NVARCHAR(255),
                    aboutCompanyText NTEXT,
                    minOrderQuantityScraped NVARCHAR(100),
                    sharesPerLotScraped NVARCHAR(100),
                    ipoSummaryText NTEXT,
                    
                    -- Date Status and Parsing
                    ipoIssueOpeningDateStatus NVARCHAR(50),
                    ipoIssueOpeningDateParsed DATE,
                    ipoIssueClosingDateStatus NVARCHAR(50),
                    ipoIssueClosingDateParsed DATE,
                    ipoOpenDate NVARCHAR(100),
                    ipoCloseDate NVARCHAR(100),
                    basisOfAllotment NVARCHAR(100),
                    initiationOfRefunds NVARCHAR(100),
                    creditOfSharesToDemat NVARCHAR(100),
                    listingDate NVARCHAR(100),
                    ipoOpenDateStatus NVARCHAR(50),
                    ipoOpenDateParsed DATE,
                    ipoCloseDateStatus NVARCHAR(50),
                    ipoCloseDateParsed DATE,
                    listingDateStatus NVARCHAR(50),
                    listingDateParsed DATE,
                    basisOfAllotmentStatus NVARCHAR(50),
                    basisOfAllotmentParsed DATE,
                    initiationOfRefundsStatus NVARCHAR(50),
                    initiationOfRefundsParsed DATE,
                    creditOfSharesToDematStatus NVARCHAR(50),
                    creditOfSharesToDematParsed DATE,
                    
                    -- Lot Information
                    lotIssuePrice NVARCHAR(100),
                    lotMarketLot NVARCHAR(100),
                    lotIndividualInvestor NVARCHAR(100),
                    lotMinHniLots NVARCHAR(100),
                    lotMinSmallHniLots210Lakh NVARCHAR(100),
                    lotMinBigHniLots10PlusLakh NVARCHAR(100),
                    
                    -- GMP (Grey Market Premium) Data
                    seq NVARCHAR(50),
                    idGmpData NVARCHAR(50),
                    ipoIdGmpData NVARCHAR(50),
                    gmpDate NVARCHAR(100),
                    currentGmp NVARCHAR(50),
                    gmpComments NTEXT,
                    gmpCompareDesc NTEXT,
                    subjectToSauda NVARCHAR(100),
                    gmpCity NVARCHAR(100),
                    gmpVariation NVARCHAR(100),
                    maxIpoPrice NVARCHAR(50),
                    estimatedListingPrice NVARCHAR(50),
                    gmpPercentCalc NVARCHAR(50),
                    gmpDescOther NTEXT,
                    upDownStatus NVARCHAR(10),
                    gmpActiveRecordFlag NVARCHAR(10),
                    sub2SaudaRate NVARCHAR(50),
                    estProfit NVARCHAR(50),
                    createDate DATETIME2,
                    createDateGmp NVARCHAR(100),
                    lastUpdatedGmp NVARCHAR(100),
                    lastUpdated NVARCHAR(100),
                    
                    -- Table Data Fields
                    ipoIssueOpeningDateTable NVARCHAR(100),
                    ipoIssueClosingDateTable NVARCHAR(100),
                    ipoIssuePriceTable NVARCHAR(100),
                    drhpLinkTable NVARCHAR(500),
                    rhpLinkTable NVARCHAR(500),
                    listingAtTable NVARCHAR(100),
                    retailQuotaTable NVARCHAR(100),
                    ipoIssueTypeTable NVARCHAR(100),
                    ipoIssueSizeTable NVARCHAR(100),
                    freshIssueTable NVARCHAR(100),
                    faceValueTable NVARCHAR(100),
                    promoterHoldingPreIpoTable NVARCHAR(50),
                    promoterHoldingPostIpoTable NVARCHAR(50),
                    anchorListLinkTable NVARCHAR(500),
                    minOrderQuantityTable NVARCHAR(100),
                    lotSizeTable NVARCHAR(100),
                    allotmentStatusTable NVARCHAR(500),
                    
                    -- Metadata
                    lastUpdatedTimestamp NVARCHAR(100),
                    metaTitle NVARCHAR(500),
                    pageTitle NVARCHAR(500),
                    metaDesc NTEXT,
                    cacheKey NVARCHAR(100),
                    currentTime NVARCHAR(100),
                    scrapedAt DATETIME2,
                    companyFullName NVARCHAR(255),
                    companyFullNameNew NVARCHAR(255),
                    
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

                    -- Database management fields
                    createdAtDb DATETIME2 DEFAULT GETDATE(),
                    lastUpdatedDb DATETIME2 DEFAULT GETDATE(),
                    timestamp DATETIME2 DEFAULT GETDATE()
                )
                """
                
                cursor.execute(create_table_query)
                self.sql_connection.commit()
                logger.info(f"Table {table_name} created successfully with new schema")
                
                # Update config to use new table name
                self.sql_server_config['table'] = table_name
            else:
                logger.info(f"Table {table_name} already exists")
                # Update config to use new table name
                self.sql_server_config['table'] = table_name
            
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
        Updates existing records based on ipoId rather than delete-replace.
        Handles new IPO data format with nested objects and arrays.
        
        Args:
            data (list): List of IPO data dictionaries with new format
            
        Returns:
            dict: Result summary with counts
        """
        collection_name = "investorgain_ipo_data_v1"  # Updated to v1 for new format

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
                ipo_id = record.get('ipoId')
                if not ipo_id:
                    logger.warning("Record missing ipoId, skipping")
                    continue
                
                # Add updated timestamp
                record['lastUpdatedDb'] = datetime.now().isoformat()
                if 'createdAtDb' not in record:
                    record['createdAtDb'] = datetime.now().isoformat()
                
                # Use upsert operation with ipoId as unique identifier
                result = self.upsert_record(
                    collection_name=collection_name,
                    filter_criteria={"ipoId": ipo_id},
                    update_data=record
                )
                
                if result:
                    if result.upserted_id:
                        inserted_count += 1
                        logger.debug(f"Inserted new IPO record with ipoId: {ipo_id}")
                    elif result.modified_count > 0:
                        updated_count += 1
                        logger.debug(f"Updated existing IPO record with ipoId: {ipo_id}")
            
            logger.info(f"InvestorGain IPO data operation completed: {inserted_count} inserted, {updated_count} updated")
            
            return {
                "success": True,
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "total_processed": len(data),
                "collection_name": collection_name
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
        Handles the new IPO data format with proper type conversion.
        
        Args:
            data (list): List of IPO data dictionaries with new format
            
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
                ipo_id = record.get('ipoId')
                if not ipo_id:
                    logger.warning("Record missing ipoId, skipping SQL insert")
                    continue
                
                try:
                    # Check if record exists
                    check_query = f"SELECT COUNT(*) FROM {self.sql_server_config['table']} WHERE ipoId = ?"
                    cursor.execute(check_query, (ipo_id,))
                    exists = cursor.fetchone()[0] > 0
                    
                    # Helper function to safely convert values for SQL Server (updated for new format)
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
                                                
                                    return None
                                except:
                                    return None
                            return None
                            
                        if data_type == 'decimal':
                            try:
                                if isinstance(value, str):
                                    # Extract numbers from strings, handle special cases
                                    number_match = re.search(r'(\d+(?:\.\d+)?)', value.replace(',', '').replace('₹', ''))
                                    if number_match:
                                        return float(number_match.group(1))
                                return float(str(value).replace(',', '').replace('₹', '')) if value is not None else None
                            except:
                                return None
                                
                        if data_type == 'int':
                            try:
                                if isinstance(value, str):
                                    number_match = re.search(r'(\d+)', value.replace(',', ''))
                                    if number_match:
                                        return int(number_match.group(1))
                                return int(float(str(value).replace(',', ''))) if value is not None else None
                            except:
                                return None
                                
                        # Default string handling - truncate if too long
                        if value is None:
                            return None
                        str_value = str(value)
                        return str_value[:4000] if len(str_value) > 4000 else str_value  # SQL Server NVARCHAR limit
                    
                    # Prepare values for SQL insertion based on new IPO data format
                    sql_values = (
                        safe_sql_value(record.get('ipoId')),  # ipoId
                        
                        # API Company Information
                        safe_sql_value(record.get('apiCompanyName')),
                        safe_sql_value(record.get('apiIpoStatus')),
                        safe_sql_value(record.get('apiIpoStatusFormatted')),
                        safe_sql_value(record.get('apiListedPrice'), 'decimal'),
                        safe_sql_value(record.get('apiListingGain'), 'decimal'),
                        safe_sql_value(record.get('apiGmpValue'), 'decimal'),
                        safe_sql_value(record.get('apiGmpPercent'), 'decimal'),
                        safe_sql_value(record.get('apiFireRating')),
                        safe_sql_value(record.get('apiFireRatingCount'), 'int'),
                        safe_sql_value(record.get('apiSubscription')),
                        safe_sql_value(record.get('apiPrice'), 'decimal'),
                        safe_sql_value(record.get('apiEstimatedListingPrice'), 'decimal'),
                        safe_sql_value(record.get('apiEstimatedListingPercent'), 'decimal'),
                        safe_sql_value(record.get('apiIssueSize')),
                        safe_sql_value(record.get('apiLot')),
                        safe_sql_value(record.get('apiPe'), 'decimal'),
                        safe_sql_value(record.get('apiIssueOpenDate'), 'date'),
                        safe_sql_value(record.get('apiIssueCloseDate'), 'date'),
                        safe_sql_value(record.get('apiBoaDate'), 'date'),
                        safe_sql_value(record.get('apiListingAt'), 'date'),
                        safe_sql_value(record.get('apiUrl')),
                        safe_sql_value(record.get('apiIpoCategory')),
                        safe_sql_value(record.get('apiIpoYear')),
                        
                        # Scraping Information
                        safe_sql_value(record.get('scrapingDate'), 'datetime'),
                        safe_sql_value(record.get('detailUrl')),
                        safe_sql_value(record.get('scrapedCompanyName')),
                        safe_sql_value(record.get('companyLogoUrl')),
                        safe_sql_value(record.get('localLogoPath')),
                        safe_sql_value(record.get('companyFullNameScraped')),
                        safe_sql_value(record.get('aboutCompanyText')),
                        safe_sql_value(record.get('minOrderQuantityScraped')),
                        safe_sql_value(record.get('sharesPerLotScraped')),
                        safe_sql_value(record.get('ipoSummaryText')),
                        
                        # Date Status and Parsing
                        safe_sql_value(record.get('ipoIssueOpeningDateStatus')),
                        safe_sql_value(record.get('ipoIssueOpeningDateParsed'), 'date'),
                        safe_sql_value(record.get('ipoIssueClosingDateStatus')),
                        safe_sql_value(record.get('ipoIssueClosingDateParsed'), 'date'),
                        safe_sql_value(record.get('ipoOpenDate')),
                        safe_sql_value(record.get('ipoCloseDate')),
                        safe_sql_value(record.get('basisOfAllotment')),
                        safe_sql_value(record.get('initiationOfRefunds')),
                        safe_sql_value(record.get('creditOfSharesToDemat')),
                        safe_sql_value(record.get('listingDate')),
                        safe_sql_value(record.get('ipoOpenDateStatus')),
                        safe_sql_value(record.get('ipoOpenDateParsed'), 'date'),
                        safe_sql_value(record.get('ipoCloseDateStatus')),
                        safe_sql_value(record.get('ipoCloseDateParsed'), 'date'),
                        safe_sql_value(record.get('listingDateStatus')),
                        safe_sql_value(record.get('listingDateParsed'), 'date'),
                        safe_sql_value(record.get('basisOfAllotmentStatus')),
                        safe_sql_value(record.get('basisOfAllotmentParsed'), 'date'),
                        safe_sql_value(record.get('initiationOfRefundsStatus')),
                        safe_sql_value(record.get('initiationOfRefundsParsed'), 'date'),
                        safe_sql_value(record.get('creditOfSharesToDematStatus')),
                        safe_sql_value(record.get('creditOfSharesToDematParsed'), 'date'),
                        
                        # Lot Information
                        safe_sql_value(record.get('lotIssuePrice')),
                        safe_sql_value(record.get('lotMarketLot')),
                        safe_sql_value(record.get('lotIndividualInvestor')),
                        safe_sql_value(record.get('lotMinHniLots')),
                        safe_sql_value(record.get('lotMinSmallHniLots210Lakh')),
                        safe_sql_value(record.get('lotMinBigHniLots10PlusLakh')),
                        
                        # GMP Data
                        safe_sql_value(record.get('seq')),
                        safe_sql_value(record.get('idGmpData')),
                        safe_sql_value(record.get('ipoIdGmpData')),
                        safe_sql_value(record.get('gmpDate')),
                        safe_sql_value(record.get('currentGmp')),
                        safe_sql_value(record.get('gmpComments')),
                        safe_sql_value(record.get('gmpCompareDesc')),
                        safe_sql_value(record.get('subjectToSauda')),
                        safe_sql_value(record.get('gmpCity')),
                        safe_sql_value(record.get('gmpVariation')),
                        safe_sql_value(record.get('maxIpoPrice')),
                        safe_sql_value(record.get('estimatedListingPrice')),
                        safe_sql_value(record.get('gmpPercentCalc')),
                        safe_sql_value(record.get('gmpDescOther')),
                        safe_sql_value(record.get('upDownStatus')),
                        safe_sql_value(record.get('gmpActiveRecordFlag')),
                        safe_sql_value(record.get('sub2SaudaRate')),
                        safe_sql_value(record.get('estProfit')),
                        safe_sql_value(record.get('createDate'), 'datetime'),
                        safe_sql_value(record.get('createDateGmp')),
                        safe_sql_value(record.get('lastUpdatedGmp')),
                        safe_sql_value(record.get('lastUpdated')),
                        
                        # Table Data Fields
                        safe_sql_value(record.get('ipoIssueOpeningDateTable')),
                        safe_sql_value(record.get('ipoIssueClosingDateTable')),
                        safe_sql_value(record.get('ipoIssuePriceTable')),
                        safe_sql_value(record.get('drhpLinkTable')),
                        safe_sql_value(record.get('rhpLinkTable')),
                        safe_sql_value(record.get('listingAtTable')),
                        safe_sql_value(record.get('retailQuotaTable')),
                        safe_sql_value(record.get('ipoIssueTypeTable')),
                        safe_sql_value(record.get('ipoIssueSizeTable')),
                        safe_sql_value(record.get('freshIssueTable')),
                        safe_sql_value(record.get('faceValueTable')),
                        safe_sql_value(record.get('promoterHoldingPreIpoTable')),
                        safe_sql_value(record.get('promoterHoldingPostIpoTable')),
                        safe_sql_value(record.get('anchorListLinkTable')),
                        safe_sql_value(record.get('minOrderQuantityTable')),
                        safe_sql_value(record.get('lotSizeTable')),
                        safe_sql_value(record.get('allotmentStatusTable')),
                        
                        # Metadata
                        safe_sql_value(record.get('lastUpdatedTimestamp')),
                        safe_sql_value(record.get('metaTitle')),
                        safe_sql_value(record.get('pageTitle')),
                        safe_sql_value(record.get('metaDesc')),
                        safe_sql_value(record.get('cacheKey')),
                        safe_sql_value(record.get('currentTime')),
                        safe_sql_value(record.get('scrapedAt'), 'datetime'),
                        safe_sql_value(record.get('companyFullName')),
                        safe_sql_value(record.get('companyFullNameNew')),
                        
                        # Array Fields (stored as JSON)
                        safe_sql_value(record.get('ipoShareAllocation'), 'json'),
                        safe_sql_value(record.get('ipoDaywiseSubscriptionTable'), 'json'),
                        safe_sql_value(record.get('ipoSharesBidAmountTable'), 'json'),
                        safe_sql_value(record.get('ipoBiddingHistoryJson'), 'json'),
                        safe_sql_value(record.get('gmpTrendHistoryTable'), 'json'),
                        safe_sql_value(record.get('strengths'), 'json'),
                        safe_sql_value(record.get('objectives'), 'json'),
                        safe_sql_value(record.get('companyFinancialInformationRestatedConsolidated'), 'json'),
                        safe_sql_value(record.get('peerComparison'), 'json'),
                        
                        # Object Fields (stored as JSON)
                        safe_sql_value(record.get('companyAddress'), 'json'),
                        safe_sql_value(record.get('ipoRegistrar'), 'json'),
                        safe_sql_value(record.get('ipoLeadManager'), 'json'),
                        safe_sql_value(record.get('companySectorInfo'), 'json'),
                    )
                    
                    if exists:
                        # Update existing record
                        update_query = f"""
                        UPDATE {self.sql_server_config['table']} SET
                            apiCompanyName=?, apiIpoStatus=?, apiIpoStatusFormatted=?, apiListedPrice=?, apiListingGain=?,
                            apiGmpValue=?, apiGmpPercent=?, apiFireRating=?, apiFireRatingCount=?, apiSubscription=?,
                            apiPrice=?, apiEstimatedListingPrice=?, apiEstimatedListingPercent=?, apiIssueSize=?, apiLot=?,
                            apiPe=?, apiIssueOpenDate=?, apiIssueCloseDate=?, apiBoaDate=?, apiListingAt=?,
                            apiUrl=?, apiIpoCategory=?, apiIpoYear=?, scrapingDate=?, detailUrl=?, scrapedCompanyName=?,
                            companyLogoUrl=?, localLogoPath=?, companyFullNameScraped=?, aboutCompanyText=?, minOrderQuantityScraped=?,
                            sharesPerLotScraped=?, ipoSummaryText=?, ipoIssueOpeningDateStatus=?, ipoIssueOpeningDateParsed=?, ipoIssueClosingDateStatus=?,
                            ipoIssueClosingDateParsed=?, ipoOpenDate=?, ipoCloseDate=?, basisOfAllotment=?, initiationOfRefunds=?,
                            creditOfSharesToDemat=?, listingDate=?, ipoOpenDateStatus=?, ipoOpenDateParsed=?, ipoCloseDateStatus=?,
                            ipoCloseDateParsed=?, listingDateStatus=?, listingDateParsed=?, basisOfAllotmentStatus=?, basisOfAllotmentParsed=?,
                            initiationOfRefundsStatus=?, initiationOfRefundsParsed=?, creditOfSharesToDematStatus=?, creditOfSharesToDematParsed=?, lotIssuePrice=?,
                            lotMarketLot=?, lotIndividualInvestor=?, lotMinHniLots=?, lotMinSmallHniLots210Lakh=?, lotMinBigHniLots10PlusLakh=?,
                            seq=?, idGmpData=?, ipoIdGmpData=?, gmpDate=?, currentGmp=?,
                            gmpComments=?, gmpCompareDesc=?, subjectToSauda=?, gmpCity=?, gmpVariation=?,
                            maxIpoPrice=?, estimatedListingPrice=?, gmpPercentCalc=?, gmpDescOther=?, upDownStatus=?,
                            gmpActiveRecordFlag=?, sub2SaudaRate=?, estProfit=?, createDate=?, createDateGmp=?,
                            lastUpdatedGmp=?, lastUpdated=?, ipoIssueOpeningDateTable=?, ipoIssueClosingDateTable=?, ipoIssuePriceTable=?,
                            drhpLinkTable=?, rhpLinkTable=?, listingAtTable=?, retailQuotaTable=?, ipoIssueTypeTable=?,
                            ipoIssueSizeTable=?, freshIssueTable=?, faceValueTable=?, promoterHoldingPreIpoTable=?, promoterHoldingPostIpoTable=?,
                            anchorListLinkTable=?, minOrderQuantityTable=?, lotSizeTable=?, allotmentStatusTable=?, lastUpdatedTimestamp=?,
                            metaTitle=?, pageTitle=?, metaDesc=?, cacheKey=?, currentTime=?,
                            scrapedAt=?, companyFullName=?, companyFullNameNew=?, ipoShareAllocation=?, ipoDaywiseSubscriptionTable=?,
                            ipoSharesBidAmountTable=?, ipoBiddingHistoryJson=?, gmpTrendHistoryTable=?, strengths=?, objectives=?,
                            companyFinancialInformationRestatedConsolidated=?, peerComparison=?, companyAddress=?, ipoRegistrar=?, ipoLeadManager=?,
                            companySectorInfo=?, lastUpdatedDb=GETDATE()
                        WHERE ipoId=?
                        """
                        cursor.execute(update_query, sql_values[1:] + (ipo_id,))
                        updated_count += 1
                    else:
                        # Insert new record
                        insert_query = f"""
                        INSERT INTO {self.sql_server_config['table']} (
                            ipoId, apiCompanyName, apiIpoStatus, apiIpoStatusFormatted, apiListedPrice, apiListingGain,
                            apiGmpValue, apiGmpPercent, apiFireRating, apiFireRatingCount, apiSubscription,
                            apiPrice, apiEstimatedListingPrice, apiEstimatedListingPercent, apiIssueSize, apiLot,
                            apiPe, apiIssueOpenDate, apiIssueCloseDate, apiBoaDate, apiListingAt,
                            apiUrl, apiIpoCategory, apiIpoYear, scrapingDate, detailUrl, scrapedCompanyName,
                            companyLogoUrl, localLogoPath, companyFullNameScraped, aboutCompanyText, minOrderQuantityScraped,
                            sharesPerLotScraped, ipoSummaryText, ipoIssueOpeningDateStatus, ipoIssueOpeningDateParsed, ipoIssueClosingDateStatus,
                            ipoIssueClosingDateParsed, ipoOpenDate, ipoCloseDate, basisOfAllotment, initiationOfRefunds,
                            creditOfSharesToDemat, listingDate, ipoOpenDateStatus, ipoOpenDateParsed, ipoCloseDateStatus,
                            ipoCloseDateParsed, listingDateStatus, listingDateParsed, basisOfAllotmentStatus, basisOfAllotmentParsed,
                            initiationOfRefundsStatus, initiationOfRefundsParsed, creditOfSharesToDematStatus, creditOfSharesToDematParsed, lotIssuePrice,
                            lotMarketLot, lotIndividualInvestor, lotMinHniLots, lotMinSmallHniLots210Lakh, lotMinBigHniLots10PlusLakh,
                            seq, idGmpData, ipoIdGmpData, gmpDate, currentGmp,
                            gmpComments, gmpCompareDesc, subjectToSauda, gmpCity, gmpVariation,
                            maxIpoPrice, estimatedListingPrice, gmpPercentCalc, gmpDescOther, upDownStatus,
                            gmpActiveRecordFlag, sub2SaudaRate, estProfit, createDate, createDateGmp,
                            lastUpdatedGmp, lastUpdated, ipoIssueOpeningDateTable, ipoIssueClosingDateTable, ipoIssuePriceTable,
                            drhpLinkTable, rhpLinkTable, listingAtTable, retailQuotaTable, ipoIssueTypeTable,
                            ipoIssueSizeTable, freshIssueTable, faceValueTable, promoterHoldingPreIpoTable, promoterHoldingPostIpoTable,
                            anchorListLinkTable, minOrderQuantityTable, lotSizeTable, allotmentStatusTable, lastUpdatedTimestamp,
                            metaTitle, pageTitle, metaDesc, cacheKey, currentTime,
                            scrapedAt, companyFullName, companyFullNameNew, ipoShareAllocation, ipoDaywiseSubscriptionTable,
                            ipoSharesBidAmountTable, ipoBiddingHistoryJson, gmpTrendHistoryTable, strengths, objectives,
                            companyFinancialInformationRestatedConsolidated, peerComparison, companyAddress, ipoRegistrar, ipoLeadManager,
                            companySectorInfo
                        ) VALUES ({','.join(['?' for _ in sql_values])})
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
                "total_processed": len(data),
                "table_name": self.sql_server_config['table']
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




