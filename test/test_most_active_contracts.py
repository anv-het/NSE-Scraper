import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.most_active_contract import NSEMostActiveContractsController

def test_scrap_most_active_contracts():
    """
    Test the scraping of Most Active Contracts data from NSE.
    """
    controller = NSEMostActiveContractsController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_most_active_contracts())

    # print("test_scrap_most_active_contracts:", result)

if __name__ == "__main__":
    test_scrap_most_active_contracts()
    print("Test completed successfully.")