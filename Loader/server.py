from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from API.Router import top_gainers_loosers
import threading
# from Services.cron_jobs_top_gainer_looser import job as run_gainers_loosers_cron




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
app.include_router(top_gainers_loosers.router)



# Home route
@app.get("/")
async def root():
    return {"message": "Welcome to NSE Scraper API"}




