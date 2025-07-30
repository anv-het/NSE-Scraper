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
from Constant.general import CRON_INTERVALS, DATA_RETENTION_DAYS

# Import controllers
from API.Controller.top_gainers_loosers import NSETopGainersloosersController
from API.Controller.nse_all_indexes import NSEAllIndexesController
from API.Controller.most_active_data_eq import NSEMostActiveEquitiesController
from API.Controller.nse_price_band_hitter import NSEPriceBandHittersController
from API.Controller.nse_52week_high_low import NSE52WeekHighLowController
from API.Controller.large_deal import NSELargeDealsController
from API.Controller.advances_declines_unchanged import NSEAdvancesDeclinesUnchangedController
from API.Controller.new_listing_stoks import NSENewListingsController
from API.Controller.most_active_contract import NSEMostActiveContractsController
from API.Controller.most_active_underlying import NSEMostActiveUnderlyingController
from API.Controller.stockwise_event_data import StockwiseEventDataController

logger = get_logger(__name__)

class NSEDataCronJobs:
    """Main cron job manager for NSE data collection"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.is_running = False
        self.job_stats = {}
        
        # Initialize controllers
        self.controllers = {
            'gainers_losers': NSETopGainersloosersController(),
            'all_indexes': NSEAllIndexesController(),
            'most_active': NSEMostActiveEquitiesController(),
            'price_band': NSEPriceBandHittersController(),
            '52week': NSE52WeekHighLowController(),
            'large_deals': NSELargeDealsController(),
            'advances_declines': NSEAdvancesDeclinesUnchangedController(),
            'new_listings': NSENewListingsController(),
            'most_active_contracts': NSEMostActiveContractsController(),
            'most_active_underlying': NSEMostActiveUnderlyingController(),
            'stock_events': StockwiseEventDataController()
        }
        
        logger.info("NSE Data Cron Jobs initialized")
    
    def log_job_execution(self, job_name: str, success: bool, records_saved: int = 0, error_msg: str = ""):
        """Log job execution statistics"""
        timestamp = datetime.now(timezone.utc)
        
        if job_name not in self.job_stats:
            self.job_stats[job_name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'total_records_saved': 0,
                'last_run': None,
                'last_success': None,
                'last_error': None
            }
        
        stats = self.job_stats[job_name]
        stats['total_runs'] += 1
        stats['last_run'] = timestamp
        
        if success:
            stats['successful_runs'] += 1
            stats['total_records_saved'] += records_saved
            stats['last_success'] = timestamp
            logger.info(f"{job_name}: SUCCESS - {records_saved} records saved")
        else:
            stats['failed_runs'] += 1
            stats['last_error'] = error_msg
            logger.error(f"{job_name}: FAILED - {error_msg}")
    
    def job_gainers_losers(self):
        """Cron job for gainers and losers data"""
        job_name = "GAINERS_LOSERS"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            total_records = 0
            
            # Gainers
            gainers_response = self.controllers['gainers_losers'].scrape_top_gainers()
            if gainers_response.get('success') and gainers_response.get('data'):
                raw_data = gainers_response['data']
                if self.db_manager.save_data_with_cleanup(raw_data, "gainers", DATA_RETENTION_DAYS['GAINERS_LOSERS']):
                    total_records += len(gainers_response['data'].get('data', []))
            
            # Losers
            losers_response = self.controllers['gainers_losers'].scrape_top_loosers()
            if losers_response.get('success') and losers_response.get('data'):
                raw_data = losers_response['data']
                if self.db_manager.save_data_with_cleanup(raw_data, "losers", DATA_RETENTION_DAYS['GAINERS_LOSERS']):
                    total_records += len(losers_response['data'].get('data', []))
            
            self.log_job_execution(job_name, True, total_records)
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_indices_data(self):
        """Cron job for indices data"""
        job_name = "INDICES"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            # Use the scrape_all_indices_from_list method instead
            try:
                response = self.controllers['all_indexes'].scrape_all_indices_from_list()
                
                if response and response.get('total_scraped', 0) > 0:
                    total_records = response.get('total_scraped', 0)
                    self.log_job_execution(job_name, True, total_records)
                else:
                    self.log_job_execution(job_name, False, 0, "No data scraped")
                    
            except Exception as e:
                logger.warning(f"Failed to collect indices data: {str(e)}")
                self.log_job_execution(job_name, False, 0, str(e))
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_most_active_data(self):
        """Cron job for most active securities data"""
        job_name = "MOST_ACTIVE"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.controllers['most_active'].scrape_most_active_equities())
            loop.close()
            
            total_records = 0
            
            if response.get('success') and response.get('data'):
                raw_data = response['data']
                if self.db_manager.save_data_with_cleanup(
                    raw_data, "most_active", DATA_RETENTION_DAYS['MOST_ACTIVE'], index_type="equities"
                ):
                    total_records = len(raw_data.get('data', []))
            
            self.log_job_execution(job_name, total_records > 0, total_records)
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_price_band_data(self):
        """Cron job for price band hitters data"""
        job_name = "PRICE_BAND"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            total_records = 0
            
            # Use the available scrap_price_band_hitters method
            try:
                response = self.controllers['price_band'].scrap_price_band_hitters()
                
                if response.get('success') and response.get('data'):
                    total_records = len(response.get('data', []))
                    self.log_job_execution(job_name, True, total_records)
                else:
                    self.log_job_execution(job_name, False, 0, "No data retrieved")
                    
            except Exception as e:
                logger.warning(f"Failed to collect price band data: {str(e)}")
                self.log_job_execution(job_name, False, 0, str(e))
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_52week_data(self):
        """Cron job for 52-week high/low data"""
        job_name = "52_WEEK_DATA"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            total_records = 0
            
            # Use the available scrape_52_week_high_low method
            try:
                response = self.controllers['52week'].scrape_52_week_high_low()
                
                if response.get('success') and response.get('data'):
                    total_records = len(response.get('data', []))
                    self.log_job_execution(job_name, True, total_records)
                else:
                    self.log_job_execution(job_name, False, 0, "No data retrieved")
                    
            except Exception as e:
                logger.warning(f"Failed to collect 52-week data: {str(e)}")
                self.log_job_execution(job_name, False, 0, str(e))
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_large_deals_data(self):
        """Cron job for large deals data"""
        job_name = "LARGE_DEALS"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            # Use the available scrap_large_deals method
            try:
                response = self.controllers['large_deals'].scrap_large_deals()
                
                if response.get('success') and response.get('data'):
                    total_records = len(response.get('data', []))
                    self.log_job_execution(job_name, True, total_records)
                else:
                    self.log_job_execution(job_name, False, 0, "No data retrieved")
                    
            except Exception as e:
                logger.warning(f"Failed to collect large deals data: {str(e)}")
                self.log_job_execution(job_name, False, 0, str(e))
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_advances_declines_data(self):
        """Cron job for advances/declines data"""
        job_name = "ADVANCES_DECLINES"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            total_records = 0
            
            # Use the unified scrap_advance_decline_unchanged method
            response = self.controllers['advances_declines'].scrap_advance_decline_unchanged()
            
            if response.get('success') and response.get('data'):
                raw_data = response['data']
                if self.db_manager.save_data_with_cleanup(raw_data, "advances_declines_unchanged", DATA_RETENTION_DAYS['ADVANCES_DECLINES']):
                    # Count total records from all three categories
                    advances_count = len(raw_data.get('advances', []))
                    declines_count = len(raw_data.get('declines', []))
                    unchanged_count = len(raw_data.get('unchanged', []))
                    total_records = advances_count + declines_count + unchanged_count
                    self.log_job_execution(job_name, True, total_records)
                else:
                    self.log_job_execution(job_name, False, 0, "Failed to save data")
            else:
                self.log_job_execution(job_name, False, 0, "No data retrieved")
                
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_most_active_contracts(self):
        """Cron job for most active contracts data"""
        job_name = "CONTRACTS"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.controllers['most_active_contracts'].scrap_most_active_contracts())
            loop.close()
            
            total_records = 0
            
            if response.get('success') and response.get('data'):
                raw_data = response['data']
                if self.db_manager.save_data_with_cleanup(raw_data, "most_active_contracts", DATA_RETENTION_DAYS['CONTRACTS']):
                    total_records = len(raw_data.get('data', []))
            
            self.log_job_execution(job_name, total_records > 0, total_records)
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_stock_events_data(self):
        """Cron job for stock events data"""
        job_name = "STOCK_EVENTS"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            # Use the bulk scraping method for multiple symbols
            response = self.controllers['stock_events'].scrape_bulk_event_data()
            
            total_records = 0
            
            if response.get('success') and response.get('data'):
                total_records = response.get('successful_symbols', 0)
            
            self.log_job_execution(job_name, total_records > 0, total_records)
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_cookie_refresh(self):
        """Cron job to refresh NSE cookies"""
        job_name = "COOKIE_REFRESH"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            # Refresh cookies
            new_cookies = get_nse_cookies()
            
            if new_cookies:
                logger.info("NSE cookies refreshed successfully")
                self.log_job_execution(job_name, True, 1)
            else:
                self.log_job_execution(job_name, False, 0, "Failed to refresh cookies")
                
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def job_data_cleanup(self):
        """Cron job for data cleanup (old data removal)"""
        job_name = "DATA_CLEANUP"
        try:
            logger.info(f"Starting {job_name} cron job...")
            
            total_deleted = 0
            collections_info = self.db_manager.get_all_collections_info()
            
            for collection_name in collections_info.keys():
                # Map collection names to retention periods
                retention_map = {
                    'gainers_losers': DATA_RETENTION_DAYS['GAINERS_LOSERS'],
                    'indices_data': DATA_RETENTION_DAYS['INDICES'],
                    'most_active_securities': DATA_RETENTION_DAYS['MOST_ACTIVE'],
                    'price_band_hitters': DATA_RETENTION_DAYS['PRICE_BAND'],
                    'week_52_data': DATA_RETENTION_DAYS['52_WEEK_DATA'],
                    'large_deals': DATA_RETENTION_DAYS['LARGE_DEALS'],
                    'advances_declines': DATA_RETENTION_DAYS['ADVANCES_DECLINES'],
                    'new_listings': DATA_RETENTION_DAYS['NEW_LISTINGS'],
                    'most_active_contracts': DATA_RETENTION_DAYS['CONTRACTS'],
                    'most_active_underlying': DATA_RETENTION_DAYS['UNDERLYING'],
                    'stock_events': DATA_RETENTION_DAYS['STOCK_EVENTS']
                }
                
                retention_days = retention_map.get(collection_name, 30)  # Default 30 days
                deleted_count = self.db_manager.cleanup_old_data(collection_name, retention_days)
                total_deleted += deleted_count
            
            self.log_job_execution(job_name, True, total_deleted)
            
        except Exception as e:
            self.log_job_execution(job_name, False, 0, str(e))
    
    def setup_cron_schedules(self):
        """Setup all cron job schedules"""
        logger.info("Setting up cron job schedules...")
        
        # Schedule jobs based on intervals defined in constants
        schedule.every(CRON_INTERVALS['GAINERS_LOSERS']).minutes.do(self.job_gainers_losers)
        schedule.every(CRON_INTERVALS['INDICES']).minutes.do(self.job_indices_data)
        schedule.every(CRON_INTERVALS['MOST_ACTIVE']).minutes.do(self.job_most_active_data)
        schedule.every(CRON_INTERVALS['PRICE_BAND']).minutes.do(self.job_price_band_data)
        schedule.every(CRON_INTERVALS['52_WEEK_DATA']).minutes.do(self.job_52week_data)
        schedule.every(CRON_INTERVALS['LARGE_DEALS']).minutes.do(self.job_large_deals_data)
        schedule.every(CRON_INTERVALS['ADVANCES_DECLINES']).minutes.do(self.job_advances_declines_data)
        schedule.every(CRON_INTERVALS['CONTRACTS']).minutes.do(self.job_most_active_contracts)
        schedule.every(CRON_INTERVALS['STOCK_EVENTS']).minutes.do(self.job_stock_events_data)
        
        # Special schedules
        schedule.every(CRON_INTERVALS['COOKIE_REFRESH']).minutes.do(self.job_cookie_refresh)
        schedule.every(CRON_INTERVALS['DATA_CLEANUP']).minutes.do(self.job_data_cleanup)
        
        logger.info("All cron jobs scheduled successfully")
        logger.info("Schedule Summary:")
        logger.info(f"   • Gainers/Losers: Every {CRON_INTERVALS['GAINERS_LOSERS']} minutes")
        logger.info(f"   • Indices: Every {CRON_INTERVALS['INDICES']} minutes")
        logger.info(f"   • Most Active: Every {CRON_INTERVALS['MOST_ACTIVE']} minutes")
        logger.info(f"   • Price Band: Every {CRON_INTERVALS['PRICE_BAND']} minutes")
        logger.info(f"   • 52-Week Data: Every {CRON_INTERVALS['52_WEEK_DATA']} minutes")
        logger.info(f"   • Large Deals: Every {CRON_INTERVALS['LARGE_DEALS']} minutes")
        logger.info(f"   • Advances/Declines: Every {CRON_INTERVALS['ADVANCES_DECLINES']} minutes")
        logger.info(f"   • Contracts: Every {CRON_INTERVALS['CONTRACTS']} minutes")
        logger.info(f"   • Cookie Refresh: Every {CRON_INTERVALS['COOKIE_REFRESH']} minutes")
        logger.info(f"   • Data Cleanup: Every {CRON_INTERVALS['DATA_CLEANUP']} minutes")
    
    def print_job_statistics(self):
        """Print job execution statistics"""
        logger.info("=" * 60)
        logger.info("📊 NSE CRON JOB STATISTICS")
        logger.info("=" * 60)
        
        for job_name, stats in self.job_stats.items():
            success_rate = (stats['successful_runs'] / stats['total_runs'] * 100) if stats['total_runs'] > 0 else 0
            logger.info(f"🔧 {job_name}:")
            logger.info(f"   Total Runs: {stats['total_runs']}")
            logger.info(f"   Success Rate: {success_rate:.1f}%")
            logger.info(f"   Records Saved: {stats['total_records_saved']}")
            logger.info(f"   Last Success: {stats['last_success']}")
            if stats['last_error']:
                logger.info(f"   Last Error: {stats['last_error']}")
        
        logger.info("=" * 60)
    
    def run_cron_jobs(self):
        """Main cron job runner"""
        self.setup_cron_schedules()
        self.is_running = True
        
        logger.info("NSE Data Cron Jobs started successfully!")
        logger.info("Press Ctrl+C to stop")
        
        try:
            # Run initial cookie refresh
            self.job_cookie_refresh()
            
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Print statistics every hour
                if datetime.now().minute == 0:
                    self.print_job_statistics()
                    
        except KeyboardInterrupt:
            logger.info("⚠️  Cron jobs stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Cron job runner error: {str(e)}")
            self.is_running = False
        finally:
            self.db_manager.close_connection()
            logger.info("🔒 Database connections closed")

def main():
    """Main function to start cron jobs"""
    cron_manager = NSEDataCronJobs()
    
    try:
        # Test database connection
        if not cron_manager.db_manager.test_connection():
            logger.error("❌ Database connection failed. Exiting...")
            return
        
        # Start cron jobs
        cron_manager.run_cron_jobs()
        
    except Exception as e:
        logger.error(f"❌ Failed to start cron jobs: {str(e)}")

if __name__ == "__main__":
    main()
