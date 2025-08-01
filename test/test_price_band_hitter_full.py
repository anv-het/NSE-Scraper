import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController

def test_scrap_price_band_hitters():
    """
    Test the scraping of Price Band Hitters data from NSE.
    """
    controller = NSEPriceBandHittersController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_price_band_hitters())

    # print("test_scrap_price_band_hitters:", result)

if __name__ == "__main__":
    test_scrap_price_band_hitters()
    print("Test completed successfully.")
    # print("✅ NSE Price Band Hitter Full data scraping test passed!")


