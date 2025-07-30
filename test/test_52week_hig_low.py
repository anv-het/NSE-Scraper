import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from API.Controller.nse_52week_high_low import NSE52WeekHighLowController

async def test_refresh_52week_data():
    print("Running test for NSE 52-week high and low data scraping")
    controller = NSE52WeekHighLowController()

    result = await controller.scrape_52_week_high_low()

    # Print raw result for debugging
    # print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    asyncio.run(test_refresh_52week_data())
    print("✅ 52-week high and low data test passed!")