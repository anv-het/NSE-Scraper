# NSE Scraper - Complete Data Collection System

<div align="center">

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)

*A comprehensive Python-based web scraper for real-time NSE (National Stock Exchange) data collection with automated cron jobs, MongoDB storage, and REST API access.*

</div>

## 🚀 Features

- **Real-time Data Collection**: Automated scraping of NSE data every minute
- **Comprehensive Coverage**: Gainers, losers, indices, stock events, large deals, and more
- **MongoDB Integration**: Structured data storage with automatic cleanup
- **REST API Server**: FastAPI-based server for data access
- **Cookie Management**: Automatic NSE session management
- **Robust Error Handling**: Comprehensive logging and retry mechanisms
- **Production Ready**: Docker support, systemd integration, monitoring

## 📊 Data Sources

| Data Type | Update Frequency | Description |
|-----------|------------------|-------------|
| **Gainers/Losers** | Every minute | Top performing stocks by percentage change |
| **All Indices** | Every minute | NIFTY 50, BANK NIFTY, and other index data |
| **Stock Events** | Every minute | Corporate actions and events |
| **Most Active** | Every minute | Most traded securities by volume |
| **Large Deals** | Every minute | Block deals and bulk transactions |
| **Price Band Hitters** | Every minute | Stocks hitting circuit limits |
| **52-Week Data** | Every minute | Stocks at 52-week highs/lows |

## 🏗️ Architecture

```
NSE-Scraper/
├── main.py                 # Main application entry point
├── config.ini             # Configuration settings
├── API/                   # Data scraping controllers
│   └── Controller/        # Individual scrapers for each data type
├── Services/              # Background services
│   ├── cron_jobs.py      # Automated data collection
│   └── get_nse_cookies.py # Cookie management
├── Utils/                 # Utility functions
│   ├── db.py            # MongoDB operations
│   ├── logger.py        # Logging configuration
│   └── data_formatter.py # Data formatting
├── Loader/               # FastAPI server setup
├── docs/                 # Documentation
└── test/                 # Test scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- 4GB RAM (recommended)

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/anv-het/NSE-Scraper.git
   cd NSE-Scraper
   ```

2. **Setup Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database**
   ```ini
   # Edit config.ini
   [DATABASE]
   MONGO_URI = mongodb://localhost:27017
   DATABASE_NAME = NSE_SCRAPER
   ```

5. **Run Application**
   ```bash
   python main.py
   ```

6. **Access API Documentation**
   ```
   http://localhost:1020/docs
   ```

## 🔧 Configuration

### Basic Configuration (config.ini)
```ini
[SERVER]
HOST = 127.0.0.1
PORT = 1020

[DATABASE]
MONGO_URI = mongodb://username:password@host:port
DATABASE_NAME = NSE_SCRAPER

[CRON_JOBS]
DATA_COLLECTION_INTERVAL = 1    # Minutes (1 for testing, 5+ for production)
COOKIE_REFRESH_INTERVAL = 60    # Minutes
```

### Testing Mode vs Production Mode
```ini
# Testing (every minute)
DATA_COLLECTION_INTERVAL = 1

# Production (every 5 minutes)
DATA_COLLECTION_INTERVAL = 5
```

## 📡 API Endpoints

The application provides a RESTful API for accessing collected data:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs` | GET | Interactive API documentation |
| `/health` | GET | Application health check |
| `/api/gainers` | GET | Latest gainers data |
| `/api/losers` | GET | Latest losers data |
| `/api/indices` | GET | All indices data |
| `/api/events/{symbol}` | GET | Stock events for symbol |

### Example API Usage
```python
import requests

# Get latest gainers
response = requests.get('http://localhost:1020/api/gainers')
gainers = response.json()

# Get NIFTY 50 data
response = requests.get('http://localhost:1020/api/indices?index=NIFTY%2050')
nifty_data = response.json()
```

## 💾 Database Schema

### Collections Overview
- `gainers_losers`: Top gaining/losing stocks
- `indices_data`: Index and constituent stock data
- `stock_events`: Corporate actions and events
- `most_active_securities`: High-volume stocks
- `large_deals`: Block and bulk deals
- `price_band_hitters`: Circuit limit stocks
- `week_52_data`: 52-week high/low stocks

### Sample Document Structure
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-07-30T12:00:00.000Z",
  "symbol": "RELIANCE",
  "series": "EQ",
  "last_price": 3140,
  "change": 20,
  "percent_change": 0.64,
  "volume": 5000000,
  "value": 15700000000
}
```

## 🔄 Automated Operations

### Cron Jobs
- **Data Collection**: Every 1-5 minutes (configurable)
- **Cookie Refresh**: Every 60 minutes
- **Data Cleanup**: Every 10 minutes
- **Log Rotation**: Daily

### Data Retention Policy
| Data Type | Retention Period |
|-----------|------------------|
| Gainers/Losers | 7 days |
| Indices | 7 days |
| Stock Events | 30 days |
| Large Deals | 30 days |
| Others | 3-14 days |

## 📊 Monitoring & Logging

### Log Files
```
Logs/
├── __main__.log                    # Main application logs
├── Services.cron_jobs.log         # Cron job execution logs
├── API.Controller.*.log           # Individual scraper logs
└── Utils.db.log                   # Database operation logs
```

### Health Monitoring
```bash
# Check application status
curl http://localhost:1020/health

# View real-time logs
tail -f Logs/__main__.log

# Monitor MongoDB
mongo NSE_SCRAPER --eval "db.stats()"
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t nse-scraper .

# Run container
docker run -d \
  -p 1020:1020 \
  -v /data/mongodb:/data/db \
  --name nse-scraper \
  nse-scraper
```

### Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/nse-scraper.service

# Enable and start
sudo systemctl enable nse-scraper
sudo systemctl start nse-scraper
```

### PM2 Process Manager
```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start main.py --interpreter python3 --name nse-scraper

# Enable startup
pm2 startup
pm2 save
```

## 🧪 Testing

### Run Tests
```bash
# Test database connection
python test/test_db.py

# Test individual scrapers
python test/test_nse_gainers_loosers.py
python test/test_all_indexes.py

# Test API endpoints
python test/test_api.py
```

### Load Testing
```bash
# Install dependencies
pip install locust

# Run load test
locust -f test/load_test.py --host=http://localhost:1020
```

## 🛠️ Development

### Project Structure
```python
# Add new scraper
class NewScraperController:
    def scrape_data(self):
        # Implementation
        pass

# Register in cron_jobs.py
self.controllers['new_scraper'] = NewScraperController()
```

### Adding New Data Source
1. Create controller in `API/Controller/`
2. Add to `Services/cron_jobs.py`
3. Update MongoDB schema
4. Add API endpoints
5. Create tests

## 📈 Performance

### System Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **Network**: Stable internet connection

### Performance Metrics
- **Data Collection**: ~1000 records/minute
- **API Response Time**: <100ms average
- **Memory Usage**: ~200MB average
- **Database Size**: ~1GB/month (with cleanup)

## 🔒 Security

### Best Practices
- Regular dependency updates
- Secure MongoDB configuration
- Network access restrictions
- Environment variable usage for secrets
- Regular backup procedures

### Security Checklist
- [ ] MongoDB authentication enabled
- [ ] Firewall configured
- [ ] SSL/TLS for external connections
- [ ] Regular security updates
- [ ] Access logging enabled

## 📚 Documentation

- **[MongoDB Schema](docs/mongodb_schema.md)**: Database structure and field definitions
- **[NSE API Documentation](docs/nse_api_documentation.md)**: Complete API reference
- **[Deployment Guide](docs/deployment_guide.md)**: Production deployment instructions
- **[Project Overview](docs/PROJECT_OVERVIEW.md)**: Technical architecture details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run code formatting
black .
flake8 .

# Run tests
pytest test/
```

## 📊 Current Status

### ✅ Working Features
- Real-time NSE data scraping (every minute)
- MongoDB data storage with cleanup
- FastAPI server with documentation
- Automated cookie management
- Comprehensive logging
- Error handling and recovery

### 🔄 Recent Updates
- Optimized cron job scheduling
- Enhanced error handling
- Improved data formatting
- Added comprehensive documentation
- Production-ready configuration

## 🐛 Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Test connection
python test/test_db.py
```

**NSE API Access Issues**
```bash
# Test cookie refresh
python Services/get_nse_cookies.py

# Check API directly
curl -H "User-Agent: Mozilla/5.0" https://www.nseindia.com/api/allIndices
```

**Application Won't Start**
```bash
# Check configuration
python -c "from Utils.config_reader import configure; # print('Config OK')"

# Verify dependencies
pip check
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- NSE (National Stock Exchange of India) for providing public APIs
- MongoDB team for excellent database technology
- FastAPI team for the modern web framework
- Python community for amazing libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/anv-het/NSE-Scraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anv-het/NSE-Scraper/discussions)
- **Documentation**: Check `docs/` directory

---

<div align="center">
<b>Built with ❤️ for the trading community</b>
<br><br>
<i>⭐ Star this repo if you find it useful!</i>
</div> - National Stock Exchange Data API

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
