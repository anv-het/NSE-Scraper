import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.large_deal import NSELargeDealsController


def test_scrape_large_deals():
    print("Running test for NSE Large Deals scraping")
    controller = NSELargeDealsController()
    
    # Await the async method properly
    result = asyncio.run(controller.scrap_large_deals())

    # Print raw result for debugging (optional)
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    test_scrape_large_deals()
    print("✅ Large Deals test passed!")
