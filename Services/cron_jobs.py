"""
NSE Data Collection Cron Jobs
Automated data scraping and saving to MongoDB with proper error handling and logging
"""

import asyncio
import schedule
import time
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.logger import get_logger
from Utils.db import DatabaseManager
from Services.get_nse_cookies import get_nse_cookies
from Constant.general import CRON_INTERVALS
from Utils.utilities_functions import is_market_open


# Import controllers
from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController
from API.Controller.forth_comming_listing import NSEForthcomingListingsController
from API.Controller.large_deal import NSELargeDealsController
from API.Controller.most_active_contract import NSEMostActiveContractsController
from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController
from API.Controller.most_active_underlying import NSEMostActiveUnderlyingController
from API.Controller.new_listing_stoks import NSENewListingsController
from API.Controller.nse_52week_high_low import NSE52WeekHighLowController
from API.Controller.nse_all_indexes import NSEAllIndexesController
from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController
from API.Controller.recent_listing import NSERecentListingsController
from API.Controller.special_preopen_listing import NSESpecialPreopenListingsController
from API.Controller.top_gainers_loosers import NSETopGainersloosersController
from API.Controller.scrap_investorgain_ipo_data import NSEInvestorGainIPOController


logger = get_logger(__name__)




# class CronJobManager:
#     """
#     Class for managing cron jobs
#     """

#     def run_cron_jobs(self):
#         """
#         Run all cron jobs based on the defined intervals
#         """
#         try:
#             # Check if the market is open before scheduling jobs
#             if is_market_open():
#                 logger.info("Cron-jobs:Market is open. Scheduling cron jobs.")

#                 schedule.every(CRON_INTERVALS['ADVANCES_DECLINES_UNCHANGED']).minutes.do(
#                     self.run_advances_declines_unchanged
#                 )
#                 schedule.every(CRON_INTERVALS['FORTHCOMING_LISTINGS']).minutes.do(
#                     self.run_forthcoming_listings
#                 )
#                 schedule.every(CRON_INTERVALS['LARGE_DEALS']).minutes.do(
#                     self.run_large_deals
#                 )
#                 schedule.every(CRON_INTERVALS['MOST_ACTIVE_CONTRACTS']).minutes.do(
#                     self.run_most_active_contracts
#                 )
#                 schedule.every(CRON_INTERVALS['MOST_ACTIVE_EQUITIES']).minutes.do(
#                     self.run_most_active_equities
#                 )
#                 schedule.every(CRON_INTERVALS['MOST_ACTIVE_UNDERLYING']).minutes.do(
#                     self.run_most_active_underlying
#                 )
#                 schedule.every(CRON_INTERVALS['NEW_LISTINGS']).minutes.do(
#                     self.run_new_listings
#                 )
#                 schedule.every(CRON_INTERVALS['NSE_52_WEEK_HIGH_LOW']).minutes.do(
#                     self.run_nse_52_week_high_low
#                 )
#                 schedule.every(CRON_INTERVALS['NSE_ALL_INDEXES']).minutes.do(
#                     self.run_nse_all_indexes
#                 )
#                 schedule.every(CRON_INTERVALS['PRICE_BAND_HITTERS']).minutes.do(
#                     self.run_price_band_hitters
#                 )
#                 schedule.every(CRON_INTERVALS['RECENT_LISTINGS']).minutes.do(
#                     self.run_recent_listings
#                 )
#                 schedule.every(CRON_INTERVALS['SPECIAL_PREOPEN_LISTINGS']).minutes.do(
#                     self.run_special_preopen_listings
#                 )
#                 schedule.every(CRON_INTERVALS['TOP_GAINERS_LOOSERS']).minutes.do(
#                     self.run_top_gainers_loosers
#                 )
#                 schedule.every(CRON_INTERVALS['INVESTORGAIN_IPO_DATA']).minutes.do(
#                     self.run_investorgain_ipo_data
#                 )
#                 schedule.every(CRON_INTERVALS['COOKIE_REFRESH']).minutes.do(
#                     self.refresh_cookies
#                 )
            
#             else:
#                 logger.info("Cron-jobs:Market is closed. Cron jobs will not run.")
            
#         except Exception as e:
#             logger.error(f"Cron-jobs:Error in run_cron_jobs: {e}")
#             raise

#         # Start the scheduler
#         while True:
#             schedule.run_pending()
#             time.sleep(1)
    

class CronJobManager:
    """
    Class for managing cron jobs dynamically
    """

    def __init__(self):
        self.jobs_scheduled = False


    def schedule_jobs(self):
        """Schedule all cron jobs"""

        schedule.every(CRON_INTERVALS['ADVANCES_DECLINES_UNCHANGED']).minutes.do(
        self.run_advances_declines_unchanged
        )
        schedule.every(CRON_INTERVALS['FORTHCOMING_LISTINGS']).minutes.do(
            self.run_forthcoming_listings
        )
        schedule.every(CRON_INTERVALS['LARGE_DEALS']).minutes.do(
            self.run_large_deals
        )
        schedule.every(CRON_INTERVALS['MOST_ACTIVE_CONTRACTS']).minutes.do(
            self.run_most_active_contracts
        )
        schedule.every(CRON_INTERVALS['MOST_ACTIVE_EQUITIES']).minutes.do(
            self.run_most_active_equities
        )
        schedule.every(CRON_INTERVALS['MOST_ACTIVE_UNDERLYING']).minutes.do(
            self.run_most_active_underlying
        )
        schedule.every(CRON_INTERVALS['NEW_LISTINGS']).minutes.do(
            self.run_new_listings
        )
        schedule.every(CRON_INTERVALS['NSE_52_WEEK_HIGH_LOW']).minutes.do(
            self.run_nse_52_week_high_low
        )
        schedule.every(CRON_INTERVALS['NSE_ALL_INDEXES']).minutes.do(
            self.run_nse_all_indexes
        )
        schedule.every(CRON_INTERVALS['PRICE_BAND_HITTERS']).minutes.do(
            self.run_price_band_hitters
        )
        schedule.every(CRON_INTERVALS['RECENT_LISTINGS']).minutes.do(
            self.run_recent_listings
        )
        schedule.every(CRON_INTERVALS['SPECIAL_PREOPEN_LISTINGS']).minutes.do(
            self.run_special_preopen_listings
        )
        schedule.every(CRON_INTERVALS['TOP_GAINERS_LOOSERS']).minutes.do(
            self.run_top_gainers_loosers
        )
        schedule.every(CRON_INTERVALS['INVESTORGAIN_IPO_DATA']).minutes.do(
            self.run_investorgain_ipo_data
        )
        schedule.every(CRON_INTERVALS['COOKIE_REFRESH']).minutes.do(
            self.refresh_cookies
        )

    def run_cron_jobs(self):
        """Run cron jobs dynamically based on market status"""
        try:
            while True:
                if is_market_open():
                    if not self.jobs_scheduled:
                        logger.info("Market is OPEN. Scheduling cron jobs...")
                        self.schedule_jobs()
                        self.jobs_scheduled = True
                else:
                    if self.jobs_scheduled:
                        logger.info("Market is CLOSED. Clearing all scheduled jobs...")
                        schedule.clear()
                        self.jobs_scheduled = False

                # Run pending jobs if any
                schedule.run_pending()
                time.sleep(1)

        except Exception as e:
            logger.error(f"Cron-jobs: Error in run_cron_jobs: {e}")
            raise


    def refresh_cookies(self):
        """
        Refresh NSE cookies
        """
        try:
            get_nse_cookies()
            logger.info("Cron-jobs:NSE cookies refreshed successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error refreshing NSE cookies: {e} at " + datetime.now().isoformat())
            raise

    def run_advances_declines_unchanged(self):
        """
        Run the NSE Advances Declines Unchanged job
        """
        try:
            controller = NSEAdvancesDeclinesUnchangedController()
            asyncio.run(controller.scrap_advance_decline_unchanged())
            logger.info("Cron-jobs:Cron Job-NSE Advances Declines Unchanged data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron Job-Error in run_advances_declines_unchanged: {e} at " + datetime.now().isoformat())
            raise
    
    def run_forthcoming_listings(self):
        """
        Run the NSE Forthcoming Listings job
        """
        try:
            controller = NSEForthcomingListingsController()
            asyncio.run(controller.scrap_forthcoming_listings())
            logger.info("Cron-jobs:NSE Forthcoming Listings data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_forthcoming_listings: {e} at " + datetime.now().isoformat())
            raise
    
    def run_large_deals(self):
        """
        Run the NSE Large Deals job
        """
        try:
            controller = NSELargeDealsController()
            asyncio.run(controller.scrap_large_deals())
            logger.info("Cron-jobs:NSE Large Deals data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_large_deals: {e} at " + datetime.now().isoformat())
            raise
    
    def run_most_active_contracts(self):
        """
        Run the NSE Most Active Contracts job
        """
        try:
            controller = NSEMostActiveContractsController()
            asyncio.run(controller.scrap_most_active_contracts())
            logger.info("Cron-jobs:NSE Most Active Contracts data saved successfully.   at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_most_active_contracts: {e} at " + datetime.now().isoformat())
            raise
    
    def run_most_active_equities(self):
        """
        Run the NSE Most Active Equities job
        """
        try:
            controller = NSEMostActiveEquitiesController()
            asyncio.run(controller.scrape_most_active_equities())
            logger.info("Cron-jobs:NSE Most Active Equities data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_most_active_equities: {e} at " + datetime.now().isoformat())
            raise
    
    def run_most_active_underlying(self):
        """
        Run the NSE Most Active Underlying job
        """
        try:
            controller = NSEMostActiveUnderlyingController()
            asyncio.run(controller.scrap_most_active_underlying())
            logger.info("Cron-jobs:NSE Most Active Underlying data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_most_active_underlying: {e} at " + datetime.now().isoformat())
            raise
    
    def run_new_listings(self):
        """
        Run the NSE New Listings job
        """
        try:
            controller = NSENewListingsController()
            asyncio.run(controller.scrap_new_listing())
            logger.info("Cron-jobs:NSE New Listings data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_new_listings: {e} at " + datetime.now().isoformat())
            raise
    
    def run_nse_52_week_high_low(self):
        """
        Run the NSE 52 Week High Low job
        """
        try:
            controller = NSE52WeekHighLowController()
            asyncio.run(controller.scrape_52_week_high_low())
            logger.info("Cron-jobs:NSE 52 Week High Low data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_nse_52_week_high_low: {e} at " + datetime.now().isoformat())
            raise

    def run_nse_all_indexes(self):
        """
        Run the NSE All Indexes job
        """
        try:
            controller = NSEAllIndexesController()
            asyncio.run(controller.scrape_all_indices_from_list())
            logger.info("Cron-jobs:NSE All Indexes data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_nse_all_indexes: {e} at " + datetime.now().isoformat())
            raise

    def run_price_band_hitters(self):
        """
        Run the NSE Price Band Hitters job
        """
        try:
            controller = NSEPriceBandHittersController()
            asyncio.run(controller.scrap_price_band_hitters())
            logger.info("Cron-jobs:NSE Price Band Hitters data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_price_band_hitters: {e} at " + datetime.now().isoformat())
            raise

    def run_recent_listings(self):
        """
        Run the NSE Recent Listings job
        """
        try:
            controller = NSERecentListingsController()
            asyncio.run(controller.scrap_recent_listings())
            logger.info("Cron-jobs:NSE Recent Listings data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_recent_listings: {e} at " + datetime.now().isoformat())
            raise
    
    def run_special_preopen_listings(self):
        """
        Run the NSE Special Preopen Listings job
        """
        try:
            controller = NSESpecialPreopenListingsController()
            asyncio.run(controller.scrap_special_preopen_listings())
            logger.info("Cron-jobs:NSE Special Preopen Listings data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_special_preopen_listings: {e} at " + datetime.now().isoformat())
            raise
    
    def run_top_gainers_loosers(self):
        """
        Run the Top Gainers and Losers job
        """
        try:
            controller = NSETopGainersloosersController()
            asyncio.run(controller.top_gainer_loosers())
            logger.info("Cron-jobs:Top Gainers and Losers data saved successfully. at " + datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_top_gainers_loosers: {e} at " + datetime.now().isoformat())
            raise

    def run_investorgain_ipo_data(self):
        """
        Run the InvestorGain IPO Data scraping job
        """
        try:
            controller = NSEInvestorGainIPOController()
            result = controller.scrape_investorgain_ipo_data()
            
            if result["success"]:
                logger.info(f"Cron-jobs:InvestorGain IPO data saved successfully. {result['message']} at {datetime.now().isoformat()}")
            else:
                logger.error(f"Cron-jobs:InvestorGain IPO data scraping failed: {result['message']} at {datetime.now().isoformat()}")
                
        except Exception as e:
            logger.error(f"Cron-jobs:Error in run_investorgain_ipo_data: {e} at {datetime.now().isoformat()}")
            raise



