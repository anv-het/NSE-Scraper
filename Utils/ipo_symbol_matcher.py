import re
from datetime import datetime, timedelta
from thefuzz import fuzz
from contextlib import closing
from Utils.db import DatabaseManager
from Utils.ipo_utils import (
        calculate_company_name_similarity,
        validate_ipo_match,

        # Constants for matching logic
        MATCH_THRESHOLD,
        DATE_TOLERANCE_DAYS,
        PRICE_TOLERANCE,
        MIN_VALIDATION_MATCHES
    )
import logging

# Configure logging
logger = logging.getLogger(__name__)


def get_ipo_symbol_with_fallback(master_record, formatted_record):
    """
    Get IPO symbol with proper fallback logic.
    Priority: 1. Master symbol 2. ipoNseCodeTable 3. ipoBseCodeTable 4. null
    """
    # First priority: Get symbol from master table
    master_symbol = master_record.get("symbol")
    if master_symbol and master_symbol.strip() and master_symbol.strip().upper() not in ['Y', 'N', 'NULL', 'NONE']:
        return master_symbol.strip(), "MASTER"
    
    # Second priority: Get from formatted record's NSE code
    nse_code = formatted_record.get("ipoNseCodeTable")
    if nse_code and nse_code.strip() and nse_code.strip().upper() not in ['N/A', 'NULL', 'NONE', '']:
        return nse_code.strip(), "NSE_SCRAPED"
    
    # Third priority: Get from formatted record's BSE code  
    bse_code = formatted_record.get("ipoBseCodeTable")
    if bse_code and bse_code.strip() and bse_code.strip().upper() not in ['N/A', 'NULL', 'NONE', '']:
        return bse_code.strip(), "BSE_SCRAPED"
    
    # No valid symbol found
    return None, None

def determine_exchange_preference(master_record, formatted_record, symbol_source):
    """
    Determine the preferred exchange based on symbol source and availability.
    """
    if symbol_source == "MASTER":
        # Check which exchanges are available in master
        bse_available = master_record.get("BSE") == "Y"
        nse_available = master_record.get("NSE") == "Y"
        
        # Check listing preference from scraped data
        listing_table = (formatted_record.get("listingAtTable") or "").upper()
        
        # Prefer NSE if available and in listing, otherwise BSE
        if nse_available and ("NSE" in listing_table or not listing_table):
            return "NSE"
        elif bse_available and ("BSE" in listing_table or not listing_table):
            return "BSE"
        elif nse_available:  # NSE available but not in listing preference
            return "NSE"
        elif bse_available:  # BSE available but not in listing preference
            return "BSE"
        else:
            return "NSE"  # Default to NSE
    
    elif symbol_source == "NSE_SCRAPED":
        return "NSE"
    elif symbol_source == "BSE_SCRAPED":
        return "BSE"
    else:
        # Default preference
        return formatted_record.get("listingAtTable") or "NSE"

def fetch_nse_bse_codes(formatted_data):
    """
    Enhanced function to match formatted IPO data with IPO_Master and add symbols.
    Fixed version that gets actual symbols from master table instead of Y/N values.
    
    Args:
        formatted_data (list of dicts): The list of IPOs to be enriched.
        
    Returns:
        list of dicts: The enriched list of IPOs with 'ipoSymbol' and 'ipoExchange' added.
    """
    db_manager = DatabaseManager()
    
    # Check if SQL connection can be established
    if not db_manager._create_sql_server_connection():
        logger.error("Failed to connect to SQL Server. Adding None symbols.")
        for record in formatted_data:
            record['ipoSymbol'] = None
            record['ipoExchange'] = None
        return formatted_data
    
    try:
        with closing(db_manager.sql_connection.cursor()) as cursor:
            # Fetch master data - Include symbol column for actual IPO codes
            cursor.execute("""
                SELECT symbol, name, biddingStartDate, biddingEndDate, lotSize, 
                       cutOffPrice, isin, BSE, NSE
                FROM IPO_Master
                WHERE name IS NOT NULL
            """)
            ipo_master_data = cursor.fetchall()
            ipo_master_columns = [col[0] for col in cursor.description]
            
            master_records = [dict(zip(ipo_master_columns, row)) for row in ipo_master_data]
            
            logger.info(f"Processing {len(formatted_data)} IPO records against {len(master_records)} master records")
            
            matched_count = 0
            
            # Process each formatted IPO record
            for record in formatted_data:
                record['ipoSymbol'] = None
                record['ipoExchange'] = None
                
                best_match = None
                best_score = 0
                best_validations = 0
                
                try:
                    # Compare with each master record
                    for master_record in master_records:
                        # Calculate name similarity
                        similarity_score = calculate_company_name_similarity(record, master_record)
                        
                        # Skip if similarity is below threshold
                        if similarity_score < MATCH_THRESHOLD:
                            continue
                        
                        # Validate the match
                        validations_passed, validation_details = validate_ipo_match(record, master_record)
                        
                        # Check if this is the best match so far
                        if (validations_passed >= MIN_VALIDATION_MATCHES and 
                            (validations_passed > best_validations or 
                             (validations_passed == best_validations and similarity_score > best_score))):
                            
                            best_match = master_record
                            best_score = similarity_score
                            best_validations = validations_passed
                    
                    # Assign symbol if match found
                    if best_match:
                        # Use proper fallback logic to get symbol
                        symbol, symbol_source = get_ipo_symbol_with_fallback(best_match, record)
                        
                        if symbol:
                            # Determine exchange based on symbol source and master data
                            exchange = determine_exchange_preference(best_match, record, symbol_source)
                            
                            record['ipoSymbol'] = symbol
                            record['ipoExchange'] = exchange
                            matched_count += 1
                            
                            logger.info(f"✓ Matched '{record.get('apiCompanyName')}' → "
                                      f"Symbol: {symbol} ({exchange}) | Source: {symbol_source} | "
                                      f"Score: {best_score} | Validations: {best_validations}")
                        else:
                            logger.warning(f"Match found but no valid symbol for '{record.get('apiCompanyName')}'")
                    else:
                        # Try fallback - use codes from scraped data if available
                        fallback_symbol = record.get("ipoNseCodeTable") or record.get("ipoBseCodeTable")
                        if fallback_symbol and fallback_symbol != "N/A":
                            record['ipoSymbol'] = fallback_symbol
                            record['ipoExchange'] = record.get("listingAtTable")
                            logger.info(f"◉ Used fallback symbol for '{record.get('apiCompanyName')}': {fallback_symbol}")
                        else:
                            logger.warning(f"✗ No match found for '{record.get('apiCompanyName')}'")
                
                except Exception as e:
                    logger.error(f"Error processing record '{record.get('apiCompanyName')}': {e}")
                    continue
            
            logger.info(f"Symbol matching complete: {matched_count}/{len(formatted_data)} records matched")
            return formatted_data
            
    except Exception as e:
        logger.error(f"Database error in fetch_nse_bse_codes: {e}")
        # Return original data with None symbols if error occurs
        for record in formatted_data:
            if 'ipoSymbol' not in record:
                record['ipoSymbol'] = "N/A"
            if 'ipoExchange' not in record:
                record['ipoExchange'] = "N/A"
        return formatted_data
    
    finally:
        # Ensure connection is properly closed
        try:
            if db_manager.sql_connection:
                db_manager.sql_connection.close()
        except:
            pass

