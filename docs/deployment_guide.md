# NSE Scraper - Deployment Guide

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space minimum
- **Network**: Stable internet connection

### Software Requirements
- **Python**: 3.8+ (tested with 3.13)
- **MongoDB**: 4.4+ (local or remote)
- **Operating System**: Windows/Linux/macOS

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/anv-het/NSE-Scraper.git
cd NSE-Scraper
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB

#### Option A: Local MongoDB
```bash
# Install MongoDB Community Edition
# Start MongoDB service
mongod --dbpath /data/db
```

#### Option B: MongoDB Atlas (Cloud)
1. Create account at https://cloud.mongodb.com
2. Create cluster and get connection string
3. Update connection string in config.ini

### 5. Configure Application

#### Edit config.ini
```ini
[SERVER]
HOST = 0.0.0.0        # Change to 0.0.0.0 for external access
PORT = 8000           # Change port if needed

[DATABASE]
MONGO_URI = mongodb://username:password@host:port
DATABASE_NAME = NSE_SCRAPER

[CRON_JOBS]
DATA_COLLECTION_INTERVAL = 5    # Minutes (1 for testing, 5+ for production)
```

### 6. Test Installation
```bash
# Test MongoDB connection
python test/test_db.py

# Test NSE API access
python test/test_nse_gainers_loosers.py
```

### 7. Run Application
```bash
python main.py
```

## Production Deployment

### Using systemd (Linux)

#### Create service file
```bash
sudo nano /etc/systemd/system/nse-scraper.service
```

```ini
[Unit]
Description=NSE Scraper Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/NSE-Scraper
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and start service
```bash
sudo systemctl daemon-reload
sudo systemctl enable nse-scraper
sudo systemctl start nse-scraper
sudo systemctl status nse-scraper
```

### Using Docker

#### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

#### Build and run
```bash
docker build -t nse-scraper .
docker run -d -p 8000:8000 --name nse-scraper nse-scraper
```

### Using PM2 (Node.js Process Manager)

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
pm2 ecosystem
```

```javascript
module.exports = {
  apps: [{
    name: 'nse-scraper',
    script: 'python',
    args: 'main.py',
    cwd: '/path/to/NSE-Scraper',
    interpreter: '/path/to/venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
```

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Environment Configuration

### Development
```ini
[CRON_JOBS]
DATA_COLLECTION_INTERVAL = 1     # Test every minute
LOG_LEVEL = DEBUG
```

### Production
```ini
[CRON_JOBS]
DATA_COLLECTION_INTERVAL = 5     # Every 5 minutes
LOG_LEVEL = INFO
```

## Security Considerations

### Database Security
- Use strong MongoDB credentials
- Enable MongoDB authentication
- Use SSL/TLS for remote connections
- Restrict database network access

### Application Security
- Run application with limited user privileges
- Use environment variables for sensitive data
- Enable firewall rules
- Regular security updates

### Network Security
```bash
# Firewall configuration (Ubuntu/CentOS)
sudo ufw allow 8000/tcp         # API port
sudo ufw allow 27017/tcp        # MongoDB (if external)
sudo ufw enable
```

## Monitoring & Maintenance

### Log Management
```bash
# View logs
tail -f Logs/__main__.log

# Rotate logs (add to crontab)
0 0 * * * find /path/to/NSE-Scraper/Logs -name "*.log" -mtime +7 -delete
```

### Database Maintenance
```javascript
// MongoDB maintenance commands
use NSE_SCRAPER

// Check database size
db.stats()

// Compact collections
db.gainers_losers.compact()

// Create indexes
db.gainers_losers.createIndex({"timestamp": -1, "symbol": 1})
```

### Health Checks
```python
# health_check.py
import requests
import sys

try:
    response = requests.get('http://localhost:8000/health')
    if response.status_code == 200:
        print("✅ Application healthy")
        sys.exit(0)
    else:
        print("❌ Application unhealthy")
        sys.exit(1)
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
```

### Automated Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +"%Y%m%d_%H%M%S")
mongodump --host localhost --port 27017 --db NSE_SCRAPER --out /backups/nse_$DATE
tar -czf /backups/nse_backup_$DATE.tar.gz /backups/nse_$DATE
rm -rf /backups/nse_$DATE

# Keep only last 7 days of backups
find /backups -name "nse_backup_*.tar.gz" -mtime +7 -delete
```

## Performance Optimization

### Database Optimization
```javascript
// MongoDB indexes for better performance
db.gainers_losers.createIndex({"timestamp": -1})
db.gainers_losers.createIndex({"symbol": 1})
db.gainers_losers.createIndex({"data_type": 1, "timestamp": -1})

// Compound indexes
db.indices_data.createIndex({"index_name": 1, "timestamp": -1})
db.stock_events.createIndex({"symbol": 1, "timestamp": -1})
```

### Application Optimization
- Adjust cron job intervals based on requirements
- Monitor memory usage and restart if needed
- Use connection pooling for database
- Implement request caching where appropriate

## Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check connection
mongo --eval "db.stats()"

# Check network connectivity
telnet mongodb_host 27017
```

#### 2. NSE API Access Issues
```python
# Test cookie refresh
python Services/get_nse_cookies.py

# Test API directly
curl -H "User-Agent: Mozilla/5.0" https://www.nseindia.com/api/allIndices
```

#### 3. Application Won't Start
```bash
# Check Python environment
which python
python --version

# Check dependencies
pip list

# Check configuration
python -c "from Utils.config_reader import configure; print('Config loaded')"
```

#### 4. High Memory Usage
```bash
# Monitor memory
htop
ps aux | grep python

# Check logs for memory issues
grep -i "memory\|oom" Logs/__main__.log
```

### Debug Commands
```bash
# Check application status
curl http://localhost:8000/health

# View real-time logs
tail -f Logs/__main__.log | grep ERROR

# Check MongoDB collections
mongo NSE_SCRAPER --eval "db.getCollectionNames()"

# Test specific scraper
python test/test_all_indexes.py
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple instances
- Separate read/write operations
- Implement message queue for background tasks

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database queries
- Use SSD storage for database

### Data Management
- Implement data archiving strategy
- Use read replicas for analytics
- Consider data partitioning for large datasets

## Backup & Recovery

### Automated Backup Strategy
```bash
# Daily backup script
#!/bin/bash
mongodump --db NSE_SCRAPER --gzip --archive=/backups/daily_$(date +%Y%m%d).gz

# Weekly backup with retention
find /backups -name "daily_*.gz" -mtime +7 -delete
```

### Recovery Procedure
```bash
# Restore from backup
mongorestore --db NSE_SCRAPER --gzip --archive=/backups/daily_20250730.gz

# Verify data integrity
mongo NSE_SCRAPER --eval "db.gainers_losers.count()"
```

## Support & Maintenance

### Regular Maintenance Tasks
- [ ] Weekly log cleanup
- [ ] Monthly database maintenance
- [ ] Quarterly security updates
- [ ] Annual configuration review

### Contact Information
- **Repository**: https://github.com/anv-het/NSE-Scraper
- **Issues**: Create GitHub issue for bugs/features
- **Documentation**: Check docs/ directory for latest info
