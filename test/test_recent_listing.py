import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.recent_listing import NSERecentListingsController

def test_scrap_recent_listings():
    print("Running test for NSE Recent Listings scraping")
    controller = NSERecentListingsController()

    result = asyncio.run(controller.scrap_recent_listings())
    # print("Recent Listings Result:", result)

if __name__ == "__main__":
    test_scrap_recent_listings()
    print("All tests completed successfully.")