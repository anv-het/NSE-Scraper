import sys
import os
import asyncio  # Import asyncio


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.large_deal import NSELargeDealsController

def test_scrape_large_deals():
    controller = NSELargeDealsController()


    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_large_deals())


if __name__ == "__main__":
    test_scrape_large_deals()
    print("Test completed successfully.")