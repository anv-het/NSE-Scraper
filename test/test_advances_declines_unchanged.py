import sys
import os
import asyncio

# Ensure the correct import path for your modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController

def test_scrap_advance_decline_unchanged():
    print("Running test for NSE Advances, Declines, and Unchanged scraping")
    controller = NSEAdvancesDeclinesUnchangedController()
    
    # ❌ Don't use asyncio.run — the method is not async
    result = controller.scrap_advance_decline_unchanged()

    # Debug print
    print("Result:", result)

    # ✅ Assertions
    assert isinstance(result, dict), "Response is not a dictionary"
    assert "success" in result, "Missing 'success' key"

    if result["success"]:
        assert "Advances" in result["data"], "Missing 'Advances' key"
        assert "Declines" in result["data"], "Missing 'Declines' key"
        assert "Unchange" in result["data"], "Missing 'Unchange' key"



if __name__ == "__main__":
    test_scrap_advance_decline_unchanged()
    print("✅ Advances, Declines, and Unchanged test passed!")
