import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_contract import NSEMostActiveContractsController

def test_scrap_most_active_contracts():
    """
    Test the scraping of Most Active Contracts data from NSE.
    This test will demonstrate the enhanced masterdata integration.
    """
    print("🚀 Testing Enhanced Most Active Contracts with Masterdata Integration")
    print("="*80)
    
    controller = NSEMostActiveContractsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_most_active_contracts())

    # Enhanced output to show masterdata fields
    print("\n📊 Test Results:")
    print(f"Status: {result.get('status', 'Unknown')}")
    print(f"Message: {result.get('message', 'No message')}")
    
    data = result.get('data', [])
    print(f"Total Records Retrieved: {len(data)}")
    
    # Show first few records with masterdata fields
    derivatives_count = 0
    enriched_count = 0
    
    print("\n🔍 Sample Records with Masterdata Enhancement:")
    print("-" * 80)
    
    for i, record in enumerate(data[:5], 1):  # Show first 5 records
        print(f"\nRecord {i}:")
        print(f"  Identifier: {record.get('identifier', 'N/A')}")
        print(f"  Instrument Type: {record.get('instrumentType', 'N/A')}")
        print(f"  Underlying: {record.get('underlying', 'N/A')}")
        print(f"  Strike Price: {record.get('strikePrice', 'N/A')}")
        print(f"  Option Type: {record.get('optionType', 'N/A')}")
        print(f"  Expiry Date: {record.get('expiryDate', 'N/A')}")
        
        # Check if this is a derivative with masterdata
        is_derivative = record.get('instrumentType') in ['OPTIDX', 'OPTSTK']
        if is_derivative:
            derivatives_count += 1
            
        # Show masterdata fields
        exchange_id = record.get('ExchangeInstrumentID')
        exchange_segment = record.get('ExchangeSegment')
        masterdata_series = record.get('MasterdataSeries')
        
        print(f"  --- Masterdata Fields ---")
        print(f"  ExchangeInstrumentID: {exchange_id}")
        print(f"  ExchangeSegment: {exchange_segment}")
        print(f"  MasterdataSeries: {masterdata_series}")
        
        if exchange_id and is_derivative:
            enriched_count += 1
            print(f"  ✅ Masterdata Enhancement: SUCCESS")
        elif is_derivative:
            print(f"  ⚠️  Masterdata Enhancement: Not found")
        else:
            print(f"  ℹ️  Non-derivative: No enhancement needed")
    
    # Summary statistics
    print(f"\n📈 Enhancement Summary:")
    print(f"  Total Records: {len(data)}")
    print(f"  Derivatives Found: {derivatives_count}")
    print(f"  Successfully Enriched: {enriched_count}")
    if derivatives_count > 0:
        enrichment_rate = (enriched_count / derivatives_count) * 100
        print(f"  Enrichment Rate: {enrichment_rate:.1f}%")
    
    return result

if __name__ == "__main__":
    test_scrap_most_active_contracts()
    print("Test completed successfully.")