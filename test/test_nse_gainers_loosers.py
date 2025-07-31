import sys
import os
import asyncio  # Import asyncio

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.top_gainers_loosers import NSETopGainersloosersController

def test_nse_top_gainers_loosers():
    """
    Test the NSE Top Gainers and Losers API endpoint.
    """
    controller = NSETopGainersloosersController()
    
    # Use asyncio.run to await the async method
    response = asyncio.run(controller.top_gainer_loosers())

    # # print("response:", response)
    
if __name__ == "__main__":
    test_nse_top_gainers_loosers()
    # print("All tests passed for NSE Top Gainers and Losers API.")
