import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.top_gainers_loosers import NSETopGainersloosersController

def test_top_gainer_loosers():
    """
    Test the scraping of Top Gainers and Losers data from NSE.
    """
    controller = NSETopGainersloosersController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.top_gainer_loosers())

    # print("test_top_gainer_loosers:", result)

if __name__ == "__main__":
    test_top_gainer_loosers()
    print("Test completed successfully.")
