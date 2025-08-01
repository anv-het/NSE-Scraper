from pymongo import MongoClient
from Utils.logger import get_logger
from Utils.mongo_client_master import get_masterdata_db

logger = get_logger(__name__)

def logger_extra_dict(user_id):
    return {"user_id": user_id}

def get_masterdata_info(symbol):
    """
    Get ExchangeInstrumentID, ExchangeSegment, and Series for a given symbol
    from GETMASTERDATA.MASTERDATA collection.
    """
    try:
        db = get_masterdata_db()

        # ✅ FIXED: explicit check for None
        if db is None:
            logger.warning("No DB connection returned by get_masterdata_db()", extra=logger_extra_dict("-"))
            return {
                "ExchangeInstrumentID": None,
                "ExchangeSegment": None,
                "Series": None
            }

        collection = db["MASTERDATA"]
        symbol_upper = symbol.strip().upper()

        # First try to match by Name field
        results = list(collection.find({"Name": symbol_upper}))

        # If no results found, try to match by identifier
        if not results:
            logger.info(f"No masterdata found for Name: {symbol_upper}, trying identifier match", extra=logger_extra_dict("-"))
            results = list(collection.find({"identifier": symbol_upper}))

        if not results:
            logger.warning(f"No masterdata found for symbol: {symbol_upper} (tried both Name and identifier)", extra=logger_extra_dict("-"))
            return {
                "ExchangeInstrumentID": None,
                "ExchangeSegment": None,
                "Series": None
            }

        def sort_key(doc):
            segment_priority = {"NSECM": 0, "BSECM": 1}
            segment = doc.get("ExchangeSegment", "")
            series = doc.get("Series", "")
            return (
                segment_priority.get(segment, 99),
                0 if (segment == "NSECM" and series == "EQ") else
                0 if (segment == "BSECM" and series == "A") else 1
            )

        results.sort(key=sort_key)
        best_match = results[0]

        return {
            "ExchangeInstrumentID": best_match.get("ExchangeInstrumentID"),
            "ExchangeSegment": best_match.get("ExchangeSegment"),
            "Series": best_match.get("Series")
        }

    except Exception as e:
        logger.error(f"Error in get_masterdata_info: {str(e)}", extra=logger_extra_dict("-"))
        return {
            "ExchangeInstrumentID": None,
            "ExchangeSegment": None,
            "Series": None
        }


def get_all_nsecm_bsecm_data():
    """
    Retrieve all documents from MASTERDATA where ExchangeSegment is either NSECM or BSECM.
    Returns a list of dictionaries.
    """
    try:
        db = get_masterdata_db()

        if db is None:
            logger.warning("No DB connection returned by get_masterdata_db()", extra=logger_extra_dict("-"))
            return []

        collection = db["MASTERDATA"]

        query = {
            "ExchangeSegment": {"$in": ["NSECM", "BSECM"]}
        }

        results = list(collection.find(query))

        logger.info(f"Retrieved {len(results)} documents from MASTERDATA where ExchangeSegment is NSECM or BSECM", extra=logger_extra_dict("-"))
        return results

    except Exception as e:
        logger.error(f"Error in get_all_nsecm_bsecm_data: {str(e)}", extra=logger_extra_dict("-"))
        return []