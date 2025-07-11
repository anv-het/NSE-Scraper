# NSE Scraper - National Stock Exchange Data API

A comprehensive Python-based web scraper and REST API for fetching real-time data from the National Stock Exchange (NSE) of India. This project provides a robust, scalable solution for collecting and serving NSE market data through RESTful APIs.

## 🚀 Features

### Market Data APIs
- **Top Gainers & loosers** - Real-time top performing and underperforming stocks
- **Market Indices** - All NSE indices data (NIFTY, BANKNIFTY, etc.)
- **Most Active Securities** - Highest volume trading stocks
- **52-Week High/Low** - Stocks hitting yearly extremes
- **Derivatives Data** - Options, futures, and derivatives information
- **Bulk & Block Deals** - Large volume transactions data
- **System Status** - Market status, holidays, and system health

### Technical Features
- **Dual Database Support** - MongoDB and SQLite3 with configuration switching
- **Cookie Management** - Automated NSE cookie handling with undetected_chromedriver
- **Scheduled Jobs** - Automated data collection with configurable cron jobs
- **RESTful APIs** - FastAPI-based REST endpoints with OpenAPI documentation
- **Docker Support** - Complete containerization with Docker Compose
- **Comprehensive Logging** - Structured logging with file rotation
- **Error Handling** - Robust error handling and recovery mechanisms
- **Testing Suite** - Unit tests for all major components

## Project Structure

```
NSE-scraper/
├── main.py                    # Application entry point
├── config.ini                 # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── API/
│   ├── Controller/            # Business logic controllers
│   └── Router/               # FastAPI route definitions
├── Constant/
│   ├── general.py            # General constants
│   └── http.py               # HTTP status codes
├── Loader/
│   └── server.py             # FastAPI server configuration
├── Services/
│   ├── get_nse_cookies.py    # NSE cookie management
│   └── cron_jobs.py          # Scheduled tasks
├── Utils/
│   ├── config_reader.py      # Configuration management
│   ├── db.py                 # Database utilities
│   ├── logger.py             # Logging utilities
│   ├── objects.py            # Data models
│   ├── response.py           # API response formatting
│   ├── utilities_functions.py # Helper functions
│   └── verify_token.py       # Token verification
├── Tests/                    # Unit tests
└── Dockerfile               # Docker configuration
```

## 📋 Prerequisites

- Python 3.8 or higher
- Google Chrome browser (for cookie management)
- MongoDB (optional, if using MongoDB backend)
- Docker & Docker Compose (for containerized deployment)

## 🛠️ Installation

### Option 1: Quick Start with Setup Script

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd NSE-scraper
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```
   
   This will:
   - Check Python version compatibility
   - Create configuration files
   - Install dependencies (optional)
   - Create necessary directories

### Option 2: Docker Deployment (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd NSE-scraper
   ```

2. **Run the deployment script:**
   
   **Windows:**
   ```cmd
   deploy.bat
   ```
   
   **Linux/macOS:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Access the application:**
   - API Server: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MongoDB Express: http://localhost:8081

### Option 3: Manual Installation

1. **Clone and navigate:**
   ```bash
   git clone <repository-url>
   cd NSE-scraper
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application:**
   ```bash
   cp config.ini.example config.ini
   # Edit config.ini with your settings
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

The application uses `config.ini` for configuration. Copy `config.ini.example` to `config.ini` and modify as needed:

```ini
[DEFAULT]
HOST = 0.0.0.0
PORT = 8000
LOG_LEVEL = INFO
DEBUG = False

[DATABASE]
USE_MONGODB = true
MONGODB_URI = mongodb://localhost:27017
MONGODB_DATABASE = nse_scraper
SQLITE_DB_PATH = data/nse_scraper.db

[NSE]
BASE_URL = https://www.nseindia.com
COOKIES_REFRESH_HOURS = 24
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

[CRON]
ENABLE_CRON_JOBS = true
COOKIES_REFRESH_CRON = 0 */6 * * *
DATA_COLLECTION_CRON = */5 * * * *
DATA_BACKUP_CRON = 0 2 * * *
DATA_CLEANUP_CRON = 0 3 * * 0
```

### Key Configuration Options

- **USE_MONGODB**: Set to `true` for MongoDB, `false` for SQLite
- **ENABLE_CRON_JOBS**: Enable/disable scheduled data collection
- **LOG_LEVEL**: Set logging level (DEBUG, INFO, WARNING, ERROR)
- **DEBUG**: Enable debug mode for development

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Available Endpoints

#### Market Data
- `GET /api/v1/gainers-loosers/top-gainers` - Get top gaining stocks
- `GET /api/v1/gainers-loosers/top-loosers` - Get top losing stocks
- `GET /api/v1/indices/all-indices` - Get all market indices
- `GET /api/v1/indices/index-data?symbol=NIFTY` - Get specific index data
- `GET /api/v1/most-active/most-active-securities` - Get most active stocks
- `GET /api/v1/most-active/value` - Get most active by value
- `GET /api/v1/most-active/volume` - Get most active by volume
- `GET /api/v1/52week/52week-high` - Get 52-week high stocks
- `GET /api/v1/52week/52week-low` - Get 52-week low stocks

#### Derivatives
- `GET /api/v1/derivatives/index-derivatives?symbol=NIFTY` - Get index derivatives
- `GET /api/v1/derivatives/equity-derivatives?symbol=RELIANCE` - Get equity derivatives
- `GET /api/v1/derivatives/option-chain?symbol=NIFTY` - Get option chain
- `GET /api/v1/derivatives/futures-data` - Get futures data
- `GET /api/v1/derivatives/oi-spurts` - Get OI spurts data

#### Bulk Deals
- `GET /api/v1/bulk-deals/bulk-deals?date_str=15-01-2024` - Get bulk deals
- `GET /api/v1/bulk-deals/block-deals?date_str=15-01-2024` - Get block deals
- `GET /api/v1/bulk-deals/historical-bulk-deals?symbol=RELIANCE` - Get historical bulk deals
- `GET /api/v1/bulk-deals/historical-block-deals?symbol=RELIANCE` - Get historical block deals

#### System Status
- `GET /api/v1/system/market-status` - Get market status
- `GET /api/v1/system/holidays` - Get NSE holidays
- `GET /api/v1/system/circulars` - Get NSE circulars
- `GET /api/v1/system/server-time` - Get NSE server time
- `GET /api/v1/system/health` - Health check

### Interactive API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

### Example API Response
```json
{
  "success": true,
  "data": [
    {
      "symbol": "RELIANCE",
      "open": 2500.00,
      "high": 2550.00,
      "low": 2480.00,
      "last": 2540.00,
      "change": 40.00,
      "pChange": 1.60
    }
  ],
  "message": "Data fetched successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔄 Scheduled Jobs

The application includes automated scheduled jobs:

- **Cookie Refresh** - Every 6 hours (configurable)
- **Data Collection** - Every 5 minutes (configurable)
- **Data Backup** - Daily at 2 AM (configurable)
- **Data Cleanup** - Weekly on Sunday at 3 AM (configurable)

### Cron Schedule Format
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## 🧪 Testing

### Run All Tests
```bash
# With virtual environment activated
python -m pytest Tests/ -v

# Or using the deployment script
./deploy.sh  # Choose option 3
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest Tests/test_utils.py -v

# API tests only
python -m pytest Tests/test_api.py -v

# Database tests only
python -m pytest Tests/test_database.py -v
```

### Test Coverage
The test suite covers:
- API endpoint functionality
- Database operations (MongoDB and SQLite)
- Utility functions
- Error handling scenarios
- Configuration management

## 📁 Project Structure

```
NSE-scraper/
├── main.py                    # Application entry point
├── config.ini                 # Configuration file
├── config.ini.example         # Configuration template
├── requirements.txt           # Python dependencies
├── setup.py                   # Quick setup script
├── status_check.py            # Status monitoring script
├── Dockerfile                 # Docker container definition
├── docker-compose.yml         # Multi-container setup
├── deploy.sh / deploy.bat     # Deployment scripts
├── mongo-init.js              # MongoDB initialization
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── README.md                  # This file
├── API/
│   ├── Controller/            # Business logic controllers
│   │   ├── nse_top_gainers_looser.py
│   │   ├── nse_all_indexes.py
│   │   ├── nse_most_active.py
│   │   ├── nse_52week_high_low.py
│   │   ├── nse_derivatives.py
│   │   ├── nse_bulk_deals.py
│   │   └── nse_system_status.py
│   └── Router/               # FastAPI route handlers
│       ├── nse_top_gainers_looser.py
│       ├── nse_all_indexes.py
│       ├── nse_most_active.py
│       ├── nse_52week_high_low.py
│       ├── nse_derivatives.py
│       ├── nse_bulk_deals.py
│       └── nse_system_status.py
├── Constant/                  # Application constants
│   ├── general.py
│   └── http.py
├── Loader/                    # Application bootstrap
│   └── server.py
├── Services/                  # Core services
│   ├── get_nse_cookies.py     # Cookie management
│   └── cron_jobs.py           # Scheduled tasks
├── Utils/                     # Utility functions and helpers
│   ├── config_reader.py       # Configuration management
│   ├── db.py                  # Database operations
│   ├── logger.py              # Logging utilities
│   ├── objects.py             # Data models
│   ├── response.py            # API response formatting
│   ├── utilities_functions.py # Helper functions
│   └── verify_token.py        # Token verification
├── Tests/                     # Test suite
│   ├── conftest.py            # Test configuration
│   ├── test_api.py            # API endpoint tests
│   ├── test_database.py       # Database tests
│   └── test_utils.py          # Utility function tests
├── logs/                      # Application logs (created at runtime)
└── data/                      # Data storage (created at runtime)
```

## 🐳 Docker Deployment

### Complete Stack with Docker Compose

The application includes a complete Docker Compose setup with:
- **NSE Scraper API** - Main application server
- **MongoDB** - Primary database
- **Redis** - Caching and session storage
- **Mongo Express** - Database management interface

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f nse-scraper

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

### Services and Ports
- **API Server**: http://localhost:8000
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379
- **Mongo Express**: http://localhost:8081

### Docker Environment Variables
Copy `.env.example` to `.env` and modify as needed for Docker deployment.

## 📊 Database Schema

### MongoDB Collections / SQLite Tables

#### Market Data Tables
- **gainers** - Top gaining stocks data
- **loosers** - Top losing stocks data
- **indices** - Market indices data
- **most_active** - Most active securities
- **high_52week** - 52-week high stocks
- **low_52week** - 52-week low stocks

#### Derivatives Tables
- **derivatives** - Derivatives and options data
- **option_chain** - Option chain data
- **futures** - Futures data

#### Transactions Tables
- **bulk_deals** - Bulk deals transactions
- **block_deals** - Block deals transactions

#### System Tables
- **system_logs** - Application logs
- **api_logs** - API access logs
- **cookies** - NSE cookies storage

### Common Data Fields
```json
{
  "symbol": "RELIANCE",
  "timestamp": "2024-01-15T10:30:00Z",
  "open": 2500.00,
  "high": 2550.00,
  "low": 2480.00,
  "close": 2540.00,
  "volume": 1000000,
  "change": 40.00,
  "pChange": 1.60
}
```

## 📈 Monitoring and Status

### Status Check Script
Use the included status monitoring script:

```bash
# Single status check
python status_check.py

# Continuous monitoring
python status_check.py --watch

# Custom URL and interval
python status_check.py --url http://localhost:8000 --watch --interval 60
```

### Log Files
- `logs/app.log` - Main application logs
- `logs/error.log` - Error logs
- `logs/access.log` - API access logs

### Health Monitoring
- Health check endpoint: `/api/v1/system/health`
- Metrics and status information
- Database connectivity checks
- Cookie validity status

## 🛡️ Security and Best Practices

### Security Features
- Request timeout handling
- Input validation and sanitization
- SQL injection prevention
- XSS protection through FastAPI
- CORS middleware configuration
- Rate limiting (configurable)

### Production Deployment Checklist
- [ ] Change default passwords in `docker-compose.yml`
- [ ] Set strong JWT secret key in configuration
- [ ] Configure CORS origins appropriately
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up firewall rules
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Regular backup of data
- [ ] Update dependencies regularly

## 🚨 Troubleshooting

### Common Issues

#### 1. Chrome/Chromedriver Issues
```bash
# Error: Chrome binary not found
# Solution: Install Chrome or set CHROME_BIN environment variable
export CHROME_BIN=/usr/bin/google-chrome

# Error: Chromedriver version mismatch
# Solution: Update undetected-chromedriver
pip install --upgrade undetected-chromedriver
```

#### 2. Database Connection Issues
```bash
# MongoDB connection error
# Check if MongoDB is running and accessible
docker-compose logs mongo

# SQLite permission error
# Check file permissions
chmod 755 data/
chmod 644 data/nse_scraper.db
```

#### 3. NSE Cookie Issues
```bash
# Cookies expired or invalid
# Force refresh cookies
# Check logs/error.log for details
```

#### 4. Port Already in Use
```bash
# Error: Port 8000 already in use
# Change port in config.ini or stop conflicting service
netstat -tulpn | grep 8000
```

### Debug Mode
Enable debug mode in `config.ini`:
```ini
[DEFAULT]
DEBUG = True
LOG_LEVEL = DEBUG
```

### Getting Help
1. Check the logs in `logs/` directory
2. Run the status check script: `python status_check.py`
3. Use the health check endpoint: `GET /api/v1/system/health`
4. Enable debug mode for detailed error information

## 📈 Performance Optimization

### Recommended Settings
- Use MongoDB for high-volume deployments
- Enable Redis caching in Docker setup
- Adjust `REQUEST_TIMEOUT` based on network conditions
- Configure appropriate `MAX_RETRIES` for NSE API calls
- Use connection pooling for database operations

### Scaling Considerations
- Deploy multiple API instances behind a load balancer
- Use Redis for shared session storage
- Implement database sharding for large datasets
- Monitor memory usage and optimize accordingly
- Consider using async workers for background tasks

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies: `pip install -r requirements.txt`
4. Run tests: `python -m pytest Tests/ -v`
5. Make your changes
6. Add tests for new features
7. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write unit tests for new functionality
- Update documentation for API changes

### Testing Guidelines
- Maintain test coverage above 80%
- Test both success and error scenarios
- Mock external API calls in tests
- Use appropriate test data and fixtures

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Important Disclaimers

### Legal Compliance
- This tool is for educational and research purposes only
- Ensure compliance with NSE's terms of service and robots.txt
- Respect rate limits and avoid overloading NSE servers
- Use responsibly and ethically

### Data Accuracy
- Market data is provided "as is" without warranty
- Always verify critical data with official NSE sources
- Data may be delayed or incomplete during market hours
- Not intended for high-frequency trading applications

### Usage Responsibility
- Users are responsible for their use of this software
- Authors are not liable for any financial losses
- Use appropriate risk management practices
- Understand the limitations and risks involved

## 🆘 Support and Community

### Getting Support
- **Issues**: Create an issue in the repository
- **Documentation**: Check this README and API docs
- **Logs**: Review application logs for error details
- **Status**: Use the status check script for diagnostics

### Contributing to the Project
- **Bug Reports**: Use GitHub issues with detailed descriptions
- **Feature Requests**: Propose new features via issues
- **Code Contributions**: Submit pull requests with tests
- **Documentation**: Improve docs and examples

### Community Guidelines
- Be respectful and constructive
- Provide detailed information in bug reports
- Test thoroughly before submitting pull requests
- Follow the project's coding standards

## 🔄 Roadmap and Future Enhancements

### Planned Features
- [ ] Real-time WebSocket data streaming
- [ ] Advanced data analytics and visualization
- [ ] Machine learning integration for predictions
- [ ] Mobile app API support
- [ ] Advanced caching strategies
- [ ] Multi-exchange support (BSE, other exchanges)
- [ ] Enhanced security features
- [ ] Performance monitoring dashboard

### Version History
- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added Docker support and improved error handling
- **v1.2.0** - Enhanced testing and monitoring capabilities

---

**Happy Trading! 📈**

**Remember**: Always trade responsibly and within your risk tolerance. This tool is designed to provide data access, not trading advice.
