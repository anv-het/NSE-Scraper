import time
import random
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from Utils.logger import get_logger

logger = get_logger(__name__)

def clean_numeric_value(value: Any) -> Optional[float]:
    """
    Clean and convert numeric values to float
    
    Args:
        value: Value to clean and convert
        
    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    
    try:
        # Convert to string first to handle various input types
        str_value = str(value).strip()
        
        # Remove common non-numeric characters
        str_value = str_value.replace(',', '').replace('%', '').replace(' ', '')
        
        # Handle empty strings
        if not str_value or str_value in ['-', 'N/A', 'NA', 'null']:
            return None
        
        return float(str_value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert value to float: {value}")
        return None

def clean_string_value(value: Any) -> Optional[str]:
    """
    Clean and normalize string values
    
    Args:
        value: Value to clean
        
    Returns:
        Cleaned string or None
    """
    if value is None:
        return None
    
    try:
        str_value = str(value).strip()
        
        # Handle empty or null values
        if not str_value or str_value.lower() in ['null', 'none', 'n/a', 'na', '-']:
            return None
        
        return str_value
    except Exception:
        return None

def format_date_string(date_str: str, input_format: str = None, output_format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Format date string to standard format
    
    Args:
        date_str: Input date string
        input_format: Input date format (auto-detect if None)
        output_format: Output date format
        
    Returns:
        Formatted date string or None
    """
    if not date_str:
        return None
    
    try:
        # Common date formats to try
        formats = [
            "%d-%b-%Y",     # 10-Jul-2025
            "%d-%m-%Y",     # 10-07-2025
            "%Y-%m-%d",     # 2025-07-10
            "%d/%m/%Y",     # 10/07/2025
            "%Y/%m/%d",     # 2025/07/10
            "%d.%m.%Y",     # 10.07.2025
            "%Y.%m.%d",     # 2025.07.10
        ]
        
        if input_format:
            formats.insert(0, input_format)
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime(output_format)
            except ValueError:
                continue
        
        logger.warning(f"Failed to parse date string: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Error formatting date string: {str(e)}")
        return None

def calculate_percentage_change(current: float, previous: float) -> Optional[float]:
    """
    Calculate percentage change between two values
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Percentage change or None
    """
    try:
        if previous is None or current is None or previous == 0:
            return None
        
        return round(((current - previous) / previous) * 100, 2)
    except Exception:
        return None

def generate_hash(data: str) -> str:
    """
    Generate MD5 hash for data
    
    Args:
        data: Data to hash
        
    Returns:
        MD5 hash string
    """
    return hashlib.md5(data.encode()).hexdigest()

def safe_dict_get(data: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with nested key support
    
    Args:
        data: Dictionary to search
        key: Key (supports dot notation for nested keys)
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    try:
        if '.' in key:
            keys = key.split('.')
            value = data
            for k in keys:
                value = value.get(k, {})
            return value if value != {} else default
        else:
            return data.get(key, default)
    except Exception:
        return default

def filter_data_by_criteria(data: List[Dict], criteria: Dict) -> List[Dict]:
    """
    Filter list of dictionaries by criteria
    
    Args:
        data: List of dictionaries to filter
        criteria: Filter criteria (key-value pairs)
        
    Returns:
        Filtered list
    """
    try:
        filtered_data = []
        for item in data:
            match = True
            for key, value in criteria.items():
                if safe_dict_get(item, key) != value:
                    match = False
                    break
            if match:
                filtered_data.append(item)
        return filtered_data
    except Exception as e:
        logger.error(f"Error filtering data: {str(e)}")
        return data

def sort_data_by_field(data: List[Dict], field: str, reverse: bool = False) -> List[Dict]:
    """
    Sort list of dictionaries by field
    
    Args:
        data: List of dictionaries to sort
        field: Field to sort by
        reverse: Sort in descending order if True
        
    Returns:
        Sorted list
    """
    try:
        return sorted(data, key=lambda x: safe_dict_get(x, field, 0), reverse=reverse)
    except Exception as e:
        logger.error(f"Error sorting data: {str(e)}")
        return data

def paginate_data(data: List[Any], page: int, per_page: int) -> Dict:
    """
    Paginate data list
    
    Args:
        data: List to paginate
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dictionary with paginated data and metadata
    """
    try:
        total = len(data)
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_data = data[start:end]
        total_pages = (total + per_page - 1) // per_page
        
        return {
            'data': paginated_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
    except Exception as e:
        logger.error(f"Error paginating data: {str(e)}")
        return {'data': data, 'pagination': {}}

def validate_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Basic validation - alphanumeric and common characters
    return symbol.replace('-', '').replace('&', '').replace('.', '').isalnum()

def format_currency(amount: float, currency: str = '₹') -> str:
    """
    Format amount as currency
    
    Args:
        amount: Amount to format
        currency: Currency symbol
        
    Returns:
        Formatted currency string
    """
    try:
        if amount is None:
            return f"{currency}0.00"
        
        # Format with commas for thousands
        if amount >= 10000000:  # 1 crore
            return f"{currency}{amount/10000000:.2f}Cr"
        elif amount >= 100000:  # 1 lakh
            return f"{currency}{amount/100000:.2f}L"
        else:
            return f"{currency}{amount:,.2f}"
    except Exception:
        return f"{currency}0.00"

def calculate_market_cap(shares: float, price: float) -> Optional[float]:
    """
    Calculate market capitalization
    
    Args:
        shares: Number of shares
        price: Price per share
        
    Returns:
        Market cap or None
    """
    try:
        if shares is None or price is None:
            return None
        return shares * price
    except Exception:
        return None

def is_market_open() -> bool:
    """
    Check if Indian stock market is open
    
    Returns:
        True if market is open, False otherwise
    """
    try:
        now = datetime.now()
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Market is closed on weekends
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    except Exception:
        return False

def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """
    Retry function on failure
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Function result or raises last exception
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {str(e)}")
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception

def add_random_delay(min_seconds: float = 0.5, max_seconds: float = 2.0):
    """
    Add random delay to avoid being blocked
    
    Args:
        min_seconds: Minimum delay
        max_seconds: Maximum delay
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip('_')

def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def create_backup_filename(base_name: str, extension: str = '.json') -> str:
    """
    Create backup filename with timestamp
    
    Args:
        base_name: Base filename
        extension: File extension
        
    Returns:
        Backup filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_backup_{timestamp}{extension}"
