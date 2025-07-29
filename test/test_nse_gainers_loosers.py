import sys
import os

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.top_gainers_loosers import NSETopGainersloosersController

def test_get_nse_gainers_loosers_data():
    controller = NSETopGainersloosersController()
    
    # Test scraping top gainers
    gainers_data = controller.scrape_top_gainers()
    
    
    # Test scraping top loosers
    loosers_data = controller.scrape_top_loosers()


if __name__ == "__main__":
    test_get_nse_gainers_loosers_data()
    print("✅ NSE Gainers and Loosers test passed!")