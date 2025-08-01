import asyncio
import json
import requests
from typing import Dict, Any, Optional
from Utils.logger import get_logger
from fastapi import APIRouter, Request

from API.Controller.stockwise_event_data import StockwiseEventDataController

router = APIRouter()

from bson import ObjectId

def convert_object_ids(doc: dict) -> dict:
    """
    Recursively convert all ObjectId instances to strings.
    """
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = convert_object_ids(value)
        elif isinstance(value, list):
            doc[key] = [convert_object_ids(item) if isinstance(item, dict) else item for item in value]
    return doc

@router.get("/stoks_wise_event_data/{symbol}")
def get_stoks_wise_event_data(request: Request, symbol: str) -> Dict[str, Any]:
    """
    Endpoint to get stockwise event data for a given symbol.
    """
    symbol = symbol.upper()
    print(f"Fetching stockwise event data for symbol: {symbol}")
    controller = StockwiseEventDataController()
    result = asyncio.run(controller.scrape_stockwise_event_data(symbol))

    if result:
        if isinstance(result, list):
            result = [convert_object_ids(doc) for doc in result]
        elif isinstance(result, dict):
            result = convert_object_ids(result)
        return {"status": "success", "data": result}
    else:
        return {"status": "error", "message": "No data found for the given symbol."}

