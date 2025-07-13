from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from API.Controller.nse_52week_high_low import NSE52WeekHighLowController
from Utils.verify_token import verify_token
from Utils.response import create_response
from Constant.http import HTTP_STATUS
from Utils.monitor import update_service_health, get_service_health


router = APIRouter()
controller = NSE52WeekHighLowController()


@router.get("/scrape-high-low")
async def scrape_52week_data(token: str = Depends(verify_token)):
    update_service_health("nse_52week_high_low", "/scrape-high-low")
    """
    Scrape 52-week high and low data from NSE website.
    Requires valid authentication token.
    """
    try:
        result = controller.scrape_52_week_high_low()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape 52-week high/low data: {str(e)}"
        )

@router.get("/get-high-low-data")
async def get_52_week_high_low_data(
    week_type: str,
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    update_service_health("nse_52week_high_low", "/get-high-low-data")
    """
    Get 52-week high or low data from database.

    Parameters:
    - week_type: "high" or "low"
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    try:
        result = controller.get_52_week_high_low_data_from_db(week_type, limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve 52-week {week_type} data: {str(e)}"
        )


@router.get("/get-52-week-high")
async def get_52_week_high(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    update_service_health("nse_52week_high_low", "/get-52-week-high")
    """
    Get 52-week high data from database.

    Parameters:
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    try:
        result = controller.get_52_week_high_low_data_from_db("high", limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve 52-week high data: {str(e)}"
        )
    
@router.get("/get-52-week-low")
async def get_52_week_low(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Number of records to return"),
    token: str = Depends(verify_token)
):
    update_service_health("nse_52week_high_low", "/get-52-week-low")
    """
    Get 52-week low data from database.

    Parameters:
    - limit: Number of records to return (1-100, default: 50)
    - token: Authentication token
    """
    try:
        result = controller.get_52_week_high_low_data_from_db("low", limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve 52-week low data: {str(e)}"
        )

@router.get("/refresh-52week-high-low")
async def refresh_52_week_high_low_data(token: str = Depends(verify_token)):
    update_service_health("nse_52week_high_low", "/refresh-52week-high-low")
    """
    Refresh 52-week high and low data by scraping again.
    Requires valid authentication token.
    """
    try:
        result = controller.scrape_52_week_high_low()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh 52-week high/low data: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for 52-week high/low service.
    Returns service health status.
    """
    try:
        health = get_service_health("nse_52week_high_low")
        return create_response(
            success=True,
            data=health,
            message="52-week high/low service health status"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve service health: {str(e)}"
        )
    finally:
        # Perform any necessary cleanup or logging
        pass
