"""
NSE Data Formatter Utility
Formats raw NSE API responses into MongoDB-ready documents according to schema
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from Utils.logger import get_logger
from Utils.utilities_functions import clean_numeric_value

logger = get_logger(__name__)

class NSEDataFormatter:
    """Utility class for formatting NSE API responses into schema-compliant MongoDB documents"""

    # IST timezone offset
    IST = timezone(timedelta(hours=5, minutes=30))

    @staticmethod
    def generate_unique_id(identifier):
        # This function generates a unique id, you can replace this with any method like hashing
        return f"{identifier}-{datetime.now().timestamp()}"

    @staticmethod
    def parse_timestamp(timestamp_str: Optional[str] = None) -> str:
        """
        Returns ISO timestamp in IST from input string or current time.
        """
        try:
            if timestamp_str is None:
                dt = datetime.utcnow().replace(tzinfo=timezone.utc)
            else:
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str[:-1]
                dt = datetime.fromisoformat(timestamp_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            dt = datetime.utcnow().replace(tzinfo=timezone.utc)

        dt_ist = dt.astimezone(NSEDataFormatter.IST)
        return dt_ist.isoformat()

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert value to int"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def format_adv_decl_unch_data(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            formatted_data = []

            # Extract timestamp string from summary or use current UTC time
            timestamp_str = summary.get("timestamp", datetime.utcnow().isoformat())
            # Parse it uniformly using class method
            current_time_ist = NSEDataFormatter.parse_timestamp(None)

            # Helper function to format one entry
            def format_item(item: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "identifier": item.get("identifier"),
                    "symbol": item.get("symbol"),
                    "series": item.get("series"),
                    "market_type": item.get("marketType"),
                    "price_change_percent": item.get("pchange"),
                    "price_change_value": item.get("change"),
                    "base_price": item.get("basePrice"),
                    "previous_close": item.get("previousClose"),
                    "last_price": item.get("lastPrice"),
                    "total_traded_volume": item.get("totalTradedVolume"),
                    "issued_cap": item.get("issuedCap"),
                    "total_traded_value": item.get("totalTradedValue"),
                    "total_market_cap": item.get("totalMarketCap")
                }

            # Loop over all three categories
            for category in ["advance", "decline", "unchanged"]:
                for item in summary.get(category, []):
                    formatted_entry = format_item(item)
                    formatted_entry["category"] = category
                    formatted_entry["timestamp"] = current_time_ist
                    formatted_data.append(formatted_entry)

            logger.info(f"Formatted {len(formatted_data)} advance/decline/unchanged records")
            return formatted_data

        except Exception as e:
            logger.error(f"Error formatting advance/decline/unchanged data: {str(e)}")
            return []

    @staticmethod
    def format_forthcoming_listings(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats raw forthcoming listing data from NSE into MongoDB-ready format.
        """
        formatted = []
        current_time_ist = NSEDataFormatter.parse_timestamp(None)

        for item in data:
            formatted.append({
                "symbol": item.get("symbol"),
                "series": item.get("series"),
                "companyName": item.get("companyName"),
                "isin": item.get("isin"),
                "effectiveDate": item.get("effectiveDate"),
                "specialPreOpen": item.get("specialPreOpen"),
                "remark": item.get("remark"),
                "shdAttachment": item.get("shdAttachment"),
                "financialResults": item.get("financialResults"),
                "open": item.get("open"),
                "dayHigh": item.get("dayHigh"),
                "dayLow": item.get("dayLow"),
                "previousClose": item.get("previousClose"),
                "totalTradedVolume": item.get("totalTradedVolume"),
                "totalTradedValue": item.get("totalTradedValue"),
                "lastPrice": item.get("lastPrice"),
                "change": item.get("change"),
                "pChange": item.get("pChange"),
                "chartTodayPath": item.get("chartTodayPath"),
                # Use the class parse_timestamp method for uniformity if item has 'scrapedAt'
                "scrapedAt": NSEDataFormatter.parse_timestamp(item.get("scrapedAt")) if item.get("scrapedAt") else current_time_ist
            })

        logger.info(f"Formatted {len(formatted)} forthcoming listing records")
        return formatted

    @staticmethod
    def format_large_deals(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        formatted = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for deal_type in ["BULK_DEALS", "SHORT_DEALS", "BLOCK_DEALS"]:
            deal_data = raw_data.get(f"{deal_type}_DATA", [])
            for item in deal_data:
                formatted.append({
                    "types": deal_type,
                    "date": item.get("date"),
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "client_name": item.get("clientName"),
                    "buy_sell": item.get("buySell"),
                    "quantity": clean_numeric_value(item.get("qty")) or 0.0,
                    "watp": clean_numeric_value(item.get("watp")) or 0.0,
                    "remarks": item.get("remarks"),
                    "timestamp": current_time
                })

        logger.info(f"Formatted {len(formatted)} large deal records")
        return formatted

    
    @staticmethod
    def format_most_active_contracts(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        from datetime import datetime
        formatted_data = []
        timestamp = NSEDataFormatter.parse_timestamp(None)

        for data_type, sort_dict in raw_data.items():
            if not isinstance(sort_dict, dict):
                continue

            for sort_by, payload in sort_dict.items():
                data_items = payload.get("data", [])
                if not isinstance(data_items, list) or not data_items:
                    continue

                print(f"🔍 Processing {data_type} | sort_by={sort_by} | Records={len(data_items)}")

                for record in data_items:
                    formatted_record = {
                        "types_of_data": data_type,
                        "sort_by": sort_by,
                        "timestamp": timestamp,
                        "identifier": record.get("identifier"),
                        "instrumentType": record.get("instrumentType"),
                        "instrument": record.get("instrument"),
                        "underlying": record.get("underlying"),
                        "expiryDate": record.get("expiryDate"),
                        "optionType": record.get("optionType", "-"),
                        "strikePrice": record.get("strikePrice", 0),
                        "lastPrice": record.get("lastPrice"),
                        "numberOfContractsTraded": record.get("numberOfContractsTraded"),
                        "totalTurnover": record.get("totalTurnover"),
                        "premiumTurnover": record.get("premiumTurnover"),
                        "openInterest": record.get("openInterest"),
                        "underlyingValue": record.get("underlyingValue"),
                        "pChange": record.get("pChange")
                    }
                    formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} most active contracts records")
        return formatted_data

    @staticmethod
    def format_most_active_equities(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats the most active equities data from raw API responses.

        Handles EQ, SME, ETF, and variation categories with both 'by_value' and 'by_volume' keys.
        """
        from datetime import datetime
        formatted_data = []
        timestamp = NSEDataFormatter.parse_timestamp(None)

        for data_type, content in raw_data.items():
            # Skip if no data or wrong structure
            if not isinstance(content, dict):
                continue

            records = content.get("data", [])
            if not isinstance(records, list):
                continue

            # Determine base data type (eq/sme/etf/variation/etc.)
            base_type = None
            if "sme" in data_type:
                base_type = "sme"
            elif "etf" in data_type:
                base_type = "etf"
            elif "variation" in data_type or "volume_gainers" in data_type:
                base_type = "variation"
            else:
                base_type = "eq"

            sort_by = "by_value" if "value" in data_type else "by_volume"

            for record in records:
                formatted_record = {
                    "types_of_data": data_type,  # full key like 'sme_by_value'
                    "sort_by": sort_by,
                    "timestamp": timestamp,
                    "symbol": record.get("symbol"),
                    "identifier": record.get("identifier"),
                    "lastPrice": record.get("lastPrice"),
                    "pChange": record.get("pChange"),
                    "totalTradedVolume": record.get("totalTradedVolume") or record.get("quantityTraded"),
                    "totalTradedValue": record.get("totalTradedValue"),
                    "nav": record.get("nav", None),
                    "exDate": record.get("exDate"),
                    "purpose": record.get("purpose"),
                    "isin": record.get("isin"),
                    "yearHigh": record.get("yearHigh"),
                    "yearLow": record.get("yearLow"),
                    "change": record.get("change"),
                    "open": record.get("open"),
                    "dayHigh": record.get("dayHigh"),
                    "dayLow": record.get("dayLow"),
                    "closePrice": record.get("closePrice", 0),
                    "previousClose": record.get("previousClose", 0)
                }
                formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} most active equities records")
        return formatted_data

    @staticmethod
    def format_most_active_underlying(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw data into a list of MongoDB-ready documents.
        """
        
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for item in raw_data.get("data", []):
            formatted_record = {
                "symbol": item.get("symbol"),
                "futVolume": NSEDataFormatter._safe_int(item.get("futVolume")),
                "optVolume": NSEDataFormatter._safe_int(item.get("optVolume")),
                "totVolume": NSEDataFormatter._safe_int(item.get("totVolume")),
                "futTurnover": NSEDataFormatter._safe_float(item.get("futTurnover")),
                "optTurnover": NSEDataFormatter._safe_float(item.get("optTurnover")),
                "totTurnover": NSEDataFormatter._safe_float(item.get("totTurnover")),
                "preTurnover": NSEDataFormatter._safe_float(item.get("preTurnover")),
                "latestOI": NSEDataFormatter._safe_int(item.get("latestOI")),
                "underlying": NSEDataFormatter._safe_float(item.get("underlying")),
                "timestamp": current_time
            }
            formatted_data.append(formatted_record)
        logger.info(f"Formatted {len(formatted_data)} most active underlying records")
        # Return the formatted data
        return formatted_data

    @staticmethod
    def format_52_week_high_low(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw 52-week high/low data into a list of MongoDB-ready documents.
        """
        formatted_data = []

        current_time = NSEDataFormatter.parse_timestamp(None)

        for key, records in raw_data.items():
            for record in records:
                formatted_record = {
                    "timestamp": current_time,
                    "types": key,
                    "symbol": record.get("symbol"),
                    "series": record.get("series"),
                    "companyName": record.get("companyName"),
                    "new52WHL": record.get("new52WHL"),
                    "prev52WHL": record.get("prev52WHL"),
                    "prevHLDate": record.get("prevHLDate"),
                    "ltp": record.get("ltp"),
                    "prevClose": record.get("prevClose"),
                    "change": record.get("change"),
                    "pChange": record.get("pChange")
                }
                formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} 52-week high/low records")
        # print("Formatted 52-week high/low data:", formatted_data[:3])  # Debug print
        return formatted_data




