# NSE Scraper MongoDB Schema Documentation

## Overview
All scraped data is saved in MongoDB collections with stock-wise documents (not objects). Each data type has its own collection with standardized schema.

## Collection Schemas

### 1. Indices Data Collection (`indices_data`)

#### Index Summary Document
```json
{
    "_id": "68888dcd62f4d0660fd40afa",
    "timestamp": "2025-07-29T14:31:01.251Z",
    "index_name": "NIFTY 50",
    "priority": 1,
    "full_name": "NIFTY 50",
    "decline_stocks": 12,
    "advance_stocks": 38,
    "unchanged_stocks": 0,
    "last_update_time": "29-Jul-2025 14:30:48",
    "last_price": 24821.3,
    "previous_close": 24680.9,
    "open": 24609.65,
    "day_high": 24826.3,
    "day_low": 24598.6,
    "change": 140.39999999999782,
    "percent_change": 0.57,
    "year_high": 26277.35,
    "year_low": 21743.65,
    "total_traded_volume": 215160910,
    "total_traded_value": 193396167474.69,
    "near_52w_high_percent": 5.541083861196047,
    "near_52w_low_percent": -14.15424733197967,
    "1y_percent_change": -0.62,
    "30d_percent_change": -3.73,
    "chart_today_url": "https://nsearchives.nseindia.com/today/NIFTY-50.svg",
    "chart_30d_url": "https://nsearchives.nseindia.com/30d/NIFTY-50.svg",
    "chart_365d_url": "https://nsearchives.nseindia.com/365d/NIFTY-50.svg"
}
```

#### Individual Stock Document
```json
{
    "_id": "68888dcd62f4d0550fd40afa",
    "timestamp": "2025-07-29T14:31:01.251Z",
    "index_name": "NIFTY 50",
    "priority": 0,
    "symbol": "JIOFIN",
    "series": "EQ",
    "last_price": 319.45,
    "change": 12.1,
    "percent_change": 3.94,
    "open_price": 306.3,
    "high": 320.5,
    "low": 306.3,
    "previous_close": 307.35,
    "total_traded_volume": 20627683,
    "total_traded_value": 6514841121.89,
    "year_high": 363,
    "year_low": 198.65,
    "near_wkh": 11.997245179063363,
    "near_wkl": -60.810470677070214,
    "per_change_365d": -7.4,
    "date_365d_ago": "26-Jul-2024",
    "per_change_30d": -4.98,
    "date_30d_ago": "27-Jun-2025",
    "chart_today_path": "https://nsearchives.nseindia.com/today/JIOFINEQN.svg",
    "chart_30d_path": "https://nsearchives.nseindia.com/30d/JIOFIN-EQ.svg",
    "chart_365d_path": "https://nsearchives.nseindia.com/365d/JIOFIN-EQ.svg"
}
```

#### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | MongoDB document ID |
| `timestamp` | DateTime | Data collection timestamp |
| `index_name` | String | Index name (NIFTY 50, NIFTY NEXT 50, etc.) |
| `priority` | Number | Priority level (1 for index summary, 0 for stocks) |
| `symbol` | String | Stock symbol |
| `series` | String | Stock series (EQ, BE, etc.) |
| `last_price` | Number | Current stock price |
| `change` | Number | Price change from previous close |
| `percent_change` | Number | Percentage change |
| `open_price` | Number | Opening price |
| `high` | Number | Day's high price |
| `low` | Number | Day's low price |
| `previous_close` | Number | Previous closing price |
| `total_traded_volume` | Number | Total traded volume |
| `total_traded_value` | Number | Total traded value |
| `year_high` | Number | 52-week high |
| `year_low` | Number | 52-week low |
| `near_wkh` | Number | Percentage near 52-week high |
| `near_wkl` | Number | Percentage near 52-week low |
| `per_change_365d` | Number | 365-day percentage change |
| `per_change_30d` | Number | 30-day percentage change |
| `chart_*_path` | String | Chart URLs for different periods |

### 2. Gainers/Losers Collection (`gainers_losers`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:32:34.920Z",
    "data_type": "gainers",
    "category": "NIFTY",
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
```

### 3. Stock Events Collection (`stock_events`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:32:46.857Z",
    "symbol": "RELIANCE",
    "event_type": "corporate_action",
    "data": {
        "announcement_date": "2025-07-29",
        "event_description": "Board Meeting",
        "event_details": "Financial Results"
    },
    "raw_data": "Original API response"
}
```

### 4. Most Active Securities Collection (`most_active_securities`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "symbol": "RELIANCE",
    "series": "EQ",
    "traded_quantity": 5000000,
    "traded_value": 15000000000,
    "last_traded_price": 3000,
    "change": 50,
    "percent_change": 1.69
}
```

### 5. Large Deals Collection (`large_deals`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "symbol": "TCS",
    "quantity": 100000,
    "trade_price": 4100,
    "trade_value": 410000000,
    "client_name": "INSTITUTIONAL",
    "deal_type": "BLOCK_DEAL"
}
```

### 6. Price Band Hitters Collection (`price_band_hitters`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "symbol": "EXAMPLE",
    "series": "EQ",
    "band_type": "upper_circuit",
    "current_price": 500,
    "circuit_price": 550,
    "percent_change": 10,
    "traded_volume": 50000
}
```

### 7. 52-Week High/Low Collection (`week_52_data`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "symbol": "INFY",
    "series": "EQ",
    "data_type": "52_week_high",
    "current_price": 1800,
    "new_high": 1850,
    "previous_high": 1800,
    "volume": 75000
}
```

### 8. Advances/Declines Collection (`advances_declines`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "market_type": "equity",
    "advances": 1200,
    "declines": 800,
    "unchanged": 100,
    "total_issues": 2100
}
```

### 9. New Listings Collection (`new_listings`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "symbol": "NEWCOMPANY",
    "company_name": "New Company Ltd",
    "listing_date": "2025-07-30",
    "issue_price": 100,
    "listing_price": 110,
    "listing_gains": 10
}
```

### 10. Most Active Contracts Collection (`most_active_contracts`)

```json
{
    "_id": "ObjectId",
    "timestamp": "2025-07-30T06:30:00.000Z",
    "underlying": "NIFTY",
    "expiry_date": "2025-08-30",
    "strike_price": 25000,
    "option_type": "CE",
    "volume": 1000000,
    "open_interest": 5000000,
    "ltp": 150
}
```

## Collection Indexing

All collections have the following standard indexes:
- `timestamp` (descending) - for time-based queries
- `symbol` (ascending) - for symbol-based queries
- Compound indexes on frequently queried fields

## Data Retention Policy

| Collection | Retention Period | Cleanup Frequency |
|------------|------------------|-------------------|
| `gainers_losers` | 7 days | Daily |
| `indices_data` | 7 days | Daily |
| `stock_events` | 30 days | Weekly |
| `most_active_securities` | 3 days | Daily |
| `large_deals` | 30 days | Weekly |
| `price_band_hitters` | 3 days | Daily |
| `week_52_data` | 14 days | Daily |
| `advances_declines` | 3 days | Daily |
| `new_listings` | 30 days | Weekly |
| `most_active_contracts` | 3 days | Daily |

## Data Validation Rules

1. All documents must have `timestamp` field
2. Stock documents must have valid `symbol` field
3. Numerical fields validated for range and type
4. Duplicate prevention based on timestamp and symbol combination
5. Automatic data cleanup based on retention policies
