import sys
import os
sys.path.append(os.getcwd())
from Utils.db import DatabaseManager

print("🔍 Checking MongoDB data after cron jobs...")
db = DatabaseManager()

# Get all collections
collections = list(db.mongo_db.list_collection_names())
print(f"📊 Total collections: {len(collections)}")

# Check data in key collections
key_collections = ['gainers_losers', 'indices_data', 'stock_events', 'most_active_securities']

for collection_name in key_collections:
    if collection_name in collections:
        count = db.mongo_db[collection_name].count_documents({})
        print(f"📈 {collection_name}: {count} documents")
        
        # Show a sample document
        sample = db.mongo_db[collection_name].find_one()
        if sample:
            print(f"   Sample fields: {list(sample.keys())[:8]}...")
    else:
        print(f"❌ {collection_name}: Collection not found")

print("\n🕒 Latest data timestamps:")
for collection_name in key_collections:
    if collection_name in collections:
        latest = db.mongo_db[collection_name].find().sort("timestamp", -1).limit(1)
        for doc in latest:
            print(f"   {collection_name}: {doc.get('timestamp', 'No timestamp')}")
            break
