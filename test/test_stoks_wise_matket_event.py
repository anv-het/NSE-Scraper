import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.stockwise_event_data import StockwiseEventDataController


def test_scrap_stockwise_event_data(symbol: str = "ITC"):
    print("Running test for Stockwise Event Data scraping")
    controller = StockwiseEventDataController()
    result = controller.get_event_data(symbol)

    print("Result:", result)

    if result is None:
        print("❌ Test failed: No result returned (likely due to ChromeDriver/Chrome version mismatch or cookie error).")
        assert False, "No result returned from get_event_data (check ChromeDriver, cookies, or API availability)."
        return

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"


if __name__ == "__main__": 
    test_scrap_stockwise_event_data(symbol="ITC")
    print("✅ Stockwise Event Data test passed!")