from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from API.Router import top_gainers_loosers
import threading
# from Services.cron_jobs_top_gainer_looser import job as run_gainers_loosers_cron


from Utils.logger import get_logger
from Constant.general import APP_NAME, APP_VERSION, APP_DESCRIPTION
from Utils.monitor import get_all_services_health

# Import routers
from API.Router import (
    top_gainers_loosers,
    nse_all_indexes,
    nse_52week_high_low,
)
from Utils.response import create_response

logger = get_logger(__name__)

app = FastAPI(
    title="NSE Scraper API",
    description="Scrape and serve NSE top gainers and loosers",
    version="1.0.0"
)


# CORS middleware to allow cross-origin requests
# Enable CORS (optional but useful if using frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(top_gainers_loosers.router, prefix='/gainers-loosers', tags=['Top Gainers and Loosers'])
app.include_router(nse_all_indexes.router, prefix='/indexes', tags=['NSE Indexes'])
app.include_router(nse_52week_high_low.router, prefix='/52week-high-low', tags=['52 Week High/Low'])


# Home route
@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "message": "Welcome to NSE Scraper API"
    }

# Health check routefrom Utils.monitor import get_all_services_health

@app.get("/meta/health")
async def meta_health_check():
    return create_response(
        success=True,
        data=get_all_services_health(),
        message="Server health metadata"
    )




