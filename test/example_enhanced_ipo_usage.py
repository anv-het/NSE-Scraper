#!/usr/bin/env python3
"""
Enhanced IPO Scraper Usage Example
==================================
Simple examples showing how to use the new enhanced IPO scraping functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from API.Controller.scrap_investorgain_ipo_data import NSEInvestorGainIPOController
from Utils.ipo_utils import fetch_ipo_list_v2
from Utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

def example_basic_usage():
    """
    Example 1: Basic usage with current month/year
    """
    logger.info("📚 Example 1: Basic Usage (Current Month/Year)")
    logger.info("-" * 50)
    
    try:
        # Initialize controller
        controller = NSEInvestorGainIPOController()
        
        # Scrape current month/year (default)
        result = controller.scrape_investorgain_ipo_data()
        
        if result["success"]:
            logger.info(f"✅ Successfully scraped {result['data_count']} IPO records")
            logger.info(f"📅 Period: {result.get('month')}/{result.get('year')} (FY: {result.get('fin_year')})")
            
            # Show database results
            if result.get("database_result"):
                db_result = result["database_result"]
                logger.info(f"🗄️ Database: {db_result.get('inserted_count', 0)} inserted, {db_result.get('updated_count', 0)} updated")
            
            # Show file results
            if result.get("json_file_result"):
                json_result = result["json_file_result"]
                logger.info(f"📁 JSON file saved: {json_result.get('filepath', 'N/A')}")
        else:
            logger.error(f"❌ Scraping failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"💥 Error in basic usage example: {e}")

def example_targeted_scraping():
    """
    Example 2: Targeted scraping for specific month/year
    """
    logger.info("\n📚 Example 2: Targeted Scraping (Specific Month/Year)")
    logger.info("-" * 50)
    
    try:
        # Initialize controller
        controller = NSEInvestorGainIPOController()
        
        # Example: Scrape August 2025
        month = 8
        year = 2025
        fin_year = "2025-26"
        
        logger.info(f"🎯 Scraping IPOs for {month}/{year} (FY: {fin_year})")
        
        result = controller.scrape_investorgain_ipo_data(
            month=month,
            year=year,
            fin_year=fin_year
        )
        
        if result["success"]:
            logger.info(f"✅ Successfully scraped {result['data_count']} IPO records")
            logger.info(f"📅 Period: {result.get('month')}/{result.get('year')} (FY: {result.get('fin_year')})")
        else:
            logger.error(f"❌ Targeted scraping failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"💥 Error in targeted scraping example: {e}")

def example_direct_api_usage():
    """
    Example 3: Direct API usage without full scraping
    """
    logger.info("\n📚 Example 3: Direct API Usage")
    logger.info("-" * 50)
    
    try:
        # Get current date
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        current_fin_year = f"{current_year}-{str(current_year+1)[-2:]}"
        
        logger.info(f"🔌 Fetching IPO list directly from API for {current_month}/{current_year}")
        
        # Fetch IPO list directly
        ipo_list = fetch_ipo_list_v2(current_month, current_year, current_fin_year)
        
        if ipo_list:
            logger.info(f"✅ Successfully fetched {len(ipo_list)} IPO records from API")
            
            # Show sample data
            if ipo_list:
                sample = ipo_list[0]
                logger.info("📋 Sample IPO data:")
                logger.info(f"  IPO ID: {sample.get('ipoId')}")
                logger.info(f"  Company: {sample.get('apiCompanyName')}")
                logger.info(f"  Status: {sample.get('apiIpoStatusFormatted')}")
                logger.info(f"  Exchange: {sample.get('apiExchange')}")
                logger.info(f"  Board: {sample.get('apiBoard')}")
                logger.info(f"  GMP: {sample.get('apiGmpValue')}")
                logger.info(f"  Fire Rating: {sample.get('apiFireRating')}")
        else:
            logger.warning("⚠️ No IPO data returned from API")
            
    except Exception as e:
        logger.error(f"💥 Error in direct API usage example: {e}")

def example_batch_processing():
    """
    Example 4: Batch processing multiple months
    """
    logger.info("\n📚 Example 4: Batch Processing Multiple Months")
    logger.info("-" * 50)
    
    try:
        # Initialize controller
        controller = NSEInvestorGainIPOController()
        
        # Define months to process
        months_to_process = [
            (7, 2025, "2025-26"),  # July 2025
            (8, 2025, "2025-26"),  # August 2025
            (9, 2025, "2025-26"),  # September 2025
        ]
        
        total_records = 0
        
        for month, year, fin_year in months_to_process:
            logger.info(f"🔄 Processing {month}/{year} (FY: {fin_year})")
            
            try:
                result = controller.scrape_investorgain_ipo_data(
                    month=month,
                    year=year,
                    fin_year=fin_year
                )
                
                if result["success"]:
                    records_count = result.get('data_count', 0)
                    total_records += records_count
                    logger.info(f"✅ {month}/{year}: {records_count} records processed")
                else:
                    logger.warning(f"⚠️ {month}/{year}: {result['message']}")
                    
            except Exception as e:
                logger.error(f"❌ {month}/{year}: Error - {e}")
        
        logger.info(f"📊 Batch processing completed. Total records: {total_records}")
        
    except Exception as e:
        logger.error(f"💥 Error in batch processing example: {e}")

def main():
    """
    Main function to run all examples
    """
    logger.info("🚀 Enhanced IPO Scraper - Usage Examples")
    logger.info("=" * 60)
    
    # Run all examples
    example_basic_usage()
    example_targeted_scraping()
    example_direct_api_usage()
    example_batch_processing()
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 All examples completed!")
    logger.info("💡 Check the logs above for results and any errors.")
    logger.info("📖 For more details, see ENHANCED_IPO_SCRAPER_README.md")

if __name__ == "__main__":
    main() 