import sys
import os

# Absolute path to the root of the project (NSE-Scraper)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Add the root directory to sys.path to locate the 'API' folder
sys.path.append(project_root)

# Now, import the controller
from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController
import requests
import unittest

class TestNSEPriceBandHittersController(unittest.TestCase):

    def test_scrap_price_band_hitters(self):
        """
        Test the `scrap_price_band_hitters` method from the NSEPriceBandHittersController
        to ensure it is fetching data from NSE correctly.
        """
        # Initialize the controller instance
        controller = NSEPriceBandHittersController()

        # Call the scrap_price_band_hitters method to fetch data
        result = controller.scrap_price_band_hitters()

        # Check that the result is successful and data is not empty
        self.assertTrue(result["success"], f"Failed with message: {result['message']}")
        self.assertIsNotNone(result["data"], "No data returned.")

        # Print the result data for inspection
        print("Fetched data:", result)

    def test_get_cookies(self):
        """
        Test if the cookies are being fetched correctly.
        """
        controller = NSEPriceBandHittersController()

        cookies = controller.get_cookies()
        self.assertIsNotNone(cookies, "Failed to fetch cookies.")
        print("Cookies:", cookies)


if __name__ == '__main__':
    unittest.main()
