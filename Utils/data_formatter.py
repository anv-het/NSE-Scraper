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
    def _safe_strip(value):
        return value.strip() if isinstance(value, str) else value

    @staticmethod
    def _safe_upper(value):
        return value.upper().strip() if isinstance(value, str) else value

    @staticmethod
    def _safe_date(value):
        try:
            return datetime.strptime(value.strip(), "%d-%b-%Y").isoformat()
        except Exception:
            return value

    @staticmethod
    def _safe_percentage(value):
        try:
            if isinstance(value, str):
                return float(value.replace('%', '').strip())
            return float(value)
        except Exception:
            return value

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
            formatted_record = {
                "symbol": item.get("symbol"),
                "series": item.get("series"),
                "companyName": item.get("companyName"),
                "isin": item.get("isin"),
                "effectiveDate": item.get("effectiveDate"),
                "specialPreOpen": item.get("specialPreOpen", "N"),
                "remark": item.get("remark"),
                "shdAttachment": item.get("shdAttachment"),
                "financialResults": item.get("financialResults"),
                "timestamp": current_time_ist
            }
            formatted.append(formatted_record)

        logger.info(f"Formatted {len(formatted)} forthcoming listings records")
        # # print("Formatted forthcoming listings data:", formatted[:3])  # Debug # print
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
        # # print("Formatted 52-week high/low data:", formatted_data[:3])  # Debug # print
        return formatted_data

    @staticmethod
    def format_new_listings_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw new listings data into MongoDB-ready documents.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for item in raw_data.get("data", []):
            formatted_record = {
                "symbol": item.get("symbol"),
                "series": item.get("series"),
                "companyName": item.get("companyName"),
                "isin": item.get("isin"),
                "effectiveDate": item.get("effectiveDate"),
                "specialPreOpen": item.get("specialPreOpen", "N"),
                "remark": item.get("remark"),
                "shdAttachment": item.get("shdAttachment"),
                "financialResults": item.get("financialResults"),
                "open": NSEDataFormatter._safe_float(item.get("open")),
                "dayHigh": NSEDataFormatter._safe_float(item.get("dayHigh")),
                "dayLow": NSEDataFormatter._safe_float(item.get("dayLow")),
                "previousClose": NSEDataFormatter._safe_float(item.get("previousClose")),
                "totalTradedVolume": NSEDataFormatter._safe_int(item.get("totalTradedVolume")),
                "totalTradedValue": NSEDataFormatter._safe_float(item.get("totalTradedValue")),
                "lastPrice": NSEDataFormatter._safe_float(item.get("lastPrice")),
                "change": NSEDataFormatter._safe_float(item.get("change")),
                "pChange": NSEDataFormatter._safe_float(item.get("pChange")),
                "chartTodayPath": item.get("chartTodayPath"),
                "timestamp": current_time
            }
            formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} new listings records")
        # # print("Formatted new listings data:", formatted_data[:3])  # Debug # print
        return formatted_data

    @staticmethod
    def format_recent_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw recent listings data into MongoDB-ready documents.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for item in raw_data.get("data", []):
            formatted_record = {
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "series": item.get("series"),
                "isin": item.get("isin"),
                "listing_date": item.get("listing_date"),
                "instrument": item.get("instrument"),
                "timestamp": current_time
            }
            formatted_data.append(formatted_record)
        logger.info(f"Formatted {len(formatted_data)} recent listings records")
        # # print("Formatted recent listings data:", formatted_data[:3])  # Debug # print
        return formatted_data

    @staticmethod
    def format_special_preopen_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw special pre-open listings data into MongoDB-ready documents.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for item in raw_data.get("data", []):
            preopen_book = item.get("preopenBook", {})
            preopen_entries = preopen_book.get("preopen", [])
            preopen_data = [
                {
                    "price": entry.get("price"),
                    "buyQty": entry.get("buyQty"),
                    "sellQty": entry.get("sellQty")
                } for entry in preopen_entries
            ]

            formatted_record = {
                "symbol": item.get("symbol"),
                "series": item.get("series"),
                "isin": item.get("isin"),
                "iep": NSEDataFormatter._safe_float(item.get("iep")),
                "change": NSEDataFormatter._safe_float(item.get("change")),
                "perChange": NSEDataFormatter._safe_float(item.get("perChange")),
                "ieq": NSEDataFormatter._safe_float(item.get("ieq")),
                "ieVal": NSEDataFormatter._safe_float(item.get("ieVal")),
                "fPrice": NSEDataFormatter._safe_float(item.get("fPrice")),
                "fQty": NSEDataFormatter._safe_float(item.get("fQty")),
                "ttlIeVal": NSEDataFormatter._safe_float(item.get("ttlIeVal")),
                "prevClose": NSEDataFormatter._safe_float(item.get("prevClose")),
                "buyOrderCancCnt": NSEDataFormatter._safe_int(item.get("buyOrderCancCnt")),
                "buyOrderCancVol": NSEDataFormatter._safe_int(item.get("buyOrderCancVol")),
                "sellOrderCancCnt": NSEDataFormatter._safe_int(item.get("sellOrderCancCnt")),
                "sellOrderCancVol": NSEDataFormatter._safe_int(item.get("sellOrderCancVol")),
                "status": item.get("status"),
                "chartTodayPath": item.get("chartTodayPath"),
                "preopenBook": preopen_data,
                "timestamp": current_time
            }
            formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} special pre-open listings records")
        # # print("Formatted special pre-open listings data:", formatted_data[:3])  # Debug
        return formatted_data
    

    @staticmethod
    def format_all_indices(raw_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Formats raw all indices data into MongoDB-ready documents.
        Each index is a list of dicts, with the index metadata being the item with priority=1.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for index_data in raw_data:
            if not isinstance(index_data, list) or not index_data:
                continue

            index_metadata = next((item for item in index_data if item.get("priority") == 1), index_data[0])
            index_name = index_metadata.get("symbol", "Unknown Index")
            index_identifier = index_metadata.get("identifier", "Unknown Identifier")

            for item in index_data:
                formatted_record = {
                    "index_name": index_name,
                    "index_identifier": index_identifier,
                    "priority": item.get("priority", 0),
                    "symbol": item.get("symbol"),
                    "identifier": item.get("identifier"),
                    "series": item.get("series", ""),
                    "open": NSEDataFormatter._safe_float(item.get("open")),
                    "dayHigh": NSEDataFormatter._safe_float(item.get("dayHigh")),
                    "dayLow": NSEDataFormatter._safe_float(item.get("dayLow")),
                    "lastPrice": NSEDataFormatter._safe_float(item.get("lastPrice")),
                    "previousClose": NSEDataFormatter._safe_float(item.get("previousClose")),
                    "change": NSEDataFormatter._safe_float(item.get("change")),
                    "pChange": NSEDataFormatter._safe_float(item.get("pChange")),
                    "totalTradedVolume": NSEDataFormatter._safe_int(item.get("totalTradedVolume")),
                    "totalTradedValue": NSEDataFormatter._safe_float(item.get("totalTradedValue")),
                    "yearHigh": NSEDataFormatter._safe_float(item.get("yearHigh")),
                    "yearLow": NSEDataFormatter._safe_float(item.get("yearLow")),
                    "nearWKH": NSEDataFormatter._safe_float(item.get("nearWKH")),
                    "nearWKL": NSEDataFormatter._safe_float(item.get("nearWKL")),
                    "perChange365d": NSEDataFormatter._safe_float(item.get("perChange365d")),
                    "date365dAgo": item.get("date365dAgo"),
                    "chart365dPath": item.get("chart365dPath"),
                    "date30dAgo": item.get("date30dAgo"),
                    "perChange30d": item.get("perChange30d"),
                    "chart30dPath": item.get("chart30dPath"),
                    "chartTodayPath": item.get("chartTodayPath"),
                    "timestamp": current_time
                }
                formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} all indices records")
        # # print("Formatted all indices data:", formatted_data[:3])  # Debug # print
        return formatted_data



    @staticmethod
    def format_price_band_hitters(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats raw price band hitters data into MongoDB-ready documents.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for direction, categories in raw_data.items():
            for category, items in categories.items():
                if not isinstance(items, dict) or "data" not in items:
                    continue

                for item in items["data"]:
                    formatted_record = {
                        "direction": direction,
                        "category": category,
                        "symbol": item.get("symbol"),
                        "series": item.get("series"),
                        "ltp": NSEDataFormatter._safe_float(item.get("ltp")),
                        "change": NSEDataFormatter._safe_float(item.get("change")),
                        "pChange": NSEDataFormatter._safe_float(item.get("pChange")),
                        "priceBand": item.get("priceBand"),
                        "highPrice": NSEDataFormatter._safe_float(item.get("highPrice")),
                        "lowPrice": NSEDataFormatter._safe_float(item.get("lowPrice")),
                        "yearHigh": NSEDataFormatter._safe_float(item.get("yearHigh")),
                        "yearLow": NSEDataFormatter._safe_float(item.get("yearLow")),
                        "totalTradedVol": NSEDataFormatter._safe_float(item.get("totalTradedVol")),
                        "turnover": NSEDataFormatter._safe_float(item.get("turnover")),
                        "timestamp": current_time
                    }
                    formatted_data.append(formatted_record)
        logger.info(f"Formatted {len(formatted_data)} price band hitters records")
        # # print("Formatted price band hitters data:", formatted_data)  # Debug # print
        return formatted_data

    @staticmethod
    def format_all_indices_from_list(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats raw all indices data from a list of dictionaries into MongoDB-ready documents.
        """

        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        for category, content in raw_data.items():
            if not isinstance(content, dict):
                continue

            legends = content.get("legends", [])
            indices_data = {key: value.get("data", []) for key, value in content.items() if key != "legends"}

            for index_name, records in indices_data.items():
                for record in records:
                    formatted_record = {
                        "category": category,
                        "index_name": index_name,
                        "symbol": record.get("symbol"),
                        "series": record.get("series"),
                        "open_price": NSEDataFormatter._safe_float(record.get("open_price")),
                        "high_price": NSEDataFormatter._safe_float(record.get("high_price")),
                        "low_price": NSEDataFormatter._safe_float(record.get("low_price")),
                        "ltp": NSEDataFormatter._safe_float(record.get("ltp")),
                        "prev_price": NSEDataFormatter._safe_float(record.get("prev_price")),
                        "net_price": NSEDataFormatter._safe_float(record.get("net_price")),
                        "trade_quantity": NSEDataFormatter._safe_int(record.get("trade_quantity")),
                        "turnover": NSEDataFormatter._safe_float(record.get("turnover")),
                        "market_type": record.get("market_type"),
                        "ca_ex_dt": record.get("ca_ex_dt"),
                        "ca_purpose": record.get("ca_purpose"),
                        "perChange": NSEDataFormatter._safe_float(record.get("perChange")),
                        "timestamp": current_time
                    }
                    formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} all indices records from list")
        # # print("Formatted all indices data from list:", formatted_data)  # Debug
        return formatted_data

    @staticmethod
    def parse_date(date_str: str) -> str:
        """Try to parse different date formats and return ISO 8601 string."""
        if not date_str:
            return None
        formats = [
            "%d-%b-%Y %H:%M:%S",
            "%d-%b-%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%d %b %Y",
            "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except Exception:
                continue
        # If parsing fails, return original string to avoid losing data
        return date_str

    @staticmethod
    def format_stocks_wise_market_event(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats raw stockwise market event data into MongoDB-ready documents.
        """

        current_time = NSEDataFormatter.parse_timestamp(None)
        formatted_data = []


        for item in raw_data:
            # Use symbol from top-level or fallback to empty string
            symbol = item.get("symbol", "").upper().strip() or None

            # Sometimes symbol might be missing at top level,
            # try to get from nested data (latest announcements etc.) if available
            if not symbol:
                for key in ["latest_announcements", "corporate_actions", "borad_meeting", "board_meeting"]:
                    data_list = item.get(key, {}).get("data", [])
                    if data_list and isinstance(data_list, list) and len(data_list) > 0:
                        candidate = data_list[0].get("symbol")
                        if candidate:
                            symbol = candidate.upper().strip()
                            break
                if not symbol:
                    symbol = "UNKNOWN"

            # Clean and normalize nested data:
            def fix_symbol_and_dates(data_list, date_keys):
                for d in data_list:
                    # Ensure symbol is present and normalized
                    d["symbol"] = d.get("symbol", symbol).upper().strip()
                    # Fix dates keys to ISO format
                    for k in date_keys:
                        if k in d:
                            d[k] = NSEDataFormatter.parse_date(d[k])
                return data_list

            latest_announcements = item.get("latest_announcements", {}).get("data", [])
            latest_announcements = fix_symbol_and_dates(latest_announcements, ["broadcast_date", "broadcastdate"])

            corporate_actions = item.get("corporate_actions", {}).get("data", [])
            corporate_actions = fix_symbol_and_dates(corporate_actions, ["ex_date", "exdate"])

            shareholdings_patterns = item.get("shareholdings_patterns", {}).get("data", {})
            # Dates in shareholding keys should also be normalized:
            cleaned_shareholdings = {}
            for date_key, patterns in shareholdings_patterns.items():
                iso_date = NSEDataFormatter.parse_date(date_key)
                cleaned_patterns = []
                for pattern in patterns:
                    # Trim holder names, convert % strings to float if needed
                    cleaned_pattern = {
                        k.strip(): float(v.strip().replace('%','')) if isinstance(v, str) and v.strip().replace('%','').replace('.','',1).isdigit() else v
                        for k,v in pattern.items()
                    }
                    cleaned_patterns.append(cleaned_pattern)
                cleaned_shareholdings[iso_date] = cleaned_patterns

            financial_results = item.get("financial_results", {}).get("data", [])
            financial_results = fix_symbol_and_dates(financial_results, ["from_date", "to_date"])

            board_meeting_data = item.get("board_meeting") or item.get("borad_meeting", {})
            board_meetings = board_meeting_data.get("data", [])
            board_meetings = fix_symbol_and_dates(board_meetings, ["meeting_date", "meetingdate"])

            formatted_data.append({
                "symbol": symbol,
                "latest_announcements": {"data": latest_announcements},
                "corporate_actions": {"data": corporate_actions},
                "shareholdings_patterns": {"data": cleaned_shareholdings},
                "financial_results": {"data": financial_results},
                "borad_meeting": {"data": board_meetings},
                "timestamp": current_time
            })
        logger.info(f"Formatted {len(formatted_data)} stockwise market event records")
        # # print("Formatted stockwise market event data:", formatted_data[:3])  # Debug
        return formatted_data


