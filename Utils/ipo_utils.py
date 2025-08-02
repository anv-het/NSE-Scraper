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
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tenacity import retry, wait_random_exponential, stop_after_attempt
from Utils.logger import get_logger

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

IPO_LIST_API = "https://webnodejs.investorgain.com/cloud/ipo/list-read"
IPO_GMP_API = "https://webnodejs.investorgain.com/cloud/ipo/gmp-read"
IPO_SUBSCRIPTION_API = "https://webnodejs.investorgain.com/cloud/ipo/subscription-read"
BASE_URL = "https://www.investorgain.com"

# Directory configurations
LOGO_DOWNLOAD_DIR = "downloads/ipo/logos"
OUTPUT_DIR = "output"

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
    U = Upcoming, C = Closed, CT = Closed Today
    """
    status_mapping = {
        'U': 'Upcoming',
        'C': 'Closed', 
        'CT': 'Closed Today'
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
