import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController

def test_scrape_most_active_equities():
    print("Running test for NSE Most Active Equities scraping")
    controller = NSEMostActiveEquitiesController()
    
    # Await the async method properly
    result = controller.scrape_most_active_equities()

    # Print raw result for debugging
    print("Result:", result)

def test_scrape_most_active_etf_equities():
    print("Running test for NSE Most Active ETF Equities scraping")
    controller = NSEMostActiveEquitiesController()
    result = controller.scrape_most_active_etf_equities()
    print("Most Active ETF Equities:", result)

def test_scrape_most_active_variations():
    print("Running test for NSE Most Active Variations scraping")
    controller = NSEMostActiveEquitiesController()
    result_lower = controller.scrape_most_active_variations("lower")
    result_greater = controller.scrape_most_active_variations("greater")

    print("Most Active Variations (Lower):", result_lower)
    print("Most Active Variations (Greater):", result_greater)

def test_scrape_most_active_volume_gainers():
    print("Running test for NSE Most Active Volume Gainers scraping")
    controller = NSEMostActiveEquitiesController()
    result = controller.scrape_most_active_volume_gainers()

    print("Most Active Volume Gainers:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"
if __name__ == "__main__":
    test_scrape_most_active_equities()
    test_scrape_most_active_etf_equities()
    test_scrape_most_active_variations()
    test_scrape_most_active_volume_gainers()
    print("✅ Most Active Equities test passed!")
    print("✅ Most Active ETF Equities test passed!")