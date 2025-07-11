import requests
import sqlite3
import datetime
from Utils.cookie_headers import load_nse_headers_and_cookies

print("🚀 Script started...")

# Load headers and cookies
headers, cookies = load_nse_headers_and_cookies()

# NSE API URL
url = "https://www.nseindia.com/api/live-analysis-variations?index=gainers"

# Create session
session = requests.Session()
session.headers.update(headers)
session.cookies.update(cookies)

try:
    print("🌐 Sending request to NSE...")
    response = session.get(url, timeout=20)
    response.raise_for_status()
    print("✅ API response received.")
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    exit(1)
except ValueError as e:
    print(f"❌ JSON decode error: {e}")
    print("🔍 Response text:\n", response.text[:1000])
    exit(1)

# Save to DB
try:
    print("🔗 Connecting to database...")
    conn = sqlite3.connect("nse_scraper.db")
    cursor = conn.cursor()

    print("🛠️ Creating table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS top_gainers (
            symbol TEXT,
            series TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            ltp REAL,
            prev_price REAL,
            net_price REAL,
            trade_quantity INTEGER,
            turnover REAL,
            market_type TEXT,
            ca_ex_dt TEXT,
            ca_purpose TEXT,
            perChange REAL,
            index_name TEXT,
            timestamp TEXT
        )
    """)

    print("📦 Inserting records into DB...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0

    for index_name, block in data.items():
        if isinstance(block, dict) and "data" in block:
            for item in block["data"]:
                values = (
                    item.get("symbol"),
                    item.get("series"),
                    item.get("open_price"),
                    item.get("high_price"),
                    item.get("low_price"),
                    item.get("ltp"),
                    item.get("prev_price"),
                    item.get("net_price"),
                    item.get("trade_quantity"),
                    item.get("turnover"),
                    item.get("market_type"),
                    item.get("ca_ex_dt"),
                    item.get("ca_purpose"),
                    item.get("perChange"),
                    index_name,
                    timestamp
                )
                cursor.execute("INSERT INTO top_gainers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
                count += 1

    conn.commit()
    conn.close()
    print(f"✅ Saved {count} rows to top_gainers.")
except Exception as e:
    print(f"❌ DB Error: {e}")
    exit(1)

print("🏁 Script finished successfully.")
