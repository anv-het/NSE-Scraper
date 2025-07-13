from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from API.Controller.top_gainers_loosers import NSETopGainersloosersController
from Utils.verify_token import verify_token
from Utils.response import create_response
from Constant.http import HTTP_STATUS
from Utils.monitor import update_service_health, get_service_health

router = APIRouter()
controller = NSETopGainersloosersController()

@router.get("/top-gainers/scrape-nse")
async def scrape_top_gainers(token: str = Depends(verify_token)):
    """
    Scrape top gainers data from NSE website
    Requires valid authentication token
    """
    update_service_health("nse_gainers_loosers", "/top-gainers/scrape-nse")
    try:
        result = controller.scrape_top_gainers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape top gainers: {str(e)}"
        )

@router.get("/top-looser/scrape-nse")
async def scrape_top_looser(token: str = Depends(verify_token)):
    """
    Scrape top looser data from NSE website
    Requires valid authentication token
    """
    update_service_health("nse_gainers_loosers", "/top-looser/scrape-nse")
    try:
        result = controller.scrape_top_loosers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape top looser: {str(e)}"
        )

@router.get("/top-gainers")
async def get_top_gainers(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    """
    Get top gainers data from database
    
    Parameters:
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    update_service_health("nse_gainers_loosers", "/top-gainers")
    try:
        result = controller.get_top_gainers_from_db(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve top gainers: {str(e)}"
        )

@router.get("/top-looser")
async def get_top_looser(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    """
    Get top looser data from database
    
    Parameters:
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    update_service_health("nse_gainers_loosers", "/top-looser")
    try:
        result = controller.get_top_loosers_from_db(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve top looser: {str(e)}"
        )

@router.get("/refresh-gainers-loosers")
async def refresh_gainers_looser_data(token: str = Depends(verify_token)):
    update_service_health("nse_gainers_loosers", "/refresh-gainers-loosers")
    """
    Refresh both top gainers and looser data from NSE website
    Requires valid authentication token
    """
    try:
        gainers_result = controller.scrape_top_gainers()
        looser_result = controller.scrape_top_loosers()

        return create_response(
            success=True,
            data={
                "gainers": gainers_result,
                "looser": looser_result
            },
            message="Top gainers and looser data refreshed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh gainers/looser data: {str(e)}"
        )

@router.get("/get-loosers-gainers")
async def get_gainers_and_loosers(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    """
    Get both top gainers and looser data from database
    
    Parameters:
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    update_service_health("nse_gainers_loosers", "/get-loosers-gainers")
    try:
        result = controller.get_top_gainers_and_loosers(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve gainers/looser data: {str(e)}"
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

