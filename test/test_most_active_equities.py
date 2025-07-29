import sys
import os
import asyncio  # ✅ Required to run async functions

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController

def test_scrape_most_active_equities():
    print("Running test for NSE Most Active Equities scraping")
    controller = NSEMostActiveEquitiesController()

    # ✅ Proper way to run an async method in a sync context
    result = asyncio.run(controller.scrape_most_active_equities())

    # Debug print
    print("Result:", result)

    # ✅ Optional assertions
    assert isinstance(result, dict), "Result is not a dictionary"
    assert "success" in result, "Missing 'success' key"
    assert isinstance(result["success"], bool), "'success' must be a boolean"
    print("✅ Most Active Equities test passed!")


if __name__ == "__main__":
    test_scrape_most_active_equities()
