# NSE Scraper - AI Coding Agent Instructions

## System Architecture Overview

This is a **production NSE data scraper** with real-time MongoDB storage, FastAPI endpoints, and automated cron jobs. Key architectural decisions:

- **Data Flow**: `main.py` → Cron Jobs → Controllers → Data Formatters → MongoDB
- **Cookie Management**: Critical NSE session handling via `undetected_chromedriver`
- **Database**: MongoDB-first with collection-per-data-type pattern (no SQLite in production)
- **Scheduling**: Minute-based cron jobs for 10+ different NSE data sources

## Critical Development Patterns

### Controller Pattern (All scrapers follow this)
```python
class NSE[DataType]Controller:
    def __init__(self):
        self.db = DatabaseManager()
        self.cookies = None
        self.[data_type]_api_url = "https://www.nseindia.com/api/..."
    
    def get_cookies(self) -> Optional[Dict[str, str]]:
        # Always get fresh cookies if not cached
        
    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        # Standard request pattern with retry logic
        
    def scrape_[data_type](self) -> Dict[str, Any]:
        # Main scraping method called by cron jobs
```

### Data Formatter Pattern (NSEDataFormatter static methods)
```python
@staticmethod
def format_[data_type](raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    formatted_data = []
    timestamp = NSEDataFormatter.parse_timestamp(None)  # Always IST
    
    # Process raw API response into MongoDB-ready documents
    # Add timestamp, clean numeric values, handle nested structures
    
    return formatted_data
```

### Cron Job Integration
All controllers must be registered in `Services/cron_jobs.py`:
1. Add to `self.controllers` dict in `__init__`
2. Create job method: `def job_[data_type](self):`
3. Use `self.log_job_execution()` for success/failure tracking

## Essential File Knowledge

### Configuration (`config.ini`)
- `DATA_COLLECTION_INTERVAL = 1` for testing, `5+` for production
- `COOKIE_REFRESH_INTERVAL = 60` minutes
- MongoDB connection via `MONGO_URI` with auth
- All intervals configurable per data source

### Database Patterns (`Utils/db.py`)
- **One collection per data type**: `gainers_losers`, `most_active_contracts`, etc.
- **Delete-then-insert**: Always `db.delete_old_data()` before `save_formatted_data()`
- **IST timestamps**: Use `NSEDataFormatter.parse_timestamp(None)` everywhere
- **No SQLite**: MongoDB-only system despite legacy code

### Cookie Management (`Services/get_nse_cookies.py`)
- **Critical**: NSE blocks requests without proper cookies
- **Auto-refresh**: File-based caching with validation
- **Required cookies**: 10 specific cookies from `REQUIRED_NSE_COOKIES`
- **Chrome driver**: Uses `undetected_chromedriver` to avoid detection

## Development Workflows

### Adding New Data Source
1. **Create controller**: `API/Controller/new_data_source.py` following controller pattern
2. **Add formatter**: Static method in `Utils/data_formatter.py`
3. **Register in cron**: Add to `Services/cron_jobs.py` controllers dict + job method
4. **Update constants**: Add URLs/headers to `Constant/general.py`
5. **Test endpoint**: `curl localhost:1020/health` to verify

### Testing Commands
```bash
# Start with 1-minute intervals for testing
python main.py

# Test individual scraper
python API/Controller/top_gainers_loosers.py

# Check database collections
python test_db.py

# View logs
tail -f Logs/__main__.log | grep ERROR
```

### Error Handling Patterns
- **Request failures**: 3 retries with exponential backoff
- **Cookie issues**: Auto-refresh then retry
- **Data formatting**: Log errors but continue processing
- **Database errors**: Fail fast with detailed logging

## Project-Specific Conventions

### Logging
- **Per-module**: Each file gets separate log file via `get_logger(__name__)`
- **Dual logging**: Console + file, separate error logs
- **Cron stats**: Job success/failure tracking in `job_stats`

### API Response Structure
```python
# Always use Utils/response.py helpers
return create_success_response_n(
    data=formatted_data,
    message=f"Successfully scraped {len(formatted_data)} records"
)
```

### Data Type Naming
- **Collections**: `snake_case` (e.g., `most_active_contracts`)
- **Controllers**: `PascalCase` (e.g., `NSEMostActiveContractsController`)
- **API fields**: Match NSE response keys exactly

## Common Pitfalls

1. **Never use SQLite patterns** - This is MongoDB-only despite legacy code
2. **Always validate cookies** before API requests
3. **Use IST timestamps** - Never UTC for business logic
4. **Delete old data first** - Critical for data freshness
5. **Import path issues** - Always use absolute imports from project root

## Debugging Quick Reference

```bash
# Check if MongoDB running
mongo NSE_SCRAPER --eval "db.getCollectionNames()"

# Test NSE API access
python Services/get_nse_cookies.py

# Monitor real-time data collection
tail -f Logs/Services.cron_jobs.log

# Check specific controller
python -c "from API.Controller.top_gainers_loosers import *; # print('OK')"
```
