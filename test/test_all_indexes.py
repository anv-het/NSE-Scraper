import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.nse_all_indexes import NSEAllIndexesController

def test_scrape_all_indices_from_list():
    """
    Test the scraping of All Indexes data from NSE.
    """
    controller = NSEAllIndexesController()
    
    # Use asyncio.run to await the async method
    result = controller.scrape_all_indices_from_list()

    # print("test_scrape_all_indices_from_list:", result)

if __name__ == "__main__":
    test_scrape_all_indices_from_list()
    print("Test completed successfully.")
