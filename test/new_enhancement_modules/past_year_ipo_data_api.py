"""
IPO Summary Data Scraper with Enhanced Features
This script fetches year-wise IPO summary data from investorgain.com API
and saves it to JSON files with proper status classification and user-friendly menu.
"""

import requests
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Try to import brotli for proper compression handling
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    print("⚠️  Brotli library not available. Installing it may improve compression handling.")
    print("   Run: pip install brotli")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_endpoint():
    """Test function to debug API endpoint issues"""
    test_url = "https://webnodejs.investorgain.com/cloud/report/data-read/394/1/8/2025/2025-26/0/all"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.investorgain.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }
    
    print(f"🔍 Testing API endpoint: {test_url}")
    
    try:
        response = requests.get(test_url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"Content-Encoding: {response.headers.get('content-encoding', 'None')}")
        print(f"Response Length: {len(response.content)} bytes")
        print(f"Response Text Length: {len(response.text)} chars")
        
        # Try to parse as JSON
        try:
            data = response.json()
            print("✅ JSON parsing successful!")
            print(f"Response structure: {type(data)}")
            
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                if 'reportTableData' in data:
                    records = data['reportTableData']
                    print(f"Found {len(records)} IPO records")
                    if records:
                        print("Sample record keys:", list(records[0].keys()))
                        print("Sample IPO name:", records[0].get('IPO', 'N/A'))
            elif isinstance(data, list):
                print(f"Found {len(data)} records in list format")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("Raw response preview (first 200 chars):")
            print("-" * 50)
            print(repr(response.text[:200]))
            print("-" * 50)
            
            # Try manual decompression
            try:
                import gzip
                print("🔧 Attempting manual gzip decompression...")
                if response.headers.get('content-encoding') == 'gzip':
                    decompressed = gzip.decompress(response.content)
                    decoded_text = decompressed.decode('utf-8')
                    data = json.loads(decoded_text)
                    print("✅ Manual decompression successful!")
                    print(f"Decompressed data type: {type(data)}")
                    if isinstance(data, dict) and 'reportTableData' in data:
                        print(f"Found {len(data['reportTableData'])} records after decompression")
            except Exception as decomp_err:
                print(f"❌ Manual decompression failed: {decomp_err}")
        
        # Test different URL variations with proper compression handling
        test_urls = [
            test_url + "?search=",
            "https://webnodejs.investorgain.com/cloud/report/data-read/394/1/8/2025/2024-25/0/all",
            "https://webnodejs.investorgain.com/cloud/report/data-read/394/1/12/2025/2024-25/0/all",
            "https://webnodejs.investorgain.com/cloud/report/data-read/394/1/8/2024/2024-25/0/all",
        ]
        
        print(f"\n🔍 Testing {len(test_urls)} URL variations...")
        for i, test_url_variant in enumerate(test_urls, 1):
            print(f"\n{i}. Testing: {test_url_variant}")
            try:
                response = requests.get(test_url_variant, headers=headers, timeout=30)
                print(f"   Status: {response.status_code}")
                print(f"   Encoding: {response.headers.get('content-encoding', 'None')}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and 'reportTableData' in data:
                            print(f"   ✅ SUCCESS: Found {len(data['reportTableData'])} records")
                        else:
                            print(f"   ⚠️  Unexpected format: {type(data)}")
                    except json.JSONDecodeError:
                        print(f"   ❌ JSON decode failed")
                        
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")

class IPOSummaryScraper:
    """Scraper for IPO summary data from investorgain.com"""
    
    def __init__(self):
        self.base_url_template = "https://webnodejs.investorgain.com/cloud/report/data-read/394/1/{month}/{year}/2025-26/0/all"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.investorgain.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        
        # Create data directory if it doesn't exist
        self.data_dir = "ipo_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Created data directory: {self.data_dir}")

    def extract_status_info(self, status_html: str) -> Dict[str, Optional[str]]:
        """Extract status, list price, and list gain from status HTML"""
        status_info = {
            'status': None,
            'list_price': None,
            'list_gain': None
        }
        
        if not status_html:
            return status_info
            
        # Clean HTML and extract text
        clean_status = re.sub(r'<[^>]+>', '', status_html).strip()
        
        # Determine status
        if 'Upcoming' in status_html:
            status_info['status'] = 'Upcoming'
        elif 'Open' in status_html:
            status_info['status'] = 'Open'
        elif 'Closing Today' in status_html:
            status_info['status'] = 'Closing Today'
        elif 'Close' in status_html:
            status_info['status'] = 'Close'
        elif 'L@' in status_html:
            status_info['status'] = 'Listed'
            
            # Extract listing price and gain
            # Pattern: L@2500 (66.33%)
            listing_pattern = r'L@([\d.]+)\s*\(([^)]+)\)'
            match = re.search(listing_pattern, clean_status)
            if match:
                status_info['list_price'] = float(match.group(1))
                status_info['list_gain'] = match.group(2).strip()
        
        return status_info
    
    def extract_rating_info(self, rating_html: str) -> Dict[str, Optional[float | str]]:
        """Extract rating text (e.g., 'Rated 3.5 stars') and numeric value from rating HTML img tag."""
        result: Dict[str, Optional[float | str]] = {'rating_text': None, 'rating_value': None}
        if not rating_html:
            return result
        try:
            # Prefer alt/title attribute text if present
            alt_title_match = re.search(r"(?:alt|title)\s*=\s*['\"]([^'\"]+)['\"]", rating_html)
            if alt_title_match:
                rating_text = alt_title_match.group(1).strip()
                result['rating_text'] = rating_text
                num_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", rating_text)
                if num_match:
                    result['rating_value'] = float(num_match.group(1))
            # Fallback: parse from filename like /starimages/3.5.gif
            if result['rating_value'] is None:
                file_match = re.search(r"/starimages/([0-9]+(?:\.[0-9]+)?)\\.gif", rating_html)
                if file_match:
                    result['rating_value'] = float(file_match.group(1))
            return result
        except Exception as e:
            logger.debug(f"Error extracting rating from html: {e}")
            return result

    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to standard format YYYY-MM-DD"""
        if not date_str or date_str.strip() == '':
            return None
        
        try:
            # Handle formats like "3-Jul-25", "21-Oct-24"
            if '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    day = parts[0].zfill(2)
                    month_str = parts[1]
                    year = parts[2]
                    
                    # Convert year to full year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    
                    # Convert month name to number
                    months = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    
                    month = months.get(month_str, '01')
                    return f"{year}-{month}-{day}"
            
            return None
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None

    def clean_text(self, text) -> str:
        """Clean text by removing HTML entities and extra whitespace. Accepts any type and returns string."""
        if text is None:
            return ""
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                return ""
        
        # Replace HTML entities first
        text = text.replace('&#8377;', '₹')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Remove Unicode currency symbols for cleaner data storage
        text = text.replace('\u20b9', '')
        text = text.replace('₹', '')
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def process_ipo_record(self, record: Dict, year: int) -> Dict:
        """Process a single IPO record from API response"""
        # Extract status information
        status_info = self.extract_status_info(record.get('Status', ''))
        # Extract rating
        rating_info = self.extract_rating_info(record.get('~Rating', ''))
        
        # Process the record
        # Calculate fire rating emoji string based on rating count
        fire_count = int(rating_info['rating_value']) if rating_info['rating_value'] else 0
        fire_emoji = "🔥" * fire_count if fire_count > 0 else None

        processed_record = {
            "ipoId": int(record.get('~id', 0)) if record.get('~id') else None,
            "apiCompanyName": self.clean_text(record.get('IPO', '')),
            "apiExchange": None,
            "apiBoard": None,
            "apiIpoStatus": (
            "U" if status_info['status'] == "Upcoming"
            else "O" if status_info['status'] == "Open"
            else "C" if status_info['status'] in ["Close", "Closing Today"]
            else "L" if status_info['status'] == "Listed"
            else None
            ),
            "apiIpoStatusFormatted": status_info['status'],
            "apiListedPrice": status_info['list_price'],
            "apiListingGain": status_info['list_gain'],
            "apiGmpValue": None,
            "apiGmpPercent": None,
            "apiFireRating": fire_emoji,
            "apiFireRatingCount": fire_count if fire_count > 0 else None,
            "apiSubscription": "",
            "apiPrice": (
            float(self.clean_text(record.get('IPO Price', '')))
            if self.clean_text(record.get('IPO Price', '')).replace('.', '', 1).isdigit()
            else None
            ),
            "apiEstimatedListingPrice": None,
            "apiEstimatedListingPercent": None,
            "apiIssueSize": f"₹{self.clean_text(record.get('IPO Size', ''))}" if self.clean_text(record.get('IPO Size', '')) else None,
            "apiLot": self.clean_text(record.get('Lot', '')),
            "apiPe": (
            float(self.clean_text(record.get('P/E', '')))
            if self.clean_text(record.get('P/E', '')).replace('.', '', 1).isdigit()
            else None
            ),
            "apiIssueOpenDate": self.parse_date(record.get('Open', '')),
            "apiIssueCloseDate": self.parse_date(record.get('Close', '')),
            "apiBoaDate": self.parse_date(record.get('BoA Dt', '')),
            "apiListingDate": self.parse_date(record.get('Listing', '')),
            "apiUrl": (
            f"https://www.investorgain.com/gmp/{record.get('~URLRewrite_Folder_Name', '')}/{record.get('~id', '')}/"
            if record.get('~URLRewrite_Folder_Name') and record.get('~id') else None
            ),
            "apiIpoCategory": self.clean_text(record.get('~IPO_Category', '')),
            "apiIpoYear": year
        }
        
        return processed_record
    
    def fetch_year_data(self, year: int) -> List[Dict]:
        """Fetch IPO data for a specific year, using current month dynamically"""
        current_month = datetime.now().month  # Gets the current month
        url = self.base_url_template.format(month=current_month, year=year)
        url += "?search="  # Empty search parameter
        
        try:
            logger.info(f"Fetching data for year {year} (using month {current_month}) from: {url}")
            
            # Create a session and explicitly handle compression
            session = requests.Session()
            
            # Update headers to properly handle compression
            headers = self.headers.copy()
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Debug: Log response details
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response content-encoding: {response.headers.get('content-encoding', 'None')}")
            logger.debug(f"Response content type: {response.headers.get('content-type', 'Unknown')}")
            logger.debug(f"Response content length: {len(response.content)}")
            
            # Check if response is compressed
            content_encoding = response.headers.get('content-encoding', '').lower()
            if content_encoding in ['gzip', 'deflate', 'br']:
                logger.info(f"Response is compressed with: {content_encoding}")
            
            # Handle different compression types properly
            try:
                # First try the normal way (requests should auto-decompress)
                data = response.json()
                logger.info(f"Successfully parsed JSON response for year {year}")
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON decode error for year {year}: {json_err}")
                
                # Try to manually handle the response based on compression type
                try:
                    content_encoding = response.headers.get('content-encoding', '').lower()
                    logger.info(f"Attempting manual decompression for encoding: {content_encoding}")
                    
                    if content_encoding == 'br' and BROTLI_AVAILABLE:
                        # Handle Brotli compression
                        logger.info("Attempting manual Brotli decompression...")
                        decompressed = brotli.decompress(response.content)
                        data = json.loads(decompressed.decode('utf-8'))
                        logger.info("Manual Brotli decompression successful!")
                        
                    elif content_encoding == 'gzip':
                        # Handle gzip compression
                        import gzip
                        logger.info("Attempting manual gzip decompression...")
                        decompressed = gzip.decompress(response.content)
                        data = json.loads(decompressed.decode('utf-8'))
                        logger.info("Manual gzip decompression successful!")
                        
                    elif content_encoding == 'deflate':
                        # Handle deflate compression
                        import zlib
                        logger.info("Attempting manual deflate decompression...")
                        decompressed = zlib.decompress(response.content)
                        data = json.loads(decompressed.decode('utf-8'))
                        logger.info("Manual deflate decompression successful!")
                        
                    else:
                        # Try different text encodings for uncompressed content
                        logger.info("Trying different text encodings...")
                        for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                            try:
                                text_content = response.content.decode(encoding)
                                data = json.loads(text_content)
                                logger.info(f"Successfully parsed with encoding: {encoding}")
                                break
                            except (UnicodeDecodeError, json.JSONDecodeError):
                                continue
                        else:
                            raise json_err
                            
                except Exception as manual_err:
                    logger.error(f"Manual decompression failed: {manual_err}")
                    
                    # Try alternative URL patterns
                    logger.info("Trying alternative URL patterns...")
                    alternative_urls = [
                        self.base_url_template.format(month=current_month, year=year),  # Without ?search=
                        f"https://webnodejs.investorgain.com/cloud/report/data-read/394/1/{current_month}/{year}/2024-25/0/all",  # Different financial year
                        f"https://webnodejs.investorgain.com/cloud/report/data-read/394/1/12/{year}/2024-25/0/all",  # Use December
                    ]
                    
                    for alt_url in alternative_urls:
                        try:
                            logger.info(f"Trying alternative URL: {alt_url}")
                            alt_response = session.get(alt_url, headers=headers, timeout=30)
                            alt_response.raise_for_status()
                            data = alt_response.json()
                            logger.info(f"Success with alternative URL: {alt_url}")
                            break
                        except Exception as alt_err:
                            logger.debug(f"Alternative URL failed: {alt_err}")
                            continue
                    else:
                        # If all alternatives failed
                        logger.error("All URL alternatives failed")
                        return []
            
            # Check if response has the expected structure
            if isinstance(data, dict) and 'reportTableData' in data:
                records = data['reportTableData']
                total_records = data.get('totalRecords', len(records))
                logger.info(f"Found {len(records)} IPO records for year {year} (total: {total_records})")
                return records
            elif isinstance(data, list):
                logger.info(f"Found {len(data)} IPO records for year {year}")
                return data
            else:
                logger.warning(f"Unexpected response format for year {year}: {type(data)}")
                if isinstance(data, dict):
                    logger.warning(f"Response keys: {list(data.keys())}")
                    if 'msg' in data:
                        logger.info(f"API message: {data.get('msg')}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching data for year {year}: {e}")
            return []
    
    def save_to_json(self, data: List[Dict], filename: str) -> bool:
        """Save processed data to JSON file"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            
            # Prepare metadata
            metadata = {
                'scraped_at': datetime.now().isoformat(),
                'total_records': len(data),
                'years_covered': list(set([record['apiIpoYear'] for record in data])),
                'status_breakdown': {}
            }
            
            # Calculate status breakdown
            for record in data:
                status = record.get('status', 'Unknown')
                metadata['status_breakdown'][status] = metadata['status_breakdown'].get(status, 0) + 1
            
            # Create final structure
            json_data = {
                'metadata': metadata,
                'ipo_data': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Data saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving data to JSON: {e}")
            return False
    
    def scrape_year(self, year: int) -> tuple[int, List[Dict]]:
        """Scrape and process IPO data for a specific year"""
        logger.info(f"Starting scrape for year {year}")
        
        # Fetch data
        raw_data = self.fetch_year_data(year)
        if not raw_data:
            logger.warning(f"No data found for year {year}")
            return 0, []
        
        # Process data
        processed_data = []
        saved_count = 0
        
        for record in raw_data:
            try:
                processed_record = self.process_ipo_record(record, year)
                
                # Skip if essential data is missing
                if not processed_record['ipoId'] or not processed_record['apiCompanyName']:
                    logger.warning(f"Skipping record with missing essential data: {record}")
                    continue
                
                processed_data.append(processed_record)
                saved_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing record for year {year}: {e}")
                logger.debug(f"Problematic record: {record}")
        
        logger.info(f"Processed {saved_count} records for year {year}")
        return saved_count, processed_data
    
    def scrape_multiple_years(self, years: List[int]) -> Dict[int, int]:
        """Scrape IPO data for multiple years"""
        results = {}
        all_data = []
        total_saved = 0
        
        try:
            for year in years:
                saved_count, year_data = self.scrape_year(year)
                results[year] = saved_count
                total_saved += saved_count
                all_data.extend(year_data)
                
                # Save individual year data
                if year_data:
                    filename = f"ipo_data_{year}.json"
                    self.save_to_json(year_data, filename)
                
                logger.info(f"Completed year {year}: {saved_count} records processed")
            
            # Save combined data if multiple years
            if len(years) > 1 and all_data:
                years_str = "_".join(map(str, sorted(years)))
                filename = f"ipo_data_combined_{years_str}.json"
                self.save_to_json(all_data, filename)
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        
        logger.info(f"Scraping completed. Total records processed: {total_saved}")
        logger.info(f"Results by year: {results}")
        
        return results

def display_menu():
    """Display the main menu options"""
    print("\n" + "="*60)
    print("🚀 IPO SUMMARY DATA SCRAPER")
    print("="*60)
    print("1. 📊 Scrape All Years Data (2019-2025)")
    print("2. 🆕 Scrape Recent Year (2025)")
    print("3. 📅 Scrape Specific Year")
    print("4. 📈 Scrape Year 2024")
    print("5. 📋 Scrape Multiple Custom Years")
    print("6. 📂 View Saved Files")
    print("7. 🔍 Test API Endpoints (Debug)")
    print("8. ❌ Exit")
    print("="*60)

def get_user_choice():
    """Get and validate user choice"""
    while True:
        try:
            choice = input("\n👉 Enter your choice (1-8): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
                return int(choice)
            else:
                print("❌ Invalid choice. Please enter a number between 1-8.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def get_custom_year():
    """Get custom year from user"""
    while True:
        try:
            year = input("📅 Enter the year (2019-2025): ").strip()
            year_int = int(year)
            if 2019 <= year_int <= 2025:
                return year_int
            else:
                print("❌ Please enter a year between 2019 and 2025.")
        except ValueError:
            print("❌ Invalid input. Please enter a valid year.")

def get_multiple_years():
    """Get multiple years from user"""
    print("📅 Enter multiple years separated by commas (e.g., 2023,2024,2025)")
    while True:
        try:
            years_input = input("Years: ").strip()
            years = [int(year.strip()) for year in years_input.split(',')]
            
            # Validate years
            invalid_years = [year for year in years if year < 2019 or year > 2025]
            if invalid_years:
                print(f"❌ Invalid years: {invalid_years}. Please use years between 2019-2025.")
                continue
            
            # Remove duplicates and sort
            years = sorted(list(set(years)))
            return years
            
        except ValueError:
            print("❌ Invalid input. Please enter years separated by commas (e.g., 2023,2024,2025).")

def view_saved_files():
    """Display saved JSON files"""
    data_dir = "ipo_data"
    if not os.path.exists(data_dir):
        print("📁 No data directory found. Please scrape some data first.")
        return
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    if not files:
        print("📁 No JSON files found in the data directory.")
        return
    
    print("\n📂 Saved IPO Data Files:")
    print("-" * 50)
    for i, file in enumerate(sorted(files), 1):
        filepath = os.path.join(data_dir, file)
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        print(f"{i}. {file}")
        print(f"   Size: {file_size_mb:.2f} MB | Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("-" * 50)

def display_results(results: Dict[int, int]):
    """Display scraping results in a formatted way"""
    print("\n" + "="*60)
    print("📊 IPO SCRAPING RESULTS")
    print("="*60)
    
    if not results:
        print("❌ No data was scraped.")
        return
    
    total_records = 0
    for year, count in sorted(results.items()):
        status = "✅" if count > 0 else "❌"
        print(f"{status} Year {year}: {count:,} records")
        total_records += count
    
    print("-" * 60)
    print(f"🎯 Total Records Scraped: {total_records:,}")
    print(f"📁 Data saved in: ./ipo_data/")
    print("="*60)

def main():
    """Main function with interactive menu"""
    scraper = IPOSummaryScraper()
    
    print("🎉 Welcome to IPO Summary Data Scraper!")
    
    while True:
        display_menu()
        choice = get_user_choice()
        
        if choice == 1:
            # Scrape all years
            print("\n🚀 Starting to scrape all years data (2019-2025)...")
            years = [2025, 2024, 2023, 2022, 2021, 2020, 2019]
            results = scraper.scrape_multiple_years(years)
            display_results(results)
            
        elif choice == 2:
            # Scrape recent year 2025
            print("\n🆕 Scraping recent year data (2025)...")
            results = scraper.scrape_multiple_years([2025])
            display_results(results)
            
        elif choice == 3:
            # Scrape specific year
            year = get_custom_year()
            print(f"\n📅 Scraping data for year {year}...")
            results = scraper.scrape_multiple_years([year])
            display_results(results)
            
        elif choice == 4:
            # Scrape year 2024
            print("\n📈 Scraping year 2024 data...")
            results = scraper.scrape_multiple_years([2024])
            display_results(results)
            
        elif choice == 5:
            # Scrape multiple custom years
            years = get_multiple_years()
            print(f"\n📋 Scraping data for years: {', '.join(map(str, years))}")
            results = scraper.scrape_multiple_years(years)
            display_results(results)
            
        elif choice == 6:
            # View saved files
            view_saved_files()
            
        elif choice == 7:
            # Test API endpoints
            print("\n🔍 Testing API endpoints for debugging...")
            test_api_endpoint()
            
        elif choice == 8:
            # Exit
            print("\n👋 Thank you for using IPO Summary Data Scraper!")
            print("🎯 All your data is saved in the './ipo_data/' directory.")
            break
        
        # Ask if user wants to continue
        if choice != 8:
            continue_choice = input("\n❓ Do you want to perform another operation? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("\n👋 Thank you for using IPO Summary Data Scraper!")
                print("🎯 All your data is saved in the './ipo_data/' directory.")
                break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        print("👋 Thank you for using IPO Summary Data Scraper!")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please check the logs for more details.")