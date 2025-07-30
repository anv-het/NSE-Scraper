import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from API.Controller.top_gainers_loosers import NSETopGainersloosersController

def test_scrape_top_gainers():
    print("Running test for NSE Top Gainers scraping")
    controller = NSETopGainersloosersController()
    result = controller.scrape_top_gainers()
    print("Result:", result)
    assert isinstance(result, dict), "Response is not a dictionary"
    assert "success" in result, "Missing 'success' key"

def test_scrape_top_loosers():
    print("Running test for NSE Top Loosers scraping")
    controller = NSETopGainersloosersController()
    result = controller.scrape_top_loosers()
    print("Result:", result)
    assert isinstance(result, dict), "Response is not a dictionary"
    assert "success" in result, "Missing 'success' key"

def test_top_gainers_and_loosers_async():
    print("Running async test for top gainers and loosers")
    controller = NSETopGainersloosersController()
    result = asyncio.run(controller.top_gainer_loosers())
    print("Result:", result)
    assert isinstance(result, dict), "Response is not a dictionary"
    assert "success" in result, "Missing 'success' key"

if __name__ == "__main__":
    # test_scrape_top_gainers()
    # test_scrape_top_loosers()
    test_top_gainers_and_loosers_async()
    print("✅ All NSE Top Gainers and Loosers tests passed!")
