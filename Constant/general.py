# General application constants

# Application info
APP_NAME = "NSE Scraper"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A Python-based web scraper for extracting data from the National Stock Exchange (NSE)"

# Date formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

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

# NSE cookie rotation URLs
NSE_COOKIE_ROTATION_URLS = [
    "https://www.nseindia.com/all-reports#cr_equity_archives",
    "https://www.nseindia.com/market-data/top-gainers-losers",
    "https://www.nseindia.com/market-data/52-week-high-equity-market",
    "https://www.nseindia.com/option-chain"
]


# Default headers for NSE requests
NSE_GET_COOKIES_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# URLs for various NSE data

HEADERS_URL_GAINER_LOOSER = "https://www.nseindia.com/market-data/top-gainers-losers"
HEADERS_URL_ALL_INDEXES = "https://www.nseindia.com/market-data/live-equity-market"
HEADERS_URL_52_WEEK_HIGH = "https://www.nseindia.com/market-data/52-week-high-equity-market"
HEADERS_URL_52_WEEK_LOW = "https://www.nseindia.com/market-data/52-week-low-equity-market"
HEADERS_URL_UPPER_BAND_HITTERS = "https://www.nseindia.com/market-data/upper-band-hitters"
HEADERS_URL_LOWER_BAND_HITTERS = "https://www.nseindia.com/market-data/lower-band-hitters"
HEADERS_URL_BOTH_BAND_HITTERS = "https://www.nseindia.com/market-data/both-band-hitters"
HEADERS_URL_NEW_LISTINGS = "https://www.nseindia.com/market-data/new-stock-exchange-listings-today"
HEADERS_URL_RECENT_LISTINGS = "https://www.nseindia.com/market-data/new-stock-exchange-listings-recent"
HEADERS_URL_FORTHCOMING_LISTINGS = "https://www.nseindia.com/market-data/new-stock-exchange-listings-forthcoming"
HEADERS_URL_MOST_ACTIVE_EQUITIES = "https://www.nseindia.com/market-data/most-active-equities"
HEADERS_URL_LARGE_DEALS = "https://www.nseindia.com/market-data/large-deals"
HEADERS_URL_ADVANCE = "https://www.nseindia.com/market-data/advance"
HEADERS_URL_DECLINE = "https://www.nseindia.com/market-data/decline"
HEADERS_URL_UNCHANGED = "https://www.nseindia.com/market-data/unchanged"
HEADERS_URL_MOST_ACTIVE_CONTRACTS = "https://www.nseindia.com/market-data/most-active-contracts"
HEADERS_URL_MOST_ACTIVE_UNDERLYING = "https://www.nseindia.com/market-data/most-active-underlying"
HEADERS_URL_EVENT_DATA = "https://www.nseindia.com/get-quotes/equity?symbol={symbol}"

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


# NSE index names (commonly used)
ALL_INDICES_LIST = [
    "NIFTY 50",
    "NIFTY 100",
    "NIFTY NEXT 50",
    "NIFTY BANK",
    "NIFTY FINANCIAL SERVICES",
    "NIFTY IT",
    "NIFTY AUTO",
    "NIFTY PHARMA",
    "NIFTY METAL",
    "NIFTY FMCG",
    "NIFTY REALTY",
    "NIFTY ENERGY",
    "NIFTY PSU BANK",
    "NIFTY MIDCAP 100",
    "NIFTY SMALLCAP 100"
# Commented out others
# "NIFTY INDIA CONSUMPTION",
# "INDIA VIX",
# "NIFTY IPO",
# "NIFTY FINANCIAL SERVICES EX-BANK",
# "NIFTY ALPHA QUALITY LOW-VOLATILITY 30",
# "NIFTY MIDSMALL INDIA CONSUMPTION",
# "NIFTY50 PR 1X INVERSE",
# "NIFTY INDIA CORPORATE GROUP INDEX - TATA GROUP 25% CAP",
# "NIFTY500 MULTICAP INDIA MANUFACTURING 50:30:20",
# "NIFTY50 DIVIDEND POINTS",
# "NIFTY500 MOMENTUM 50",
# "NIFTY QUALITY LOW-VOLATILITY 30",
# "NIFTY SHARIAH 25",
# "NIFTY100 LIQUID 15",
# "NIFTY50 TR 1X INVERSE",
# "NIFTY SMALLCAP250 MOMENTUM QUALITY 100",
# "NIFTY FINANCIAL SERVICES 25/50",
# "NIFTY CAPITAL MARKETS",
# "NIFTY TOP 10 EQUAL WEIGHT",
# "NIFTY SERVICES SECTOR",
# "NIFTY 10 YR BENCHMARK G-SEC (CLEAN PRICE)",
# "NIFTY 11-15 YR G-SEC INDEX",
# "NIFTY50 PR 2X LEVERAGE",
# "NIFTY MIDSMALL IT & TELECOM",
# "NIFTY SMALLCAP 250",
# "NIFTY MIDSMALLCAP400 MOMENTUM QUALITY 100",
# "NIFTY 500",
# "NIFTY MIDCAP LIQUID 15",
# "NIFTY INDIA DIGITAL",
# "NIFTY DIVIDEND OPPORTUNITIES 50",
# "NIFTY MEDIA",
# "NIFTY HEALTHCARE INDEX",
# "NIFTY50 SHARIAH",
# "NIFTY100 ENHANCED ESG",
# "NIFTY ALPHA QUALITY VALUE LOW-VOLATILITY 30",
# "NIFTY PSE",
# "NIFTY500 SHARIAH",
# "NIFTY COMPOSITE G-SEC INDEX",
# "NIFTY COMMODITIES",
# "NIFTY100 LOW VOLATILITY 30",
# "NIFTY 10 YR BENCHMARK G-SEC",
# "NIFTY RURAL",
# "NIFTY PRIVATE BANK",
# "NIFTY100 ESG",
# "NIFTY MICROCAP 250",
# "NIFTY MIDCAP150 QUALITY 50",
# "NIFTY MIDSMALL HEALTHCARE",
# "NIFTY500 VALUE 50",
# "NIFTY500 MULTICAP MOMENTUM QUALITY 50",
# "NIFTY HOUSING",
# "NIFTY SMALLCAP 50",
# "NIFTY CPSE",
# "NIFTY50 EQUAL WEIGHT",
# "NIFTY INDIA MANUFACTURING",
# "NIFTY100 EQUAL WEIGHT",
# "NIFTY200 QUALITY 30",
# "NIFTY200 MOMENTUM 30",
# "NIFTY100 ESG SECTOR LEADERS",
# "NIFTY50 VALUE 20",
# "NIFTY100 QUALITY 30",
# "NIFTY MIDSMALLCAP 400",
# "NIFTY INDIA SELECT 5 CORPORATE GROUPS (MAATR)",
# "NIFTY MIDSMALL FINANCIAL SERVICES",
# "NIFTY ALPHA LOW-VOLATILITY 30",
# "NIFTY CONSUMER DURABLES",
# "NIFTY500 LOW VOLATILITY 50",
# "NIFTY 8-13 YR G-SEC",
# "NIFTY MIDCAP 50",
# "NIFTY BHARAT BOND INDEX - APRIL 2033",
# "NIFTY OIL & GAS",
# "NIFTY200 VALUE 30",
# "NIFTY MNC",
# "NIFTY50 TR 2X LEVERAGE",
# "NIFTY INDIA DEFENCE",
# "NIFTY TOP 15 EQUAL WEIGHT",
# "NIFTY100 ALPHA 30",
# "NIFTY 15 YR AND ABOVE G-SEC INDEX",
# "NIFTY TRANSPORTATION & LOGISTICS",
# "NIFTY500 MULTICAP INFRASTRUCTURE 50:30:20",
# "NIFTY BHARAT BOND INDEX - APRIL 2032",
# "NIFTY HIGH BETA 50",
# "NIFTY 200",
# "NIFTY INDIA TOURISM",
# "NIFTY BHARAT BOND INDEX - APRIL 2031",
# "NIFTY BHARAT BOND INDEX - APRIL 2030",
# "NIFTY INDIA NEW AGE CONSUMPTION",
# "NIFTY MIDCAP150 MOMENTUM 50",
# "NIFTY500 LARGEMIDSMALL EQUAL-CAP WEIGHTED",
# "NIFTY LARGEMIDCAP 250",
# "NIFTY MIDCAP 150",
# "NIFTY BHARAT BOND INDEX - APRIL 2025",
# "NIFTY 4-8 YR G-SEC INDEX",
# "NIFTY NON-CYCLICAL CONSUMER",
# "NIFTY GROWTH SECTORS 15",
# "NIFTY500 QUALITY 50",
# "NIFTY EV & NEW AGE AUTOMOTIVE",
# "NIFTY200 ALPHA 30",
# "NIFTY INFRASTRUCTURE",
# "NIFTY MIDCAP SELECT",
# "NIFTY TOTAL MARKET",
# "NIFTY SMALLCAP250 QUALITY 50",
# "NIFTY MOBILITY",
# "NIFTY500 MULTIFACTOR MQVLV 50",
# "NIFTY500 MULTICAP 50:25:25",
# "NIFTY LOW VOLATILITY 50",
# "NIFTY ALPHA 50",
# "NIFTY CORE HOUSING",
# "NIFTY500 EQUAL WEIGHT",
# "NIFTY TOP 20 EQUAL WEIGHT"
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
    "NSE_ADVANCES_DECLINES": "nse_advances_declines",
    "NSE_LARGE_DEALS": "nse_large_deals",
    "NSE_FORTHCOMING_LISTINGS": "nse_forthcoming_listings",
    "NSE_MOST_ACTIVE_CONTRACTS": "nse_most_active_contracts",
    "NSE_MOST_ACTIVE_EQUITIES": "nse_most_active_equities",
    "NSE_MOST_ACTIVE_UNDERLYING": "nse_most_active_underlying",
    "NSE_NEW_LISTINGS": "nse_new_listings",
    "NSE_WEEK_52_DATA": "nse_week_52_data",
    "NSE_INDICES_DATA": "nse_indices_data",
    "NSE_PRICE_BAND_HITTERS": "nse_price_band_hitters",
    "NSE_STOCKWISE_EVENT": "nse_stockwise_event",
    "NSE_GAINERS_LOSERS": "nse_gainers_losers",
    "NSE_SPECIAL_PREOPEN_LISTINGS": "nse_special_preopen_listings",
    "NSE_RECENT_LISTINGS": "nse_recent_listings",
}

# File paths
LOG_DIRECTORY = "Logs"

# Cache settings
CACHE_DURATION_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE = 1000


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

# Cron job timing configurations (in minutes)
# NOTE: Set to 1 minute for testing - change to production values after testing

CRON_INTERVALS = {
    "ADVANCES_DECLINES_UNCHANGED": 8,  # 1 minute for testing, DEFAULT: 5
    "FORTHCOMING_LISTINGS": 8,         # 1 minute for testing, DEFAULT: 5
    "LARGE_DEALS": 7,                  # 1 minute for testing, DEFAULT: 5
    "MOST_ACTIVE_CONTRACTS": 8,        # 1 minute for testing, DEFAULT: 5
    "MOST_ACTIVE_EQUITIES": 8,         # 1 minute for testing, DEFAULT: 5
    "MOST_ACTIVE_UNDERLYING": 7,       # 1 minute for testing, DEFAULT: 5
    "NEW_LISTINGS": 7,                 # 1 minute for testing, DEFAULT: 5
    "NSE_52_WEEK_HIGH_LOW": 8,         # 1 minute for testing, DEFAULT: 5
    "NSE_ALL_INDEXES": 7,              # 1 minute for testing, DEFAULT: 5
    "PRICE_BAND_HITTERS": 7,           # 1 minute for testing, DEFAULT: 5
    "RECENT_LISTINGS": 8,              # 1 minute for testing, DEFAULT: 5
    "SPECIAL_PREOPEN_LISTINGS": 8,     # 1 minute for testing, DEFAULT: 5
    "TOP_GAINERS_LOOSERS": 7,          # 1 minute for testing, DEFAULT: 5
    "INVESTORGAIN_IPO_DATA": 60,       # 60 minutes for IPO data (less frequent than market data)
    "COOKIE_REFRESH": 4,               # 1 minute for testing, DEFAULT: 60
}



# NSE/BSE Holidays (2025)
# 📌 Note: This list is based on official NSE circulars. 
# Update this every year as exchanges publish the holiday calendar.

MARKET_HOLIDAYS = [
    "2025-01-26",  # Republic Day
    "2025-02-26",  # Mahashivratri
    "2025-03-14",  # Holi
    "2025-04-10",  # Ram Navami
    "2025-04-14",  # Dr. Babasaheb Ambedkar Jayanti
    "2025-04-18",  # Good Friday
    "2025-05-01",  # Maharashtra Day
    "2025-08-15",  # Independence Day
    "2025-08-27",  # Ganesh Chaturthi
    "2025-10-02",  # Gandhi Jayanti
    "2025-10-20",  # Diwali (Laxmi Pujan) *Muhurat Trading may be allowed
    "2025-10-21",  # Diwali Balipratipada
    "2025-11-05",  # Gurunanak Jayanti
    "2025-12-25",  # Christmas
]


