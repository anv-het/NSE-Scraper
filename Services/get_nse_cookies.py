import os
import json
import time
from datetime import datetime
from typing import Dict, Optional

import requests
import undetected_chromedriver as uc
from Utils.logger import get_logger
from Utils.config_reader import configure
from Constant.general import NSE_GET_COOKIES_HEADERS, REQUIRED_NSE_COOKIES

# Prevent destructor re-quit errors on Windows
uc.Chrome.__del__ = lambda self: None

logger = get_logger(__name__)

class NSECookieService:
    def __init__(self):
        self.cookies_url = configure.get('NSE', 'NSE_GET_COOKIES_URL')
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.cookies_file = configure.get('NSE', 'COOKIES_FILE')
        self.session = requests.Session()

    def get_driver(self):
        logger.info("Launching undetected Chrome...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--headless=new")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        return uc.Chrome(options=options, use_subprocess=True)

    def get_nse_cookies(self) -> Optional[Dict[str, str]]:
        try:
            logger.info("Getting fresh NSE cookies...")
            driver = self.get_driver()
            driver.get(self.cookies_url)
            time.sleep(10)  # Allow cookies to be set
            cookies = driver.get_cookies()
            driver.quit()

            if not cookies:
                logger.warning("No cookies received")
                return None

            filtered = {c['name']: c['value'] for c in cookies if c['name'] in REQUIRED_NSE_COOKIES}
            missing = [name for name in REQUIRED_NSE_COOKIES if name not in filtered]
            if missing:
                logger.warning(f"Missing cookies: {missing}")
            else:
                logger.info("All required cookies collected")

            self._save_cookies_to_file(filtered)
            return filtered
        except Exception as e:
            logger.error(f"Error in get_nse_cookies: {e}")
            return None

    def _save_cookies_to_file(self, cookies: Dict[str, str]):
        try:
            data = {
                "cookies": cookies,
                "timestamp": datetime.now().isoformat(),
                "expiry": time.time() + 3600  # 1-hour expiry
            }
            with open(self.cookies_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cookies saved to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def load_cookies_from_file(self) -> Optional[Dict[str, str]]:
        if not os.path.exists(self.cookies_file):
            logger.info("Cookie file not found")
            return None
        try:
            with open(self.cookies_file, "r") as f:
                data = json.load(f)
            if time.time() > data.get("expiry", 0):
                logger.info("Stored cookies expired")
                return None
            cookies = data.get("cookies")
            if cookies:
                logger.info("Loaded cookies from file")
                return cookies
            return None
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return None

    def validate_cookies(self, cookies: Dict[str, str]) -> bool:
        try:
            test_url = f"{self.base_url}/api/allIndices"
            resp = self.session.get(test_url, headers=NSE_GET_COOKIES_HEADERS, cookies=cookies, timeout=10)
            if resp.status_code == 200:
                logger.info("Cookies validation successful")
                return True
            logger.warning(f"Cookie validation failed: status {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error validating cookies: {e}")
            return False

    def refresh_cookies(self) -> Optional[Dict[str, str]]:
        logger.info("Refreshing cookies...")
        return self.get_nse_cookies()

cookie_service = NSECookieService()

def get_nse_cookies() -> Optional[Dict[str, str]]:
    cookies = cookie_service.load_cookies_from_file()
    if cookies and cookie_service.validate_cookies(cookies):
        return cookies
    logger.info("Fetching fresh cookies")
    cookies = cookie_service.refresh_cookies()
    if cookies and cookie_service.validate_cookies(cookies):
        return cookies
    logger.error("Unable to obtain valid cookies")
    return None

def refresh_nse_cookies() -> Optional[Dict[str, str]]:
    return cookie_service.refresh_cookies()

if __name__ == "__main__":
    logger.info("Running NSECookieService tests")
    cookies = get_nse_cookies()
    print("Final cookies:", cookies)
    print("Validation result:", cookie_service.validate_cookies(cookies or {}))
