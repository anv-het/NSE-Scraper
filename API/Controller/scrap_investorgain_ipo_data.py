#!/usr/bin/env python3
"""
NSE InvestorGain IPO Data Controller
==================================
Comprehensive IPO data scraper following NSE Controller patterns.
Scrapes all IPO data from InvestorGain with proper logging and database storage.

Features:
- NSE Controller pattern implementation
- Complete IPO data extraction (16 modules)
- MongoDB storage with update-based operations
- Proper logging and error handling
- JSON file output
- Automatic logo downloading
"""

import json
import os
import random
import re
import json
import os
import re
import time
import zlib
import brotli
from datetime import datetime
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, wait_random_exponential, stop_after_attempt

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Utils.data_formatter import NSEDataFormatter  # Commented out as no longer needed
from Utils.config_reader import ConfigReader
from Utils.ipo_utils import (
    # Constants
    COMMON_HEADERS, IPO_LIST_API, IPO_GMP_API, IPO_SUBSCRIPTION_API, 
    BASE_URL, LOGO_DOWNLOAD_DIR, OUTPUT_DIR, IPO_LIST_API_V2,
    # Utility functions
    clean_text, convert_to_float, convert_to_int, clean_html_entities,
    format_ipo_status, parse_date_status, ensure_directory_exists,
    make_robust_request, fetch_ipo_list_from_api, fetch_gmp_data_for_ipo,
    fetch_subscription_data_for_ipo, fetch_ipo_list_v2,
)

logger = get_logger(__name__)


class NSEInvestorGainIPOController:
    """
    Controller for scraping InvestorGain IPO data following NSE patterns.
    Handles comprehensive IPO data collection and database operations.
    """
    
    def __init__(self):
        self.db = DatabaseManager()  # Commented out as per user request
        self.config = ConfigReader()
        self.investorgain_ipo_api_url = IPO_LIST_API_V2
        self.collection_name = "investorgain_ipo_data_v1"
        self.output_filename = "investorgain_ipo_data_v1.json"
        
    def scrape_investorgain_ipo_data(self, month=None, year=None, fin_year=None) -> Dict[str, Any]:
        """
        Main scraping method called by cron jobs.
        Now enhanced to support month/year parameters for targeted scraping.
        Scrapes all IPO data and saves to database and file.
        
        Args:
            month: Month for API call (1-12), defaults to current month
            year: Year for API call, defaults to current year
            fin_year: Financial year string (e.g., "2025-26"), defaults to current financial year
        """
        try:
            # Set default values if not provided
            if month is None or year is None or fin_year is None:
                now = datetime.now()
                month = month or now.month
                year = year or now.year
                fin_year = fin_year or f"{year}-{str(year+1)[-2:]}"
            
            logger.info(f"Starting InvestorGain IPO data scraping for {month}/{year} (FY: {fin_year})")
            
            # Fetch all IPO data using enhanced API
            ipo_data = scrape_all_ipo_data_comprehensive(month=month, year=year, fin_year=fin_year)
            
            if not ipo_data:
                logger.warning("No IPO data retrieved")
                return {
                    "success": False,
                    "message": "No IPO data retrieved",
                    "data_count": 0,
                    "month": month,
                    "year": year,
                    "fin_year": fin_year
                }
            
            # Format data using NSEDataFormatter
            formatted_data = NSEDataFormatter.format_investorgain_ipo_data(ipo_data)
            
            # Save to database with update logic
            save_result = self.save_investorgain_ipo_data(formatted_data)
            
            # Save to JSON file
            json_result = self.save_to_json_file(formatted_data)
            
            logger.info(f"Successfully processed {len(formatted_data)} IPO records for {month}/{year}")
            
            return {
                "success": True,
                "message": f"Successfully scraped {len(formatted_data)} IPO records for {month}/{year}",
                "data_count": len(formatted_data),
                "month": month,
                "year": year,
                "fin_year": fin_year,
                "database_result": save_result,
                "json_file_result": json_result
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_investorgain_ipo_data: {str(e)}")
            return {
                "success": False,
                "message": f"Error scraping IPO data: {str(e)}",
                "data_count": 0,
                "month": month,
                "year": year,
                "fin_year": fin_year
            }
    
    def save_investorgain_ipo_data(self, formatted_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Saves IPO data to both MongoDB and SQL Server using update-based operations.
        Updates existing records based on ipo_id rather than delete-replace.
        """
        try:
            if not formatted_data:
                return {"success": False, "message": "No data to save"}
            
            # Save to MongoDB (existing functionality) - Commented out as per user request
            mongo_result = self.db.save_investorgain_ipo_data(formatted_data)
            
            # Save to SQL Server (new functionality) - Commented out as per user request
            sql_result = self.db.save_investorgain_ipo_data_to_sql(formatted_data)
            
            # Combine results - All database operations commented out as per user request
            combined_result = {
                "success": True,  # Set to True since we're not doing database operations
                "message": "Database operations commented out as requested",
                "total_processed": len(formatted_data)
            }

            # Log the combined result
            logger.info(f"Combined result: {combined_result}")

            return combined_result
            
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            return {
                "success": False,
                "message": f"Database error: {str(e)}"
            }
    
    def save_to_json_file(self, formatted_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Saves formatted IPO data to JSON file.
        """
        try:
            # Ensure output directory exists
            ensure_directory_exists(OUTPUT_DIR)
            
            filepath = os.path.join(OUTPUT_DIR, self.output_filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Successfully saved {len(formatted_data)} records to {filepath}")
            
            return {
                "success": True,
                "filepath": filepath,
                "record_count": len(formatted_data)
            }
            
        except Exception as e:
            logger.error(f"Error saving to JSON file: {str(e)}")
            return {
                "success": False,
                "message": f"File save error: {str(e)}"
            }


# ===== IPO DATA EXTRACTION MODULES =====
# All utility functions, constants, and API functions are imported from Utils/ipo_utils.py
# This preserves all the existing scraping logic while following NSE patterns

# ===== MODULE 01: COMPANY NAMES AND LOGOS =====
def extract_company_name_and_logo(soup, base_url):
    """
    Extracts company name and logo URL from IPO detail page.
    Based on 01_get_ipo_name.py logic.
    """
    company_data = {}
    
    # 1. Extract IPO/Company Name
    ipo_name_tag = soup.find('div', class_='col-lg-6')
    if ipo_name_tag:
        h1_tag = ipo_name_tag.find('h1')
        if h1_tag:
            company_data['scraped_company_name'] = clean_text(h1_tag.get_text(strip=True))
    
    # If not found in h1, try alternative selectors
    if not company_data.get('scraped_company_name'):
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Extract company name from title (usually in format "Company Name IPO...")
            if 'IPO' in title_text:
                company_name = title_text.split('IPO')[0].strip()
                company_data['scraped_company_name'] = clean_text(company_name)
    
    # Fallback to N/A if still not found
    if not company_data.get('scraped_company_name'):
        company_data['scraped_company_name'] = 'N/A'

    # 2. Extract Company Logo
    logo_img_tag = soup.find('div', class_='div-logo')
    if logo_img_tag:
        img_tag = logo_img_tag.find('img')
        if img_tag:
            logo_src = img_tag.get('src')
            # Convert relative URLs to absolute URLs
            if logo_src:
                if logo_src.startswith('http'):
                    company_data['company_logo_url'] = logo_src
                else:
                    company_data['company_logo_url'] = urljoin(base_url, logo_src)
            else:
                company_data['company_logo_url'] = 'N/A'
        else:
            company_data['company_logo_url'] = 'N/A'
    else:
        company_data['company_logo_url'] = 'N/A'
    
    return company_data

def download_company_logo(logo_url, company_name, ipo_id):
    """
    Downloads company logo and saves it to downloads/ipo/logos/ directory.
    Returns the local file path if successful, None otherwise.
    """
    if logo_url == 'N/A' or not logo_url:
        return None
    
    try:
        # Ensure logos directory exists
        ensure_directory_exists(LOGO_DOWNLOAD_DIR)
        
        # Clean company name for filename
        safe_company_name = re.sub(r'[<>:"/\\\\|?*]', '_', company_name)
        safe_company_name = safe_company_name.replace(' ', '_')
        
        # Get file extension from URL
        file_extension = logo_url.split('.')[-1].split('?')[0]  # Remove query parameters
        if file_extension.lower() not in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
            file_extension = 'jpg'  # Default extension
        
        filename = f"{ipo_id}_{safe_company_name}_logo.{file_extension}"
        filepath = os.path.join(LOGO_DOWNLOAD_DIR, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            logger.info(f"Logo already exists: {filepath}")
            return filepath
        
        # Download the logo
        response = make_robust_request(logo_url)
        
        # Save the file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
        
    except Exception as e:
        logger.error(f"     Error downloading logo: {e}")
        return None

# ===== MODULE 02: IPO DETAILS EXTRACTION =====
def extract_company_about(soup):
    """
    Extracts the full company name and the 'About Company' paragraph(s) from the soup object.
    Based on 02_get_ipo_details.py logic.
    """
    company_full_name = "N/A"
    about_company_text = "N/A"

    # Find the <h3> tag with itemprop="about"
    about_h3 = soup.find('h3', itemprop="about")

    if about_h3:
        h3_text = clean_text(about_h3.get_text())

        # Extract "Company Full Name" from the h3 tag's text
        match = re.search(r'About Company\s*-\s*(.+)', h3_text, re.IGNORECASE)
        if match:
            company_full_name = clean_text(match.group(1))

        # Find the <div> immediately after the <h3>
        about_content_container = None
        current_sibling = about_h3.next_sibling
        while current_sibling:
            if isinstance(current_sibling, str):  # Skip NavigableString (whitespace, newlines)
                current_sibling = current_sibling.next_sibling
                continue

            if current_sibling.name == 'div':
                about_content_container = current_sibling
                break
            else:
                break
            
            current_sibling = current_sibling.next_sibling

        if about_content_container:
            # Find all <p> tags within this specific div
            about_paragraphs = []
            paragraphs_in_div = about_content_container.find_all('p')
            
            for p_tag in paragraphs_in_div:
                paragraph_text = clean_text(p_tag.get_text())
                if paragraph_text:
                    about_paragraphs.append(paragraph_text)
            
            if about_paragraphs:
                about_company_text = "\n\n".join(about_paragraphs)

    return {
        'company_full_name_scraped': company_full_name,
        'about_company_text': about_company_text
    }

def extract_ipo_other_details(soup):
    """
    Extracts various IPO details from the first table within the specific div.
    Based on 02_get_ipo_details.py logic.
    """
    other_details = {}
    
    # Find the target column div for IPO Details table
    target_col_div = None
    for div in soup.find_all('div', class_=['col-lg-6', 'col-md-6', 'col-sm-12']):
        h2_tag = div.find('h2', itemprop='about', string=re.compile(r'IPO\s+Details', re.IGNORECASE))
        if h2_tag:
            target_col_div = div
            break

    if not target_col_div:
        return {
            "ipo_issue_price": "N/A", "drhp_url": "N/A", "rhp_url": "N/A", "anchor_list_url": "N/A",
            "retail_quota": "N/A", "ipo_issue_type": "N/A", "ipo_issue_size_scraped": "N/A", 
            "fresh_issue": "N/A", "face_value": "N/A", "promoter_holding_pre_ipo": "N/A", 
            "promoter_holding_post_ipo": "N/A", "ipo_issue_opening_date": "N/A", 
            "ipo_issue_closing_date": "N/A",
        }

    # Find the table within this div
    details_table = target_col_div.find('table', class_=['table', 'table-bordered', 'table-striped', 'table-hover', 'w-auto'])

    if not details_table:
        return {
            "ipo_issue_price": "N/A", "drhp_url": "N/A", "rhp_url": "N/A", "anchor_list_url": "N/A",
            "retail_quota": "N/A", "ipo_issue_type": "N/A", "ipo_issue_size_scraped": "N/A", 
            "fresh_issue": "N/A", "face_value": "N/A", "promoter_holding_pre_ipo": "N/A", 
            "promoter_holding_post_ipo": "N/A", "ipo_issue_opening_date": "N/A", 
            "ipo_issue_closing_date": "N/A",
        }

    # Define mapping from cleaned label text to output key
    label_to_key_map = {
        "ipo issue opening date": "ipo_issue_opening_date",
        "ipo issue closing date": "ipo_issue_closing_date",
        "ipo issue price": "ipo_issue_price",
        "drhp": "drhp_url",
        "rhp": "rhp_url",
        "anchor list": "anchor_list_url",
        "retail quota": "retail_quota",
        "ipo issue type": "ipo_issue_type",
        "ipo issue size": "ipo_issue_size_scraped",
        "fresh issue": "fresh_issue",
        "face value": "face_value",
        "promoter holding pre ipo": "promoter_holding_pre_ipo",
        "promoter holding post ipo": "promoter_holding_post_ipo",
    }

    rows = details_table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 2:
            label_strong = cols[0].find('strong')
            if label_strong:
                label_raw = label_strong.get_text()
                label = clean_text(label_raw).lower()
                value_td = cols[1]
                
                output_key = label_to_key_map.get(label)
                if output_key:
                    if "url" in output_key:  # Check if it's a URL field
                        link_tag = value_td.find('a')
                        extracted_value = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "N/A"
                    else:
                        extracted_value = clean_text(value_td.get_text())
                        # Clean HTML entities for issue size
                        if output_key == "ipo_issue_size_scraped":
                            extracted_value = clean_html_entities(extracted_value)
                    
                    other_details[output_key] = extracted_value

    # Ensure all keys are present, even if N/A
    for key in label_to_key_map.values():
        if key not in other_details:
            other_details[key] = "N/A"

    return other_details

def extract_summary_block_details(soup):
    """
    Extracts IPO Summary Text and minimum lot size (shares per lot) 
    from the div with class 'float-none mb-2 ms-2'.
    Based on 02_get_ipo_details.py logic.
    """
    summary_details = {
        'min_order_quantity_scraped': '1 lot',
        'shares_per_lot_scraped': 'N/A',
        'ipo_summary_text': 'N/A'
    }

    div_logo = soup.find('div', class_='div-logo')
    target_div = None

    if div_logo:
        target_div = div_logo.find_next_sibling('div', class_=['float-none', 'mb-2', 'ms-2'])

    if target_div:
        ipo_summary_paragraphs = []
        for p_tag in target_div.find_all('p'):
            paragraph_text = clean_text(p_tag.get_text())
            if paragraph_text:
                ipo_summary_paragraphs.append(paragraph_text)

        if ipo_summary_paragraphs:
            full_summary_text = "\n\n".join(ipo_summary_paragraphs)
            summary_details['ipo_summary_text'] = full_summary_text

            # Regex to find lot size: "comprising 211 shares", etc.
            match = re.search(r'comprising\s+(\d+)\s+shares', full_summary_text, re.IGNORECASE)
            if match:
                summary_details['shares_per_lot_scraped'] = match.group(1)

    return summary_details

def add_date_status_fields(comprehensive_data):
    """
    Adds parsed date status for key dates in IPO data.
    """
    key_dates_for_status = [
        ('ipo_issue_opening_date', 'ipo_issue_opening_date_status', 'ipo_issue_opening_date_parsed'),
        ('ipo_issue_closing_date', 'ipo_issue_closing_date_status', 'ipo_issue_closing_date_parsed')
    ]
    
    for date_key, status_key, parsed_key in key_dates_for_status:
        if date_key in comprehensive_data:
            parsed_date, status, original = parse_date_status(comprehensive_data[date_key])
            comprehensive_data[status_key] = status
            if parsed_date:
                comprehensive_data[parsed_key] = parsed_date.strftime('%Y-%m-%d')
            else:
                comprehensive_data[parsed_key] = 'N/A'
    
    return comprehensive_data

# ===== MODULE 03: IPO IMPORTANT DATES =====
def extract_ipo_important_dates(soup):
    """
    Extracts IPO Important Dates from the IPO detail page by directly targeting
    <strong> tags with core date labels and getting their next sibling <td>.
    Based on 03_get_ipo_important_dates.py logic.
    """
    dates_data = {}
    
    # Define patterns for the core date labels
    date_field_patterns = {
        "ipo_open_date": re.compile(r'Opening Date', re.IGNORECASE),
        "ipo_close_date": re.compile(r'Closing Date', re.IGNORECASE),
        "basis_of_allotment": re.compile(r'Basis of Allotment Date', re.IGNORECASE),
        "initiation_of_refunds": re.compile(r'Refunds Initiation', re.IGNORECASE),
        "credit_of_shares_to_demat": re.compile(r'Credit of Shares to Demat', re.IGNORECASE),
        "listing_date": re.compile(r'Listing Date', re.IGNORECASE), 
    }

    # Iterate through all <strong> tags first, then check their text
    all_strong_tags = soup.find_all('strong')

    for output_key, pattern in date_field_patterns.items():
        found = False
        for strong_tag in all_strong_tags:
            strong_text = clean_text(strong_tag.get_text())
            
            if pattern.search(strong_text):
                # Found the strong tag containing our pattern
                # Find its parent <td>
                target_td = strong_tag.find_parent('td')
                if target_td:
                    # The date value is usually in the immediate next sibling <td>
                    value_td = target_td.find_next_sibling('td')
                    if value_td:
                        value = clean_text(value_td.get_text(strip=True))
                        dates_data[output_key] = value
                        found = True
                        break

    # Ensure all expected keys are present, even if with 'N/A'
    for key in date_field_patterns.keys():
        if key not in dates_data:
            dates_data[key] = 'N/A'
    
    return dates_data

def add_important_dates_status_fields(comprehensive_data):
    """
    Adds parsed date status for important dates in IPO data.
    """
    key_dates_for_status = [
        ('ipo_open_date', 'ipo_open_date_status', 'ipo_open_date_parsed'),
        ('ipo_close_date', 'ipo_close_date_status', 'ipo_close_date_parsed'),
        ('listing_date', 'listing_date_status', 'listing_date_parsed'),
        ('basis_of_allotment', 'basis_of_allotment_status', 'basis_of_allotment_parsed'),
        ('initiation_of_refunds', 'initiation_of_refunds_status', 'initiation_of_refunds_parsed'),
        ('credit_of_shares_to_demat', 'credit_of_shares_to_demat_status', 'credit_of_shares_to_demat_parsed')
    ]
    
    for date_key, status_key, parsed_key in key_dates_for_status:
        if date_key in comprehensive_data:
            parsed_date, status, original = parse_date_status(comprehensive_data[date_key])
            comprehensive_data[status_key] = status
            if parsed_date:
                comprehensive_data[parsed_key] = parsed_date.strftime('%Y-%m-%d')
            else:
                comprehensive_data[parsed_key] = 'N/A'
    
    return comprehensive_data

# ===== MODULE 04: IPO LOTS DATA =====
def extract_ipo_lots_data(soup):
    """
    Extracts IPO Lots table data from the IPO detail page.
    Based on 04_get_ipo_lots.py logic.
    """
    ipo_lots_data = {}

    # Define patterns for mapping scraped labels to desired output keys
    lot_field_patterns_map = {
        "lot_issue_price": re.compile(r'Issue Price', re.IGNORECASE),
        "lot_market_lot": re.compile(r'Market Lot', re.IGNORECASE),
        "lot_individual_investor": re.compile(r'Individual Investor', re.IGNORECASE),
        "lot_min_hni_lots": re.compile(r'Min HNI Lots', re.IGNORECASE),
        "lot_min_small_hni_lots_2_10_lakh": re.compile(r'Min Small HNI Lots\(2-10 Lakh\)', re.IGNORECASE),
        "lot_min_big_hni_lots_10_plus_lakh": re.compile(r'Min Big HNI Lots\(10\+ Lakh\)', re.IGNORECASE),
    }

    ipo_lots_table = None
    # Find the h2 tag that contains "IPO Lots" in its text content
    for h2_tag in soup.find_all('h2'):
        h2_text_content = clean_text(h2_tag.get_text())
        if re.search(r'IPO.*Lots', h2_text_content, re.IGNORECASE):
            # The desired table is its immediate next sibling with the specified class
            ipo_lots_table = h2_tag.find_next_sibling('table', class_='table table-bordered table-striped table-hover w-auto')
            if ipo_lots_table:
                break

    if ipo_lots_table:
        # Iterate through table rows to extract data
        for row in ipo_lots_table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:  # Ensure there are at least two cells (label and value)
                label_element = cells[0]
                value_element = cells[1]

                label_text = clean_text(label_element.get_text(strip=True))
                value = clean_text(value_element.get_text(strip=True))
                
                # Default to 'N/A' if the value is empty after cleaning
                if not value and value != '':
                    value = 'N/A'

                # Map the scraped label to our desired output key
                for output_key, pattern in lot_field_patterns_map.items():
                    if pattern.search(label_text):
                        ipo_lots_data[output_key] = value
                        break

    # Ensure all expected keys are present in the final output, defaulting to 'N/A' if not found
    for key in lot_field_patterns_map.keys():
        if key not in ipo_lots_data:
            ipo_lots_data[key] = 'N/A'
    
    return ipo_lots_data

# ===== MODULE 05: IPO GMP DATA =====
def clean_html_content(html_content):
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

def extract_percentage_value(gmp_percent_calc):
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

def fetch_gmp_data_for_ipo(ipo_id):
    """
    Fetches GMP data for a specific IPO ID from the Investorgain API.
    Based on 05_get_ipo_gmp.py logic.
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
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            # Handle compression manually if needed
            content_encoding = response.headers.get('Content-Encoding')
            if content_encoding == 'gzip':
                try:
                    import zlib
                    decompressed_content = zlib.decompress(response.content, 16 + zlib.MAX_WBITS).decode('utf-8')
                    data = json.loads(decompressed_content)
                except Exception:
                    return None
            elif content_encoding == 'br':
                try:
                    import brotli
                    decompressed_content = brotli.decompress(response.content).decode('utf-8')
                    data = json.loads(decompressed_content)
                except Exception:
                    return None
            else:
                return None

        if data.get("msg") == 1:
            return data
        else:
            return None
    except Exception:
        return None

def parse_gmp_api_data(gmp_data_array):
    """
    Parses the 'ipoGmpData' list from the GMP API response.
    Cleans HTML content from specified fields as requested.
    """
    gmp_json_data = {}
    if gmp_data_array and isinstance(gmp_data_array, list) and len(gmp_data_array) > 0:
        latest_gmp = gmp_data_array[0] 
        
        # Get raw gmp_comments, gmp_compare_desc, and gmp_percent_calc
        raw_gmp_comments = latest_gmp.get("gmp_comments", "N/A")
        raw_gmp_compare_desc = latest_gmp.get("gmp_compare_desc", "N/A") 
        raw_gmp_percent_calc = latest_gmp.get("gmp_percent_calc", "N/A")
        
        gmp_json_data = {
            "Seq": clean_text(str(latest_gmp.get("Seq", "N/A"))),
            "id (GMP Data)": clean_text(str(latest_gmp.get("id", "N/A"))),
            "ipo_id (GMP Data)": clean_text(str(latest_gmp.get("ipo_id", "N/A"))),
            "gmp_date": clean_text(latest_gmp.get("gmp_date", "N/A")),
            "gmp": clean_text(latest_gmp.get("gmp", "N/A")),
            # Clean HTML content from these fields as requested
            "gmp_comments": clean_html_content(raw_gmp_comments),
            "gmp_compare_desc": clean_html_content(raw_gmp_compare_desc),
            "subject_to_sauda": clean_text(latest_gmp.get("subject_to_sauda", "N/A")),
            "gmp_city": clean_text(latest_gmp.get("gmp_city", "N/A")),
            "gmp_variation": clean_text(latest_gmp.get("gmp_variation", "N/A")),
            "max_ipo_price": clean_text(latest_gmp.get("max_ipo_price", "N/A")),
            "estimated_listing_price": clean_text(latest_gmp.get("estimated_listing_price", "N/A")),
            # Extract just the percentage value (e.g., "25.33" from "25.33%")
            "gmp_percent_calc": extract_percentage_value(raw_gmp_percent_calc),
            "gmp_desc_other": clean_text(latest_gmp.get("gmp_desc_other", "N/A")),
            "up_down_status": clean_text(latest_gmp.get("up_down_status", "N/A")),
            "gmp_active_record_flag": clean_text(str(latest_gmp.get("gmp_active_record_flag", "N/A"))),
            "sub2 Sauda Rate": clean_text(latest_gmp.get("sub2", "N/A")),
            "est_profit": clean_text(latest_gmp.get("est_profit", "N/A")),
            "create_date": clean_text(latest_gmp.get("create_date", "N/A")),
            "create_date_gmp": clean_text(latest_gmp.get("create_date_gmp", "N/A")),
            "last_updated_gmp": clean_text(latest_gmp.get("last_updated_gmp", "N/A")),
            "last_updated": clean_text(latest_gmp.get("last_updated", "N/A"))
        }
    return gmp_json_data

def parse_gmp_trend_table(html_table_string):
    """
    Parses the HTML table string (ipoGmpTable) to extract day-wise GMP trends.
    """
    gmp_trend_data = []
    if not html_table_string:
        return gmp_trend_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    table = soup.find('table')

    if not table:
        return gmp_trend_data

    desired_columns = [
        "GMP Date",
        "IPO Price", 
        "GMP",
        "Sub2 Sauda Rate",
        "Estimated Listing Price",
        "Estimated Profit",
        "Last Updated"
    ]
    
    thead = table.find('thead')
    if not thead:
        return gmp_trend_data
        
    raw_headers_from_table = [clean_text(th.get_text()) for th in thead.find_all('th')]
    
    header_to_output_key_map = {}
    for header in raw_headers_from_table:
        if "Estimated Profit" in header:
            header_to_output_key_map[header] = "Estimated Profit"
        else:
            header_to_output_key_map[header] = header

    tbody = table.find('tbody')
    if not tbody:
        return gmp_trend_data
        
    body_rows = tbody.find_all('tr')
    for row in body_rows:
        row_data = {}
        cells = row.find_all('td')
        
        if len(cells) >= len(desired_columns):
            for i, cell in enumerate(cells):
                if i < len(raw_headers_from_table):
                    raw_header = raw_headers_from_table[i]
                    output_key = header_to_output_key_map.get(raw_header)
                    
                    if output_key in desired_columns:
                        cell_text = clean_text(cell.get_text(separator=" ", strip=True))
                        row_data[output_key] = cell_text
            
            if all(col in row_data for col in desired_columns):
                gmp_trend_data.append(row_data)

    return gmp_trend_data

# ===== MODULE 07: IPO STRENGTHS DATA =====
def extract_ipo_strengths(soup):
    """
    Extracts IPO strengths data from the IPO detail page.
    Based on 07_get_ipo_strengths.py logic.
    Returns a list of strength points.
    """
    strengths = []
    
    # Search for any H3 tag containing "Strengths" (case-insensitive)
    for h3 in soup.find_all('h3'):
        cleaned_h3_text = clean_text(h3.get_text())
        if re.search(r'strengths', cleaned_h3_text, re.IGNORECASE):
            # Look for the next sibling div containing the strengths list
            div = h3.find_next_sibling('div')
            if div:
                ul = div.find('ul')
                if ul:
                    # Extract all list items and clean the text
                    strengths = [clean_text(li.get_text()) for li in ul.find_all('li') if clean_text(li.get_text())]
                    break  # Found the strengths, no need to check other h3s
    
    return strengths

# ===== MODULE 09: IPO OBJECTIVES DATA =====
def extract_ipo_objectives(soup):
    """
    Extracts IPO objectives data from the IPO detail page.
    Based on 09_get_ipo_objective.py logic.
    Returns a list of objective dictionaries with s_no, object, and amount.
    """
    objectives = []
    
    try:
        # Search for H3 tag containing "IPO Objective"
        for h3 in soup.find_all("h3"):
            h3_text = clean_text(h3.get_text())
            if "IPO Objective" in h3_text or "objective" in h3_text.lower():
                # Look for table with id "ObjectiveIssue"
                table = soup.find("table", {"id": "ObjectiveIssue"})
                if not table:
                    # If no table with specific ID, look for nearby tables
                    table = h3.find_next("table")
                
                if table:
                    tbody = table.find("tbody")
                    if tbody:
                        rows = tbody.find_all("tr")
                        for row in rows:
                            cols = row.find_all("td")
                            if len(cols) >= 2:
                                s_no = clean_text(cols[0].get_text(strip=True))
                                objective_text = clean_text(cols[1].get_text(strip=True))
                                amount = clean_text(cols[2].get_text(strip=True)) if len(cols) > 2 else ""
                                
                                # Only add if we have meaningful content
                                if objective_text and objective_text != "":
                                    objectives.append({
                                        "s_no": s_no,
                                        "object": objective_text,
                                        "amount": amount
                                    })
                break
    except Exception as e:
        # Log the error but don't add error to objectives list   
        logger.error(f"Error extracting IPO objectives: {e}") 
    return objectives

# ===== MODULE 10: IPO SUBSCRIPTION DATA =====
def fetch_subscription_data_for_ipo(ipo_id):
    """
    Fetches IPO subscription data for a specific IPO ID from the Investorgain API.
    Based on 10_get_live_subscription_summary.py logic.
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
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            # Handle compression manually if needed
            content_encoding = response.headers.get('Content-Encoding')
            if content_encoding == 'gzip':
                try:
                    import zlib
                    decompressed_content = zlib.decompress(response.content, 16 + zlib.MAX_WBITS).decode('utf-8')
                    data = json.loads(decompressed_content)
                except Exception:
                    return None
            elif content_encoding == 'br':
                try:
                    import brotli
                    decompressed_content = brotli.decompress(response.content).decode('utf-8')
                    data = json.loads(decompressed_content)
                except Exception:
                    return None
            else:
                return None

        if data.get("msg") == 1:
            return data
        else:
            return None
    except Exception:
        return None

def parse_ipo_bidding_data_json(bidding_data_array):
    """
    Parses the 'ipoBiddingData' list from the Subscription API response.
    """
    parsed_data = []
    if not bidding_data_array:
        return parsed_data

    for entry in bidding_data_array:
        parsed_entry = {
            "Seq": convert_to_int(clean_text(str(entry.get("Seq", "N/A")))),
            "id (Subscription Data)": convert_to_int(clean_text(str(entry.get("id", "N/A")))),
            "tsb_ipo_id": convert_to_int(clean_text(str(entry.get("tsb_ipo_id", "N/A")))),
            "cor_id": convert_to_int(clean_text(str(entry.get("cor_id", "N/A")))),
            "bid_date": clean_text(entry.get("bid_date", "N/A")),
            "qib_offered": convert_to_int(clean_text(entry.get("qib_offered", "N/A"))),
            "nii_offered": convert_to_int(clean_text(entry.get("nii_offered", "N/A"))),
            "nii_offered_big": convert_to_int(clean_text(entry.get("nii_offered_big", "N/A"))),
            "nii_offered_small": convert_to_int(clean_text(entry.get("nii_offered_small", "N/A"))),
            "rii_offered": convert_to_int(clean_text(entry.get("rii_offered", "N/A"))),
            "emp_offered": convert_to_int(clean_text(entry.get("emp_offered", "N/A"))),
            "other_offered": convert_to_int(clean_text(entry.get("other_offered", "N/A"))),
            "total_offered": convert_to_int(clean_text(entry.get("total_offered", "N/A"))),
            "qib_shares_bid_for": convert_to_int(clean_text(entry.get("qib_shares_bid_for", "N/A"))),
            "nii_shares_bid_for": convert_to_int(clean_text(entry.get("nii_shares_bid_for", "N/A"))),
            "nii_shares_bid_for_big": convert_to_int(clean_text(entry.get("nii_shares_bid_for_big", "N/A"))),
            "nii_shares_bid_for_small": convert_to_int(clean_text(entry.get("nii_shares_bid_for_small", "N/A"))),
            "rii_shares_bid_for": convert_to_int(clean_text(entry.get("rii_shares_bid_for", "N/A"))),
            "emp_shares_bid_for": convert_to_int(clean_text(entry.get("emp_shares_bid_for", "N/A"))),
            "other_shares_bid_for": convert_to_int(clean_text(entry.get("other_shares_bid_for", "N/A"))),
            "total_shares_bid_for": convert_to_int(clean_text(entry.get("total_shares_bid_for", "N/A"))),
            "qib_bid_amt": convert_to_float(clean_text(entry.get("qib_bid_amt", "N/A"))),
            "nii_bid_amt": convert_to_float(clean_text(entry.get("nii_bid_amt", "N/A"))),
            "nii_bid_amt_big": convert_to_float(clean_text(entry.get("nii_bid_amt_big", "N/A"))),
            "nii_bid_amt_small": convert_to_float(clean_text(entry.get("nii_bid_amt_small", "N/A"))),
            "rii_bid_amt": convert_to_float(clean_text(entry.get("rii_bid_amt", "N/A"))),
            "emp_bid_amt": convert_to_float(clean_text(entry.get("emp_bid_amt", "N/A"))),
            "other_bid_amt": convert_to_float(clean_text(entry.get("other_bid_amt", "N/A"))),
            "total_bid_amt": convert_to_float(clean_text(entry.get("total_bid_amt", "N/A"))),
            "qib": convert_to_float(clean_text(entry.get("qib", "N/A"))),
            "nii": convert_to_float(clean_text(entry.get("nii", "N/A"))),
            "nii_big": convert_to_float(clean_text(entry.get("nii_big", "N/A"))),
            "nii_small": convert_to_float(clean_text(entry.get("nii_small", "N/A"))),
            "rii": convert_to_float(clean_text(entry.get("rii", "N/A"))),
            "emp": convert_to_float(clean_text(entry.get("emp", "N/A"))),
            "other": convert_to_float(clean_text(entry.get("other", "N/A"))),
            "total": convert_to_float(clean_text(entry.get("total", "N/A"))),
            "cor_date_added": clean_text(entry.get("cor_date_added", "N/A")),
            "create_date": clean_text(entry.get("create_date", "N/A")),
            "ipo_category_desc": clean_text(entry.get("ipo_category_desc", "N/A")),
            "listing_at": clean_text(entry.get("listing_at", "N/A")),
            "company_short_name": clean_text(entry.get("company_short_name", "N/A"))
        }
        parsed_data.append(parsed_entry)
    return parsed_data

def parse_ipo_share_allocation(html_string):
    """
    Parses the 'listItemsHTML' to extract IPO Share Allocation data.
    """
    allocation_data = []
    if not html_string:
        return allocation_data

    soup = BeautifulSoup(html_string, 'html.parser')
    list_items = soup.find_all('li')

    # Regex to handle format: "Category: X Shares (Y%)"
    allocation_regex = re.compile(
        r'(.+?):\s*([\d,\.]+(?:\.\d{2})?)\s*Shares\s*\(([\d\.]+)\%\)'
    )

    for item in list_items:
        text = item.get_text().strip()
        match = allocation_regex.search(text)
        if match:
            raw_category = match.group(1).strip()
            raw_shares = match.group(2).strip()
            raw_percentage = match.group(3).strip()

            category = clean_text(raw_category)
            shares_allocated = convert_to_int(clean_text(raw_shares))
            allocation_pct = convert_to_float(clean_text(raw_percentage))
            
            allocation_data.append({
                "category": category,
                "shares_allocated": shares_allocated,
                "allocation_pct": allocation_pct
            })

    return allocation_data

def parse_ipo_daywise_subscription_table(html_table_string):
    """
    Parses the HTML table string for IPO Day-wise Subscription.
    """
    daywise_data = []
    if not html_table_string:
        return daywise_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return daywise_data
    
    tbody = table.find('tbody')
    if not tbody:
        return daywise_data
    
    rows = tbody.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 2:
            continue
            
        # Check if this is a day row
        day_cell = cells[0]
        date_cell = cells[1]
        
        day_text = clean_text(day_cell.get_text())
        if not day_text or not day_text.isdigit():
            continue
            
        row_data = {
            "day_number": convert_to_int(day_text),
            "date_time": clean_text(date_cell.get_text()),
        }
        
        # Parse subscription ratios from remaining cells
        if len(cells) >= 7:  # Day, Date, QIB, NII, RII, EMP, Total
            row_data["qib_ratio"] = convert_to_float(clean_text(cells[2].get_text()))
            row_data["nii_ratio"] = convert_to_float(clean_text(cells[3].get_text()))
            row_data["rii_ratio"] = convert_to_float(clean_text(cells[4].get_text()))
            row_data["emp_ratio"] = convert_to_float(clean_text(cells[5].get_text()))
            row_data["total_ratio"] = convert_to_float(clean_text(cells[6].get_text()))
        
        daywise_data.append(row_data)
    
    return daywise_data

def parse_ipo_shares_bid_amount_table(html_table_string):
    """
    Parses the HTML table string for IPO Shares Bid Amount.
    """
    bid_amount_data = []
    if not html_table_string:
        return bid_amount_data

    soup = BeautifulSoup(html_table_string, 'html.parser')
    
    # Look for the table with caption "IPO Bidding Live Number of Shares by Category"
    target_table = None
    all_tables = soup.find_all('table')
    
    for table in all_tables:
        caption = table.find('caption')
        if caption and 'Number of Shares by Category' in caption.get_text():
            target_table = table
            break
    
    if not target_table:
        return bid_amount_data

    # Parse the table body
    tbody = target_table.find('tbody')
    if not tbody:
        return bid_amount_data
    
    rows = tbody.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 4:  # Need at least Category, Shares Offered, Shares Bid, Bid Amount
            continue
            
        category_text = clean_text(cells[0].get_text())
        shares_offered_text = clean_text(cells[1].get_text())
        shares_bid_text = clean_text(cells[2].get_text())
        bid_amount_text = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
        
        bid_amount_data.append({
            "category": category_text,
            "shares_offered": convert_to_int(shares_offered_text),
            "shares_bid": convert_to_int(shares_bid_text),
            "bid_amount_cr": convert_to_float(bid_amount_text)
        })
    
    return bid_amount_data

# ===== MODULE 12: COMPANY FINANCIAL DATA =====
def find_financial_table_alternative(soup):
    """
    Tries to find the financial table using heading proximity if standard ID-based lookup fails.
    Based on 12_get_company_financials.py logic.
    """
    # Look for h2 heading containing "Financial Information"
    heading = soup.find('h2', string=lambda text: text and 'Financial Information' in text)
    if heading:
        parent_div = heading.find_next('div', class_='table-responsive')
        if parent_div:
            table = parent_div.find('table')
            if table:
                return table
    return None

def extract_financial_data(soup):
    """
    Extracts company financial data from the IPO detail page.
    Based on 12_get_company_financials.py logic.
    """
    financial_data = []
    
    try:
        # First try to find table with id 'financialTable'
        table = soup.find('table', {'id': 'financialTable'})
        
        # If not found, try alternative method
        if not table:
            table = find_financial_table_alternative(soup)
        
        if not table:
            return financial_data
        
        # Extract all rows from the table
        rows = table.find_all('tr')
        data = []
        
        for row in rows:
            cols = [clean_text(col.get_text()) for col in row.find_all(['td', 'th'])]
            data.append(cols)
        
        if len(data) < 2:  # Need at least header and one data row
            return financial_data
        
        # First row contains headers (years)
        headers = data[0]
        
        # Process each subsequent row as a financial metric
        for row_data in data[1:]:
            if len(row_data) < 2:  # Need at least metric name and one value
                continue
                
            metric = clean_text(row_data[0])
            if not metric:  # Skip empty metric names
                continue
                
            entry = {"Metric": metric}
            
            # Add values for each year column
            for i, header in enumerate(headers[1:], 1):
                if i < len(row_data):
                    value = clean_text(row_data[i])
                    # Try to convert to float and format, or keep as string
                    float_value = convert_to_float(value)
                    if float_value is not None:
                        entry[header] = f"{float_value:.2f}"
                    else:
                        entry[header] = None if not value else value
                else:
                    entry[header] = None
            
            financial_data.append(entry)
    
    except Exception as e:
        logger.warning(f"Error extracting financial data: {e}")

    return financial_data

# ===== MODULE 13: IPO PEER COMPARISON DATA =====
def find_peer_comparison_table(soup):
    """
    Find peer comparison table robustly using multiple methods.
    Based on 13_get_ipo_peer_comparison.py logic.
    """
    # Method 1: Find heading h2 containing "Peer Comparison" and then get next table
    for h2 in soup.find_all("h2"):
        if "Peer Comparison" in h2.get_text():
            table = h2.find_next("table")
            if table:
                return table

    # Method 2: Search all tables for expected headers
    expected_headers = {"Company", "EPS Basic", "EPS Diluted", "NAV", "P/E(x)", "RoNW", "Financial statements"}
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if expected_headers.issubset(set(headers)):
            return table

    return None

def extract_peer_comparison(soup):
    """
    Extracts peer comparison data from the IPO detail page.
    Based on 13_get_ipo_peer_comparison.py logic.
    """
    peer_comparison_data = []
    
    try:
        table = find_peer_comparison_table(soup)
        if not table:
            return peer_comparison_data

        # Get headers from thead
        thead = table.find("thead")
        if not thead:
            return peer_comparison_data
            
        headers = [clean_text(th.get_text(strip=True)) for th in thead.find_all("th")]
        
        # Get data from tbody
        tbody = table.find("tbody")
        if not tbody:
            return peer_comparison_data
            
        rows = tbody.find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            row_data = {}
            
            # Map available columns to headers, even if counts mismatch
            for i in range(min(len(cols), len(headers))):
                header = headers[i]
                cell_value = clean_text(cols[i].get_text(strip=True))
                row_data[header] = cell_value if cell_value else ""
            
            # Only add row if it has meaningful data
            if any(value for value in row_data.values()):
                peer_comparison_data.append(row_data)

    except Exception as e:
        logger.warning(f"Error extracting peer comparison: {e}")

    return peer_comparison_data

# ===== MODULE 14: CONTACT MANAGEMENT DETAILS =====
def standardize_company_name(name):
    """
    Standardizes the company name:
    - 'Ltd.' -> 'Limited'
    - 'Pvt.' / 'Pvt' / 'PVR' -> 'Private'
    - '&' -> 'and'
    - Proper title casing
    """
    if not name:
        return ""

    # Replace abbreviations and symbols
    replacements = {
        r'\bPvt\.?\b': 'Private',
        r'\bPVR\.?\b': 'Private',
        r'\bLtd\.?\b': 'Limited',
        r'&': 'and'
    }

    for pattern, repl in replacements.items():
        name = re.sub(pattern, repl, name, flags=re.IGNORECASE)

    # Remove trailing punctuation and extra spaces
    name = re.sub(r'\s*\.\s*$', '', name)
    name = re.sub(r'\s+', ' ', name).strip()

    # Title case the full name
    return name.title()

def extract_company_address(card):
    """
    Extracts company address details from a card element.
    """
    result = {
        "name": "",
        "address": "",
        "website": "",
        "phone": "",
        "email": ""
    }
    
    try:
        body = card.find("div", class_="card-body")
        if not body:
            return result
            
        children = list(body.children)

        # Find first strong tag (company name)
        name = None
        start_index = 0
        for i, child in enumerate(children):
            if getattr(child, "name", None) == "strong":
                name = clean_text(child.get_text(strip=True))
                start_index = i + 1
                break
        
        if name:
            result["name"] = name

        # Collect address parts until next <strong> tag
        address_parts = []
        for child in children[start_index:]:
            if getattr(child, "name", None) == "strong":
                break
            text = ''
            if isinstance(child, str):
                text = child.strip()
            else:
                text = clean_text(child.get_text(strip=True))
            if text:
                address_parts.append(text)

        result["address"] = ', '.join(address_parts).replace(",,", ",")

        # Parse labels after address (Website, Phone, Email)
        strongs_after = [c for c in children if getattr(c, "name", None) == "strong"][1:]  # exclude first

        for strong_tag in strongs_after:
            label = clean_text(strong_tag.get_text(strip=True)).lower()
            # Get the next sibling text/value
            next_node = strong_tag.next_sibling
            while next_node and (isinstance(next_node, str) and not next_node.strip()):
                next_node = next_node.next_sibling
            
            value = ''
            if next_node:
                if isinstance(next_node, str):
                    value = clean_text(next_node.strip())
                else:
                    value = clean_text(next_node.get_text(strip=True))

            if "website" in label:
                result["website"] = value
            elif "phone" in label:
                result["phone"] = value
            elif "email" in label:
                result["email"] = value

    except Exception as e:
        logger.warning(f"Error extracting company address: {e}")

    return result

def extract_ipo_registrar(card):
    """
    Extracts IPO registrar details from a card element.
    Uses same structure as company address.
    """
    return extract_company_address(card)

def extract_ipo_lead_manager(card):
    """
    Extracts IPO lead manager list from a card element.
    """
    try:
        body = card.find("div", class_="card-body")
        if not body:
            return []
            
        ol = body.find("ol")
        if ol:
            return [clean_text(li.get_text(strip=True)) for li in ol.find_all("li")]
        
        # If no ordered list, try to find list items directly
        ul = body.find("ul")
        if ul:
            return [clean_text(li.get_text(strip=True)) for li in ul.find_all("li")]
        
        return []
        
    except Exception as e:
        logger.warning(f"Error extracting lead manager: {e}")
        return []

def extract_contact_management_details(soup):
    """
    Extracts contact and management details from the IPO detail page.
    Adds 'company_full_name' and 'company_full_name_new' fields.
    """
    data = {
        "company_address": {},
        "ipo_registrar": {},
        "ipo_lead_manager": []
    }

    try:
        cards = soup.find_all("div", class_="card")

        for card in cards:
            h3 = card.find("h3")
            if not h3:
                continue

            heading = clean_text(h3.get_text(strip=True))

            if "Company Address" in heading:
                data["company_address"] = extract_company_address(card)
            elif "Registrar" in heading:
                data["ipo_registrar"] = extract_ipo_registrar(card)
            elif "Lead Manager" in heading:
                data["ipo_lead_manager"] = extract_ipo_lead_manager(card)

        # Add company_full_name and formatted version
        company_name = data["company_address"].get("name")
        if company_name:
            data["company_full_name"] = company_name
            data["company_full_name_new"] = standardize_company_name(company_name)

    except Exception as e:
        logger.warning(f"Error extracting contact management details: {e}")

    return data

# ===== MODULE 15: LAST UPDATED TIMESTAMP =====
def extract_last_updated(soup):
    """
    Extracts the last updated timestamp from the IPO detail page.
    Based on 15_get_last_updated.py logic.
    """
    try:
        # Method 1: Primary method - search in row/col-12 structure
        row_divs = soup.find_all("div", class_="row")
        for row in row_divs:
            col_div = row.find("div", class_="col-12")
            if col_div:
                p_tag = col_div.find("p")
                if p_tag and "Last Updated on" in p_tag.get_text():
                    timestamp = clean_text(p_tag.get_text(strip=True).replace("Last Updated on", "").strip())
                    if timestamp:
                        return timestamp

        # Method 2: Fallback search anywhere in <p> tags
        for p in soup.find_all("p"):
            text = clean_text(p.get_text(strip=True))
            if "Last Updated on" in text:
                timestamp = text.replace("Last Updated on", "").strip()
                if timestamp:
                    return timestamp

        # Method 3: Last fallback - look for exact datetime format pattern
        import re
        match = re.search(r"\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}", soup.get_text())
        if match:
            return match.group(0)

        return "N/A"
        
    except Exception as e:
        logger.warning(f"Error extracting last updated: {e}")
        return "N/A"

# ===== MODULE 16: Company Sector Information =====
def extract_company_sector_info(soup):
    """
    Extract company sector information including Incorporation, Sector, IPO Issue Size, Website.
    Based on get_companysite_sec.py logic.
    """
    sector_info = {
        "Incorporation": "N/A",
        "Sector": "N/A", 
        "IPO Issue Size": "N/A",
        "Website": "N/A"
    }
    
    try:
        expected_keys = {"Incorporation", "Sector", "IPO Issue Size", "Website"}
        
        # Find all tables in the page
        tables = soup.find_all('table')
        
        for table in tables:
            thead = table.find('thead')
            tbody = table.find('tbody')
            
            if not thead or not tbody:
                continue
            
            header_cells = thead.find_all(['th', 'td'])
            headers_text = [clean_text(cell.get_text()) for cell in header_cells]
            
            # Check if at least one expected key is present in headers
            if not any(key in headers_text for key in expected_keys):
                continue
            
            # Extract first data row in tbody
            data_row = tbody.find('tr')
            if not data_row:
                continue
            
            data_cells = data_row.find_all('td')
            if len(data_cells) != len(headers_text):
                continue
            
            for header, cell in zip(headers_text, data_cells):
                if header in expected_keys:
                    link = cell.find('a')
                    value = link.get('href') if link and link.has_attr('href') else clean_text(cell.get_text())
                    
                    if value and value != "N/A":
                        sector_info[header] = value
            
            # If we found any real data (not just "N/A"), we can stop searching further
            if any(value != "N/A" for value in sector_info.values()):
                break
        
        # Optional: fallback heuristics can be kept here if needed
        
        return sector_info
        
    except Exception as e:
        # You may want to log the exception here for debugging
        return sector_info

# ===== MODULE 17: IPO Table Details =====
def extract_ipo_table_details(soup):
    """
    Extract detailed IPO issue information from the main table on an IPO detail page.
    Based on scrap_ipo_table_details.py logic.
    """
    
    # Define patterns for mapping scraped labels to desired output keys
    detail_field_patterns_map = {
        "IPO Issue Opening Date": re.compile(r'Issue Opening Date', re.IGNORECASE),
        "IPO Issue Closing Date": re.compile(r'Issue Closing Date', re.IGNORECASE),
        "IPO Issue Price": re.compile(r'Issue Price', re.IGNORECASE),
        "DRHP Link": re.compile(r'DRHP', re.IGNORECASE),
        "RHP Link": re.compile(r'RHP', re.IGNORECASE),
        "Anchor List Link": re.compile(r'Anchor List', re.IGNORECASE),
        "Listing At": re.compile(r'Listing At|Listing On', re.IGNORECASE),
        "Retail Quota": re.compile(r'Retail Quota|Retail Allotment %', re.IGNORECASE),
        "IPO Issue Type": re.compile(r'Issue Type', re.IGNORECASE),
        "IPO Issue Size (Cr)": re.compile(r'Issue Size', re.IGNORECASE),
        "Fresh Issue (Cr)": re.compile(r'Fresh Issue', re.IGNORECASE),
        "Face Value": re.compile(r'Face Value', re.IGNORECASE),
        "Promoter Holding Pre IPO (%)": re.compile(r'Promoter Holding Pre IPO', re.IGNORECASE),
        "Promoter Holding Post IPO (%)": re.compile(r'Promoter Holding Post IPO', re.IGNORECASE),
        "Min Order Quantity (Table)": re.compile(r'Min Order Quantity|Min Application', re.IGNORECASE),
        "Lot Size (Table)": re.compile(r'Market Lot|Lot Size', re.IGNORECASE),
        "Allotment Status": re.compile(r'Allotment Status', re.IGNORECASE),
    }
    
    issue_details_data = {}
    
    try:
        # Find the main table with IPO details using its distinctive classes
        main_details_table = soup.find('table', class_='table table-bordered table-striped table-hover w-auto')
        
        if main_details_table:
            
            for row in main_details_table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label_element = cells[0]
                    value_element = cells[1]

                    label_text = clean_text(label_element.get_text(strip=True))
                    value = 'N/A'

                    # 1. Prioritize 'data-title' for dates (as some dates might be hidden in text)
                    if 'data-title' in value_element.attrs and \
                       any(re.search(pattern, label_text) for pattern in [r'Issue Opening Date', r'Issue Closing Date']):
                        value = clean_text(value_element['data-title'])
                    else:
                        # 2. Check for any link within the value element
                        found_link_element = value_element.find('a', href=True)
                        if found_link_element:
                            link_href = found_link_element['href']
                            # If it's a relative URL, make it absolute
                            if link_href.startswith('/'):
                                value = f"https://www.investorgain.com{link_href}"
                            else:
                                value = link_href
                        else:
                            # 3. Fallback to get_text() if no specific pattern matched
                            value = clean_text(value_element.get_text(strip=True))
                    
                    # Ensure that if value is an empty string after cleaning, it defaults to 'N/A'
                    if not value and value != '':
                        value = 'N/A'

                    # Match the scraped label text against our patterns
                    for output_key, pattern in detail_field_patterns_map.items():
                        if pattern.search(label_text):
                            issue_details_data[output_key] = value
                            break  # Move to the next row once a match is found for this row
        else:
            logger.warning("No main IPO details table found on the page.")

        # Ensure all expected keys are present, even if N/A
        for key in detail_field_patterns_map.keys():
            if key not in issue_details_data:
                issue_details_data[key] = 'N/A'
        
        return issue_details_data
        
    except Exception as e:
        # Return default values for all expected keys
        return {key: 'N/A' for key in detail_field_patterns_map.keys()}

# ===== MAIN SCRAPING FUNCTION =====
def scrape_single_ipo_comprehensive(ipo_entry):
    """
    Scrapes complete data for a single IPO using all modules.
    Now enhanced to use the new API data structure.
    Automatically downloads logos by default.
    Returns comprehensive IPO data dictionary.
    """
    ipo_id = ipo_entry.get('ipoId')  # Updated to use new API field
    company_short_name = ipo_entry.get('apiCompanyName')  # Updated to use new API field
    url_rewrite_folder_name = ipo_entry.get('urlrewrite_folder_name')  # This might need to be extracted from apiUrl
    ipo_category = ipo_entry.get('apiIpoCategory')  # Updated to use new API field
    
    if not ipo_id:
        return None

    # Extract urlrewrite_folder_name from apiUrl if not directly available
    if not url_rewrite_folder_name:
        api_url = ipo_entry.get('apiUrl', '')
        if api_url:
            # Extract folder name from URL like: https://www.investorgain.com/gmp/vikram-solar-ipo/1377/
            match = re.search(r'/gmp/([^/]+)/\d+/?$', api_url)
            if match:
                url_rewrite_folder_name = match.group(1)
            else:
                # Fallback: try to construct from company name
                url_rewrite_folder_name = re.sub(r'[^a-zA-Z0-9\s-]', '', company_short_name).lower().replace(' ', '-')

    # Initialize comprehensive data with enhanced API information
    comprehensive_data = {
        'ipoId': ipo_id,
        "apiIpoStatus": ipo_entry.get('apiIpoStatus'),
        'apiCompanyName': company_short_name,
        'apiExchange': ipo_entry.get('apiExchange'),
        'apiIpoStatusFormatted': ipo_entry.get('apiIpoStatusFormatted'),
        'apiListedPrice': ipo_entry.get('apiListedPrice'),
        'apiListingGain': ipo_entry.get('apiListingGain'),
        'apiGmpValue': ipo_entry.get('apiGmpValue'),
        'apiGmpPercent': ipo_entry.get('apiGmpPercent'),
        'apiFireRating': ipo_entry.get('apiFireRating'),
        'apiFireRatingCount': ipo_entry.get('apiFireRatingCount'),
        'apiSubscription': ipo_entry.get('apiSubscription'),
        'apiPrice': ipo_entry.get('apiPrice'),
        'apiEstimatedListingPrice': ipo_entry.get('apiEstimatedListingPrice'),
        'apiEstimatedListingPercent': ipo_entry.get('apiEstimatedListingPercent'),
        'apiIssueSize': ipo_entry.get('apiIssueSize'),
        'apiLot': ipo_entry.get('apiLot'),
        'apiPe': ipo_entry.get('apiPe'),
        'apiIssueOpenDate': ipo_entry.get('apiIssueOpenDate'),
        'apiIssueCloseDate': ipo_entry.get('apiIssueCloseDate'),
        'apiBoaDate': ipo_entry.get('apiBoaDate'),
        'apiListingAt': ipo_entry.get('apiListingAt'),
        'apiUrl': ipo_entry.get('apiUrl'),
        'apiIpoCategory': ipo_category,
        'scrapingDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Construct detail page URL for additional scraping
    if url_rewrite_folder_name:
        detail_url = f"{BASE_URL}/ipo/{url_rewrite_folder_name}/{ipo_id}/"
        comprehensive_data['detailUrl'] = detail_url
    else:
        comprehensive_data['detailUrl'] = ipo_entry.get('apiUrl', 'N/A')
    
    try:
        # Always proceed with detailed scraping to get complete data structure
        # Fetch and parse detail page
        response = make_robust_request(detail_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # MODULE 01: Extract company name and logo
        name_logo_data = extract_company_name_and_logo(soup, BASE_URL)
        comprehensive_data.update(name_logo_data)
        
        # Download logo automatically (skip if already exists)
        local_logo_path = download_company_logo(
            name_logo_data.get('company_logo_url', 'N/A'),
            name_logo_data.get('scraped_company_name', company_short_name),
            ipo_id
        )
        comprehensive_data['localLogoPath'] = local_logo_path if local_logo_path else 'N/A'
        
        # MODULE 02: Extract IPO details, about company, and summary
        company_about_data = extract_company_about(soup)
        comprehensive_data.update(company_about_data)
        
        ipo_other_details = extract_ipo_other_details(soup)
        comprehensive_data.update(ipo_other_details)
        
        summary_block_details = extract_summary_block_details(soup)
        comprehensive_data.update(summary_block_details)
        
        # Add date status fields for Module 02 dates
        comprehensive_data = add_date_status_fields(comprehensive_data)
        
        # MODULE 03: Extract important dates
        important_dates_data = extract_ipo_important_dates(soup)
        comprehensive_data.update(important_dates_data)
        
        # Add date status fields for Module 03 dates
        comprehensive_data = add_important_dates_status_fields(comprehensive_data)
        
        # MODULE 04: Extract IPO lots data
        ipo_lots_data = extract_ipo_lots_data(soup)
        comprehensive_data.update(ipo_lots_data)
        
        # MODULE 05: Extract GMP data from API
        gmp_api_response = fetch_gmp_data_for_ipo(ipo_id)
        if gmp_api_response:
            # Parse latest GMP details
            latest_gmp_details = parse_gmp_api_data(gmp_api_response.get("ipoGmpData", []))
            comprehensive_data.update(latest_gmp_details)
            
            # Parse GMP trend table
            gmp_trend_table_data = parse_gmp_trend_table(gmp_api_response.get("ipoGmpTable", ""))
            comprehensive_data["GMP Trend History (Table)"] = gmp_trend_table_data
        else:
            # Add default GMP fields if API call fails
            default_gmp_fields = {
                "Seq": "N/A", "id (GMP Data)": "N/A", "ipo_id (GMP Data)": "N/A",
                "gmp_date": "N/A", "gmp": "N/A", "gmp_comments": "N/A", "gmp_compare_desc": "N/A",
                "subject_to_sauda": "N/A", "gmp_city": "N/A", "gmp_variation": "N/A",
                "max_ipo_price": "N/A", "estimated_listing_price": "N/A", "gmp_percent_calc": "N/A",
                "gmp_desc_other": "N/A", "up_down_status": "N/A", "gmp_active_record_flag": "N/A",
                "sub2": "N/A", "est_profit": "N/A", "create_date": "N/A", "create_date_gmp": "N/A",
                "last_updated_gmp": "N/A", "last_updated": "N/A", "GMP Trend History (Table)": []
            }
            comprehensive_data.update(default_gmp_fields)
        
        # MODULE 07: Extract IPO strengths
        ipo_strengths = extract_ipo_strengths(soup)
        comprehensive_data['strengths'] = ipo_strengths
        
        # MODULE 09: Extract IPO objectives 
        ipo_objectives = extract_ipo_objectives(soup)
        comprehensive_data['objectives'] = ipo_objectives
        
        # MODULE 10: Extract subscription data from API
        subscription_api_response = fetch_subscription_data_for_ipo(ipo_id)
        if subscription_api_response and 'data' in subscription_api_response:
            subscription_data = subscription_api_response['data']
            
            # Parse bidding history JSON
            bidding_history = parse_ipo_bidding_data_json(subscription_data.get("ipoBiddingData", []))
            comprehensive_data["IPO Bidding History (JSON)"] = bidding_history
            
            # Parse metadata
            comprehensive_data["metaTitle"] = clean_text(subscription_data.get("metaTitle", "N/A"))
            comprehensive_data["pageTitle"] = clean_text(subscription_data.get("pageTitle", "N/A"))
            comprehensive_data["metaDesc"] = clean_text(subscription_data.get("metaDesc", "N/A"))
            comprehensive_data["cacheKey"] = clean_text(subscription_data.get("cacheKey", "N/A"))
            comprehensive_data["currentTime"] = clean_text(subscription_data.get("currentTime", "N/A"))
            
            # Parse share allocation from HTML
            share_allocation = parse_ipo_share_allocation(subscription_data.get("listItemsHTML", ""))
            comprehensive_data["IPO Share Allocation"] = share_allocation
            
            # Parse daywise subscription table
            daywise_subscription = parse_ipo_daywise_subscription_table(subscription_data.get("sResultIPOBidding", ""))
            comprehensive_data["IPO Daywise Subscription (Table)"] = daywise_subscription
            
            # Parse shares bid amount table
            shares_bid_amount = parse_ipo_shares_bid_amount_table(subscription_data.get("biddingReport", ""))
            comprehensive_data["IPO Shares Bid Amount (Table)"] = shares_bid_amount
            
        else:
            # Add default subscription fields if API call fails
            comprehensive_data["IPO Bidding History (JSON)"] = []
            comprehensive_data["metaTitle"] = "N/A"
            comprehensive_data["pageTitle"] = "N/A"
            comprehensive_data["metaDesc"] = "N/A"
            comprehensive_data["cacheKey"] = "N/A"
            comprehensive_data["currentTime"] = "N/A"
            comprehensive_data["IPO Share Allocation"] = []
            comprehensive_data["IPO Daywise Subscription (Table)"] = []
            comprehensive_data["IPO Shares Bid Amount (Table)"] = []
        
        # Add scraped_at timestamp
        comprehensive_data["scraped_at"] = datetime.now().isoformat()
        
        # MODULE 12: Extract financial data
        financial_data = extract_financial_data(soup)
        comprehensive_data["Company Financial Information (Restated Consolidated)"] = financial_data
        
        # MODULE 13: Extract peer comparison data
        peer_comparison_data = extract_peer_comparison(soup)
        comprehensive_data["peer_comparison"] = peer_comparison_data
        
        # MODULE 14: Extract contact management details
        contact_details = extract_contact_management_details(soup)
        comprehensive_data.update(contact_details)
        
        # MODULE 15: Extract last updated timestamp
        last_updated = extract_last_updated(soup)
        comprehensive_data["last_updated"] = last_updated
        comprehensive_data["last_updated_timestamp"] = last_updated

        # MODULE 16: Extract company sector information
        sector_info = extract_company_sector_info(soup)
        comprehensive_data["company_sector_info"] = sector_info

        # MODULE 17: Extract IPO table details
        table_details = extract_ipo_table_details(soup)
        comprehensive_data.update(table_details)

        # ===== ALL MODULES COMPLETED =====
        #  MODULE 01: extract_company_name_and_logo() - COMPLETED
        #  MODULE 02: extract_company_about(), extract_ipo_other_details(), extract_summary_block_details() - COMPLETED
        #  MODULE 03: extract_ipo_important_dates() - COMPLETED
        #  MODULE 04: extract_ipo_lots_data(soup) - COMPLETED
        #  MODULE 05: fetch_gmp_data_for_ipo(ipo_id) - COMPLETED
        #  MODULE 07: extract_ipo_strengths(soup) - COMPLETED
        #  MODULE 09: extract_ipo_objectives(soup) - COMPLETED
        #  MODULE 10: fetch_subscription_data_for_ipo(ipo_id) - COMPLETED
        #  MODULE 12: extract_financial_data(soup) - COMPLETED
        #  MODULE 13: extract_peer_comparison(soup) - COMPLETED
        #  MODULE 14: extract_contact_management_details(soup) - COMPLETED
        #  MODULE 15: extract_last_updated(soup) - COMPLETED
        #  MODULE 16: extract_company_sector_info(soup) - COMPLETED
        #  MODULE 17: extract_ipo_table_details(soup) - COMPLETED
        
        # 🎉 COMPREHENSIVE IPO SCRAPER IS NOW COMPLETE WITH ENHANCED API INTEGRATION! 🎉
        # Now always runs all modules to get complete data structure
        
        return comprehensive_data
        
    except Exception as e:
        # Return basic data even on error
        comprehensive_data['scraping_error'] = str(e)
        return comprehensive_data

def scrape_all_ipo_data_comprehensive(max_workers=5, month=None, year=None, fin_year=None):
    """
    Main function to scrape comprehensive data for all IPOs.
    Now enhanced to use the new API with month/year parameters.
    Logos are automatically downloaded by default.
    
    Args:
        max_workers: Number of concurrent workers for processing
        month: Month for API call (1-12), defaults to current month
        year: Year for API call, defaults to current year
        fin_year: Financial year string (e.g., "2025-26"), defaults to current financial year
    """
    
    # Fetch IPO List from enhanced API with month/year parameters
    ipo_list = fetch_ipo_list_v2(month, year, fin_year)
    if not ipo_list:
        logger.error("No IPO data found in the enhanced API response.")
        return []

    all_comprehensive_data = []
    
    # Process IPOs with controlled concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks (logos are downloaded by default)
        future_to_ipo = {
            executor.submit(scrape_single_ipo_comprehensive, ipo_entry): ipo_entry 
            for ipo_entry in ipo_list
        }
        
        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_ipo), 1):
            ipo_entry = future_to_ipo[future]
            try:
                comprehensive_data = future.result()
                if comprehensive_data:
                    all_comprehensive_data.append(comprehensive_data)
                
                # Progress update
                if i % 5 == 0:
                    logger.info(f" Progress: {i}/{len(ipo_list)} IPOs processed ({i/len(ipo_list)*100:.1f}%)")

            except Exception as e:
                logger.error(f" Failed to process IPO {ipo_entry.get('apiCompanyName', 'Unknown')}: {e}")
                # Add error record
                error_data = {
                    'ipoId': ipo_entry.get('ipoId'),
                    'apiCompanyName': ipo_entry.get('apiCompanyName', 'N/A'),
                    'processing_error': str(e),
                    'scrapingDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                all_comprehensive_data.append(error_data)

    return all_comprehensive_data

def save_comprehensive_data(data, filename="comprehensive_ipo_data_new.json"):
    """
    Saves comprehensive IPO data to JSON file.
    """
    try:
        # Ensure output directory exists
        ensure_directory_exists(OUTPUT_DIR)
        
        # Full file path
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        
        # Show statistics
        successful_records = len([record for record in data if 'processing_error' not in record and 'scraping_error' not in record])
        
        if successful_records > 0:
            # Show sample data structure
            sample = data[0]
            for key, value in list(sample.items())[:10]:  # Show first 10 fields
                if isinstance(value, str) and len(value) > 100:
                    logger.info(f"  {key}: {value[:100]}...")
                else:
                    logger.info(f"  {key}: {value}")
            if len(sample) > 10:
                logger.info(f"  ... and {len(sample) - 10} more fields")

        return filepath
        
    except Exception as e:
        logger.error(f" Error saving data: {e}")
        return None

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    try:
        # Initialize controller
        controller = NSEInvestorGainIPOController()
        
        # Example 1: Scrape current month/year (default)
        logger.info("=== Example 1: Scraping current month/year ===")
        result = controller.scrape_investorgain_ipo_data()
        
        # Example 2: Scrape specific month/year
        logger.info("=== Example 2: Scraping specific month/year ===")
        # Uncomment the line below to scrape a specific month/year
        # result = controller.scrape_investorgain_ipo_data(month=8, year=2025, fin_year="2025-26")
        
        if result["success"]:
            logger.info(f"✅ {result['message']}")
            logger.info(f"📊 Data count: {result['data_count']}")
            logger.info(f"📅 Period: {result.get('month')}/{result.get('year')} (FY: {result.get('fin_year')})")
            if result.get("database_result"):
                db_result = result["database_result"]
                logger.info(f"🗄️ Database: {db_result.get('inserted_count', 0)} inserted, {db_result.get('updated_count', 0)} updated")
            if result.get("json_file_result"):
                json_result = result["json_file_result"]
                logger.info(f"📁 JSON file: {json_result.get('filepath', 'N/A')}")
        else:
            logger.error(f"❌ {result['message']}")

    except KeyboardInterrupt:
        logger.warning("\n🛑 Scraping interrupted by user")
    except Exception as e:
        logger.critical(f"💥 Critical error: {e}")
        import traceback
        traceback.print_exc()
