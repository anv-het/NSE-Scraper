"""
IPO Data Utilities
==================
Utility functions for InvestorGain IPO data scraping and processing.
Contains helper functions for text cleaning, data conversion, date parsing, and scraping utilities.
"""

import re
import time
import random
import requests
import json
import zlib
import brotli
import pytz 
import traceback
import os
import re
import logging

from contextlib import closing
from thefuzz import fuzz
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tenacity import retry, wait_random_exponential, stop_after_attempt
from Utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# ===== CONFIGURATION CONSTANTS =====
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

COMMON_PARAMS = {
    "timeout": 15,
    "max_retries": 3,
    "delay_range": (0.5, 1.5)
}

# Updated API endpoints
IPO_LIST_API = "https://webnodejs.investorgain.com/cloud/ipo/list-read"
IPO_LIST_API_V2 = "https://webnodejs.investorgain.com/cloud/report/data-read/331/1/{month}/{year}/{fin_year}/0/all"
IPO_GMP_API = "https://webnodejs.investorgain.com/cloud/ipo/ipo-gmp-read"
IPO_SUBSCRIPTION_API = "https://webnodejs.investorgain.com/cloud/ipo/subscription-read"
BASE_URL = "https://www.investorgain.com"

# Directory configurations
LOGO_DOWNLOAD_DIR = "downloads/ipo/logos"
OUTPUT_DIR = "output"

# Constants for matching logic Symbol
MATCH_THRESHOLD = 65  # Increased for better accuracy
DATE_TOLERANCE_DAYS = 2  # More flexible date matching
PRICE_TOLERANCE = 5  # More flexible price matching
MIN_VALIDATION_MATCHES = 2  # Reduced for better matching while maintaining quality


# ===== TEXT CLEANING UTILITIES =====
def clean_text(text: str) -> str:
    """
    Standard text cleaning function used across all modules.
    Removes extra spaces, newlines, and non-breaking spaces.
    """
    if text:
        text = str(text).replace('\xa0', ' ').replace('\n', ' ').strip()
        text = re.sub(r'\s+', ' ', text)
    return text

def clean_html_entities(text: str) -> str:
    """
    Cleans HTML entities from text, specifically handles &#8377; (₹ symbol).
    """
    if not text:
        return text
    
    # Replace common HTML entities
    cleaned_text = str(text).replace('&#8377;', '').strip()
    return cleaned_text

def clean_html_content(html_content: str) -> str:
    """
    Removes HTML tags and entities from content.
    Used for cleaning gmp_comments, gmp_compare_desc, and gmp_percent_calc.
    """
    if not html_content or html_content == 'N/A':
        return html_content
    
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    # Extract text content only
    clean_content = soup.get_text()
    # Clean extra spaces and entities
    clean_content = clean_text(clean_content)
    # Remove ₹ symbol that appears as &#8377;
    clean_content = clean_content.replace('₹', '')
    return clean_content

# ===== DATA CONVERSION UTILITIES =====
def convert_to_float(value: Any) -> Optional[float]:
    """
    Converts a cleaned string to a float, handling Indian currency symbols.
    Returns None if conversion fails.
    """
    try:
        if value is None or not str(value).strip():
            return None
        # Remove common symbols and clean
        cleaned = str(value).replace('₹', '').replace(',', '').replace('%', '').replace('x', '').strip()
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None

def convert_to_int(value: Any) -> Optional[int]:
    """
    Converts a cleaned string to an integer via float first.
    Returns None if conversion fails.
    """
    try:
        float_val = convert_to_float(value)
        return int(float_val) if float_val is not None else None
    except (ValueError, TypeError):
        return None

def extract_percentage_value(gmp_percent_calc: str) -> str:
    """
    Extracts just the percentage number from gmp_percent_calc field.
    Example: '<span class="text-success fw-bold">25.33%</span>' -> '25.33'
    """
    if not gmp_percent_calc or gmp_percent_calc == 'N/A':
        return 'N/A'
    
    # First clean HTML tags
    clean_content = clean_html_content(gmp_percent_calc)
    
    # Extract percentage value using regex
    percent_match = re.search(r'([\d.]+)%', clean_content)
    if percent_match:
        return percent_match.group(1)
    
    return 'N/A'

# ===== DATE PARSING UTILITIES =====
def format_ipo_status(status_code: str) -> str:
    """
    Converts IPO status code to human-readable format.
    U = Upcoming, C = Closed, CT = Closed Today, LT = List Today, L = Listed, O = Currently Open, P = Pending
    """
    status_mapping = {
        'U': 'Upcoming',
        'C': 'Closed', 
        'CT': 'Closed Today',
        'LT': 'List Today',
        'L': 'Listed',
        'O': 'Open',
        'P': 'Pending'
    }
    
    return status_mapping.get(status_code, status_code)

def parse_date_status(date_string: str) -> tuple:
    """
    Parses date string and determines if it's past, present, or future.
    Returns tuple: (parsed_date, status, original_string)
    """
    if not date_string or date_string == 'N/A':
        return None, 'Unknown', date_string
    
    # Remove ordinal suffixes (st, nd, rd, th) before parsing
    cleaned_date_string = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_string, flags=re.IGNORECASE)

    date_formats_to_try = [
        '%d %b %Y', '%d %B %Y', '%d/%m/%Y', '%d-%m-%Y',
        '%B %d, %Y', '%b %d, %Y'
    ]
    
    current_date = datetime.now()
    
    for fmt in date_formats_to_try:
        try:
            parsed_date = datetime.strptime(cleaned_date_string, fmt)
            if parsed_date.date() < current_date.date():
                status = 'Past'
            elif parsed_date.date() == current_date.date():
                status = 'Today'
            else:
                status = 'Future'
            return parsed_date, status, date_string
        except ValueError:
            continue
    
    return None, 'Unknown', date_string

# ===== HTTP REQUEST UTILITIES =====
@retry(wait=wait_random_exponential(multiplier=0.5, min=1, max=4), 
       stop=stop_after_attempt(3), reraise=True)
def make_robust_request(url: str, custom_headers: Optional[Dict] = None) -> requests.Response:
    """
    Makes a robust HTTP request with retry logic and error handling.
    """
    request_headers = COMMON_HEADERS.copy()
    if custom_headers:
        request_headers.update(custom_headers)

    # Random delay to avoid overwhelming the server
    time.sleep(random.uniform(*COMMON_PARAMS["delay_range"]))

    try:
        response = requests.get(url, headers=request_headers, timeout=COMMON_PARAMS["timeout"])
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        raise

def handle_compressed_response(response: requests.Response) -> Dict[str, Any]:
    """
    Handles compressed API responses (gzip, br, deflate).
    Returns parsed JSON data.
    """
    try:
        return response.json()
    except json.JSONDecodeError:
        # Handle compression manually if needed
        content_encoding = response.headers.get('Content-Encoding')
        if content_encoding == 'gzip':
            try:
                decompressed_content = zlib.decompress(response.content, 16 + zlib.MAX_WBITS).decode('utf-8')
                return json.loads(decompressed_content)
            except Exception:
                return None
        elif content_encoding == 'br':
            try:
                decompressed_content = brotli.decompress(response.content).decode('utf-8')
                return json.loads(decompressed_content)
            except Exception:
                return None
        elif content_encoding == 'deflate':
            try:
                decompressed_content = zlib.decompress(response.content, -zlib.MAX_WBITS).decode('utf-8')
                return json.loads(decompressed_content)
            except Exception:
                return None
        else:
            return None

# ===== API DATA FETCHING UTILITIES =====
def fetch_ipo_list_from_api() -> List[Dict[str, Any]]:
    """
    Fetches the complete list of IPOs from the InvestorGain API.
    Returns list of IPO entries with basic information.
    """
    logger.info(f"Fetching IPO list from API: {IPO_LIST_API}")
    
    try:
        response = make_robust_request(IPO_LIST_API)
        data = response.json()
        
        if data.get("msg") == 1 and "ipoList" in data:
            ipo_list = data["ipoList"]
            logger.info(f"Successfully fetched {len(ipo_list)} IPOs from API")
            return ipo_list
        else:
            logger.warning(f"API response not as expected: {data}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching IPO list from API: {e}")
        return []

# ===== NEW API FETCH UTILITIES =====
def get_api_url():
    now = datetime.now()
    month, year = now.month, now.year
    fin_year = f"{year}-{str(year+1)[-2:]}"
    return f"https://webnodejs.investorgain.com/cloud/report/data-read/331/1/{month}/{year}/{fin_year}/0/all"

def fetch_ipo_list_v2(month: int = None, year: int = None, fin_year: str = None) -> List[Dict[str, Any]]:
    """
    Fetches IPO list from the new enhanced API endpoint.
    If no parameters provided, uses current date.
    Returns list of IPO entries with comprehensive information.
    """
    if month is None or year is None or fin_year is None:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        fin_year = fin_year or f"{year}-{str(year+1)[-2:]}"
    
    api_url = IPO_LIST_API_V2.format(month=month, year=year, fin_year=fin_year)
    logger.info(f"Fetching IPO list from enhanced API: {api_url}")
    
    try:
        response = make_robust_request(api_url)
        data = response.json()
        
        if data.get("msg") == 1 and "reportTableData" in data:
            # Use the new enhanced parsing function
            ipo_list = parse_enhanced_ipo_data(data)
            logger.info(f"Successfully fetched and parsed {len(ipo_list)} IPOs from enhanced API")
            return ipo_list
        else:
            logger.warning(f"Enhanced API response not as expected: {data.get('msg')}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching IPO list from enhanced API: {e}")
        return []

def fetch_gmp_data_for_ipo(ipo_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches Grey Market Premium data for a specific IPO.
    """
    gmp_api_url = f"https://webnodejs.investorgain.com/cloud/ipo/ipo-gmp-read/{ipo_id}/true"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Host": "webnodejs.investorgain.com",
        "Referer": f"https://www.investorgain.com/ipo-gmp/{ipo_id}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }
    
    try:
        response = make_robust_request(gmp_api_url, headers)
        data = handle_compressed_response(response)
        
        if data and data.get("msg") == 1:
            return data
        else:
            logger.warning(f"GMP API response not as expected for IPO {ipo_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching GMP data for IPO {ipo_id}: {e}")
        return None

def fetch_subscription_data_for_ipo(ipo_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches live subscription data for a specific IPO.
    """
    subscription_api_url = f"https://webnodejs.investorgain.com/cloud/ipo/ipo-subscription-read/{ipo_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Host": "webnodejs.investorgain.com",
        "Referer": f"https://www.investorgain.com/ipo-subscription/{ipo_id}/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }
    
    try:
        response = make_robust_request(subscription_api_url, headers)
        data = handle_compressed_response(response)
        
        if data and data.get("msg") == 1:
            return data
        else:
            logger.warning(f"Subscription API response not as expected for IPO {ipo_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching subscription data for IPO {ipo_id}: {e}")
        return None

def fetch_api_response_anchor(ipo_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches anchor data for a specific IPO.
    """
    url = f"https://www.investorgain.com/subscription/regaal-resources-ipo/{ipo_id}/"
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    html_string = response.text

    return html_string

# ===== ENHANCED API PARSING FUNCTIONS =====
def extract_text(html_str: str) -> str:
    """
    Extracts clean text from HTML string.
    """
    if not html_str:
        return ""
    return BeautifulSoup(html_str, "html.parser").get_text(strip=True)

def extract_status(name_html: str) -> tuple:
    """
    Extracts IPO status from HTML content.
    Returns (status_code, status_formatted).
    """
    soup = BeautifulSoup(name_html or "", "html.parser")
    badge = soup.find("span", class_="badge")

    # Map status codes to human-readable format
    status_map = {
        "U": "Upcoming",
        "O": "Open",
        "C": "Closed",
        "CT": "Close Today",
        "L": "Listed",
    }

    if badge:
        status_code = badge.text.strip()
        return status_code, status_map.get(status_code, status_code)

    # If there is no badge, detect Listed from the inline text like "L@65.90 (-0.15%)"
    text = soup.get_text(" ", strip=True)
    if re.search(r"\bL@", text):
        return "L", status_map["L"]

    return None, None

def parse_name_field(name_html: str) -> tuple:
    """
    Parses the name field to extract company name, listed price, listing gain, exchange, and board.
    Returns (name, listed_price, listing_gain, exchange, board).
    """
    soup = BeautifulSoup(name_html or "", "html.parser")
    anchor = soup.find("a")
    anchor_text = anchor.get_text(" ", strip=True) if anchor else extract_text(name_html)

    # Extract listed price and listing gain from the full text
    listed_price = listing_gain = None
    full_text = soup.get_text(" ", strip=True)
    m = re.search(r"L@([\d.]+)\s*\(([-+]?[\d.]+)%\)", full_text)
    if m:
        try:
            listed_price = float(m.group(1))
            listing_gain = float(m.group(2))
        except ValueError:
            pass

    # Detect and strip trailing exchange and board from the anchor text
    exchange = board = None
    m2 = re.search(r"\s+(BSE|NSE)\s+(SME|Mainboard|Main)\s*$", anchor_text, flags=re.IGNORECASE)
    if m2:
        exchange = m2.group(1).upper()
        board_raw = m2.group(2)
        board = "Mainboard" if board_raw.lower().startswith("main") else "SME"
        name_only = anchor_text[: m2.start()].strip()
    else:
        name_only = anchor_text.strip()

    return name_only, listed_price, listing_gain, exchange, board

def parse_gmp(html: str) -> tuple:
    """
    Parses GMP data from HTML content.
    Returns (gmp_value, gmp_percent).
    """
    txt = extract_text(html)
    m = re.search(r"₹?\b([-\d.]+)\b.*\(([-\d.]+)%\)", txt.replace(",", ""))
    val = pct = None
    if m:
        try:
            val, pct = float(m.group(1)), float(m.group(2))
        except ValueError:
            pass
    return val, pct

def parse_est_listing(html: str) -> tuple:
    """
    Parses estimated listing data from HTML content.
    Returns (estimated_price, estimated_percent).
    """
    return parse_gmp(html)

def calculate_estimated_listing(ipo_price, gmp_val):
    """
    Calculate estimated listing price and estimated percent gain.
    Returns (est_price, est_pct) or (None, None) if invalid.
    """
    if ipo_price is None or gmp_val is None:
        return None, None

    try:
        est_price = ipo_price + gmp_val
        est_pct = ((est_price - ipo_price) / ipo_price) * 100
        return est_price, est_pct
    except ZeroDivisionError:
        return est_price, None

def parse_fire_rating(html: str) -> tuple:
    """
    Parses fire rating from HTML content.
    Returns (fire_emoji, fire_count).
    """
    soup = BeautifulSoup(html or "", "html.parser")
    # Count actual fire emojis in the text content
    text = soup.get_text("", strip=True)
    count = text.count("🔥")

    # If none found, try to count HTML entities (e.g., &#128293;)
    if count == 0:
        raw = str(html) if html else ""
        count = raw.count("&#128293;")

    # Never assume a default; allow 0 if truly none
    emoji = "🔥" * count if count > 0 else ""
    return emoji, count

def parse_enhanced_ipo_data(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses the enhanced API response to extract comprehensive IPO data.
    Returns list of formatted IPO entries.
    """
    result = []
    
    try:
        data = api_response.get("reportTableData", [])

        for item in data:
            name_raw = item.get("Name", "")
            name, listed_price, listing_gain, exchange, board = parse_name_field(name_raw)
            status_code, status_formatted = extract_status(name_raw)
            gmp_val, gmp_pct = parse_gmp(item.get("GMP", ""))

            price_raw = item.get("Price", "").replace(",", "")
            ipo_price = float(price_raw) if price_raw.replace(".", "").isdigit() else None

            est_price, est_pct = calculate_estimated_listing(ipo_price, gmp_val)
            
            fire_emoji, fire_count = parse_fire_rating(item.get("Fire Rating", ""))

            ipo = {
                "ipoId": item.get("~id"),
                "apiCompanyName": name,
                "apiExchange": exchange,
                "apiBoard": board,
                "apiIpoStatus": status_code,
                "apiIpoStatusFormatted": status_formatted,
                "apiListedPrice": listed_price,
                "apiListingGain": listing_gain,
                "apiGmpValue": gmp_val,
                "apiGmpPercent": gmp_pct,
                "apiFireRating": fire_emoji,
                "apiFireRatingCount": fire_count,
                "apiSubscription": extract_text(item.get("Sub", "")),
                "apiPrice": convert_to_float(item.get("Price")) if item.get("Price") else None,
                "apiEstimatedListingPrice": est_price,
                "apiEstimatedListingPercent": est_pct,
                "apiIssueSize": extract_text(item.get("IPO Size", "")),
                "apiLot": extract_text(item.get("Lot", "")),
                "apiPe": convert_to_float(item.get("~P/E")) if item.get("~P/E") else None,
                "apiIssueOpenDate": extract_text(item.get("~Srt_Open", "")),
                "apiIssueCloseDate": extract_text(item.get("~Srt_Close", "")),
                "apiBoaDate": extract_text(item.get("~Srt_BoA_Dt", "")),
                "apiListingAt": extract_text(item.get("~Str_Listing", "")),
                "apiUrl": "https://www.investorgain.com" + item.get("~urlrewrite_folder_name", ""),
                "apiIpoCategory": item.get("~IPO_Category"),
                "apiIpoYear": datetime.now().year,
            }
            result.append(ipo)
            
    except Exception as e:
        logger.error(f"Error parsing enhanced IPO data: {e}")
    return result

# ===== DIRECTORY UTILITIES =====
def ensure_directory_exists(directory_path: str) -> None:
    """
    Creates directory if it doesn't exist.
    """
    import os
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info(f"Created directory: {directory_path}")

# ===== TABLE PARSING UTILITIES =====
def parse_html_table_to_list(html_table_string: str, expected_columns: List[str]) -> List[Dict[str, Any]]:
    """
    Generic function to parse HTML table strings into list of dictionaries.
    
    Args:
        html_table_string: HTML table as string
        expected_columns: List of expected column names
        
    Returns:
        List of dictionaries with parsed table data
    """
    table_data = []
    if not html_table_string:
        return table_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    table = soup.find('table')

    if not table:
        return table_data

    # Get headers
    thead = table.find('thead')
    if not thead:
        return table_data
        
    raw_headers = [clean_text(th.get_text()) for th in thead.find_all('th')]
    
    # Get table body
    tbody = table.find('tbody')
    if not tbody:
        return table_data
        
    rows = tbody.find_all('tr')
    for row in rows:
        row_data = {}
        cells = row.find_all('td')
        
        if len(cells) >= len(expected_columns):
            for i, cell in enumerate(cells):
                if i < len(raw_headers):
                    header = raw_headers[i]
                    if header in expected_columns:
                        cell_text = clean_text(cell.get_text(separator=" ", strip=True))
                        row_data[header] = cell_text
            
            if all(col in row_data for col in expected_columns):
                table_data.append(row_data)

    return table_data

# ===== Fetched IPO list from file =====
def fetch_ipo_list_from_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # If it's a list, return it directly
            if isinstance(data, list):
                return data
            # If it's a dict with "ipo_data" key, return that
            elif isinstance(data, dict) and "ipo_data" in data:
                return data["ipo_data"]
            else:
                logger.error("Unexpected JSON format: Not a list or expected dict")
                return []
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

# ===== DATE AND PRICE MATCHING UTILITIES GET SYMBOL =====
def parse_flexible_date(date_str):
    """Parse various date formats flexibly."""
    if not date_str:
        return None
    
    try:
        date_str = str(date_str).strip()
        
        # Handle formats like "19th Aug 2025"
        if any(suffix in date_str.lower() for suffix in ['st', 'nd', 'rd', 'th']):
            cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str, flags=re.IGNORECASE)
            try:
                return datetime.strptime(cleaned.strip(), "%d %b %Y")
            except:
                pass
        
        # Try standard formats
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.split()[0], fmt)
            except:
                continue
        
        return None
    except Exception:
        return None

def date_match(date1, date2):
    """Enhanced date matching with flexible parsing."""
    try:
        if not date1 or not date2:
            return False
        
        parsed_date1 = parse_flexible_date(date1) if isinstance(date1, str) else date1
        parsed_date2 = parse_flexible_date(date2) if isinstance(date2, str) else date2
        
        if not parsed_date1 or not parsed_date2:
            return False
            
        return abs((parsed_date1 - parsed_date2).days) <= DATE_TOLERANCE_DAYS
    except Exception:
        return False

def extract_price_value(price_str):
    """Extract numeric price from various formats."""
    if not price_str:
        return None
    
    try:
        price_str = str(price_str).strip()
        
        # Handle ranges like "₹237.00-255.00" - take the higher value (upper bound)
        if '-' in price_str:
            parts = price_str.split('-')
            if len(parts) == 2:
                price_str = parts[-1].strip()
        
        # Remove currency symbols, commas, and other non-numeric characters except decimals
        cleaned = re.sub(r'[₹,\s]', '', price_str)
        cleaned = re.sub(r'[^\d.]', '', cleaned)
        
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None

def price_match(price1, price2):
    """Enhanced price matching."""
    try:
        price1_val = extract_price_value(price1)
        price2_val = extract_price_value(price2)
        
        if price1_val is None or price2_val is None:
            return False
            
        return abs(price1_val - price2_val) <= PRICE_TOLERANCE
    except Exception:
        return False

def to_int_safe(value):
    """Convert various formats to integer safely."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    
    try:
        # Remove all non-digit characters
        cleaned = re.sub(r"[^\d]", "", str(value))
        return int(cleaned) if cleaned else None
    except:
        return None

def calculate_company_name_similarity(formatted_record, master_record):
    """Calculate the best name similarity score between records."""
    master_name = (master_record.get("name") or "").lower().strip()
    if not master_name:
        return 0
    
    # All possible company names from formatted record
    formatted_names = [
        formatted_record.get("companyFullName") or "",
        formatted_record.get("companyFullNameNew") or "",
        formatted_record.get("scrapedCompanyName") or "",
        formatted_record.get("apiCompanyName") or ""
    ]
    
    # Calculate similarity scores
    scores = []
    for name in formatted_names:
        if name:
            name_clean = name.lower().strip()
            # Use multiple fuzzy matching methods for better accuracy
            token_sort_score = fuzz.token_sort_ratio(master_name, name_clean)
            token_set_score = fuzz.token_set_ratio(master_name, name_clean)
            ratio_score = fuzz.ratio(master_name, name_clean)
            
            # Take the best score from different methods
            best_name_score = max(token_sort_score, token_set_score, ratio_score)
            scores.append(best_name_score)
    
    return max(scores) if scores else 0

def map_ipo_categories(formatted_record, master_record):
    """Map IPO categories from formatted to master record."""
    formatted_ipo = formatted_record.get("apiIpoCategory", "").strip().lower()
    master_ipo = master_record.get("IPO_type", "").strip().lower()
    
    if formatted_ipo == "ipo" and master_ipo == "mainline":
        return "MAINLINE"
    elif formatted_ipo == "sme" and master_ipo == "sme":
        return "SME"
    return None

def validate_ipo_match(formatted_record, master_record):
    """Validate IPO match using multiple criteria."""
    validations_passed = 0
    validation_details = []
    
    try:
        # 1. Opening date validation
        if date_match(master_record.get("biddingStartDate"), formatted_record.get("apiIssueOpenDate")):
            validations_passed += 1
            validation_details.append("opening_date")
        
        # 2. Closing date validation
        if date_match(master_record.get("biddingEndDate"), formatted_record.get("apiIssueCloseDate")):
            validations_passed += 1
            validation_details.append("closing_date")
        
        # 3. Lot size validation
        master_lot = to_int_safe(master_record.get("lotSize"))
        formatted_lot = to_int_safe(formatted_record.get("apiLot") or formatted_record.get("sharesPerLotScraped"))
        
        if master_lot and formatted_lot and master_lot == formatted_lot:
            validations_passed += 1
            validation_details.append("lot_size")
        
        # 4. Price validation - check multiple price fields
        master_price = master_record.get("cutOffPrice")
        formatted_prices = [
            formatted_record.get("apiPrice"),
            formatted_record.get("cutOffPrice")
        ]
        
        for fp in formatted_prices:
            if price_match(master_price, fp):
                validations_passed += 1
                validation_details.append("price")
                break
        
        # 5. Exchange validation
        listing_at = (formatted_record.get("listingAtTable") or "").upper()
        
        if master_record.get("BSE") and "BSE" in listing_at:
            validations_passed += 1
            validation_details.append("bse_listing")
        
        if master_record.get("NSE") and "NSE" in listing_at:
            validations_passed += 1
            validation_details.append("nse_listing")
        
        # 6. ISIN validation
        master_isin = master_record.get("isin")
        if master_isin:
            # Convert record to string and search for ISIN
            record_str = str(formatted_record).upper()
            if master_isin.upper() in record_str:
                validations_passed += 1
                validation_details.append("isin")
        
        # 7. Company IPO types
        if formatted_record.get("apiIpoCategory") and master_record.get("IPO_type"):
            mapped_category = map_ipo_categories(formatted_record, master_record)
            if mapped_category:
                validations_passed += 1
                validation_details.append("ipo_type")

        return validations_passed, validation_details
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return 0, []

def get_ipo_symbol_with_fallback(master_record, formatted_record):
    """
    Get IPO symbol with proper fallback logic.
    Priority: 1. Master symbol 2. ipoNseCodeTable 3. ipoBseCodeTable 4. null
    """
    # First priority: Get symbol from master table
    master_symbol = master_record.get("symbol")
    if master_symbol and master_symbol.strip() and master_symbol.strip().upper() not in ['Y', 'N', 'NULL', 'NONE']:
        return master_symbol.strip(), "MASTER"
    
    # Second priority: Get from formatted record's NSE code
    nse_code = formatted_record.get("ipoNseCodeTable")
    if nse_code and nse_code.strip() and nse_code.strip().upper() not in ['N/A', 'NULL', 'NONE', '']:
        return nse_code.strip(), "NSE_SCRAPED"
    
    # Third priority: Get from formatted record's BSE code  
    bse_code = formatted_record.get("ipoBseCodeTable")
    if bse_code and bse_code.strip() and bse_code.strip().upper() not in ['N/A', 'NULL', 'NONE', '']:
        return bse_code.strip(), "BSE_SCRAPED"
    
    # No valid symbol found
    return None, None

def determine_exchange(master_record, formatted_record, symbol_source):
    """Determine the appropriate exchange based on symbol source and listing info."""
    listing_at = (formatted_record.get("listingAtTable") or "").upper()
    
    if symbol_source == "MASTER":
        # Check which exchanges are available in master and listed
        has_nse = master_record.get("NSE") 
        has_bse = master_record.get("BSE")
        
        if "NSE" in listing_at and has_nse:
            return "NSE"
        elif "BSE" in listing_at and has_bse:
            return "BSE"
        elif "NSE" in listing_at:
            return "NSE"
        elif "BSE" in listing_at:
            return "BSE"
        else:
            return "NSE" if has_nse else ("BSE" if has_bse else None)
    
    elif symbol_source == "NSE_SCRAPED":
        return "NSE"
    elif symbol_source == "BSE_SCRAPED":
        return "BSE"
    
    return None


