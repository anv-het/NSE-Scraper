import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.scanx_scrap_stocks_data_by_symbol import main  # Import the main function

def test_scrape_single_symbol(symbol):
    """
    Test the scraping of stock data by symbol.
    """
    # Use asyncio.run to await the async main function
    result = main(symbol)  # If main is async, we need to run it using asyncio.run

    # Optionally print the result or add assertions
    # print("test_scrape_single_symbol:", result)

if __name__ == "__main__":
    test_scrape_single_symbol(symbol='rvNl') 
    print("Test completed successfully.")
