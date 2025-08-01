import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.forth_comming_listing import NSEForthcomingListingsController

def test_scrap_forthcoming_listings():
    """
    Test the scraping of Forthcoming Listings data from NSE.
    """
    controller = NSEForthcomingListingsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_forthcoming_listings())

    # print("test_scrap_forthcoming_listings:", result)

if __name__ == "__main__":
    test_scrap_forthcoming_listings()
    print("Test completed successfully.")
