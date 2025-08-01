import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.new_listing_stoks import NSENewListingsController

def test_scrap_new_listing():
    """
    Test the scraping of New Listing data from NSE.
    """
    controller = NSENewListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_new_listing())

    # print("test_scrap_new_listing:", result)

if __name__ == "__main__":
    test_scrap_new_listing()
    print("Test completed successfully.")