import sys
import os

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.scrap_investorgain_ipo_data import NSEInvestorGainIPOController

def test_scrap_investorgain_ipo_data():
    """
    Test the scraping of InvestorGain IPO data.
    """
    controller = NSEInvestorGainIPOController()
    
    # Call the scraping method
    result = controller.scrape_investorgain_ipo_data()

    # print("test_scrap_investorgain_ipo_data:", result)

if __name__ == "__main__":
    test_scrap_investorgain_ipo_data()
    print("Test completed successfully.")
