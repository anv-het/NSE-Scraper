"""
NSE Stocks Wise Market Event Controller
Handles scraping and data management for stocks wise market events
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.response import create_success_response, create_error_response
from Utils.utilities_functions import clean_numeric_value
from Utils.config_reader import configure
from Utils.cookie_headers import load_nse_headers

from Constant.http import HTTP_STATUS
from Constant.general import (
    HEADERS_URL_STOCKS_WISE_MARKET_EVENT
)
from Services.get_nse_cookies import get_nse_cookies
