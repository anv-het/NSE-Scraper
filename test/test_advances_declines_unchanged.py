import sys
import os
import asyncio  # Import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController

def test_scrap_advance_decline_unchanged():
    """
    Test the scraping of Advance, Decline, and Unchanged data from NSE.
    """
    controller = NSEAdvancesDeclinesUnchangedController()
    
    # Use asyncio.run to await the async method
    result = asyncio.run(controller.scrap_advance_decline_unchanged())

    # print("test_scrap_advance_decline_unchanged:", result)

if __name__ == "__main__":
    test_scrap_advance_decline_unchanged()
    print("Test completed successfully.")
