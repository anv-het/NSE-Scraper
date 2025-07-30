import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.large_deal import NSELargeDealsController

def test_scrape_large_deals():
    print("🔍 Running test for NSE Large Deals scraping")
    
    controller = NSELargeDealsController()
    result = controller.scrap_large_deals()

    # ✅ Base validations
    assert isinstance(result, dict), "❌ Response is not a dictionary"
    assert "success" in result, "❌ Missing 'success' key in response"
    
    if result["success"]:
        assert "data" in result, "❌ 'data' key not found in successful response"
        assert isinstance(result["data"], list), "❌ 'data' should be a list"
        
        if len(result["data"]) > 0:
            record = result["data"][0]
            # ✅ Check keys in first record
            expected_keys = [
                "types", "date", "symbol", "name", "client_name",
                "buy_sell", "quantity", "watp", "remarks", "timestamp"
            ]
            for key in expected_keys:
                assert key in record, f"❌ Missing key: {key} in data record"

    print("✅ Large Deals test passed!")

if __name__ == "__main__":
    test_scrape_large_deals()
