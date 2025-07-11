# General application constants

# Application information
APP_NAME = "NSE Scraper"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A comprehensive NSE market data scraper and API"

# Market timings (IST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30

# Market days (Monday = 0, Sunday = 6)
MARKET_DAYS = [0, 1, 2, 3, 4]  # Monday to Friday

# Data refresh intervals (in minutes)
REAL_TIME_REFRESH_INTERVAL = 1
STANDARD_REFRESH_INTERVAL = 5
SLOW_REFRESH_INTERVAL = 15

# NSE API endpoints
NSE_BASE_URL = "https://www.nseindia.com"

# Default headers for NSE requests
NSE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


# Get NSE cookies Headers
NSE_GET_COOKIES_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    "Referer": "https://www.nseindia.com/all-reports#cr_equity_archives",
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# NSE API paths
NSE_API_PATHS = {
    "gainers_loosers": "/api/live-analysis-variations",
    "equity_master": "/api/equity-master",
    "equity_indices": "/api/equity-stockIndices",
    "most_active_securities": "/api/live-analysis-most-active-securities",
    "price_band_hitter": "/api/live-analysis-price-band-hitter",
    "52week_high": "/api/live-analysis-data-52weekhighstock",
    "52week_low": "/api/live-analysis-data-52weeklowstock",
    "bulk_deals": "/api/snapshot-capital-market-largedeal",
    "advance_decline": "/api/live-analysis-advance",
    "equity_derivatives": "/api/liveEquity-derivatives",
    "derivatives_equity": "/api/snapshot-derivatives-equity",
    "most_active_underlying": "/api/live-analysis-most-active-underlying",
    "oi_spurts": "/api/live-analysis-oi-spurts-underlyings",
    "special_preopen": "/api/special-preopen-listing",
    "new_listing": "/api/new-listing-today-ipo"
}

# NSE data types
NSE_DATA_TYPES = {
    "GAINERS": "gainers",
    "looserS": "loosers",  # Note: NSE API uses "loosers" spelling
    "VOLUME": "volume",
    "VALUE": "value",
    "CONTRACTS": "contracts",
    "TOP20_CONTRACTS": "top20_contracts"
}

# NSE index names (commonly used)
NSE_INDICES = [
    "NIFTY 50",
    "NIFTY BANK", 
    "NIFTY NEXT 50",
    "NIFTY FINANCIAL SERVICES",
    "NIFTY MIDCAP SELECT",
    "NIFTY MIDCAP 50",
    "NIFTY MIDCAP 100",
    "NIFTY SMALLCAP 50",
    "NIFTY SMALLCAP 100",
    "NIFTY 100",
    "NIFTY 200",
    "NIFTY 500",
    "NIFTY AUTO",
    "NIFTY ENERGY",
    "NIFTY FMCG",
    "NIFTY IT",
    "NIFTY MEDIA",
    "NIFTY METAL",
    "NIFTY PHARMA",
    "NIFTY PSU BANK",
    "NIFTY REALTY",
    "NIFTY PRIVATE BANK",
    "NIFTY HEALTHCARE INDEX",
    "NIFTY CONSUMER DURABLES",
    "NIFTY OIL & GAS"
]

# Required NSE cookies
REQUIRED_NSE_COOKIES = [
    "_ga", 
    "AKA_A2", 
    "_abck", 
    "ak_bmsc", 
    "nsit", 
    "nseappid",
    "_ga_87M7PJ3R97", 
    "bm_sz", 
    "bm_sv", 
    "RT"
]

# Database collection/table names
DB_COLLECTIONS = {
    "GAINERS_looserS": "gainers_loosers",
    "INDICES": "indices",
    "MOST_ACTIVE": "most_active",
    "52_WEEK_HIGH_LOW": "52week_high_low",
    "DERIVATIVES": "derivatives",
    "BULK_DEALS": "bulk_deals",
    "PRICE_BAND": "price_band",
    "ADVANCE_DECLINE": "advance_decline",
    "OI_SPURTS": "oi_spurts",
    "NEW_LISTINGS": "new_listings"
}

# File paths
LOG_DIRECTORY = "Logs"
COOKIES_FILE = "nse_cookies.json"

# Pagination limits
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Cache settings
CACHE_DURATION_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE = 1000

# User roles and permissions
USER_ROLES = {
    "ADMIN": "admin",
    "PREMIUM": "premium",
    "STANDARD": "standard",
    "BASIC": "basic"
}

PERMISSIONS = {
    "READ_ALL": "read_all",
    "READ_BASIC": "read_basic",
    "WRITE_DATA": "write_data",
    "ADMIN_ACCESS": "admin_access",
    "PREMIUM_ACCESS": "premium_access",
    "STANDARD_ACCESS": "standard_access"
}

# Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Data validation constants
MIN_PRICE = 0.01
MAX_PRICE = 999999.99
MIN_VOLUME = 0
MAX_VOLUME = 999999999999

# Error messages
ERROR_MESSAGES = {
    "INVALID_TOKEN": "Invalid or expired authentication token",
    "INSUFFICIENT_PERMISSIONS": "Insufficient permissions to access this resource",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please try again later",
    "INVALID_PARAMETERS": "Invalid request parameters",
    "DATA_NOT_FOUND": "Requested data not found",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
    "INVALID_INDEX": "Invalid index name provided",
    "COOKIE_REFRESH_REQUIRED": "NSE cookies need to be refreshed"
}



# Database types
DB_SQLITE = "sqlite"
DB_MONGODB = "mongodb"
