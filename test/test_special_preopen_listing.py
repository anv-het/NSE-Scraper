import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.special_preopen_listing import NSESpecialPreopenListingsController

def test_scrap_special_preopen_listings():
    """
    Test the scraping of Special Pre-Open Listings data from NSE.
    """
    controller = NSESpecialPreopenListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_special_preopen_listings())

    # print("test_scrap_special_preopen_listings:", result)

if __name__ == "__main__":
    test_scrap_special_preopen_listings()
    print("Test completed successfully.")
