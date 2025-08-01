import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.nse_52week_high_low import NSE52WeekHighLowController

def test_scrape_52_week_high_low():
    """
    Test the scraping of 52-week high and low data from NSE.
    """
    controller = NSE52WeekHighLowController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_52_week_high_low())

    # print("test_scrape_52_week_high_low:", result)

if __name__ == "__main__":
    test_scrape_52_week_high_low()
    print("Test completed successfully.")