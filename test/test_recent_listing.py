import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.recent_listing import NSERecentListingsController

def test_scrap_recent_listings():
    """
    Test the scraping of Recent Listings data from NSE.
    """
    controller = NSERecentListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_recent_listings())

    # print("test_scrap_recent_listings:", result)

if __name__ == "__main__":
    test_scrap_recent_listings()
    print("Test completed successfully.")