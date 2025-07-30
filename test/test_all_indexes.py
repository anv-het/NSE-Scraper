import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.nse_all_indexes import NSEAllIndexesController

def test_scrap_all_indexes():
    print("Running test for NSE All Indexes scraping")
    controller = NSEAllIndexesController()
    
    result = controller.scrape_all_indices_from_list()  # ✅ No asyncio.run

    assert isinstance(result, dict), "Response is not a dictionary"
    assert "success" in result, "Missing 'success' key"

    # print("Result:", result)

if __name__ == "__main__":
    test_scrap_all_indexes()
    print("✅ All Indexes test passed!")
