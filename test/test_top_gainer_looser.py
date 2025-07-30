import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from API.Controller.top_gainers_loosers import NSETopGainersloosersController

def test_top_gainers_loosers():
    controller = NSETopGainersloosersController()
    print("Running test for top gainers and loosers data scraping")

    # Call the method to get top gainers and loosers data
    result = asyncio.run(controller.top_gainer_loosers())

    # Print the result for debugging
    # print("Result:", result)

if __name__ == "__main__":
    test_top_gainers_loosers()
    print("✅ Top gainers and loosers data scraping test passed!")

