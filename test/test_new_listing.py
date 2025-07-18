import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.new_listing_stoks import NSEPriceBandHittersController

def test_scrap_new_listings():
    print("Running test for NSE New Listings scraping")
    controller = NSEPriceBandHittersController()
    result = controller.scrap_new_listings()

def test_scrap_special_preopen_listings():
    print("Running test for NSE Special Pre-Open Listings scraping")
    controller = NSEPriceBandHittersController()
    result = controller.scrap_special_preopen_listings()


def test_scrap_recent_listings():
    print("Running test for NSE Recent Listings scraping")
    controller = NSEPriceBandHittersController()
    result = controller.scrap_recent_listings()

    # Print raw result for debugging
    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"

if __name__ == "__main__":
    test_scrap_new_listings()
    test_scrap_special_preopen_listings()
    test_scrap_recent_listings()
    print("✅ Special Pre-Open Listings test passed!")
    print("✅ New Listings test passed!")