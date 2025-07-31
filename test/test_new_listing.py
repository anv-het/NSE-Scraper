import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.new_listing_stoks import NSENewListingsController

def test_scrap_new_listings_recent_and_preopen():
    # print("Running test for NSE New Listings, Special Pre-Open Listings, and Recent Listings scraping")
    controller = NSENewListingsController()

    result = asyncio.run(controller.scrap_new_listing())
    # # print("New Listings Result:", result)

if __name__ == "__main__":
    test_scrap_new_listings_recent_and_preopen()
    # print("All tests completed successfully.")