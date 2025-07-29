
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from API.Controller.top_gainers_loosers import NSETopGainersloosersController


def test_scrape_top_gainers():
    print("Running test for NSE Top Gainers scraping")
    controller = NSETopGainersloosersController()
    
    # Await the async method properly
    result = controller.scrape_top_gainers()

    # Print raw result for debugging
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"
    
def test_scrape_top_loosers():
    print("Running test for NSE Top Loosers scraping")
    controller = NSETopGainersloosersController()
    
    # Await the async method properly
    result = controller.scrape_top_loosers()

    # Print raw result for debugging
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    test_scrape_top_gainers()
    test_scrape_top_loosers()
    print("✅ Top Gainers and Loosers tests passed!")
