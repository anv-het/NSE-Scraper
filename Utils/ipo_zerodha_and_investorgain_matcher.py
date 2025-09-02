"""
Ultimate IPO Matcher - Maximum Accuracy System
This script provides the most accurate IPO matching between Zerodha and InvestorGain data
with comprehensive analysis, multiple matching strategies, and detailed reporting.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
import logging
from typing import Dict, List, Tuple, Optional
import os
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateIPOMatcher:
    def __init__(self):
        self.zerodha_data = []
        self.investorgain_data = []
        self.matched_data = []
        self.unmatched_zerodha = []
        self.unmatched_investorgain = []
        self.manual_review_needed = []
        
        # Preprocess common name mappings for known variations
        self.name_mappings = {
            'mangal electrical industries': 'mangal electrical',
            'classic electrodes (india)': 'classic electrodes',
            'mahendra realtors & infrastructure': 'mahendra realtors infrastructure',
            'bluestone jewellery and lifestyle': 'bluestone jewellery lifestyle',
            # Add more mappings as needed
        }

    # ==================== ADVANCED NAME PROCESSING ====================
    def create_normalized_name(self, name: str) -> str:
        """Create a highly normalized version of the name for exact matching"""
        if not name:
            return ""
        
        # Apply manual mappings first
        name_lower = name.lower().strip()
        for key, value in self.name_mappings.items():
            if key in name_lower:
                name_lower = name_lower.replace(key, value)
        
        # Comprehensive cleaning
        normalized = re.sub(r'\b(ltd\.?|limited|pvt\.?|private|llp|ipo|inc\.?|corporation|corp\.?)\b', '', name_lower, flags=re.IGNORECASE)
        normalized = re.sub(r'\b(nse\s*sme|bse\s*sme|sme|bse|nse|nse bse|bse nse)\b', '', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\([^)]*\)', '', normalized)  # Remove parenthetical content
        normalized = re.sub(r'[&\-\.\,\'\"]', ' ', normalized)  # Replace special chars with spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize spaces
        normalized = re.sub(r'\.$', '', normalized).strip()  # Remove trailing dots
        
        return normalized

    def create_search_variants(self, name: str) -> List[str]:
        """Create comprehensive search variants for maximum matching potential"""
        variants = set()
        normalized = self.create_normalized_name(name)
        
        if not normalized:
            return []
        
        # Add normalized name
        variants.add(normalized)
        
        words = normalized.split()
        if not words:
            return list(variants)
        
        # Remove common business words
        common_words = {
            'technologies', 'technology', 'tech', 'systems', 'system', 'solutions', 'solution',
            'industries', 'industry', 'services', 'service', 'enterprises', 'enterprise',
            'international', 'global', 'india', 'indian', 'group', 'company', 'co', 'and',
            'the', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by'
        }
        
        # Core words (non-common words)
        core_words = [w for w in words if w not in common_words and len(w) > 2]
        
        if core_words:
            variants.add(' '.join(core_words))
            
            # First significant word
            variants.add(core_words[0])
            
            # Last significant word
            if len(core_words) > 1:
                variants.add(core_words[-1])
        
        # First two words combination
        if len(words) >= 2:
            variants.add(f"{words[0]} {words[1]}")
        
        # Acronym from all words
        if len(words) > 1:
            acronym = ''.join([w[0] for w in words if w and len(w) > 0])
            if len(acronym) > 1:
                variants.add(acronym)
        
        # Acronym from core words only
        if len(core_words) > 1:
            core_acronym = ''.join([w[0] for w in core_words])
            if len(core_acronym) > 1:
                variants.add(core_acronym)
        
        return [v for v in variants if v and len(v) > 1]

    # ==================== ENHANCED SIMILARITY CALCULATIONS ====================
    def calculate_exact_match_score(self, name1: str, name2: str) -> float:
        """Calculate exact match score"""
        n1 = self.create_normalized_name(name1)
        n2 = self.create_normalized_name(name2)
        
        if n1 == n2:
            return 1.0
        
        # Check if one is contained in the other
        if n1 and n2:
            if n1 in n2 or n2 in n1:
                return 0.9
        
        return 0.0

    def calculate_variant_match_score(self, name1: str, name2: str) -> float:
        """Calculate best match score using variants"""
        variants1 = self.create_search_variants(name1)
        variants2 = self.create_search_variants(name2)
        
        if not variants1 or not variants2:
            return 0.0
        
        max_score = 0.0
        
        # Exact variant matches
        for v1 in variants1:
            for v2 in variants2:
                if v1 == v2:
                    return 1.0
                
                # Partial matches
                if len(v1) > 3 and len(v2) > 3:
                    if v1 in v2 or v2 in v1:
                        score = min(len(v1), len(v2)) / max(len(v1), len(v2))
                        max_score = max(max_score, score * 0.8)
                
                # Similarity score
                sim = SequenceMatcher(None, v1, v2).ratio()
                max_score = max(max_score, sim * 0.7)
        
        return max_score

    def calculate_word_overlap_score(self, name1: str, name2: str) -> float:
        """Calculate word overlap score"""
        words1 = set(self.create_normalized_name(name1).split())
        words2 = set(self.create_normalized_name(name2).split())
        
        # Remove very short words
        words1 = {w for w in words1 if len(w) > 2}
        words2 = {w for w in words2 if len(w) > 2}
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def calculate_fuzzy_score(self, name1: str, name2: str) -> float:
        """Calculate fuzzy similarity score"""
        n1 = self.create_normalized_name(name1)
        n2 = self.create_normalized_name(name2)
        
        if not n1 or not n2:
            return 0.0
        
        return SequenceMatcher(None, n1, n2).ratio()

    # ==================== DATE AND PRICE VALIDATION ====================
    def calculate_date_validation_score(self, z_ipo: Dict, inv_ipo: Dict) -> float:
        """Validate dates between both sources"""
        try:
            score = 0.0
            
            # Get dates from both sources
            z_dates = z_ipo.get('ipo_open_close_date', '')
            z_listing = z_ipo.get('ipo_listing_date', '')
            
            inv_open = inv_ipo.get('~Issue_Open_Date', '')
            inv_close = inv_ipo.get('~IssueCloseDate', '')
            inv_listing = inv_ipo.get('~ListingDate', '')
            
            # Check opening dates
            if inv_open and z_dates:
                inv_open_date = datetime.strptime(inv_open, '%Y-%m-%d').date()
                # Extract month from Zerodha format
                month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', z_dates)
                if month_match:
                    month_name = month_match.group(1)
                    inv_month = inv_open_date.strftime('%b')
                    if month_name == inv_month:
                        score += 0.4
            
            # Check listing dates
            if inv_listing and z_listing and z_listing != '–':
                try:
                    inv_list_date = datetime.strptime(inv_listing, '%Y-%m-%d').date()
                    # Try to parse Zerodha listing date
                    z_list_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', z_listing)
                    z_list_date = datetime.strptime(z_list_clean, '%d %b %Y').date()
                    
                    if inv_list_date == z_list_date:
                        score += 0.6
                    elif abs((inv_list_date - z_list_date).days) <= 3:
                        score += 0.3
                except:
                    pass
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Date validation error: {e}")
            return 0.0

    def calculate_price_validation_score(self, z_ipo: Dict, inv_ipo: Dict) -> float:
        """Validate price ranges between both sources"""
        try:
            z_price = z_ipo.get('ipo_price_range', '').replace(',', '')
            inv_price = inv_ipo.get('Issue Price (Rs.)', '').replace(',', '')
            
            if not z_price or not inv_price or z_price == '–' or inv_price == '–':
                return 0.0
            
            # Extract numbers from both
            z_numbers = [float(x) for x in re.findall(r'\d+\.?\d*', z_price)]
            inv_numbers = [float(x) for x in re.findall(r'\d+\.?\d*', inv_price)]
            
            if not z_numbers or not inv_numbers:
                return 0.0
            
            # Check if any Zerodha price is close to InvestorGain price
            for z_price_val in z_numbers:
                for inv_price_val in inv_numbers:
                    diff_percent = abs(z_price_val - inv_price_val) / max(z_price_val, inv_price_val)
                    if diff_percent <= 0.05:  # Within 5%
                        return 1.0
                    elif diff_percent <= 0.15:  # Within 15%
                        return 0.7
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Price validation error: {e}")
            return 0.0

    # ==================== COMPREHENSIVE MATCHING ALGORITHM ====================
    def calculate_comprehensive_score(self, z_ipo: Dict, inv_ipo: Dict) -> Tuple[float, Dict]:
        """Calculate comprehensive matching score using all available methods"""
        z_name = z_ipo.get('name', '').strip()
        inv_name = inv_ipo.get('Company_Name', '').strip()
        
        if not z_name or not inv_name:
            return 0.0, {}
        
        # Calculate individual scores
        exact_score = self.calculate_exact_match_score(z_name, inv_name)
        variant_score = self.calculate_variant_match_score(z_name, inv_name)
        word_score = self.calculate_word_overlap_score(z_name, inv_name)
        fuzzy_score = self.calculate_fuzzy_score(z_name, inv_name)
        date_score = self.calculate_date_validation_score(z_ipo, inv_ipo)
        price_score = self.calculate_price_validation_score(z_ipo, inv_ipo)
        
        # Weighted calculation with emphasis on exact matches
        weights = {
            'exact': 0.30,     # Highest weight for exact matches
            'variant': 0.25,   # High weight for variant matches
            'word': 0.20,      # Word overlap
            'fuzzy': 0.15,     # Fuzzy similarity
            'date': 0.07,      # Date validation
            'price': 0.03      # Price validation
        }
        
        final_score = (
            exact_score * weights['exact'] +
            variant_score * weights['variant'] +
            word_score * weights['word'] +
            fuzzy_score * weights['fuzzy'] +
            date_score * weights['date'] +
            price_score * weights['price']
        )
        
        # Bonus for perfect exact matches
        if exact_score == 1.0:
            final_score = min(final_score + 0.1, 1.0)
        
        # Penalty if no significant word matches
        if word_score == 0.0 and variant_score < 0.3:
            final_score *= 0.5
        
        score_details = {
            'exact_score': round(exact_score, 3),
            'variant_score': round(variant_score, 3),
            'word_score': round(word_score, 3),
            'fuzzy_score': round(fuzzy_score, 3),
            'date_score': round(date_score, 3),
            'price_score': round(price_score, 3),
            'final_score': round(final_score, 3),
            'zerodha_variants': self.create_search_variants(z_name)[:3],  # Top 3 variants
            'investorgain_variants': self.create_search_variants(inv_name)[:3]
        }
        
        return final_score, score_details

    # ==================== ENHANCED SCRAPING (REUSING PREVIOUS METHODS) ====================
    def scrape_zerodha_ipos(self):
        """Scrape Zerodha IPOs with enhanced error handling"""
        logger.info("🔄 Scraping Zerodha IPOs...")
        url = "https://zerodha.com/ipo/"
        
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code != 200:
                logger.error(f"❌ Failed to retrieve Zerodha page. Status: {response.status_code}")
                return False

            soup = BeautifulSoup(response.text, 'html.parser')
            self.zerodha_data = []

            sections = [
                ('upcoming-ipo', 'upcoming'),
                ('live-ipo', 'current'),
                ('closed-ipo', 'closed')
            ]
            
            for section_id, status in sections:
                try:
                    self.parse_zerodha_section(soup, section_id, status)
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing {section_id}: {e}")

            logger.info(f"✅ Scraped {len(self.zerodha_data)} IPOs from Zerodha")
            return True

        except Exception as e:
            logger.error(f"❌ Error scraping Zerodha: {e}")
            return False

    def parse_zerodha_section(self, soup, section_id, default_status):
        """Parse Zerodha section with enhanced data extraction"""
        section = soup.find('div', id=section_id)
        if not section:
            return
        
        table = section.find('table')
        if not table:
            return
        
        rows = table.find_all('tr')[1:]
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 5:
                    continue
                
                symbol_elem = row.find('span', class_='ipo-symbol')
                name_elem = row.find('span', class_='ipo-name')
                
                if not symbol_elem or not name_elem:
                    continue
                
                symbol = symbol_elem.get_text(strip=True)
                name = name_elem.get_text(strip=True)
                
                ipo_dates = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                listing_date = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                price_range = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                
                price_range = price_range.replace("₹", "").strip()
                
                self.zerodha_data.append({
                    "name": name,
                    "symbol": symbol,
                    "ipo_open_close_date": ipo_dates,
                    "ipo_listing_date": listing_date,
                    "ipo_price_range": price_range,
                    "status": default_status
                })
                
            except Exception as e:
                logger.debug(f"Row parsing error: {e}")
                continue

    def scrape_investorgain_ipos(self):
        """Scrape InvestorGain IPOs with enhanced data processing"""
        logger.info("🔄 Scraping InvestorGain IPOs...")
        url = "https://webnodejs.investorgain.com/cloud/report/data-read/331/1/8/2025/2025-26/0/all?search=&v=10-49"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ Failed to retrieve InvestorGain data. Status: {response.status_code}")
                return False

            data = response.json()
            self.investorgain_data = []

            if "reportTableData" in data:
                for ipo in data["reportTableData"]:
                    try:
                        raw_name = self.clean_html_tags(ipo.get("Name", "").strip())
                        clean_name = self.create_normalized_name(ipo.get("~ipo_name", raw_name))

                        ipo_info = {
                            "Company": raw_name,
                            "Company_Name": clean_name,
                            "Opening Date": ipo.get("Open", "").strip(),
                            "Closing Date": ipo.get("Close", "").strip(),
                            "Listing Date": ipo.get("Listing", "").strip(),
                            "Issue Price (Rs.)": ipo.get("Price", "").strip(),
                            "Total Issue Amount (Rs.cr.)": ipo.get("IPO Size", "").replace("&#8377;", "").strip(),
                            "Lead Manager": ipo.get("Lead Manager", "").strip(),
                            "Listing at": ipo.get("Listing at", "").strip(),
                            "~Issue_Open_Date": ipo.get("~Srt_Open", "").strip(),
                            "~IssueCloseDate": ipo.get("~Srt_Close", "").strip(),
                            "~ListingDate": ipo.get("~Str_Listing", "").strip(),
                            "Status": self.determine_investorgain_status(ipo)
                        }

                        self.investorgain_data.append(ipo_info)
                        
                    except Exception as e:
                        logger.debug(f"InvestorGain IPO parsing error: {e}")
                        continue

            logger.info(f"✅ Scraped {len(self.investorgain_data)} IPOs from InvestorGain")
            return True

        except Exception as e:
            logger.error(f"❌ Error scraping InvestorGain: {e}")
            return False

    def clean_html_tags(self, text):
        """Remove HTML tags"""
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text)

    def clean_symbol(self, symbol):
        """Clean symbol by removing SME suffix and other unwanted suffixes"""
        if not symbol:
            return symbol
        
        # Remove SME suffix (case insensitive)
        cleaned = re.sub(r'SME$', '', symbol, flags=re.IGNORECASE)
        
        # Remove other common suffixes if needed
        # cleaned = re.sub(r'(NSE|BSE|LTD)$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()

    def determine_investorgain_status(self, ipo):
        """Determine status from InvestorGain data"""
        try:
            current_date = datetime.now().date()
            
            open_date = datetime.strptime(ipo.get("~Srt_Open", ""), "%Y-%m-%d").date() if ipo.get("~Srt_Open") else None
            close_date = datetime.strptime(ipo.get("~Srt_Close", ""), "%Y-%m-%d").date() if ipo.get("~Srt_Close") else None
            listing_date = datetime.strptime(ipo.get("~Str_Listing", ""), "%Y-%m-%d").date() if ipo.get("~Str_Listing") else None

            if listing_date and current_date >= listing_date:
                return "Listed"
            elif close_date and current_date > close_date:
                return "Closed"
            elif open_date and current_date >= open_date:
                return "Current"
            elif open_date and current_date < open_date:
                return "Upcoming"
            
            return "Unknown"
        except:
            return "Unknown"

    # ==================== ULTIMATE MATCHING ALGORITHM ====================
    def match_ipos_ultimate(self):
        """Ultimate IPO matching with maximum accuracy"""
        logger.info("🔄 Starting ultimate IPO matching...")
        
        self.matched_data = []
        used_investorgain = set()
        
        # Sort Zerodha IPOs by completeness (ones with dates/prices first)
        zerodha_sorted = sorted(self.zerodha_data, key=lambda x: (
            x.get('ipo_open_close_date', '') != 'To be announced',
            x.get('ipo_price_range', '') != '–',
            len(x.get('name', ''))
        ), reverse=True)
        
        # Phase 1: Perfect matches (>= 0.90)
        logger.info("Phase 1: Perfect matches (>= 0.90)")
        perfect_matches = 0
        for z_ipo in zerodha_sorted:
            if any(m['symbol'] == z_ipo.get('symbol') for m in self.matched_data):
                continue
                
            best_score = 0
            best_inv = None
            best_inv_idx = None
            best_details = {}
            
            for j, inv_ipo in enumerate(self.investorgain_data):
                if j in used_investorgain:
                    continue
                    
                score, details = self.calculate_comprehensive_score(z_ipo, inv_ipo)
                if score > best_score:
                    best_score = score
                    best_inv = inv_ipo
                    best_inv_idx = j
                    best_details = details
            
            if best_score >= 0.90 and best_inv:
                self.add_ultimate_match(z_ipo, best_inv, best_score, best_details, "Perfect")
                used_investorgain.add(best_inv_idx)
                perfect_matches += 1
        
        logger.info(f"Perfect matches: {perfect_matches}")
        
        # Phase 2: High confidence matches (0.75-0.89)
        logger.info("Phase 2: High confidence matches (0.75-0.89)")
        high_matches = 0
        for z_ipo in zerodha_sorted:
            if any(m['symbol'] == z_ipo.get('symbol') for m in self.matched_data):
                continue
                
            best_score = 0
            best_inv = None
            best_inv_idx = None
            best_details = {}
            
            for j, inv_ipo in enumerate(self.investorgain_data):
                if j in used_investorgain:
                    continue
                    
                score, details = self.calculate_comprehensive_score(z_ipo, inv_ipo)
                if score > best_score:
                    best_score = score
                    best_inv = inv_ipo
                    best_inv_idx = j
                    best_details = details
            
            if 0.75 <= best_score < 0.90 and best_inv:
                self.add_ultimate_match(z_ipo, best_inv, best_score, best_details, "High")
                used_investorgain.add(best_inv_idx)
                high_matches += 1
        
        logger.info(f"High confidence matches: {high_matches}")
        
        # Phase 3: Medium confidence matches (0.60-0.74)
        logger.info("Phase 3: Medium confidence matches (0.60-0.74)")
        medium_matches = 0
        for z_ipo in zerodha_sorted:
            if any(m['symbol'] == z_ipo.get('symbol') for m in self.matched_data):
                continue
                
            best_score = 0
            best_inv = None
            best_inv_idx = None
            best_details = {}
            
            for j, inv_ipo in enumerate(self.investorgain_data):
                if j in used_investorgain:
                    continue
                    
                score, details = self.calculate_comprehensive_score(z_ipo, inv_ipo)
                if score > best_score:
                    best_score = score
                    best_inv = inv_ipo
                    best_inv_idx = j
                    best_details = details
            
            if 0.60 <= best_score < 0.75 and best_inv:
                # Additional validation for medium confidence
                if best_details.get('word_score', 0) > 0.3 or best_details.get('variant_score', 0) > 0.5:
                    self.add_ultimate_match(z_ipo, best_inv, best_score, best_details, "Medium")
                    used_investorgain.add(best_inv_idx)
                    medium_matches += 1
                else:
                    # Add to manual review
                    self.manual_review_needed.append({
                        'zerodha_ipo': z_ipo,
                        'investorgain_ipo': best_inv,
                        'score': best_score,
                        'details': best_details,
                        'reason': 'Low word/variant match despite medium score'
                    })
        
        logger.info(f"Medium confidence matches: {medium_matches}")
        
        # Identify unmatched
        matched_symbols = {m['symbol'] for m in self.matched_data}
        self.unmatched_zerodha = [ipo for ipo in self.zerodha_data if ipo.get('symbol') not in matched_symbols]
        self.unmatched_investorgain = [ipo for i, ipo in enumerate(self.investorgain_data) if i not in used_investorgain]
        
        logger.info(f"✅ Total matched: {len(self.matched_data)}")
        logger.info(f"📊 Manual review needed: {len(self.manual_review_needed)}")
        logger.info(f"📊 Unmatched Zerodha: {len(self.unmatched_zerodha)}")
        logger.info(f"📊 Unmatched InvestorGain: {len(self.unmatched_investorgain)}")
        
        return len(self.matched_data)

    def add_ultimate_match(self, z_ipo: Dict, inv_ipo: Dict, score: float, details: Dict, confidence: str):
        """Add an ultimate matched IPO to results"""
        # Clean symbol by removing SME suffix
        original_symbol = z_ipo.get('symbol', '')
        cleaned_symbol = self.clean_symbol(original_symbol)
        
        match = {
            'symbol': cleaned_symbol,
            'original_symbol': original_symbol,
            'zerodha_status': z_ipo.get('status', ''),
            'zerodha_ipo_name': z_ipo.get('name', ''),
            'investorgain_ipo_name': inv_ipo.get('Company_Name', ''),
            'investorgain_status': inv_ipo.get('Status', ''),
            'confidence': confidence,
            'similarity_score': round(score, 3),
            'matching_details': details,
            'ipo_price_range': z_ipo.get('ipo_price_range', ''),
            'ipo_open_close_date': z_ipo.get('ipo_open_close_date', ''),
            'ipo_listing_date': z_ipo.get('ipo_listing_date', ''),
            'issue_amount': inv_ipo.get('Total Issue Amount (Rs.cr.)', ''),
            'lead_manager': inv_ipo.get('Lead Manager', ''),
            'listing_at': inv_ipo.get('Listing at', ''),
            'opening_date': inv_ipo.get('Opening Date', ''),
            'closing_date': inv_ipo.get('Closing Date', ''),
            'listing_date': inv_ipo.get('Listing Date', ''),
            'match_timestamp': datetime.now().isoformat()
        }
        self.matched_data.append(match)

    # ==================== SAVE ULTIMATE RESULTS ====================
    def save_ultimate_results(self, base_path=r'D:\scraping\NSE-Scrap\nse-scraper-new-git\NSE-Scraper\output'):
        """Save ultimate matching results with comprehensive analysis"""
        try:
            # Ensure output directory exists
            os.makedirs(base_path, exist_ok=True)

            # Final fixed file path
            final_file = os.path.join(base_path, 'zerodha_investorgain_matched_ipos.json')

            # # Timestamped backup file path
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # backup_file = os.path.join(base_path, f'ultimate_matched_ipos_{timestamp}.json')

            # Helper to write atomically
            def atomic_write(target_path):
                fd, tmp_path = tempfile.mkstemp(prefix='._ultimate_matched_ipos_', dir=base_path, text=True)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as tmpf:
                        json.dump(self.matched_data, tmpf, indent=4, ensure_ascii=False)
                    os.replace(tmp_path, target_path)
                finally:
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass

            # Remove older timestamped backups (keep only the latest one)
            for fname in os.listdir(base_path):
                if fname.startswith('ultimate_matched_ipos_') and fname.endswith('.json'):
                    try:
                        os.remove(os.path.join(base_path, fname))
                    except Exception:
                        pass

            # Write both fixed file and the new timestamped backup
            atomic_write(final_file)
            # atomic_write(backup_file)

            logger.info(f"💾 Ultimate matches saved to: {final_file}")
            # logger.info(f"💾 Backup saved to: {backup_file}")

            # # Save perfect + high confidence matches
            # reliable_matches = [m for m in self.matched_data if m['confidence'] in ['Perfect', 'High']]
            # reliable_file = f"{base_path}\\reliable_ipo_matches_{timestamp}.json"
            # with open(reliable_file, 'w', encoding='utf-8') as f:
            #     json.dump(reliable_matches, f, indent=4, ensure_ascii=False)
            # logger.info(f"💾 Reliable matches saved to: {reliable_file}")

            # # Save manual review cases
            # if self.manual_review_needed:
            #     review_file = f"{base_path}\\manual_review_needed_{timestamp}.json"
            #     with open(review_file, 'w', encoding='utf-8') as f:
            #         json.dump(self.manual_review_needed, f, indent=4, ensure_ascii=False)
            #     logger.info(f"💾 Manual review cases saved to: {review_file}")

            # # Save comprehensive analysis
            # analysis = self.generate_ultimate_analysis()
            # analysis_file = f"{base_path}\\ultimate_analysis_{timestamp}.json"
            # with open(analysis_file, 'w', encoding='utf-8') as f:
            #     json.dump(analysis, f, indent=4, ensure_ascii=False)
            # logger.info(f"💾 Ultimate analysis saved to: {analysis_file}")

            return True

        except Exception as e:
            logger.error(f"❌ Error saving ultimate results: {e}")
            return False

    def generate_ultimate_analysis(self):
        """Generate comprehensive analysis of matching results"""
        perfect_matches = [m for m in self.matched_data if m['confidence'] == 'Perfect']
        high_matches = [m for m in self.matched_data if m['confidence'] == 'High']
        medium_matches = [m for m in self.matched_data if m['confidence'] == 'Medium']
        
        # Calculate average scores by confidence level
        perfect_avg = sum(m['similarity_score'] for m in perfect_matches) / len(perfect_matches) if perfect_matches else 0
        high_avg = sum(m['similarity_score'] for m in high_matches) / len(high_matches) if high_matches else 0
        medium_avg = sum(m['similarity_score'] for m in medium_matches) / len(medium_matches) if medium_matches else 0
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_sources': {
                'zerodha_total': len(self.zerodha_data),
                'investorgain_total': len(self.investorgain_data)
            },
            'matching_results': {
                'total_matched': len(self.matched_data),
                'perfect_matches': len(perfect_matches),
                'high_confidence': len(high_matches),
                'medium_confidence': len(medium_matches),
                'manual_review_needed': len(self.manual_review_needed),
                'unmatched_zerodha': len(self.unmatched_zerodha),
                'unmatched_investorgain': len(self.unmatched_investorgain)
            },
            'quality_metrics': {
                'overall_match_rate': round(len(self.matched_data) / len(self.zerodha_data) * 100, 2) if self.zerodha_data else 0,
                'reliable_match_rate': round(len(reliable_matches := [m for m in self.matched_data if m['confidence'] in ['Perfect', 'High']]) / len(self.zerodha_data) * 100, 2) if self.zerodha_data else 0,
                'average_scores': {
                    'perfect_avg': round(perfect_avg, 3),
                    'high_avg': round(high_avg, 3),
                    'medium_avg': round(medium_avg, 3)
                }
            },
            'top_matches': [
                {
                    'symbol': m['symbol'],
                    'zerodha_name': m['zerodha_ipo_name'],
                    'investorgain_name': m['investorgain_ipo_name'],
                    'score': m['similarity_score'],
                    'confidence': m['confidence']
                }
                for m in sorted(self.matched_data, key=lambda x: x['similarity_score'], reverse=True)[:10]
            ],
            'unmatched_analysis': {
                'zerodha_unmatched_reasons': self.analyze_unmatched_zerodha(),
                'investorgain_unmatched_count': len(self.unmatched_investorgain)
            }
        }

    def analyze_unmatched_zerodha(self):
        """Analyze reasons why Zerodha IPOs weren't matched"""
        reasons = {}
        for ipo in self.unmatched_zerodha:
            if ipo.get('ipo_open_close_date') == 'To be announced':
                reasons.setdefault('no_dates_announced', []).append(ipo['name'])
            elif len(ipo.get('name', '')) < 5:
                reasons.setdefault('short_name', []).append(ipo['name'])
            else:
                reasons.setdefault('no_match_found', []).append(ipo['name'])
        
        return {k: len(v) for k, v in reasons.items()}

    # ==================== MAIN EXECUTION ====================
    def run_ultimate_matching(self):
        """Run the ultimate IPO matching process"""
        logger.info("🚀 Starting Ultimate IPO Matching Process...")
        logger.info("=" * 70)

        # Step 1: Scrape Zerodha
        if not self.scrape_zerodha_ipos():
            logger.error("❌ Failed to scrape Zerodha data")
            return False

        # Step 2: Scrape InvestorGain
        if not self.scrape_investorgain_ipos():
            logger.error("❌ Failed to scrape InvestorGain data")
            return False

        # Step 3: Ultimate matching
        matches = self.match_ipos_ultimate()
        if matches == 0:
            logger.warning("⚠️ No IPOs matched")

        # Step 4: Save ultimate results
        if not self.save_ultimate_results():
            logger.error("❌ Failed to save results")
            return False

        # Final summary
        analysis = self.generate_ultimate_analysis()
        
        logger.info("=" * 70)
        logger.info("🎉 Ultimate IPO matching process completed!")
        logger.info(f"📊 Ultimate Summary:")
        logger.info(f"   • Zerodha IPOs: {analysis['data_sources']['zerodha_total']}")
        logger.info(f"   • InvestorGain IPOs: {analysis['data_sources']['investorgain_total']}")
        logger.info(f"   • Total Matched: {analysis['matching_results']['total_matched']}")
        logger.info(f"   • Perfect Matches: {analysis['matching_results']['perfect_matches']}")
        logger.info(f"   • High Confidence: {analysis['matching_results']['high_confidence']}")
        logger.info(f"   • Medium Confidence: {analysis['matching_results']['medium_confidence']}")
        logger.info(f"   • Manual Review: {analysis['matching_results']['manual_review_needed']}")
        logger.info(f"   • Overall Match Rate: {analysis['quality_metrics']['overall_match_rate']}%")
        logger.info(f"   • Reliable Match Rate: {analysis['quality_metrics']['reliable_match_rate']}%")
        
        return True

def main():
    """Main function to run the ultimate IPO matcher"""
    matcher = UltimateIPOMatcher()
    success = matcher.run_ultimate_matching()
    
    if success:
        logger.info("🎯 Ultimate IPO matching completed successfully!")
        logger.info("📁 Check the generated files for detailed results.")
    else:
        logger.error("❌ Ultimate IPO matching failed!")

if __name__ == "__main__":
    main()
