import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.nse_all_indexes import NSEAllIndexesController

def test_scrap_all_indexes():
    print("Running test for NSE All Indexes scraping")
    controller = NSEAllIndexesController()
    
    # Await the async method properly
    result = asyncio.run(controller.scrape_all_indices_from_list())

    # Print raw result for debugging (optional)
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"
    assert "index_info" in result, "Missing 'index_info' key"
    assert "stocks" in result, "Missing 'stocks' key"

if __name__ == "__main__":
    test_scrap_all_indexes()
    print("✅ All Indexes test passed!")
