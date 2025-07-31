import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.stockwise_event_data import StockwiseEventDataController


def test_scrape_stockwise_event_data():
    controller = StockwiseEventDataController()
    # print("Running test for stockwise event data scraping")

    # Example symbol to test
    symbol = "ITC"
    
    # Call the method to scrape stockwise event data
    result = controller.scrape_stockwise_event_data(symbol)

    # # print the result for debugging
    # # print("Result:", result)
if __name__ == "__main__":
    test_scrape_stockwise_event_data()
    # print("✅ Stockwise event data scraping test passed!")