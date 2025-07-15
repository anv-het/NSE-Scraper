# main.py
"""Main entry point for the NSE Scraper API server.
This script initializes and runs the FastAPI application.
"""
import uvicorn
from Utils.config_reader import configure
from Loader.server import apiserver

if __name__ == "__main__":
    uvicorn.run(
        "Loader.server:apiserver",
        host=configure.get("SERVER", "HOST"),
        port=configure.getint("SERVER", "PORT"),
        reload=True  
    )

