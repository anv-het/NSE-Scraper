from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from API.Controller.nse_all_indexes import NSEAllIndexesController
from Utils.verify_token import verify_token
from Utils.response import create_response
from Constant.http import HTTP_STATUS
from Constant.general import ALL_INDICES_LIST
from Utils.monitor import update_service_health, get_service_health


router = APIRouter()
controller = NSEAllIndexesController()


@router.get("/scrape")
async def scrape_index(index_name: str, token: str = Depends(verify_token)):
    update_service_health("nse_indexes", "/scrape")
    """
    Scrape specific NSE index data by index_name from NSE website.
    Requires valid authentication token.
    Example index_name values: "NIFTY 50", "NIFTY BANK"
    """
    try:
        result = controller.scrape_index_data(index_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape index '{index_name}': {str(e)}"
        )

@router.get("/get-name-wise-index-data")
async def get_index_data(
    index_name: str,
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    update_service_health("nse_indexes", "/get-name-wise-index-data")
    """
    Get NSE index data from database by index_name.

    Parameters:
    - index_name: Index to fetch data for, e.g. "NIFTY 50"
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    try:
        result = controller.get_index_data_from_db(index_name, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve index '{index_name}' data: {str(e)}"
        )

@router.get("/scrape-all")
async def scrape_all_indexes(token: str = Depends(verify_token)):
    update_service_health("nse_indexes", "/scrape-all")
    """
    Scrape all NSE indexes defined in the list.
    Requires valid authentication token.
    """
    results = {}
    try:
        for index_name in ALL_INDICES_LIST:
            result = controller.scrape_index_data(index_name)
            if result["success"]:
                results[index_name] = result["data"]
            else:
                results[index_name] = {"error": result["message"]}
        return create_response(
            success=True,
            data=results,
            message="All indexes scraped successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape all indexes: {str(e)}"
        )
    
@router.get("/get-all-indexes")
async def get_all_indexes(token: str = Depends(verify_token)):
    update_service_health("nse_indexes", "/get-all-indexes")
    """
    Get all NSE indexes from the database.
    Requires valid authentication token.
    """
    try:
        result = controller.get_all_indexes_from_db()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve all indexes: {str(e)}"
        )

@router.get("/health")
async def health_check():
    health = get_service_health("nse_indexes")
    return create_response(
        success=True,
        data={
            "status": "healthy",
            "service": "nse_indexes",
            "last_hit_time": health["last_hit_time"],
            "last_endpoint": health["last_endpoint"]
        },
        message="NSE Indexes service is running"
    )

