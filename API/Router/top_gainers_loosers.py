from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from API.Controller.top_gainers_loosers import NSETopGainersloosersController
from Utils.verify_token import verify_token
# from Utils.verify_token import verify_token
from Utils.response import create_response
from Constant.http import HTTP_STATUS

router = APIRouter()
controller = NSETopGainersloosersController()

@router.get("/top-gainers/scrape")
async def scrape_top_gainers(token: str = Depends(verify_token)):
    """
    Scrape top gainers data from NSE website
    Requires valid authentication token
    """
    try:
        result = controller.scrape_top_gainers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape top gainers: {str(e)}"
        )

@router.get("/top-looser/scrape")
async def scrape_top_looser(token: str = Depends(verify_token)):
    """
    Scrape top looser data from NSE website
    Requires valid authentication token
    """
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
    try:
        result = controller.get_top_gainers_from_db(limit=limit)
        print(f"🔍 Retrieved {len(result)} top gainers from database")
        print(f"🔍 Limit applied: {limit}, data: {result}")
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
    try:
        result = controller.get_top_loosers_from_db(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_STATUS.INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve top looser: {str(e)}"
        )

@router.get("/gainers-looser/refresh")
async def refresh_gainers_looser_data(token: str = Depends(verify_token)):
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

@router.get("/health")
async def health_check():
    """
    Health check endpoint for top gainers/looser service
    """
    return create_response(
        success=True,
        data={"status": "healthy", "service": "top_gainers_looser"},
        message="Top gainers/looser service is running"
    )
