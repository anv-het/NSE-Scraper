#!/usr/bin/env python3
"""
ScanX Stock Data Router
======================
FastAPI router for ScanX stock data scraping API endpoints.
Handles single and multiple symbol requests with proper response formatting.
"""

import asyncio
import json
import pytz
from datetime import datetime
from bson import ObjectId
from typing import Dict, Any, List, Union
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel
from Utils.logger import get_logger

from API.Controller.scanx_scrap_stocks_data_by_symbol import ScanXStockDataController

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models for request validation
class MultipleSymbolsRequest(BaseModel):
    symbols: List[str]

class CronUpdateRequest(BaseModel):
    symbols: List[str] = None  # Optional, if None update all symbols

def convert_object_ids(doc):
    """
    Convert ObjectId instances to strings for JSON serialization.
    FastAPI handles most conversions automatically, but this ensures compatibility.
    """

    try:
        # Use JSON serialization to handle ObjectId conversion
        return json.loads(json.dumps(doc, default=str))
    except Exception:
        # Fallback to original document if conversion fails
        return doc

def get_current_time_ist():
    """
    Utility function to get current time in IST (Asia/Kolkata) as ISO string.
    """
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).isoformat()

@router.get("/get/stocks")
def get_scanx_stock_data_single(
    request: Request, 
    symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed"),
    symbols: str = Query(None, description="Comma-separated list of symbols (e.g., 'TCS,INFY'), Index are not allowed")
) -> Dict[str, Any]:
    """
    GET endpoint to fetch ScanX stock data for single or multiple symbols.
    
    Args:
        symbol: Single stock symbol
        symbols: Comma-separated list of symbols
        
    Returns:
        Dict containing stock data with symbols as keys
    """
    try:
        logger.info(f"GET request received - symbol: {symbol}, symbols: {symbols}")
        
        # Validate input
        if not symbol and not symbols:
            raise HTTPException(status_code=400, detail="Either 'symbol' or 'symbols' parameter is required")
        
        if symbol and symbols:
            raise HTTPException(status_code=400, detail="Provide either 'symbol' or 'symbols', not both")
        
        controller = ScanXStockDataController()
        
        if symbol:
            # Single symbol request
            symbol = symbol.upper().strip()
            logger.info(f"Processing single symbol: {symbol}")
            
            result = controller.scrape_single_symbol(symbol)
            
            if result:
                clean_result = convert_object_ids(result)
                return {
                    "status": "success",
                    "total_symbols": 1,
                    "successful": 1,
                    "failed": 0,
                    "data": {symbol: clean_result}
                }
            else:
                return {
                    "status": "error",
                    "total_symbols": 1,
                    "successful": 0,
                    "failed": 1,
                    "message": f"No data found for symbol: {symbol}",
                    "data": {}
                }
        
        else:
            # Multiple symbols request
            symbol_list = [s.upper().strip() for s in symbols.split(",") if s.strip()]
            logger.info(f"Processing multiple symbols: {symbol_list}")
            
            if len(symbol_list) > 50:  # Limit for performance
                raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed per request")
            
            results = controller.scrape_multiple_symbols(symbol_list)
            
            # Clean ObjectIds and prepare response
            clean_results = {}
            successful_count = 0
            failed_count = 0
            
            for sym, data in results.items():
                if data:
                    clean_results[sym] = convert_object_ids(data)
                    successful_count += 1
                else:
                    clean_results[sym] = None
                    failed_count += 1
            
            return {
                "status": "success" if successful_count > 0 else "error",
                "total_symbols": len(symbol_list),
                "successful": successful_count,
                "failed": failed_count,
                "data": clean_results
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_scanx_stock_data_single: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/stocks-multiple")
def post_scanx_stock_data_multiple(request: Request, body: MultipleSymbolsRequest) -> Dict[str, Any]:
    """
    POST endpoint to fetch ScanX stock data for multiple symbols.
    
    Args:
        body: Request body containing list of symbols
        
    Returns:
        Dict containing stock data with symbols as keys
    """
    try:
        symbol_list = [s.upper().strip() for s in body.symbols if s.strip()]
        logger.info(f"POST request for multiple symbols: {symbol_list}")
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="At least one symbol is required, Index are not allowed")

        if len(symbol_list) > 50:  # Limit for performance
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed per request, Index are not allowed")
        
        controller = ScanXStockDataController()
        results = controller.scrape_multiple_symbols(symbol_list)
        
        # Clean ObjectIds and prepare response
        clean_results = {}
        successful_count = 0
        failed_count = 0
        
        for sym, data in results.items():
            if data:
                clean_results[sym] = convert_object_ids(data)
                successful_count += 1
            else:
                clean_results[sym] = None
                failed_count += 1
        
        return {
            "status": "success" if successful_count > 0 else "error",
            "total_symbols": len(symbol_list),
            "successful": successful_count,
            "failed": failed_count,
            "data": clean_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in post_scanx_stock_data_multiple: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/update-time-sensitive")
def update_time_sensitive_data(request: Request, body: CronUpdateRequest = None) -> Dict[str, Any]:
    """
    POST endpoint to update time-sensitive data (announcements, latest_announcements, live_news_data).
    This endpoint is designed for cron job usage every 60 minutes.
    
    Args:
        body: Optional request body containing specific symbols to update. If None, updates all symbols.
        
    Returns:
        Dict containing update results summary
    """
    try:
        controller = ScanXStockDataController()
        
        if body and body.symbols:
            # Update specific symbols
            symbol_list = [s.upper().strip() for s in body.symbols if s.strip()]
            logger.info(f"Updating time-sensitive data for specific symbols: {symbol_list}")
            
            successful_count = 0
            failed_count = 0
            
            for symbol in symbol_list:
                success = controller.update_time_sensitive_data(symbol)
                if success:
                    successful_count += 1
                else:
                    failed_count += 1
            
            return {
                "status": "completed",
                "total_symbols": len(symbol_list),
                "successful": successful_count,
                "failed": failed_count,
                "message": f"Time-sensitive data update completed for {len(symbol_list)} symbols"
            }
        
        else:
            # Update all symbols in database
            logger.info("Updating time-sensitive data for all symbols in database")
            
            results = controller.update_all_time_sensitive_data()
            
            return {
                "status": "completed",
                "total_symbols": results["total"],
                "successful": results["successful"], 
                "failed": results["failed"],
                "message": f"Time-sensitive data update completed for all symbols"
            }
            
    except Exception as e:
        logger.error(f"Error in update_time_sensitive_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stocks/scrap-latest/{symbol}")
def get_scanx_stock_data_by_path(request: Request, symbol: str) -> Dict[str, Any]:
    """
    GET endpoint to fetch ScanX stock data for a specific symbol using path parameter.
    
    Args:
        symbol: Stock symbol from URL path
        
    Returns:
        Dict containing stock data
    """
    try:
        symbol = symbol.upper().strip()
        logger.info(f"Path-based request for symbol: {symbol}")
        
        controller = ScanXStockDataController()
        result = controller.scrape_single_symbol(symbol)
        
        if result:
            clean_result = convert_object_ids(result)
            return {
                "status": "success",
                "symbol": symbol,
                "data": clean_result
            }
        else:
            return {
                "status": "error",
                "symbol": symbol,
                "message": f"No data found for symbol: {symbol}",
                "data": None
            }
            
    except Exception as e:
        logger.error(f"Error in get_scanx_stock_data_by_path: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/stocks/remove-from-db/{symbol}")
def delete_scanx_stock_data_by_symbol(request: Request, symbol: str) -> Dict[str, Any]:
    """
    DELETE endpoint to remove ScanX stock data for a specific symbol from MongoDB.

    Args:
        symbol: Stock symbol to delete

    Returns:
        Dict containing deletion status
    """
    try:
        symbol = symbol.upper().strip()
        logger.info(f"Delete request for symbol: {symbol}")

        controller = ScanXStockDataController()
        deleted_count = controller.db_manager.mongo_db[controller.collection_name].delete_many({"symbol": symbol}).deleted_count

        if deleted_count > 0:
            return {
                "status": "success",
                "symbol": symbol,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} documents for symbol: {symbol}"
            }
        else:
            return {
                "status": "error",
                "symbol": symbol,
                "deleted_count": 0,
                "message": f"No documents found for symbol: {symbol}"
            }

    except Exception as e:
        logger.error(f"Error deleting data for symbol {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Patch health_check to use IST timestamp
@router.get("/scanx/health")
def health_check_ist(request: Request) -> Dict[str, Any]:
    """
    Health check endpoint for ScanX stock data service (IST timestamp).
    """
    try:
        controller = ScanXStockDataController()
        db_status = "connected" if controller.db_manager.mongo_db else "disconnected"
        collection_count = controller.db_manager.mongo_db[controller.collection_name].count_documents({})
        return {
            "status": "healthy",
            "service": "ScanX Stock Data Scraper",
            "database_status": db_status,
            "collection": controller.collection_name,
            "total_documents": collection_count,
            "timestamp": get_current_time_ist()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "ScanX Stock Data Scraper",
            "error": str(e),
            "timestamp": get_current_time_ist()
        }
        
        
