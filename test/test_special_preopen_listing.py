import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.special_preopen_listing import NSESpecialPreopenListingsController

def test_scrap_special_preopen_listings():
    print("Running test for NSE Special Pre-Open Listings scraping")
    controller = NSESpecialPreopenListingsController()

    result = asyncio.run(controller.scrap_special_preopen_listings())
    # print("Special Pre-Open Listings Result:", result)

if __name__ == "__main__":
    test_scrap_special_preopen_listings()
    print("All tests completed successfully.")
