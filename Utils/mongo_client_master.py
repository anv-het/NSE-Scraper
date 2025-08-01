from Utils.logger import get_logger
from Utils.config_reader import configure
from pymongo import MongoClient

logger = get_logger(__name__)

_masterdata_db = None  # Cached DB instance

def get_masterdata_db():
    global _masterdata_db
    if _masterdata_db is not None:
        return _masterdata_db

    try:
        uri = configure.get("DATABASE", "MONGO_URI")
        db_name = configure.get("DATABASE", "DB_NAME1")


        if not uri or not db_name:
            raise ValueError("MASTERDATA_URI or MASTERDATA_DB is missing in config")

        client = MongoClient(uri)
        db = client[db_name]

        # ✅ Validate DB object before caching
        if isinstance(db.name, str) and db.name:
            _masterdata_db = db
            logger.info(f"Connected to MongoDB Masterdata DB: {db.name}")
            return _masterdata_db
        else:
            raise ValueError("Invalid database name (NoneType)")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Masterdata: {str(e)}")
        return None
