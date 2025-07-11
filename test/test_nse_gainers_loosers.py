import sys
import os

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.top_gainers_loosers import NSETopGainersloosersController

def test_get_nse_gainers_loosers_data():
    controller = NSETopGainersloosersController()

    # First, ensure data exists
    controller.scrape_top_gainers()
    controller.scrape_top_loosers()

    # Then test gainers
    gainers_data = controller.get_top_gainers_from_db()
    assert gainers_data["success"], f"Gainers error: {gainers_data.get('message')}"
    assert "data" in gainers_data
    assert len(gainers_data["data"]) > 0, "Gainers data is empty"
    # print("data :", gainers_data["data"])

    # Then test loosers
    loosers_data = controller.get_top_loosers_from_db()
    assert loosers_data["success"], f"loosers error: {loosers_data.get('message')}"
    assert "data" in loosers_data
    assert len(loosers_data["data"]) > 0, "loosers data is empty"
    # print("data :", loosers_data["data"])


if __name__ == "__main__":
    print("Running tests for NSE Top Gainers and loosers get data API")
    test_get_nse_gainers_loosers_data()
    print("✅ All tests passed successfully!")
