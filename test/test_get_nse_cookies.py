import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Services.get_nse_cookies import NSECookieService

def test_get_nse_cookies():
    cookie_service = NSECookieService()
    
    # No asyncio, just call the method directly
    result = cookie_service.get_nse_cookies()

    # print("Result:", result)


if __name__ == "__main__":
    test_get_nse_cookies()
