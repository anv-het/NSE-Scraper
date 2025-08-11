# NSE Scraper - AI Coding Agent Instructions

## System Architecture Overview

This is a **production NSE data scraper** with real-time MongoDB storage, FastAPI endpoints, and automated cron jobs. Key architectural decisions:

- **Data Flow**: `main.py` → Cron Jobs → Controllers → Data Formatters → MongoDB
- **Cookie Management**: Critical NSE session handling via `undetected_chromedriver`
- **Database**: MongoDB-first with collection-per-data-type pattern, with additional SQL Server integration for IPO data
- **Scheduling**: Minute-based cron jobs for 14+ different NSE data sources
- **API Layer**: FastAPI server with health monitoring and standard response formats

## Critical Development Patterns

### Controller Pattern (All scrapers follow this)
```python
class NSE[DataType]Controller:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.base_url = configure.get('NSE', 'BASE_URL')
        self.nse_headers_url = HEADERS_URL_[DATA_TYPE]
        self.cookies = None
        self.[data_type]_api_url = "https://www.nseindia.com/api/..."
    
    def _get_cookies(self) -> Optional[Dict[str, str]]:
        """Get NSE cookies for authenticated requests"""
        try:
            if not self.cookies:
                self.cookies = get_nse_cookies()
            return self.cookies
        except Exception as e:
            logger.error(f"Failed to get NSE cookies: {str(e)}")
            return None
        
    def _make_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Make HTTP request to NSE API with proper error handling"""
        try:
            default_headers = load_nse_headers(self.nse_headers_url)
            
            if headers:
                default_headers.update(headers)
                
            cookies = self._get_cookies()
            
            response = requests.get(
                url, 
                headers=default_headers, 
                cookies=cookies,
                timeout=configure.getint('SCRAPING', 'TIMEOUT')
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None
    
    async def [data_type](self) -> Dict:
        """Main async data scraping method called by cron jobs"""
        # Implementation with MongoDB save
```

### Data Formatter Pattern (NSEDataFormatter static methods)
```python
@staticmethod
def format_[data_type](raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    formatted_data = []
    timestamp = NSEDataFormatter.parse_timestamp(None)  # Always IST
    
    # Process raw API response into MongoDB-ready documents
    # Add timestamp, clean numeric values, handle nested structures
    for item in raw_data.get("data", []):
        document = {
            "symbol": NSEDataFormatter._safe_strip(item.get("symbol")),
            "last_price": NSEDataFormatter._safe_float(item.get("lastPrice")),
            # Other fields...
            "timestamp": timestamp
        }
        formatted_data.append(document)
    
    return formatted_data
```

### Cron Job Integration
All controllers must be registered in `Services/cron_jobs.py`:
1. Import controller in the imports section
   ```python
   from API.Controller.[data_type] import NSE[DataType]Controller
   ```
2. Add to scheduler in `run_cron_jobs` method:
   ```python
   schedule.every(CRON_INTERVALS['[DATA_TYPE]']).minutes.do(
       self.run_[data_type]
   )
   ```
3. Create runner method:
   ```python
   def run_[data_type](self):
       """Run [DataType] data collection job"""
       job_name = "[data_type]"
       try:
           logger.info(f"Starting {job_name} job")
           controller = NSE[DataType]Controller()
           result = asyncio.run(controller.[data_type]())
           logger.info(f"Completed {job_name} job: {result}")
           return result
       except Exception as e:
           logger.error(f"Error running {job_name} job: {str(e)}")
           return None
   ```

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
- **Market hours check**: Only run jobs when `is_market_open()` returns true:
  ```python
  # Runs only during trading hours (9:15 AM - 3:30 PM IST) on weekdays
  if is_market_open():
      # Schedule jobs here
  ```
- **Retry pattern**: Use `retry_on_failure` helper for exponential backoff:
  ```python
  result = retry_on_failure(lambda: api_call(), max_retries=3, delay=1.0)
  ```

### FastAPI Integration
FastAPI is used for serving the collected data through a REST API. Key components:
- **Server Configuration**: `Loader/server.py` defines the FastAPI app with CORS middleware
- **Router Registration**: Each endpoint is registered in the `apiserver()` function
- **Health Monitoring**: `/meta/health` endpoint provides system health status
- **Standard Response Format**: All endpoints use `Utils/response.py` helpers:
  ```python
  return create_success_response_n(
      data=formatted_data,
      message=f"Successfully scraped {len(formatted_data)} records"
  )
  ```

### SQL Server Integration for IPO Data
The system uses SQL Server specifically for IPO data in addition to MongoDB:
- **Dual Connection**: `DatabaseManager` handles both MongoDB and SQL Server
- **SQL Server Config**: Defined in `config.ini` under `[DATABASE]` section
- **IPO-Specific Controller**: `NSEInvestorGainIPOController` uses SQL Server for storage
- **Connection String**: Uses pyodbc with ODBC Driver 17

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
