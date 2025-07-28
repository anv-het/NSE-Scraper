import sqlite3
import pymongo
from datetime import datetime
from typing import Dict, List
from Utils.logger import get_logger
from Utils.config_reader import configure

logger = get_logger(__name__)

class DatabaseManager:
    
    