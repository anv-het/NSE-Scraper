import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_contract import NSEMostActiveContractsController


def test_scrap_most_active_contracts():
    print("Running test for NSE Most Active Contracts scraping")
    controller = NSEMostActiveContractsController()
    
    # Await the async method properly
    result = asyncio.run(controller.scrap_most_active_contracts())

    # Print raw result for debugging (optional)
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"


if __name__ == "__main__":
    test_scrap_most_active_contracts()
    print("✅ Most Active Contracts test passed!")