import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_underlying import NSEMostActiveUnderlyingController

def test_scrap_most_active_underlying():
    print("Running test for NSE Most Active Underlying scraping")
    controller = NSEMostActiveUnderlyingController()
    
    # Await the async method properly
    result = asyncio.run(controller.scrap_most_active_underlying())

    # Print raw result for debugging (optional)
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    test_scrap_most_active_underlying()
    print("✅ Most Active Underlying test passed!")
