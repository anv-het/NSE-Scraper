#!/usr/bin/env python3
"""
Real NSE data test for masterdata integration in format_most_active_contracts
"""

import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from API.Controller.most_active_contract import NSEMostActiveContractsController

async def test_real_nse_data():
    """Test with real NSE data"""
    
    print("=" * 70)
    print("TESTING WITH REAL NSE DATA")
    print("=" * 70)
    
    try:
        controller = NSEMostActiveContractsController()
        print("✓ Controller initialized successfully")
        
        # Get real NSE data
        print("\nFetching real NSE most active contracts data...")
        result = await controller.scrap_most_active_contracts()
        
        if result and result.get("status") == "success":
            data = result.get("data", [])
            print(f"✓ Successfully fetched {len(data)} records from NSE")
            
            # Check masterdata enrichment
            enriched_count = 0
            total_derivatives = 0
            
            print("\nChecking masterdata enrichment...")
            for i, record in enumerate(data[:10]):  # Check first 10 records
                if record.get("instrumentType") in ["OPTIDX", "OPTSTK"]:
                    total_derivatives += 1
                    if record.get("ExchangeInstrumentID"):
                        enriched_count += 1
                        print(f"✓ Record {i+1}: {record['underlying']} {record['strikePrice']} {record['optionType']} -> ID: {record['ExchangeInstrumentID']}")
                    else:
                        print(f"⚠ Record {i+1}: {record['underlying']} {record['strikePrice']} {record['optionType']} -> No masterdata match")
            
            print(f"\nEnrichment Summary:")
            print(f"Total derivatives records: {total_derivatives}")
            print(f"Successfully enriched: {enriched_count}")
            print(f"Enrichment rate: {(enriched_count/total_derivatives*100):.1f}%" if total_derivatives > 0 else "N/A")
            
            # Show sample enriched record
            for record in data:
                if record.get("ExchangeInstrumentID"):
                    print(f"\nSample Enriched Record:")
                    print(f"  Underlying: {record['underlying']}")
                    print(f"  Strike Price: {record['strikePrice']}")
                    print(f"  Expiry Date: {record['expiryDate']}")
                    print(f"  Option Type: {record['optionType']}")
                    print(f"  ExchangeInstrumentID: {record['ExchangeInstrumentID']}")
                    print(f"  ExchangeSegment: {record['ExchangeSegment']}")
                    print(f"  MasterdataSeries: {record['MasterdataSeries']}")
                    break
                    
        else:
            print(f"✗ Failed to fetch NSE data: {result}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("REAL DATA TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_real_nse_data())
