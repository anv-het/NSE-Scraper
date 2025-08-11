#!/usr/bin/env python3
"""
Debug script to investigate why masterdata matching is failing for specific records
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Utils.data_formatter import NSEDataFormatter
from Utils.general_master import get_all_derivatives_masterdata
from Utils.mongo_client_master import get_masterdata_db

def debug_specific_nifty_case():
    """Debug the specific NIFTY 25000 Call case mentioned by user"""
    
    print("=" * 70)
    print("DEBUGGING NIFTY 25000 CALL MASTERDATA MATCHING")
    print("=" * 70)
    
    # The exact record from user's example that should have masterdata
    problematic_record = {
        "identifier": "OPTIDXNIFTY14-08-2025CE25000.00",
        "instrumentType": "OPTIDX",
        "instrument": "Index Options",
        "underlying": "NIFTY",
        "expiryDate": "14-Aug-2025",
        "optionType": "Call",
        "strikePrice": 25000,
        "lastPrice": 7.9,
        "numberOfContractsTraded": 553969,
        "totalTurnover": 3261.4924875,
        "premiumTurnover": 10390180.2424875,
        "openInterest": 181734,
        "underlyingValue": 24461.55,
        "pChange": -16.842105263157894
    }
    
    print("\n1. PROBLEMATIC RECORD:")
    print(f"  Underlying: {problematic_record['underlying']}")
    print(f"  StrikePrice: {problematic_record['strikePrice']}")
    print(f"  ExpiryDate: {problematic_record['expiryDate']}")
    print(f"  OptionType: {problematic_record['optionType']}")
    
    # Expected masterdata from user's query
    expected_masterdata = {
        "ExchangeInstrumentID": "44512",
        "ExchangeSegment": "NSEFO",
        "Series": "OPTIDX",
        "Name": "NIFTY",
        "StrikePrice": "25000",
        "expiryDate": "14-Aug-2025",
        "OptionTypeDesc": "Call"
    }
    
    print("\n2. EXPECTED MASTERDATA (from user's query):")
    print(f"  Name: {expected_masterdata['Name']}")
    print(f"  StrikePrice: {expected_masterdata['StrikePrice']}")
    print(f"  expiryDate: {expected_masterdata['expiryDate']}")
    print(f"  OptionTypeDesc: {expected_masterdata['OptionTypeDesc']}")
    print(f"  ExchangeInstrumentID: {expected_masterdata['ExchangeInstrumentID']}")
    
    # Test the current mapping logic step by step
    print("\n3. TESTING CURRENT MAPPING LOGIC...")
    
    # Get masterdata
    print("  → Fetching derivatives masterdata...")
    derivatives_masterdata = get_all_derivatives_masterdata()
    print(f"  → Found {len(derivatives_masterdata)} derivatives records")
    
    # Create lookup dictionary (same as in format_most_active_contracts)
    print("  → Creating lookup dictionary...")
    masterdata_lookup = {}
    matching_records = []
    
    for doc in derivatives_masterdata:
        name = str(doc.get("Name") or "").strip().upper()
        strike_price = doc.get("StrikePrice")
        expiry_date = str(doc.get("expiryDate") or "").strip()
        option_type = str(doc.get("OptionTypeDesc") or "").strip()
        
        # Check if this is our target record
        if (name == "NIFTY" and 
            str(strike_price) == "25000" and 
            expiry_date == "14-Aug-2025" and 
            option_type == "Call"):
            matching_records.append(doc)
            print(f"  ✓ Found matching record: ID={doc.get('ExchangeInstrumentID')}")
        
        if name and strike_price is not None and expiry_date and option_type:
            try:
                strike_float = float(strike_price)
                lookup_key = f"{name}_{strike_float}_{expiry_date}_{option_type}"
                masterdata_lookup[lookup_key] = doc
            except (ValueError, TypeError):
                continue
    
    print(f"  → Created lookup with {len(masterdata_lookup)} keys")
    print(f"  → Found {len(matching_records)} exact matches for NIFTY 25000 Call")
    
    # Test the exact lookup key that should be generated
    print("\n4. TESTING LOOKUP KEY GENERATION...")
    underlying = str(problematic_record.get("underlying", "")).strip().upper()
    strike_price = problematic_record.get("strikePrice")
    expiry_date = str(problematic_record.get("expiryDate", "")).strip()
    option_type = str(problematic_record.get("optionType", "")).strip()
    
    print(f"  → underlying: '{underlying}'")
    print(f"  → strike_price: {strike_price} (type: {type(strike_price)})")
    print(f"  → expiry_date: '{expiry_date}'")
    print(f"  → option_type: '{option_type}'")
    
    if underlying and strike_price is not None and expiry_date and option_type:
        try:
            strike_float = float(strike_price)
            lookup_key = f"{underlying}_{strike_float}_{expiry_date}_{option_type}"
            print(f"  → Generated lookup key: '{lookup_key}'")
            
            # Check if key exists in lookup
            masterdata_match = masterdata_lookup.get(lookup_key)
            if masterdata_match:
                print("  ✓ FOUND MATCH!")
                print(f"    ExchangeInstrumentID: {masterdata_match.get('ExchangeInstrumentID')}")
                print(f"    ExchangeSegment: {masterdata_match.get('ExchangeSegment')}")
                print(f"    Series: {masterdata_match.get('Series')}")
            else:
                print("  ✗ NO MATCH FOUND")
                print("  → Checking if similar keys exist...")
                
                # Find similar keys
                similar_keys = [key for key in masterdata_lookup.keys() if "NIFTY" in key and "25000" in key]
                print(f"  → Found {len(similar_keys)} similar keys with NIFTY and 25000:")
                for key in similar_keys[:5]:  # Show first 5
                    print(f"    - {key}")
                    
        except Exception as e:
            print(f"  ✗ Error generating lookup key: {e}")
    
    print("\n5. DIRECT DATABASE QUERY TEST...")
    # Test direct database query to confirm the record exists
    try:
        db = get_masterdata_db()
        collection = db["MASTERDATA"]
        
        query = {
            "OptionTypeDesc": "Call",
            "Name": "NIFTY", 
            "expiryDate": "14-Aug-2025",
            "StrikePrice": "25000"
        }
        
        print(f"  → Running query: {query}")
        result = collection.find_one(query)
        
        if result:
            print("  ✓ DIRECT QUERY FOUND RECORD!")
            print(f"    ExchangeInstrumentID: {result.get('ExchangeInstrumentID')}")
            print(f"    ExchangeSegment: {result.get('ExchangeSegment')}")
            print(f"    Series: {result.get('Series')}")
            print(f"    Name: {result.get('Name')}")
            print(f"    StrikePrice: {result.get('StrikePrice')} (type: {type(result.get('StrikePrice'))})")
            print(f"    expiryDate: {result.get('expiryDate')}")
            print(f"    OptionTypeDesc: {result.get('OptionTypeDesc')}")
        else:
            print("  ✗ DIRECT QUERY FAILED")
            
            # Try variations
            print("  → Trying StrikePrice as number...")
            query2 = query.copy()
            query2["StrikePrice"] = 25000
            result2 = collection.find_one(query2)
            if result2:
                print("  ✓ Found with numeric StrikePrice!")
            else:
                print("  ✗ Still not found with numeric StrikePrice")
                
    except Exception as e:
        print(f"  ✗ Database query error: {e}")

def test_format_function_with_problematic_record():
    """Test the actual format function with the problematic record"""
    
    print("\n" + "=" * 70)
    print("TESTING FORMAT FUNCTION WITH PROBLEMATIC RECORD")
    print("=" * 70)
    
    # Create mock data with the problematic record
    mock_data = {
        "most_active_oi": {
            "volume": {
                "data": [
                    {
                        "identifier": "OPTIDXNIFTY14-08-2025CE25000.00",
                        "instrumentType": "OPTIDX",
                        "instrument": "Index Options",
                        "underlying": "NIFTY",
                        "expiryDate": "14-Aug-2025",
                        "optionType": "Call",
                        "strikePrice": 25000,
                        "lastPrice": 7.9,
                        "numberOfContractsTraded": 553969,
                        "totalTurnover": 3261.4924875,
                        "premiumTurnover": 10390180.2424875,
                        "openInterest": 181734,
                        "underlyingValue": 24461.55,
                        "pChange": -16.842105263157894
                    }
                ]
            }
        }
    }
    
    print("Running format_most_active_contracts...")
    formatted_result = NSEDataFormatter.format_most_active_contracts(mock_data)
    
    if formatted_result:
        record = formatted_result[0]
        print(f"Result:")
        print(f"  ExchangeInstrumentID: {record.get('ExchangeInstrumentID')}")
        print(f"  ExchangeSegment: {record.get('ExchangeSegment')}")
        print(f"  MasterdataSeries: {record.get('MasterdataSeries')}")
        
        if record.get('ExchangeInstrumentID'):
            print("  ✓ SUCCESS: Masterdata fields populated!")
        else:
            print("  ✗ FAILED: Masterdata fields are null")
    else:
        print("  ✗ No formatted result returned")

if __name__ == "__main__":
    debug_specific_nifty_case()
    test_format_function_with_problematic_record()
