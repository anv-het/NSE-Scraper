import sys
import os
sys.path.append(os.getcwd())
from Utils.db import DatabaseManager

# print("🔍 Testing MongoDB connection...")
db = DatabaseManager()
if db.test_connection():
    # print('✅ MongoDB connection successful!')
    # print(f'Database: {db.database_name}')
    # print(f'Collections available: {list(db.mongo_db.list_collection_names())}')
else:
    # print('❌ MongoDB connection failed!')
