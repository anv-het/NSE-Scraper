import sys
import os

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController

def test_scrap_advance_decline_unchanged():
    # print("Running test for NSE Advances, Declines, and Unchanged scraping")
    controller = NSEAdvancesDeclinesUnchangedController()

    result = controller.scrap_advance_decline_unchanged()

    # Debug # print
    # # print("Result:", result)



if __name__ == "__main__":
    test_scrap_advance_decline_unchanged()
    # print("✅ Advances, Declines, and Unchanged test passed!")
