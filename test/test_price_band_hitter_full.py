import sys
import os


# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now, import the controller
from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController



def test_get_price_band_hitter_full():
    # Create an instance of the controller
    controller = NSEPriceBandHittersController()
    print("Running test for NSE Price Band Hitter Full data scraping")

    # Call the method to get the price band hitter full data
    result = controller.scrap_price_band_hitters()

    # Print the result for debugging
    # print("Result:", result)

if __name__ == "__main__":
    test_get_price_band_hitter_full()
    print("✅ NSE Price Band Hitter Full data scraping test passed!")


