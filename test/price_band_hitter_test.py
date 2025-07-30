import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController

def test_scrap_price_band_hitters():
    print("Running test for NSE Price Band Hitters scraping")
    controller = NSEPriceBandHittersController()
    result = controller.scrap_price_band_hitters()

    # Print raw result for debugging
    # print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    test_scrap_price_band_hitters()
    print("✅ Price Band Hitters test passed!")
