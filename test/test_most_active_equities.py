import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController

def test_scrape_most_active_equities():
    """
    Test the scraping of Most Active Equities data from NSE.
    """
    controller = NSEMostActiveEquitiesController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_most_active_equities())

    # print("test_scrape_most_active_equities:", result)

if __name__ == "__main__":
    test_scrape_most_active_equities()
    print("Test completed successfully.")
