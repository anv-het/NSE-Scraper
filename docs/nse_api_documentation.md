# NSE API Documentation

## Overview
This document provides comprehensive information about the NSE (National Stock Exchange) APIs used in the scraper. All APIs are publicly available and return JSON responses.

## Base URL
```
https://www.nseindia.com
```

## Authentication
NSE APIs require valid session cookies for access. The scraper automatically manages cookie refresh.

## API Endpoints

### 1. Gainers/Losers API

#### Endpoint
```
GET /api/live-analysis-variations?index=gainers
GET /api/live-analysis-variations?index=loosers
```

#### Description
Fetches top gaining and losing stocks across different market segments.

#### Parameters
| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `index` | string | `gainers`, `loosers` | Type of data to fetch |

#### Response Format
```json
{
  "legends": [
    ["NIFTY", "NIFTY 50"],
    ["BANKNIFTY", "BANK NIFTY"],
    ["NIFTYNEXT50", "NIFTY NEXT 50"]
  ],
  "NIFTY": {
    "data": [
      {
        "symbol": "MARUTI",
        "series": "EQ",
        "open_price": 12500,
        "high_price": 12667,
        "low_price": 12401,
        "ltp": 12615,
        "prev_price": 12470,
        "net_price": 1.16,
        "trade_quantity": 148107,
        "turnover": 18603.6314058,
        "market_type": "N",
        "ca_ex_dt": "02-Aug-2024",
        "ca_purpose": "Dividend - Rs 125 Per Share",
        "perChange": 1.16
      }
    ]
  }
}
```

#### Field Descriptions
- `symbol`: Stock symbol/ticker
- `series`: Stock series (EQ, BE, etc.)
- `ltp`: Last traded price
- `prev_price`: Previous close price
- `perChange`: Percentage change
- `trade_quantity`: Total traded quantity
- `turnover`: Total turnover in crores
- `ca_ex_dt`: Corporate action ex-date
- `ca_purpose`: Corporate action purpose

### 2. All Indices API

#### Endpoint
```
GET /api/allIndices
```

#### Description
Fetches data for all NSE indices including NIFTY 50, BANK NIFTY, etc.

#### Response Format
```json
{
  "data": [
    {
      "index": "NIFTY 50",
      "last": 24875.95,
      "variation": 54.85,
      "percentChange": 0.22,
      "open": 24890.4,
      "high": 24902.3,
      "low": 24771.95,
      "previousClose": 24821.1,
      "yearHigh": 26277.35,
      "yearLow": 21743.65,
      "pe": 23.85,
      "pb": 3.91,
      "dy": 1.33
    }
  ]
}
```

### 3. Index Stocks API

#### Endpoint
```
GET /api/equity-stockIndices?index={INDEX_NAME}
```

#### Parameters
| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `index` | string | `NIFTY%2050` | URL-encoded index name |

#### Description
Fetches all stocks belonging to a specific index.

#### Response Format
```json
{
  "data": [
    {
      "symbol": "RELIANCE",
      "open": 3100,
      "dayHigh": 3150,
      "dayLow": 3090,
      "lastPrice": 3140,
      "previousClose": 3120,
      "change": 20,
      "pChange": 0.64,
      "totalTradedVolume": 5000000,
      "totalTradedValue": 15700000000,
      "yearHigh": 3200,
      "yearLow": 2800
    }
  ]
}
```

### 4. Most Active Securities API

#### Endpoint
```
GET /api/market-data-pre-open?key=ALL
```

#### Description
Fetches most active securities by volume and value.

#### Response Format
```json
{
  "data": [
    {
      "metadata": {
        "symbol": "RELIANCE",
        "series": "EQ",
        "lastPrice": 3140,
        "change": 20,
        "pChange": 0.64,
        "previousClose": 3120,
        "open": 3100,
        "high": 3150,
        "low": 3090,
        "totalTradedVolume": 5000000,
        "totalTradedValue": 15700000000
      }
    }
  ]
}
```

### 5. Large Deals API

#### Endpoint
```
GET /api/block-deal
```

#### Description
Fetches large block deals and bulk deals.

#### Response Format
```json
{
  "data": [
    {
      "symbol": "TCS",
      "securityVar": "TCS-EQ",
      "quantity": 100000,
      "tradePrice": 4100,
      "tradeValue": 410000000,
      "clientName": "XYZ MUTUAL FUND",
      "dealType": "BLOCK"
    }
  ]
}
```

### 6. Price Band Hitters API

#### Endpoint
```
GET /api/live-analysis-variations?index=loosers&type=securities
```

#### Description
Fetches stocks hitting upper or lower circuit limits.

### 7. 52-Week High/Low API

#### Endpoint
```
GET /api/live-analysis-variations?index=weeklyhighlow
```

#### Description
Fetches stocks hitting 52-week highs or lows.

### 8. Corporate Actions API

#### Endpoint
```
GET /api/top-corp-info?symbol={SYMBOL}&market=equities
```

#### Parameters
| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `symbol` | string | `RELIANCE` | Stock symbol |
| `market` | string | `equities` | Market type |

#### Description
Fetches corporate actions and events for a specific stock.

#### Response Format
```json
{
  "data": [
    {
      "symbol": "RELIANCE",
      "industry": "Oil & Gas",
      "activeSeries": ["EQ"],
      "debtSeries": [],
      "isFNOSec": true,
      "isCASec": false,
      "isSLBSec": true,
      "isDebtSec": false,
      "isSuspended": false,
      "tempSuspendedSeries": []
    }
  ]
}
```

### 9. Most Active Contracts API

#### Endpoint
```
GET /api/market-data-pre-open?key=FO
```

#### Description
Fetches most active F&O contracts by volume.

### 10. Advances/Declines API

#### Endpoint
```
GET /api/market-status-all
```

#### Description
Fetches market-wide advances, declines, and unchanged count.

#### Response Format
```json
{
  "marketState": [
    {
      "market": "Capital Market",
      "marketStatus": "Open",
      "tradeDate": "30-Jul-2025",
      "index": "NIFTY 50",
      "last": 24875.95,
      "variation": 54.85,
      "percentChange": 0.22
    }
  ]
}
```

## Rate Limiting

- **Recommended Delay**: 1-2 seconds between requests
- **Maximum Requests**: No official limit, but be respectful
- **Cookie Refresh**: Required every 2-3 hours

## Error Handling

### Common HTTP Status Codes
- `200`: Success
- `403`: Forbidden (invalid/expired cookies)
- `404`: Not Found (invalid endpoint)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "error": "Invalid request",
  "message": "Detailed error message",
  "status": 403
}
```

## Request Headers

### Required Headers
```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```

### Cookie Headers
```http
Cookie: _ga=GA1.1.123456789; AKA_A2=A; _abck=xyz123; nsit=abc123; nseappid=def456
```

## Data Freshness

| Endpoint | Update Frequency | Market Hours Only |
|----------|------------------|-------------------|
| Gainers/Losers | Real-time | Yes |
| Indices | Real-time | Yes |
| Stock Prices | Real-time | Yes |
| Corporate Actions | Daily | No |
| Large Deals | Real-time | Yes |
| Market Status | Real-time | Yes |

## Usage Examples

### Python Request Example
```python
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

cookies = {
    'nsit': 'your_nsit_cookie',
    'nseappid': 'your_nseappid_cookie'
}

url = 'https://www.nseindia.com/api/live-analysis-variations?index=gainers'
response = requests.get(url, headers=headers, cookies=cookies)

if response.status_code == 200:
    data = response.json()
    # print(f"Found {len(data['NIFTY']['data'])} gainers")
else:
    # print(f"Error: {response.status_code}")
```

### JavaScript Fetch Example
```javascript
const url = 'https://www.nseindia.com/api/allIndices';
const headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
};

fetch(url, { headers })
    .then(response => response.json())
    .then(data => {
        console.log('Indices data:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

## Best Practices

1. **Respect Rate Limits**: Add delays between requests
2. **Handle Cookies**: Refresh cookies regularly
3. **Error Handling**: Implement robust error handling
4. **Data Validation**: Validate response data structure
5. **Logging**: Log all API interactions for debugging
6. **Retry Logic**: Implement exponential backoff for failures
7. **Caching**: Cache responses when appropriate
8. **Monitor**: Track API success rates and response times

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**
   - **Cause**: Expired or invalid cookies
   - **Solution**: Refresh cookies by visiting NSE website

2. **Empty Response**
   - **Cause**: Market closed or API temporarily down
   - **Solution**: Check market hours and retry

3. **Rate Limiting**
   - **Cause**: Too many requests
   - **Solution**: Implement proper delays

4. **Data Format Changes**
   - **Cause**: NSE updates API structure
   - **Solution**: Implement flexible parsing

### Debug Commands
```bash
# Test API with curl
curl -H "Accept: application/json" \
     -H "User-Agent: Mozilla/5.0" \
     "https://www.nseindia.com/api/allIndices"

# Check response headers
curl -I "https://www.nseindia.com/api/allIndices"
```
