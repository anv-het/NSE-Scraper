import sys
import os
import asyncio
from unittest import result

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController

def test_scrap_advances_declines_unchanged():
    print("Running test for NSE Advances, Declines, and Unchanged scraping")
    controller = NSEAdvancesDeclinesUnchangedController()

    # Correct: call the sync method directly
    result = controller.scrap_advance_decline_unchanged()

    print("Result:", result)

    assert isinstance(result, dict), "Response is not a dictionary"
    assert result.get("success") is True or result.get("success") is False, "Missing 'success' key"
    assert "advance" in result.get("data", {}), "Missing 'advance' data"
    assert "decline" in result.get("data", {}), "Missing 'decline' data"
    assert "unchanged" in result.get("data", {}), "Missing 'unchanged' data"


if __name__ == "__main__":
    test_scrap_advances_declines_unchanged()
    print("✅ Advances, Declines, and Unchanged test passed!")