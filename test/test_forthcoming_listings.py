import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.forth_comming_listing import NSEForthcomingListingsController


def test_scrap_forthcoming_listings():
    print("Running test for NSE Forthcoming Listings scraping")
    controller = NSEForthcomingListingsController()
    
    # Await the async method properly
    result = asyncio.run(controller.scrap_forthcoming_listings())

    # Print raw result for debugging (optional)
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    test_scrap_forthcoming_listings()
    print("✅ Forthcoming Listings test passed!")
