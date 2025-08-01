import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.stockwise_event_data import StockwiseEventDataController

def test_scrape_stockwise_event_data():
    """
    Test the scraping of Stockwise Event data from NSE.
    """
    controller = StockwiseEventDataController()
    
    # Example symbol to test
    symbol = "ITC"
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrape_stockwise_event_data(symbol))

    # print("test_scrape_stockwise_event_data:", result)

if __name__ == "__main__":
    test_scrape_stockwise_event_data()
    print("Test completed successfully.")