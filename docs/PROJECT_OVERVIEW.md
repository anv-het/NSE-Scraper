# NSE Scraper Project - Complete Overview

## Project Description
NSE Scraper is a comprehensive Python-based web scraping system that collects real-time data from the National Stock Exchange (NSE) of India. The system runs automated cron jobs to scrape various financial data and stores it in MongoDB with proper formatting and cleanup.

## Architecture Overview

### 🎯 Main Entry Point
- **File**: `main.py`
- **Purpose**: Starts FastAPI server and manages background cron jobs
- **Features**:
  - FastAPI server for data access
  - Background cron job management
  - MongoDB connection handling
  - Graceful shutdown handling
  - Comprehensive logging

### 🔄 Cron Job System
- **File**: `Services/cron_jobs.py`
- **Purpose**: Manages automated data collection
- **Current Configuration**: All jobs run every 1 minute (testing mode)
- **Data Sources Scraped**:
  1. Top Gainers & Losers
  2. All NSE Indices
  3. Most Active Securities
  4. Price Band Hitters
  5. 52-Week High/Low Data
  6. Large Deals
  7. Advances/Declines/Unchanged
  8. New Listings
  9. Most Active Contracts
  10. Most Active Underlying
  11. Stock Events

### 🍪 Cookie Management
- **File**: `Services/get_nse_cookies.py`
- **Purpose**: Maintains valid NSE session cookies
- **Refresh**: Every 5 minutes
- **Storage**: `nse_cookies.json`

### 📊 Data Controllers
Located in `API/Controller/` - Each controller handles specific NSE API endpoints:
- `top_gainers_loosers.py` - Gainers and losers data
- `nse_all_indexes.py` - All indices information
- `most_active_data_eq.py` - Most active equities
- `nse_price_band_hitter.py` - Price band hitters
- `nse_52week_high_low.py` - 52-week high/low data
- `large_deal.py` - Large deals data
- `advances_declines_unchanged.py` - Market advances/declines
- `new_listing_stoks.py` - New stock listings
- `most_active_contract.py` - Active contracts
- `most_active_underlying.py` - Active underlying assets
- `stockwise_event_data.py` - Stock-wise events

### 🗄️ Database Management
- **File**: `Utils/db.py`
- **Database**: MongoDB
- **Connection**: `mongodb://sa:963852@192.168.102.120:27017`
- **Database Name**: `WEB_SCRAPING`
- **Features**:
  - Data saving with cleanup (removes old data before saving new)
  - Connection testing
  - Automatic data retention management

### 📝 Data Format
All scraped data is formatted according to the schema defined in:
- `nse scraper api's mongo scheme.txt` - MongoDB collection schemas
- `all the NSE api and response.txt` - Raw API response examples

### ⚙️ Configuration
- **File**: `config.ini`
- **Key Settings**:
  - Server: Host 127.0.0.1, Port 1020
  - Database: MongoDB connection details
  - Cron Jobs: 1-minute intervals for testing
  - Request settings: Delays, retries, timeouts

## Data Flow

1. **Startup**: `main.py` starts FastAPI server and cron jobs
2. **Cookie Refresh**: Periodic cookie validation for NSE access
3. **Data Scraping**: Cron jobs scrape NSE APIs every minute
4. **Data Formatting**: Raw API responses formatted for MongoDB
5. **Data Storage**: 
   - Delete old data from collection
   - Save new formatted data to MongoDB
   - Log success/failure statistics

## File Structure Analysis

### ✅ Core Files (Essential)
- `main.py` - Main application entry point
- `config.ini` - Configuration settings
- `requirements.txt` - Python dependencies
- `Services/` - Core business logic
- `API/Controller/` - Data scrapers
- `Utils/` - Utility functions
- `Constant/` - Application constants
- `Loader/` - FastAPI server setup

### 📁 Documentation Files
- `nse scraper api's mongo scheme.txt` - Database schemas
- `all the NSE api and response.txt` - API documentation
- `README.md` - Project documentation

### 🧪 Test Files
- `test/` directory - Contains all test scripts
- Individual test files for each controller

### ❓ Potentially Unused Files
- `nse_realtime_scraper.py` - Appears to be duplicate functionality
- `nse_data.db` - SQLite database (not used if using MongoDB)

### 📊 Generated Files
- `nse_cookies.json` - Runtime cookie storage
- `Logs/` - Application logs
- `__pycache__/` - Python cache directories

## Current Status
- ✅ Project structure analyzed
- ✅ Configuration set for 1-minute testing intervals
- ✅ MongoDB connection configured
- ⏳ Ready for testing phase

## Next Steps
1. Test MongoDB connection
2. Run main.py and verify cron jobs
3. Monitor data scraping and saving
4. Clean up unused files
5. Optimize performance
