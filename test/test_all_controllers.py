import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.top_gainers_loosers import NSETopGainersloosersController
from API.Controller.most_active_contract import NSEMostActiveContractsController
from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController
from API.Controller.most_active_underlying import NSEMostActiveUnderlyingController
from API.Controller.recent_listing import NSERecentListingsController
from API.Controller.new_listing_stoks import NSENewListingsController
from API.Controller.forth_comming_listing import NSEForthcomingListingsController
from API.Controller.special_preopen_listing import NSESpecialPreopenListingsController
from API.Controller.nse_52week_high_low import NSE52WeekHighLowController
from API.Controller.nse_all_indexes import NSEAllIndexesController
from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController
from API.Controller.large_deal import NSELargeDealsController
from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController
from API.Controller.stockwise_event_data import StockwiseEventDataController

def test_top_gainers_loosers():
    """
    Test the scraping of Top Gainers and Loosers data from NSE.
    """
    print("Testing Top Gainers Loosers...")
    controller = NSETopGainersloosersController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.top_gainer_loosers())
    
    print(f"✅ Top Gainers Loosers: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_most_active_contracts():
    """
    Test the scraping of Most Active Contracts data from NSE.
    """
    print("Testing Most Active Contracts...")
    controller = NSEMostActiveContractsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_most_active_contracts())
    
    print(f"✅ Most Active Contracts: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_most_active_equities():
    """
    Test the scraping of Most Active Equities data from NSE.
    """
    print("Testing Most Active Equities...")
    controller = NSEMostActiveEquitiesController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_most_active_equities())
    
    print(f"✅ Most Active Equities: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_most_active_underlying():
    """
    Test the scraping of Most Active Underlying data from NSE.
    """
    print("Testing Most Active Underlying...")
    controller = NSEMostActiveUnderlyingController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_most_active_underlying())
    
    print(f"✅ Most Active Underlying: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_recent_listings():
    """
    Test the scraping of Recent Listings data from NSE.
    """
    print("Testing Recent Listings...")
    controller = NSERecentListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_recent_listings())
    
    print(f"✅ Recent Listings: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_new_listings():
    """
    Test the scraping of New Listings data from NSE.
    """
    print("Testing New Listings...")
    controller = NSENewListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_new_listing())
    
    print(f"✅ New Listings: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_forthcoming_listings():
    """
    Test the scraping of Forthcoming Listings data from NSE.
    """
    print("Testing Forthcoming Listings...")
    controller = NSEForthcomingListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_forthcoming_listings())
    
    print(f"✅ Forthcoming Listings: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_special_preopen_listings():
    """
    Test the scraping of Special Pre-Open Listings data from NSE.
    """
    print("Testing Special Pre-Open Listings...")
    controller = NSESpecialPreopenListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_special_preopen_listings())
    
    print(f"✅ Special Pre-Open Listings: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_52_week_high_low():
    """
    Test the scraping of 52-week High and Low data from NSE.
    """
    print("Testing 52-week High Low...")
    controller = NSE52WeekHighLowController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_52_week_high_low())
    
    print(f"✅ 52-week High Low: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_all_indexes():
    """
    Test the scraping of All Indexes data from NSE.
    """
    print("Testing All Indexes...")
    controller = NSEAllIndexesController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_all_indices_from_list())
    
    print(f"✅ All Indexes: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_price_band_hitters():
    """
    Test the scraping of Price Band Hitters data from NSE.
    """
    print("Testing Price Band Hitters...")
    controller = NSEPriceBandHittersController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_price_band_hitters())
    
    print(f"✅ Price Band Hitters: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_large_deals():
    """
    Test the scraping of Large Deals data from NSE.
    """
    print("Testing Large Deals...")
    controller = NSELargeDealsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_large_deals())
    
    print(f"✅ Large Deals: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_advances_declines_unchanged():
    """
    Test the scraping of Advances Declines Unchanged data from NSE.
    """
    print("Testing Advances Declines Unchanged...")
    controller = NSEAdvancesDeclinesUnchangedController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_advance_decline_unchanged())
    
    print(f"✅ Advances Declines Unchanged: {'Success' if result.get('success') else 'Failed'}")
    return result

def test_stockwise_event_data():
    """
    Test the scraping of Stockwise Event data from NSE.
    """
    print("Testing Stockwise Event Data...")
    controller = StockwiseEventDataController()
    
    # Example symbol to test
    symbol = "ITC"
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_stockwise_event_data(symbol))
    
    print(f"✅ Stockwise Event Data: {'Success' if result.get('success') else 'Failed'}")
    return result

def run_all_tests():
    """
    Run all controller tests and provide a summary.
    """
    print("=" * 60)
    print("🚀 STARTING NSE SCRAPER - ALL CONTROLLERS TEST")
    print("=" * 60)
    
    # List of all test functions
    test_functions = [
        test_top_gainers_loosers,
        test_most_active_contracts,
        test_most_active_equities,
        test_most_active_underlying,
        test_recent_listings,
        test_new_listings,
        test_forthcoming_listings,
        test_special_preopen_listings,
        test_52_week_high_low,
        test_all_indexes,
        test_price_band_hitters,
        test_large_deals,
        test_advances_declines_unchanged,
        test_stockwise_event_data
    ]
    
    results = []
    success_count = 0
    failed_count = 0
    
    for test_func in test_functions:
        try:
            result = test_func()
            results.append({
                'test': test_func.__name__,
                'success': result.get('success', False) if result else False,
                'result': result
            })
            
            if result and result.get('success'):
                success_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"❌ {test_func.__name__}: Error - {str(e)}")
            results.append({
                'test': test_func.__name__,
                'success': False,
                'error': str(e)
            })
            failed_count += 1
        
        print("-" * 40)
    
    # Print summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful Tests: {success_count}")
    print(f"❌ Failed Tests: {failed_count}")
    print(f"📈 Total Tests: {len(test_functions)}")
    print(f"🎯 Success Rate: {(success_count/len(test_functions)*100):.1f}%")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    run_all_tests()
    print("All controller tests completed!")
