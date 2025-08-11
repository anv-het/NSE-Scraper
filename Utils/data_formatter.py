"""
NSE Data Formatter Utility
Formats raw NSE API responses into MongoDB-ready documents according to schema
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from yaml import safe_load
from Utils.general_master import get_masterdata_info, get_all_nsecm_bsecm_data, get_all_derivatives_masterdata
from Utils.logger import get_logger

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
    def parse_timestamp(timestamp_str: str) -> datetime:
        # Always return current Indian time, ignore input
        return datetime.now()
   
    @staticmethod
    def get_current_indian_time(timestamp_str: str) -> datetime:
        # Get current local time without tz info
        now = datetime.now()

        # Try to detect if local time is IST by checking offset from UTC
        local_utc_offset = (now - datetime.utcnow()).total_seconds() / 3600  # in hours

        if abs(local_utc_offset - 5.5) < 0.1:  # Close enough to IST offset +5:30
            # Assume system time is IST, return naive local time or make it aware as IST
            # Return aware datetime with IST timezone
            return now.replace(tzinfo=NSEDataFormatter.IST)
        else:
            # System time is not IST, so get UTC and convert to IST explicitly
            utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
            return utc_now.astimezone(NSEDataFormatter.IST)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float, removing commas and handling strings like '1,000.5'"""
        try:
            if isinstance(value, str):
                # Remove commas (e.g., '1,000.5' -> '1000.5')
                value = value.replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float_rounded(value: Any, decimals: int = 2) -> Optional[float]:
        """
        Convert value to float safely, remove commas, and round to specified decimals.
        Returns None if conversion fails.
        """
        try:
            if isinstance(value, str):
                value = value.replace(',', '')  # remove commas if any
            float_val = float(value)
            return round(float_val, decimals)
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

            # Step 1: Get timestamp
            timestamp_str = summary.get("timestamp", datetime.utcnow().isoformat())
            current_time_ist = NSEDataFormatter.parse_timestamp(timestamp_str)

            # Step 2: Scrape data and log time
            scrape_start = datetime.now()
            scraped_data = []
            for category_name in ["advance", "decline", "unchanged"]:
                items = summary.get(category_name, [])
                for item in items:
                    item["category"] = category_name
                    scraped_data.append(item)
            scrape_end = datetime.now()
            logger.info(f"Scraped {len(scraped_data)} records in {(scrape_end - scrape_start).total_seconds():.2f}s")

            # Step 3: Get DB data and log time
            db_fetch_start = datetime.now()
            db_data = get_all_nsecm_bsecm_data()
            db_fetch_end = datetime.now()
            logger.info(f"Fetched {len(db_data)} masterdata records from DB in {(db_fetch_end - db_fetch_start).total_seconds():.2f}s")

            # Step 4: Index DB data for fast lookup
            masterdata_map = defaultdict(list)
            for doc in db_data:
                name = doc.get("Name", "").upper()
                if name:
                    masterdata_map[name].append(doc)

            masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

            # Step 5: Merge and format data
            for item in scraped_data:
                symbol = item.get("symbol", "").strip().upper()
                identifier = item.get("identifier", "").strip().upper()

                matched_docs = masterdata_map.get(symbol, [])
                masterdata_info = {}

                # Inline selection logic
                if matched_docs:
                    # Prefer NSECM + EQ
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                            masterdata_info = doc
                            break
                    else:
                        # Then any NSECM
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM":
                                masterdata_info = doc
                                break
                        else:
                            # Then BSECM + A
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then any BSECM
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM":
                                        masterdata_info = doc
                                        break
                else:
                    # Fallback: match by identifier if symbol not found
                    masterdata_info = masterdata_identifier_map.get(identifier, {})

                formatted = {
                    "identifier": item.get("identifier"),
                    "symbol": item.get("symbol"),
                    "series": item.get("series"),
                    "market_type": item.get("marketType"),
                    "price_change_percent": item.get("pchange"),
                    "price_change_value": item.get("change"),
                    "base_price": item.get("basePrice"),
                    "previous_close": item.get("previousClose"),
                    "last_price": item.get("lastPrice"),
                    "total_traded_volume": NSEDataFormatter._safe_float(item.get("totalTradedVolume")),
                    "total_traded_value": NSEDataFormatter._safe_float(item.get("totalTradedValue")),
                    "issued_cap": NSEDataFormatter._safe_float(item.get("issuedCap")),
                    "total_market_cap": NSEDataFormatter._safe_float(item.get("totalMarketCap")),

                    # New fields from masterdata
                    "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                    "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                    "MasterdataSeries": masterdata_info.get("Series"),

                    # Additional useful fields
                    "category": item.get("category"),
                    "timestamp": current_time_ist.isoformat()
                }

                formatted_data.append(formatted)

            logger.info(f"Formatted {len(formatted_data)} records for output")
            return formatted_data

        except Exception as e:
            logger.error(f"Error formatting advance/decline/unchanged data: {str(e)}")
            return []
    
    @staticmethod
    def format_forthcoming_listings(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats raw forthcoming listing data from NSE into MongoDB-ready format with masterdata enrichment.
        """
        formatted = []
        current_time_ist = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for item in data:
            symbol = item.get("symbol", "").strip().upper()
            identifier = item.get("identifier", "").strip().upper()

            matched_docs = masterdata_map.get(symbol, [])
            masterdata_info = {}

            # Inline selection logic
            if matched_docs:
                # Prefer NSECM + EQ
                for doc in matched_docs:
                    if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                        masterdata_info = doc
                        break
                else:
                    # Then any NSECM
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM":
                            masterdata_info = doc
                            break
                    else:
                        # Then BSECM + A
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                masterdata_info = doc
                                break
                        else:
                            # Then any BSECM
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM":
                                    masterdata_info = doc
                                    break
            else:
                # Fallback: match by identifier if symbol not found
                masterdata_info = masterdata_identifier_map.get(identifier, {})

            formatted_record = {
                "symbol": symbol,
                "series": item.get("series"),
                "companyName": item.get("companyName"),
                "isin": item.get("isin"),
                "effectiveDate": NSEDataFormatter._safe_date(item.get("effectiveDate", "")),
                "specialPreOpen": item.get("specialPreOpen", "N"),
                "remark": item.get("remark"),
                "shdAttachment": item.get("shdAttachment"),
                "financialResults": item.get("financialResults"),

                # Masterdata enrichment
                "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                "MasterdataSeries": masterdata_info.get("Series"),

                "timestamp": current_time_ist
            }
            formatted.append(formatted_record)

        logger.info(f"Formatted {len(formatted)} forthcoming listings records")
        return formatted

    @staticmethod
    def format_large_deals(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats large deals data from NSE with numeric cleaning and masterdata enrichment.
        """
        formatted = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for deal_type in ["BULK_DEALS", "SHORT_DEALS", "BLOCK_DEALS"]:
            deal_data = raw_data.get(f"{deal_type}_DATA", [])
            for item in deal_data:
                symbol = item.get("symbol", "").strip().upper()
                identifier = item.get("identifier", "").strip().upper()

                matched_docs = masterdata_map.get(symbol, [])
                masterdata_info = {}

                # Inline selection logic
                if matched_docs:
                    # Prefer NSECM + EQ
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                            masterdata_info = doc
                            break
                    else:
                        # Then any NSECM
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM":
                                masterdata_info = doc
                                break
                        else:
                            # Then BSECM + A
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then any BSECM
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM":
                                        masterdata_info = doc
                                        break
                else:
                    # Fallback: match by identifier if symbol not found
                    masterdata_info = masterdata_identifier_map.get(identifier, {})

                formatted.append({
                    "types": deal_type,
                    "date": NSEDataFormatter._safe_date(item.get("date", "")),
                    "symbol": symbol,
                    "name": item.get("name"),
                    "client_name": item.get("clientName"),
                    "buy_sell": item.get("buySell"),
                    "quantity": NSEDataFormatter._safe_float(item.get("qty")) or 0.0,
                    "watp": NSEDataFormatter._safe_float(item.get("watp")) or 0.0,
                    "remarks": item.get("remarks"),

                    # Masterdata enrichment
                    "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                    "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                    "MasterdataSeries": masterdata_info.get("Series"),

                    "timestamp": current_time
                })

        logger.info(f"Formatted {len(formatted)} large deal records")
        return formatted

    @staticmethod
    def format_most_active_contracts(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats the most active contracts data from raw API responses with masterdata enrichment.
        
        Args:
            raw_data: Raw API response data
            
        Returns:
            List of formatted records with masterdata fields added for derivatives
        """
        from datetime import datetime
        formatted_data = []
        timestamp = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for derivatives enrichment
        derivatives_masterdata = get_all_derivatives_masterdata()
        
        # Create lookup dictionary for fast masterdata matching
        masterdata_lookup = {}
        for doc in derivatives_masterdata:
            # Create composite key for matching: Name + StrikePrice + expiryDate + OptionTypeDesc
            name = str(doc.get("Name") or "").strip().upper()
            strike_price = doc.get("StrikePrice")
            expiry_date = str(doc.get("expiryDate") or "").strip()
            option_type = str(doc.get("OptionTypeDesc") or "").strip()
            
            if name and strike_price is not None and expiry_date and option_type:
                # Convert strike price to float for comparison
                try:
                    strike_float = float(strike_price)
                    lookup_key = f"{name}_{strike_float}_{expiry_date}_{option_type}"
                    masterdata_lookup[lookup_key] = doc
                except (ValueError, TypeError):
                    continue

        logger.info(f"Created masterdata lookup with {len(masterdata_lookup)} derivatives records")

        for data_type, sort_dict in raw_data.items():
            if not isinstance(sort_dict, dict):
                continue

            for sort_by, payload in sort_dict.items():
                data_items = payload.get("data", [])
                if not isinstance(data_items, list) or not data_items:
                    continue

                logger.info(f"Processing {data_type} | sort_by={sort_by} | Records={len(data_items)}")

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

                    # Add masterdata enrichment for derivatives/options
                    if record.get("instrumentType") in ["OPTIDX", "OPTSTK"]:
                        
                        # Extract fields for masterdata matching
                        underlying = str(record.get("underlying", "")).strip().upper()
                        strike_price = record.get("strikePrice")
                        expiry_date = str(record.get("expiryDate", "")).strip()
                        option_type = str(record.get("optionType", "")).strip()
                        
                        # Create lookup key for masterdata matching
                        if underlying and strike_price is not None and expiry_date and option_type:
                            try:
                                strike_float = float(strike_price)
                                lookup_key = f"{underlying}_{strike_float}_{expiry_date}_{option_type}"
                                
                                # Find matching masterdata
                                masterdata_match = masterdata_lookup.get(lookup_key)
                                
                                if masterdata_match:
                                    # Add masterdata fields to formatted record
                                    formatted_record["ExchangeInstrumentID"] = masterdata_match.get("ExchangeInstrumentID")
                                    formatted_record["ExchangeSegment"] = masterdata_match.get("ExchangeSegment")
                                    formatted_record["MasterdataSeries"] = masterdata_match.get("Series")
                                    logger.info(f"Masterdata match found for {lookup_key} -> ID: {masterdata_match.get('ExchangeInstrumentID')}")
                                else:
                                    # Set default values if no match found
                                    formatted_record["ExchangeInstrumentID"] = None
                                    formatted_record["ExchangeSegment"] = None
                                    formatted_record["MasterdataSeries"] = None
                                    logger.debug(f"No masterdata match for {lookup_key}")
                                    
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Error processing masterdata lookup for record: {e}")
                                formatted_record["ExchangeInstrumentID"] = None
                                formatted_record["ExchangeSegment"] = None
                                formatted_record["MasterdataSeries"] = None
                        else:
                            # Set default values if required fields are missing
                            formatted_record["ExchangeInstrumentID"] = None
                            formatted_record["ExchangeSegment"] = None
                            formatted_record["MasterdataSeries"] = None
                            logger.debug(f"Missing required fields for masterdata lookup: underlying={underlying}, strike_price={strike_price}, expiry_date={expiry_date}, option_type={option_type}")
                    else:
                        # For non-derivatives, set masterdata fields to None
                        formatted_record["ExchangeInstrumentID"] = None
                        formatted_record["ExchangeSegment"] = None
                        formatted_record["MasterdataSeries"] = None

                    formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} most active contracts records")
        print(f"Formatted most active contracts records: {formatted_data[:3]}")
        return formatted_data

    @staticmethod
    def format_most_active_equities(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats the most active equities data from raw API responses with masterdata enrichment.

        Handles EQ, SME, ETF, and variation categories with both 'by_value' and 'by_volume' keys.
        """
        formatted_data = []
        timestamp = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

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
                symbol = record.get("symbol", "").strip().upper()
                identifier = record.get("identifier", "").strip().upper()

                matched_docs = masterdata_map.get(symbol, [])
                masterdata_info = {}

                # Inline selection logic
                if matched_docs:
                    # Prefer NSECM + EQ
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                            masterdata_info = doc
                            break
                    else:
                        # Then any NSECM
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM":
                                masterdata_info = doc
                                break
                        else:
                            # Then BSECM + A
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then any BSECM
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM":
                                        masterdata_info = doc
                                        break
                else:
                    # Fallback: match by identifier if symbol not found
                    masterdata_info = masterdata_identifier_map.get(identifier, {})

                formatted_record = {
                    "types_of_data": data_type,  # full key like 'sme_by_value'
                    "sort_by": sort_by,
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "identifier": record.get("identifier"),
                    "lastPrice": NSEDataFormatter._safe_float(record.get("lastPrice")),
                    "pChange": NSEDataFormatter._safe_float(record.get("pChange")),
                    "totalTradedVolume": NSEDataFormatter._safe_int(record.get("totalTradedVolume") or record.get("quantityTraded")),
                    "totalTradedValue": NSEDataFormatter._safe_float(record.get("totalTradedValue")),
                    "nav": NSEDataFormatter._safe_float(record.get("nav")),
                    "exDate": record.get("exDate"),
                    "purpose": record.get("purpose"),
                    "isin": record.get("isin"),
                    "yearHigh": NSEDataFormatter._safe_float(record.get("yearHigh")),
                    "yearLow": NSEDataFormatter._safe_float(record.get("yearLow")),
                    "change": NSEDataFormatter._safe_float(record.get("change")),
                    "open": NSEDataFormatter._safe_float(record.get("open")),
                    "dayHigh": NSEDataFormatter._safe_float(record.get("dayHigh")),
                    "dayLow": NSEDataFormatter._safe_float(record.get("dayLow")),
                    "closePrice": NSEDataFormatter._safe_float(record.get("closePrice")),
                    "previousClose": NSEDataFormatter._safe_float(record.get("previousClose")),

                    # Masterdata enrichment
                    "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                    "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                    "MasterdataSeries": masterdata_info.get("Series")
                }
                formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} most active equities records")
        return formatted_data

    @staticmethod
    def format_most_active_underlying(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw data into a list of MongoDB-ready documents with masterdata enrichment.
        Enhanced with derivatives matching for options and futures data.
        """
        
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment (including derivatives)
        db_data = get_all_derivatives_masterdata()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        for item in raw_data.get("data", []):
            symbol = item.get("symbol", "").strip().upper()

            matched_docs = masterdata_map.get(symbol, [])
            if matched_docs:
                # Prefer NSECM + EQ
                for doc in matched_docs:
                    if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                        masterdata_info = doc
                        break
                else:
                    # Then any NSECM
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM":
                            masterdata_info = doc
                            break
                    else:
                        # Then BSECM + A
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                masterdata_info = doc
                                break
                            else:
                                # If no match found, use the last document
                                masterdata_info = doc
                                

            formatted_record = {
                "symbol": symbol,
                "futVolume": NSEDataFormatter._safe_int(item.get("futVolume")),
                "optVolume": NSEDataFormatter._safe_int(item.get("optVolume")),
                "totVolume": NSEDataFormatter._safe_int(item.get("totVolume")),
                "futTurnover": NSEDataFormatter._safe_float(item.get("futTurnover")),
                "optTurnover": NSEDataFormatter._safe_float(item.get("optTurnover")),
                "totTurnover": NSEDataFormatter._safe_float(item.get("totTurnover")),
                "preTurnover": NSEDataFormatter._safe_float(item.get("preTurnover")),
                "latestOI": NSEDataFormatter._safe_int(item.get("latestOI")),
                "underlying": NSEDataFormatter._safe_float(item.get("underlying")),

                # Masterdata enrichment (enhanced for derivatives)
                "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                "MasterdataSeries": masterdata_info.get("Series"),

                "timestamp": current_time
            }
            formatted_data.append(formatted_record)
        logger.info(f"Formatted {len(formatted_data)} most active underlying records")
        print(f"Formatted ", formatted_data[:3])
        # Return the formatted data
        return formatted_data

    @staticmethod
    def format_52_week_high_low(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw 52-week high/low data into a list of MongoDB-ready documents with masterdata enrichment.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for key, records in raw_data.items():
            for record in records:
                symbol = record.get("symbol", "").strip().upper()
                identifier = record.get("identifier", "").strip().upper()

                matched_docs = masterdata_map.get(symbol, [])
                masterdata_info = {}

                # Inline selection logic
                if matched_docs:
                    # Prefer NSECM + EQ
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                            masterdata_info = doc
                            break
                    else:
                        # Then any NSECM
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM":
                                masterdata_info = doc
                                break
                        else:
                            # Then BSECM + A
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then any BSECM
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM":
                                        masterdata_info = doc
                                        break
                else:
                    # Fallback: match by identifier if symbol not found
                    masterdata_info = masterdata_identifier_map.get(identifier, {})

                formatted_record = {
                    "timestamp": current_time,
                    "types": key,
                    "symbol": symbol,
                    "series": record.get("series"),
                    "companyName": record.get("comapnyName"),
                    "new52WHL": NSEDataFormatter._safe_float(record.get("new52WHL")),
                    "prev52WHL": NSEDataFormatter._safe_float(record.get("prev52WHL")),
                    "prevHLDate": record.get("prevHLDate"),
                    "ltp": NSEDataFormatter._safe_float(record.get("ltp")),
                    "prevClose": NSEDataFormatter._safe_float(record.get("prevClose")),
                    "change": NSEDataFormatter._safe_float(record.get("change")),
                    "pChange": NSEDataFormatter._safe_float(record.get("pChange")),

                    # Masterdata enrichment
                    "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                    "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                    "MasterdataSeries": masterdata_info.get("Series")
                }
                formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} 52-week high/low records")
        return formatted_data

    @staticmethod
    def format_new_listings_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw new listings data into MongoDB-ready documents with masterdata enrichment.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for item in raw_data.get("data", []):
            symbol = item.get("symbol", "").strip().upper()
            identifier = item.get("identifier", "").strip().upper()

            matched_docs = masterdata_map.get(symbol, [])
            masterdata_info = {}

            # Inline selection logic
            if matched_docs:
                # Prefer NSECM + EQ
                for doc in matched_docs:
                    if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                        masterdata_info = doc
                        break
                else:
                    # Then any NSECM
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM":
                            masterdata_info = doc
                            break
                    else:
                        # Then BSECM + A
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                masterdata_info = doc
                                break
                        else:
                            # Then any BSECM
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM":
                                    masterdata_info = doc
                                    break
            else:
                # Fallback: match by identifier if symbol not found
                masterdata_info = masterdata_identifier_map.get(identifier, {})

            formatted_record = {
                "symbol": symbol,
                "series": item.get("series"),
                "companyName": item.get("companyName"),
                "isin": item.get("isin"),
                "effectiveDate": NSEDataFormatter._safe_date(item.get("effectiveDate", "")),
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

                # Masterdata enrichment
                "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                "MasterdataSeries": masterdata_info.get("Series"),

                "timestamp": current_time
            }
            formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} new listings records")
        return formatted_data

    @staticmethod
    def format_recent_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw recent listings data into MongoDB-ready documents with masterdata enrichment.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for item in raw_data.get("data", []):
            symbol = item.get("symbol", "").strip().upper()
            identifier = item.get("identifier", "").strip().upper()

            matched_docs = masterdata_map.get(symbol, [])
            masterdata_info = {}

            # Inline selection logic
            if matched_docs:
                # Prefer NSECM + EQ
                for doc in matched_docs:
                    if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                        masterdata_info = doc
                        break
                else:
                    # Then any NSECM
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM":
                            masterdata_info = doc
                            break
                    else:
                        # Then BSECM + A
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                masterdata_info = doc
                                break
                        else:
                            # Then any BSECM
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM":
                                    masterdata_info = doc
                                    break
            else:
                # Fallback: match by identifier if symbol not found
                masterdata_info = masterdata_identifier_map.get(identifier, {})

            formatted_record = {
                "symbol": symbol,
                "name": item.get("name"),
                "series": item.get("series"),
                "isin": item.get("isin"),
                "listing_date": NSEDataFormatter._safe_date(item.get("listing_date", "")),
                "instrument": item.get("instrument"),

                # Masterdata enrichment
                "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                "MasterdataSeries": masterdata_info.get("Series"),

                "timestamp": current_time
            }
            formatted_data.append(formatted_record)
        logger.info(f"Formatted {len(formatted_data)} recent listings records")
        return formatted_data

    @staticmethod
    def format_special_preopen_data(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw special pre-open listings data into MongoDB-ready documents with masterdata enrichment.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for item in raw_data.get("data", []):
            symbol = item.get("symbol", "").strip().upper()
            identifier = item.get("identifier", "").strip().upper()

            matched_docs = masterdata_map.get(symbol, [])
            masterdata_info = {}

            # Inline selection logic
            if matched_docs:
                # Prefer NSECM + EQ
                for doc in matched_docs:
                    if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                        masterdata_info = doc
                        break
                else:
                    # Then any NSECM
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM":
                            masterdata_info = doc
                            break
                    else:
                        # Then BSECM + A
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                masterdata_info = doc
                                break
                        else:
                            # Then any BSECM
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM":
                                    masterdata_info = doc
                                    break
            else:
                # Fallback: match by identifier if symbol not found
                masterdata_info = masterdata_identifier_map.get(identifier, {})

            preopen_book = item.get("preopenBook", {})
            preopen_entries = preopen_book.get("preopen", [])
            preopen_data = [
                {
                    "price": NSEDataFormatter._safe_float(entry.get("price")),
                    "buyQty": NSEDataFormatter._safe_int(entry.get("buyQty")),
                    "sellQty": NSEDataFormatter._safe_int(entry.get("sellQty"))
                } for entry in preopen_entries
            ]

            formatted_record = {
                "symbol": symbol,
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

                # Masterdata enrichment
                "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                "MasterdataSeries": masterdata_info.get("Series"),

                "timestamp": current_time
            }
            formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} special pre-open listings records")
        return formatted_data
    
    @staticmethod
    def format_all_indices(raw_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Formats raw all indices data into MongoDB-ready documents with optional masterdata enrichment.
        Each index is a list of dicts, with the index metadata being the item with priority=1.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment (for individual symbols within indices)
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for index_data in raw_data:
            if not isinstance(index_data, list) or not index_data:
                continue

            index_metadata = next((item for item in index_data if item.get("priority") == 1), index_data[0])
            index_name = index_metadata.get("symbol", "Unknown Index")
            index_identifier = index_metadata.get("identifier", "Unknown Identifier")

            for item in index_data:
                symbol = item.get("symbol", "").strip().upper()
                identifier = item.get("identifier", "").strip().upper()

                matched_docs = masterdata_map.get(symbol, [])
                masterdata_info = {}

                # Inline selection logic
                if matched_docs:
                    # Prefer NSECM + EQ
                    for doc in matched_docs:
                        if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                            masterdata_info = doc
                            break
                    else:
                        # Then any NSECM
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM":
                                masterdata_info = doc
                                break
                        else:
                            # Then BSECM + A
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then any BSECM
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM":
                                        masterdata_info = doc
                                        break
                else:
                    # Fallback: match by identifier if symbol not found
                    masterdata_info = masterdata_identifier_map.get(identifier, {})

                formatted_record = {
                    "index_name": index_name,
                    "index_identifier": index_identifier,
                    "priority": item.get("priority", 0),
                    "symbol": symbol,
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
                    "perChange30d": NSEDataFormatter._safe_float(item.get("perChange30d")),
                    "chart30dPath": item.get("chart30dPath"),
                    "chartTodayPath": item.get("chartTodayPath"),

                    # Masterdata enrichment (optional for indices)
                    "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                    "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                    "MasterdataSeries": masterdata_info.get("Series"),

                    "timestamp": current_time
                }
                formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} all indices records")
        return formatted_data

    @staticmethod
    def format_price_band_hitters(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw price band hitters data into MongoDB-ready documents with masterdata enrichment.
        """
        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for direction, categories in raw_data.items():
            for category, items in categories.items():
                if not isinstance(items, dict) or "data" not in items:
                    continue

                for item in items["data"]:
                    symbol = item.get("symbol", "").strip().upper()
                    identifier = item.get("identifier", "").strip().upper()

                    matched_docs = masterdata_map.get(symbol, [])
                    masterdata_info = {}

                    # Inline selection logic
                    if matched_docs:
                        # Prefer NSECM + EQ
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                                masterdata_info = doc
                                break
                        else:
                            # Then any NSECM
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "NSECM":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then BSECM + A
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                        masterdata_info = doc
                                        break
                                else:
                                    # Then any BSECM
                                    for doc in matched_docs:
                                        if doc.get("ExchangeSegment") == "BSECM":
                                            masterdata_info = doc
                                            break
                    else:
                        # Fallback: match by identifier if symbol not found
                        masterdata_info = masterdata_identifier_map.get(identifier, {})

                    formatted_record = {
                        "direction": direction,
                        "category": category,
                        "symbol": symbol,
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

                        # Masterdata enrichment
                        "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                        "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                        "MasterdataSeries": masterdata_info.get("Series"),

                        "timestamp": current_time
                    }
                    formatted_data.append(formatted_record)
        logger.info(f"Formatted {len(formatted_data)} price band hitters records")
        return formatted_data

    @staticmethod
    def format_all_indices_from_list(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formats raw all indices data from a dictionary of categories into MongoDB-ready documents with masterdata enrichment.
        """

        formatted_data = []
        current_time = NSEDataFormatter.parse_timestamp(None)

        # Fetch masterdata for enrichment
        db_data = get_all_nsecm_bsecm_data()
        
        # Index DB data for fast lookup
        masterdata_map = defaultdict(list)
        for doc in db_data:
            name = doc.get("Name", "").upper()
            if name:
                masterdata_map[name].append(doc)

        masterdata_identifier_map = {doc.get("identifier", "").upper(): doc for doc in db_data}

        for category, content in raw_data.items():
            if not isinstance(content, dict):
                continue

            legends = content.get("legends", [])
            indices_data = {key: value.get("data", []) for key, value in content.items() if key != "legends"}

            for index_name, records in indices_data.items():
                for record in records:
                    symbol = record.get("symbol", "").strip().upper()
                    identifier = record.get("identifier", "").strip().upper()

                    matched_docs = masterdata_map.get(symbol, [])
                    masterdata_info = {}

                    # Inline selection logic
                    if matched_docs:
                        # Prefer NSECM + EQ
                        for doc in matched_docs:
                            if doc.get("ExchangeSegment") == "NSECM" and doc.get("Series") == "EQ":
                                masterdata_info = doc
                                break
                        else:
                            # Then any NSECM
                            for doc in matched_docs:
                                if doc.get("ExchangeSegment") == "NSECM":
                                    masterdata_info = doc
                                    break
                            else:
                                # Then BSECM + A
                                for doc in matched_docs:
                                    if doc.get("ExchangeSegment") == "BSECM" and doc.get("Series") == "A":
                                        masterdata_info = doc
                                        break
                                else:
                                    # Then any BSECM
                                    for doc in matched_docs:
                                        if doc.get("ExchangeSegment") == "BSECM":
                                            masterdata_info = doc
                                            break
                    else:
                        # Fallback: match by identifier if symbol not found
                        masterdata_info = masterdata_identifier_map.get(identifier, {})

                    formatted_record = {
                        "category": category,
                        "index_name": index_name,
                        "symbol": symbol,
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

                        # Masterdata enrichment (optional for indices)
                        "ExchangeInstrumentID": masterdata_info.get("ExchangeInstrumentID"),
                        "ExchangeSegment": masterdata_info.get("ExchangeSegment"),
                        "MasterdataSeries": masterdata_info.get("Series"),

                        "timestamp": current_time
                    }
                    formatted_data.append(formatted_record)

        logger.info(f"Formatted {len(formatted_data)} all indices records from list")
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
        return formatted_data

    @staticmethod
    def format_investorgain_ipo_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format InvestorGain IPO data into MongoDB-ready documents
        
        Args:
            data: List of raw IPO data dictionaries from InvestorGain API
            
        Returns:
            List[Dict[str, Any]]: Formatted IPO data documents
        """
        try:
            formatted_data = []
            
            # Get current IST timestamp
            current_time_ist = NSEDataFormatter.parse_timestamp(None)
            
            logger.info(f"Starting to format {len(data)} IPO records")
            
            for ipo_item in data:
                try:
                    # Format the IPO data according to the required output structure
                    formatted_ipo = {
                        # Basic IPO Information
                        "ipoId": ipo_item.get("ipo_id"),
                        "apiCompanyName": ipo_item.get("api_company_name"),
                        "apiIpoCategory": ipo_item.get("api_ipo_category"),
                        "apiIssueSize": ipo_item.get("api_issue_size"),
                        "apiIssueOpenDate": ipo_item.get("api_issue_open_date"),
                        "apiIssueEndDate": ipo_item.get("api_issue_end_date"),
                        "apiListingAt": ipo_item.get("api_listing_at"),
                        "apiIpoStatus": ipo_item.get("api_ipo_status"),
                        "apiIpoStatusFormatted": ipo_item.get("api_ipo_status_formatted"),
                        
                        # Scraping Information
                        "scrapingDate": ipo_item.get("scraping_date"),
                        "detailUrl": ipo_item.get("detail_url"),
                        "scrapedCompanyName": ipo_item.get("scraped_company_name"),
                        "companyLogoUrl": ipo_item.get("company_logo_url"),
                        "localLogoPath": ipo_item.get("local_logo_path"),
                        "companyFullNameScraped": ipo_item.get("company_full_name_scraped"),
                        "aboutCompanyText": ipo_item.get("about_company_text"),
                        
                        # IPO Details
                        # "ipoIssuePrice": ipo_item.get("ipo_issue_price"),
                        # "drhpUrl": ipo_item.get("drhp_url"),
                        # "rhpUrl": ipo_item.get("rhp_url"),
                        # "anchorListUrl": ipo_item.get("anchor_list_url"),
                        # "retailQuota": ipo_item.get("retail_quota"),
                        # "ipoIssueType": ipo_item.get("ipo_issue_type"),
                        # "ipoIssueSizeScraped": ipo_item.get("ipo_issue_size_scraped"),
                        # "freshIssue": ipo_item.get("fresh_issue"),
                        # "faceValue": ipo_item.get("face_value"),
                        # "promoterHoldingPreIpo": ipo_item.get("promoter_holding_pre_ipo"),
                        # "promoterHoldingPostIpo": ipo_item.get("promoter_holding_post_ipo"),
                        
                        # # Date Information
                        # "ipoIssueOpeningDate": ipo_item.get("ipo_issue_opening_date"),
                        # "ipoIssueClosingDate": ipo_item.get("ipo_issue_closing_date"),
                        "minOrderQuantityScraped": ipo_item.get("min_order_quantity_scraped"),
                        "sharesPerLotScraped": ipo_item.get("shares_per_lot_scraped"),
                        "ipoSummaryText": ipo_item.get("ipo_summary_text"),
                        
                        # Date Status and Parsing
                        "ipoIssueOpeningDateStatus": ipo_item.get("ipo_issue_opening_date_status"),
                        "ipoIssueOpeningDateParsed": ipo_item.get("ipo_issue_opening_date_parsed"),
                        "ipoIssueClosingDateStatus": ipo_item.get("ipo_issue_closing_date_status"),
                        "ipoIssueClosingDateParsed": ipo_item.get("ipo_issue_closing_date_parsed"),
                        "ipoOpenDate": ipo_item.get("ipo_open_date"),
                        "ipoCloseDate": ipo_item.get("ipo_close_date"),
                        
                        # Timeline Information
                        "basisOfAllotment": ipo_item.get("basis_of_allotment"),
                        "initiationOfRefunds": ipo_item.get("initiation_of_refunds"),
                        "creditOfSharesToDemat": ipo_item.get("credit_of_shares_to_demat"),
                        "listingDate": ipo_item.get("listing_date"),
                        
                        # Additional Date Status Fields
                        "ipoOpenDateStatus": ipo_item.get("ipo_open_date_status"),
                        "ipoOpenDateParsed": ipo_item.get("ipo_open_date_parsed"),
                        "ipoCloseDateStatus": ipo_item.get("ipo_close_date_status"),
                        "ipoCloseDateParsed": ipo_item.get("ipo_close_date_parsed"),
                        "listingDateStatus": ipo_item.get("listing_date_status"),
                        "listingDateParsed": ipo_item.get("listing_date_parsed"),
                        "basisOfAllotmentStatus": ipo_item.get("basis_of_allotment_status"),
                        "basisOfAllotmentParsed": ipo_item.get("basis_of_allotment_parsed"),
                        "initiationOfRefundsStatus": ipo_item.get("initiation_of_refunds_status"),
                        "initiationOfRefundsParsed": ipo_item.get("initiation_of_refunds_parsed"),
                        "creditOfSharesToDematStatus": ipo_item.get("credit_of_shares_to_demat_status"),
                        "creditOfSharesToDematParsed": ipo_item.get("credit_of_shares_to_demat_parsed"),
                        
                        # Lot Information
                        "lotIssuePrice": ipo_item.get("lot_issue_price"),
                        "lotMarketLot": ipo_item.get("lot_market_lot"),
                        "lotIndividualInvestor": ipo_item.get("lot_individual_investor"),
                        "lotMinHniLots": ipo_item.get("lot_min_hni_lots"),
                        "lotMinSmallHniLots210Lakh": ipo_item.get("lot_min_small_hni_lots_2_10_lakh"),
                        "lotMinBigHniLots10PlusLakh": ipo_item.get("lot_min_big_hni_lots_10_plus_lakh"),
                        
                        # GMP (Grey Market Premium) Data - Mapped from input fields
                        "seq": ipo_item.get("Seq"),
                        "idGmpData": ipo_item.get("id (GMP Data)"),  # Mapped from "id (GMP Data)"
                        "ipoIdGmpData": ipo_item.get("ipo_id (GMP Data)"),  # Mapped from "ipo_id (GMP Data)"
                        "gmpDate": ipo_item.get("gmp_date"),
                        "currentGmp": ipo_item.get("gmp"),  # Mapped from "gmp" to "current_gmp"
                        "gmpComments": ipo_item.get("gmp_comments"),
                        "gmpCompareDesc": ipo_item.get("gmp_compare_desc"),
                        "subjectToSauda": ipo_item.get("subject_to_sauda"),
                        "gmpCity": ipo_item.get("gmp_city"),
                        "gmpVariation": ipo_item.get("gmp_variation"),
                        "maxIpoPrice": ipo_item.get("max_ipo_price"),
                        "estimatedListingPrice": ipo_item.get("estimated_listing_price"),
                        "gmpPercentCalc": ipo_item.get("gmp_percent_calc"),
                        "gmpDescOther": ipo_item.get("gmp_desc_other"),
                        "upDownStatus": ipo_item.get("up_down_status"),
                        "gmpActiveRecordFlag": ipo_item.get("gmp_active_record_flag"),
                        "sub2SaudaRate": ipo_item.get("sub2 Sauda Rate"),
                        "estProfit": ipo_item.get("est_profit"),
                        "createDate": ipo_item.get("create_date"),
                        "createDateGmp": ipo_item.get("create_date_gmp"),
                        "lastUpdatedGmp": ipo_item.get("last_updated_gmp"),
                        "lastUpdated": ipo_item.get("last_updated"),
                        
                        # Table Data Fields - Mapped from input fields
                        "ipoIssueOpeningDateTable": ipo_item.get("IPO Issue Opening Date"),
                        "ipoIssueClosingDateTable": ipo_item.get("IPO Issue Closing Date"),
                        "ipoIssuePriceTable": ipo_item.get("IPO Issue Price"),
                        "drhpLinkTable": ipo_item.get("DRHP Link"),
                        "rhpLinkTable": ipo_item.get("RHP Link"),
                        "listingAtTable": ipo_item.get("Listing At"),
                        "retailQuotaTable": ipo_item.get("Retail Quota"),
                        "ipoIssueTypeTable": ipo_item.get("IPO Issue Type"),
                        "ipoIssueSizeTable": ipo_item.get("IPO Issue Size (Cr)"),
                        "freshIssueTable": ipo_item.get("Fresh Issue (Cr)"),
                        "faceValueTable": ipo_item.get("Face Value"),
                        "promoterHoldingPreIpoTable": ipo_item.get("Promoter Holding Pre IPO (%)"),
                        "promoterHoldingPostIpoTable": ipo_item.get("Promoter Holding Post IPO (%)"),
                        "anchorListLinkTable": ipo_item.get("Anchor List Link"),
                        "minOrderQuantityTable": ipo_item.get("Min Order Quantity (Table)"),
                        "lotSizeTable": ipo_item.get("Lot Size (Table)"),
                        "allotmentStatusTable": ipo_item.get("Allotment Status"),
                        
                        # Metadata
                        "lastUpdatedTimestamp": ipo_item.get("last_updated_timestamp"),
                        "metaTitle": ipo_item.get("metaTitle"),
                        "pageTitle": ipo_item.get("pageTitle"),
                        "metaDesc": ipo_item.get("metaDesc"),
                        "cacheKey": ipo_item.get("cacheKey"),
                        "currentTime": ipo_item.get("currentTime"),
                        "scrapedAt": ipo_item.get("scraped_at"),
                        
                        # Array Fields - Direct mapping
                        "ipoShareAllocation": ipo_item.get("IPO Share Allocation", []),
                        "ipoDaywiseSubscriptionTable": ipo_item.get("IPO Daywise Subscription (Table)", []),
                        "ipoSharesBidAmountTable": ipo_item.get("IPO Shares Bid Amount (Table)", []),
                        "ipoBiddingHistoryJson": ipo_item.get("IPO Bidding History (JSON)", []),
                        "gmpTrendHistoryTable": ipo_item.get("GMP Trend History (Table)", []),
                        "strengths": ipo_item.get("strengths", []),
                        "objectives": ipo_item.get("objectives", []),
                        "companyFinancialInformationRestatedConsolidated": ipo_item.get("Company Financial Information (Restated Consolidated)", []),
                        "peerComparison": ipo_item.get("peer_comparison", []),
                        
                        # Object Fields - Direct mapping
                        "companyAddress": ipo_item.get("company_address", {}),
                        "ipoRegistrar": ipo_item.get("ipo_registrar", {}),
                        "ipoLeadManager": ipo_item.get("ipo_lead_manager", []),
                        "companySectorInfo": ipo_item.get("company_sector_info", {}),
                        
                        # System timestamp for tracking
                        "timestamp": current_time_ist.isoformat()
                    }

                    formatted_data.append(formatted_ipo)
                    
                except Exception as item_error:
                    logger.error(f"Error formatting individual IPO record {ipo_item.get('ipo_id', 'unknown')}: {str(item_error)}")
                    continue
            
            logger.info(f"Successfully formatted {len(formatted_data)} IPO records")
            # print("from format_investorgain_ipo_data:", formatted_data)
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting InvestorGain IPO data: {str(e)}")
            return []
        


