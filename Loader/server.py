from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from API.Router import top_gainers_loosers
import threading
# from Services.cron_jobs_top_gainer_looser import job as run_gainers_loosers_cron


from API.Router import stoks_wise_event_data
from API.Router import scanx_scrap_stocks_data_by_symbol_router
from API.Router import scanx_stock_data_getter_router
from Utils.logger import get_logger
from Constant.general import APP_NAME, APP_VERSION, APP_DESCRIPTION
from Utils.monitor import get_all_services_health

# Import routers
# from API.Router import (
#     top_gainers_loosers,
#     nse_all_indexes,
#     nse_52week_high_low,
# )
from Utils.response import create_response

logger = get_logger(__name__)


def apiserver() -> FastAPI:
    app = FastAPI(
        title="NSE Scraper API",
        description="Scrape and serve NSE data (gainers, loosers, indexes)",
        version="1.0.0",
        docs_url="/docs",         # <== Make sure this line exists or not overridden
        redoc_url="/redoc",       # Optional: also serves docs
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
    # app.include_router(top_gainers_loosers.router, prefix='/gainers-loosers', tags=['Top Gainers and Loosers'])
    # app.include_router(nse_all_indexes.router, prefix='/indexes', tags=['NSE Indexes'])
    # app.include_router(nse_52week_high_low.router, prefix='/52week-high-low', tags=['52 Week High/Low'])
    app.include_router(stoks_wise_event_data.router, prefix='/stoks-wise-event-data', tags=['Stockwise Event Data'])
    app.include_router(scanx_scrap_stocks_data_by_symbol_router.router, prefix='/scanx', tags=['ScanX Stock Data'])
    app.include_router(scanx_stock_data_getter_router.router, prefix='/scanx/getter', tags=['ScanX Getter'])

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


    return app


def create_application() -> FastAPI:
    """Create and configure FastAPI application for main.py integration"""
    app = FastAPI(
        title="NSE Scraper API",
        description="Scrape and serve NSE data (gainers, loosers, indexes)",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Home route
    @app.get("/")
    async def root():
        """Root endpoint to check if the API is running."""
        return {
            "app": APP_NAME,
            "version": APP_VERSION,
            "description": APP_DESCRIPTION,
            "message": "Welcome to NSE Scraper API with Automated Data Collection"
        }

    # Health check route
    @app.get("/meta/health")
    async def meta_health_check():
        return create_response(
            success=True,
            data=get_all_services_health(),
            message="Server health metadata"
        )

    return app


