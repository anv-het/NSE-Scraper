#!/usr/bin/env python3
"""
NSE Real-time Data Scraper
This script scrapes real NSE data and saves it to MongoDB
"""

import time
import traceback
from datetime import datetime
from typing import Dict, List, Any
from Utils.logger import get_logger
from Utils.db import DatabaseManager

logger = get_logger(__name__)

class NSERealTimeScraper:
    def __init__(self):
        """Initialize the NSE real-time scraper"""
        self.db = DatabaseManager()
        self.controllers = {}
        self.available_scrapers = []
        
        # Initialize available controllers
        self._initialize_controllers()
        
        logger.info(f"✅ Initialized scraper with {len(self.available_scrapers)} available scrapers")

    def _initialize_controllers(self):
        """Initialize all available controllers safely"""
        controller_configs = [
            {
                'name': 'top_gainers_losers',
                'module': 'API.Controller.top_gainers_loosers',
                'class': 'NSETopGainersloosersController',
                'methods': ['scrape_top_gainers', 'scrape_top_loosers']
            },
            {
                'name': 'all_indexes',
                'module': 'API.Controller.nse_all_indexes',
                'class': 'NSEAllIndexesController', 
                'methods': ['scrape_all_indices_from_list']
            },
            {
                'name': '52_week_data',
                'module': 'API.Controller.nse_52week_high_low',
                'class': 'NSE52WeekHighLowController',
                'methods': ['scrape_52_week_high', 'scrape_52_week_low']
            },
            {
                'name': 'price_band',
                'module': 'API.Controller.nse_price_band_hitter', 
                'class': 'NSEPriceBandHittersController',
                'methods': ['scrape_upper_circuit', 'scrape_lower_circuit']
            },
            {
                'name': 'advances_declines',
                'module': 'API.Controller.advances_declines_unchanged',
                'class': 'NSEAdvancesDeclinesUnchangedController',
                'methods': ['scrape_advances', 'scrape_declines', 'scrape_unchanged']
            },
            {
                'name': 'most_active_equities',
                'module': 'API.Controller.most_active_data_eq',
                'class': 'NSEMostActiveEquitiesController',
                'methods': ['scrape_most_active_equities']
            },
            {
                'name': 'most_active_contracts',
                'module': 'API.Controller.most_active_contract',
                'class': 'NSEMostActiveContractsController',
                'methods': ['scrape_most_active_contracts']
            },
            {
                'name': 'large_deals',
                'module': 'API.Controller.large_deal',
                'class': 'NSELargeDealsController',
                'methods': ['scrape_large_deals']
            },
            {
                'name': 'forthcoming_listings',
                'module': 'API.Controller.forth_comming_listing',
                'class': 'NSEForthcomingListingsController',
                'methods': ['scrape_forthcoming_listings']
            }
        ]
        
        for config in controller_configs:
            try:
                # Dynamic import
                module = __import__(config['module'], fromlist=[config['class']])
                controller_class = getattr(module, config['class'])
                controller_instance = controller_class()
                
                # Verify methods exist
                available_methods = []
                for method_name in config['methods']:
                    if hasattr(controller_instance, method_name):
                        available_methods.append(method_name)
                
                if available_methods:
                    self.controllers[config['name']] = {
                        'instance': controller_instance,
                        'methods': available_methods
                    }
                    self.available_scrapers.extend([f"{config['name']}.{method}" for method in available_methods])
                    logger.info(f"✅ Loaded {config['name']}: {', '.join(available_methods)}")
                else:
                    logger.warning(f"⚠️  {config['name']}: No methods available")
                    
            except Exception as e:
                logger.warning(f"⚠️  Failed to load {config['name']}: {str(e)}")

    def scrape_gainers_losers(self) -> Dict[str, bool]:
        """Scrape gainers and losers data"""
        results = {}
        
        if 'top_gainers_losers' not in self.controllers:
            logger.warning("❌ Gainers/Losers controller not available")
            return {'gainers': False, 'losers': False}
        
        controller = self.controllers['top_gainers_losers']['instance']
        
        # Scrape gainers
        if 'scrape_top_gainers' in self.controllers['top_gainers_losers']['methods']:
            try:
                logger.info("🔄 Scraping top gainers...")
                gainers_data = controller.scrape_top_gainers()
                
                if gainers_data.get('success') and gainers_data.get('data'):
                    success = self.db.save_data(gainers_data['data'], "gainers")
                    results['gainers'] = success
                    logger.info(f"✅ Gainers data saved: {success}")
                else:
                    results['gainers'] = False
                    logger.warning("⚠️  No gainers data received")
                    
            except Exception as e:
                logger.error(f"❌ Error scraping gainers: {str(e)}")
                results['gainers'] = False
        
        # Scrape losers  
        if 'scrape_top_loosers' in self.controllers['top_gainers_losers']['methods']:
            try:
                logger.info("🔄 Scraping top losers...")
                losers_data = controller.scrape_top_loosers()
                
                if losers_data.get('success') and losers_data.get('data'):
                    success = self.db.save_data(losers_data['data'], "losers")
                    results['losers'] = success
                    logger.info(f"✅ Losers data saved: {success}")
                else:
                    results['losers'] = False
                    logger.warning("⚠️  No losers data received")
                    
            except Exception as e:
                logger.error(f"❌ Error scraping losers: {str(e)}")
                results['losers'] = False
        
        return results

    def scrape_all_indexes(self) -> bool:
        """Scrape all NSE indexes"""
        if 'all_indexes' not in self.controllers:
            logger.warning("❌ All indexes controller not available")
            return False
        
        try:
            controller = self.controllers['all_indexes']['instance']
            logger.info("🔄 Scraping all NSE indexes...")
            
            indexes_data = controller.scrape_all_indices_from_list()
            
            if indexes_data.get('success') and indexes_data.get('data'):
                success = self.db.save_data(indexes_data['data'], "indices", index_name="ALL_INDEXES")
                logger.info(f"✅ Indexes data saved: {success}")
                return success
            else:
                logger.warning("⚠️  No indexes data received")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error scraping indexes: {str(e)}")
            return False

    def scrape_52_week_data(self) -> Dict[str, bool]:
        """Scrape 52-week high/low data"""
        results = {}
        
        if '52_week_data' not in self.controllers:
            logger.warning("❌ 52-week data controller not available")
            return {'52week_high': False, '52week_low': False}
        
        controller = self.controllers['52_week_data']['instance']
        
        # Scrape 52-week highs
        if 'scrape_52_week_high' in self.controllers['52_week_data']['methods']:
            try:
                logger.info("🔄 Scraping 52-week highs...")
                high_data = controller.scrape_52_week_high()
                
                if high_data.get('success') and high_data.get('data'):
                    success = self.db.save_data(high_data['data'], "52week_high")
                    results['52week_high'] = success
                    logger.info(f"✅ 52-week high data saved: {success}")
                else:
                    results['52week_high'] = False
                    logger.warning("⚠️  No 52-week high data received")
                    
            except Exception as e:
                logger.error(f"❌ Error scraping 52-week highs: {str(e)}")
                results['52week_high'] = False
        
        # Scrape 52-week lows
        if 'scrape_52_week_low' in self.controllers['52_week_data']['methods']:
            try:
                logger.info("🔄 Scraping 52-week lows...")
                low_data = controller.scrape_52_week_low()
                
                if low_data.get('success') and low_data.get('data'):
                    success = self.db.save_data(low_data['data'], "52week_low")
                    results['52week_low'] = success
                    logger.info(f"✅ 52-week low data saved: {success}")
                else:
                    results['52week_low'] = False
                    logger.warning("⚠️  No 52-week low data received")
                    
            except Exception as e:
                logger.error(f"❌ Error scraping 52-week lows: {str(e)}")
                results['52week_low'] = False
        
        return results

    def scrape_comprehensive_data(self) -> Dict[str, Any]:
        """Scrape all available NSE data"""
        logger.info("=" * 60)
        logger.info("🚀 Starting comprehensive NSE data scraping...")
        logger.info(f"📊 Available scrapers: {len(self.available_scrapers)}")
        logger.info("=" * 60)
        
        start_time = time.time()
        all_results = {}
        
        # Define scraping tasks
        scraping_tasks = [
            ("💰 Gainers & Losers", self.scrape_gainers_losers),
            ("📈 All Indexes", self.scrape_all_indexes), 
            ("📊 52-Week Data", self.scrape_52_week_data),
        ]
        
        # Add more tasks based on available controllers
        if 'price_band' in self.controllers:
            scraping_tasks.append(("🎯 Price Band Data", self.scrape_price_band_data))
        
        if 'advances_declines' in self.controllers:
            scraping_tasks.append(("📊 Advances & Declines", self.scrape_advances_declines))
        
        if 'most_active_equities' in self.controllers:
            scraping_tasks.append(("⚡ Most Active Equities", self.scrape_most_active_equities))
        
        if 'most_active_contracts' in self.controllers:
            scraping_tasks.append(("📋 Most Active Contracts", self.scrape_most_active_contracts))
        
        if 'large_deals' in self.controllers:
            scraping_tasks.append(("💎 Large Deals", self.scrape_large_deals))
        
        if 'forthcoming_listings' in self.controllers:
            scraping_tasks.append(("🆕 Forthcoming Listings", self.scrape_forthcoming_listings))
        
        # Execute scraping tasks
        for task_name, task_func in scraping_tasks:
            logger.info(f"\n{task_name}")
            logger.info("-" * 40)
            
            try:
                result = task_func()
                all_results[task_name] = result
                
                # Log results
                if isinstance(result, dict):
                    for key, value in result.items():
                        status = "✅ SUCCESS" if value else "❌ FAILED"
                        logger.info(f"   {key}: {status}")
                else:
                    status = "✅ SUCCESS" if result else "❌ FAILED" 
                    logger.info(f"   Result: {status}")
                    
            except Exception as e:
                logger.error(f"❌ {task_name} failed: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                all_results[task_name] = False
            
            # Delay between requests to be respectful to NSE servers
            time.sleep(3)
        
        # Generate summary
        self._print_scraping_summary(all_results, time.time() - start_time)
        return all_results

    def scrape_price_band_data(self) -> Dict[str, bool]:
        """Scrape price band data"""
        results = {}
        
        if 'price_band' not in self.controllers:
            return {'upper_circuit': False, 'lower_circuit': False}
        
        controller = self.controllers['price_band']['instance']
        
        # Upper circuit
        if 'scrape_upper_circuit' in self.controllers['price_band']['methods']:
            try:
                logger.info("🔄 Scraping upper circuit...")
                upper_data = controller.scrape_upper_circuit()
                if upper_data.get('success') and upper_data.get('data'):
                    success = self.db.save_data(upper_data['data'], "price_band", band_type="upper")
                    results['upper_circuit'] = success
                    logger.info(f"✅ Upper circuit saved: {success}")
                else:
                    results['upper_circuit'] = False
                    logger.warning("⚠️  No upper circuit data")
            except Exception as e:
                logger.error(f"❌ Error scraping upper circuit: {str(e)}")
                results['upper_circuit'] = False
        
        # Lower circuit
        if 'scrape_lower_circuit' in self.controllers['price_band']['methods']:
            try:
                logger.info("🔄 Scraping lower circuit...")
                lower_data = controller.scrape_lower_circuit()
                if lower_data.get('success') and lower_data.get('data'):
                    success = self.db.save_data(lower_data['data'], "price_band", band_type="lower")
                    results['lower_circuit'] = success
                    logger.info(f"✅ Lower circuit saved: {success}")
                else:
                    results['lower_circuit'] = False
                    logger.warning("⚠️  No lower circuit data")
            except Exception as e:
                logger.error(f"❌ Error scraping lower circuit: {str(e)}")
                results['lower_circuit'] = False
        
        return results

    def scrape_advances_declines(self) -> Dict[str, bool]:
        """Scrape advances/declines data"""
        results = {}
        
        if 'advances_declines' not in self.controllers:
            return {'advances': False, 'declines': False}
        
        controller = self.controllers['advances_declines']['instance']
        
        for data_type in ['advances', 'declines']:
            method_name = f'scrape_{data_type}'
            if method_name in self.controllers['advances_declines']['methods']:
                try:
                    logger.info(f"🔄 Scraping {data_type}...")
                    method = getattr(controller, method_name)
                    data = method()
                    if data.get('success') and data.get('data'):
                        success = self.db.save_data(data['data'], data_type)
                        results[data_type] = success
                        logger.info(f"✅ {data_type} saved: {success}")
                    else:
                        results[data_type] = False
                        logger.warning(f"⚠️  No {data_type} data")
                except Exception as e:
                    logger.error(f"❌ Error scraping {data_type}: {str(e)}")
                    results[data_type] = False
        
        return results

    def scrape_most_active_equities(self) -> bool:
        """Scrape most active equities"""
        if 'most_active_equities' not in self.controllers:
            return False
        
        try:
            controller = self.controllers['most_active_equities']['instance']
            logger.info("🔄 Scraping most active equities...")
            data = controller.scrape_most_active_equities()
            if data.get('success') and data.get('data'):
                success = self.db.save_data(data['data'], "most_active", index_type="equity")
                logger.info(f"✅ Most active equities saved: {success}")
                return success
            else:
                logger.warning("⚠️  No most active equities data")
                return False
        except Exception as e:
            logger.error(f"❌ Error scraping most active equities: {str(e)}")
            return False

    def scrape_most_active_contracts(self) -> bool:
        """Scrape most active contracts"""
        if 'most_active_contracts' not in self.controllers:
            return False
        
        try:
            controller = self.controllers['most_active_contracts']['instance']
            logger.info("🔄 Scraping most active contracts...")
            data = controller.scrape_most_active_contracts()
            if data.get('success') and data.get('data'):
                success = self.db.save_data(data['data'], "most_active", index_type="contracts")
                logger.info(f"✅ Most active contracts saved: {success}")
                return success
            else:
                logger.warning("⚠️  No most active contracts data")
                return False
        except Exception as e:
            logger.error(f"❌ Error scraping most active contracts: {str(e)}")
            return False

    def scrape_large_deals(self) -> bool:
        """Scrape large deals"""
        if 'large_deals' not in self.controllers:
            return False
        
        try:
            controller = self.controllers['large_deals']['instance']
            logger.info("🔄 Scraping large deals...")
            data = controller.scrape_large_deals()
            if data.get('success') and data.get('data'):
                success = self.db.save_data(data['data'], "block_deals")
                logger.info(f"✅ Large deals saved: {success}")
                return success
            else:
                logger.warning("⚠️  No large deals data")
                return False
        except Exception as e:
            logger.error(f"❌ Error scraping large deals: {str(e)}")
            return False

    def scrape_forthcoming_listings(self) -> bool:
        """Scrape forthcoming listings"""
        if 'forthcoming_listings' not in self.controllers:
            return False
        
        try:
            controller = self.controllers['forthcoming_listings']['instance']
            logger.info("🔄 Scraping forthcoming listings...")
            data = controller.scrape_forthcoming_listings()
            if data.get('success') and data.get('data'):
                success = self.db.save_data(data['data'], "new_listings", listing_type="forthcoming")
                logger.info(f"✅ Forthcoming listings saved: {success}")
                return success
            else:
                logger.warning("⚠️  No forthcoming listings data")
                return False
        except Exception as e:
            logger.error(f"❌ Error scraping forthcoming listings: {str(e)}")
            return False

    def _print_scraping_summary(self, results: Dict, duration: float):
        """Print detailed scraping summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 COMPREHENSIVE SCRAPING SUMMARY")
        logger.info("=" * 60)
        
        total_tasks = 0
        successful_tasks = 0
        
        for task_name, result in results.items():
            logger.info(f"\n📋 {task_name}:")
            if isinstance(result, dict):
                for sub_task, success in result.items():
                    status = "✅ SUCCESS" if success else "❌ FAILED"
                    logger.info(f"   • {sub_task}: {status}")
                    total_tasks += 1
                    if success:
                        successful_tasks += 1
            else:
                status = "✅ SUCCESS" if result else "❌ FAILED"
                logger.info(f"   • Result: {status}")
                total_tasks += 1
                if result:
                    successful_tasks += 1
        
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        logger.info(f"\n📈 OVERALL STATISTICS:")
        logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
        logger.info(f"📊 Success Rate: {successful_tasks}/{total_tasks} ({success_rate:.1f}%)")
        logger.info(f"💾 Database: MongoDB WEB_SCRAPING")
        logger.info(f"🔄 Available Scrapers: {len(self.available_scrapers)}")
        
        if successful_tasks > 0:
            logger.info(f"✅ Data successfully saved to MongoDB collections!")
        else:
            logger.info(f"⚠️  No data was saved. Check NSE connectivity and controllers.")
        
        logger.info("=" * 60)

    def continuous_scraping(self, interval_minutes: int = 5):
        """Run continuous scraping"""
        logger.info(f"🔄 Starting continuous scraping every {interval_minutes} minutes...")
        logger.info(f"📡 Available controllers: {list(self.controllers.keys())}")
        
        try:
            while True:
                logger.info(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting scraping cycle...")
                self.scrape_comprehensive_data()
                logger.info(f"😴 Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("🛑 Continuous scraping stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in continuous scraping: {str(e)}")

    def __del__(self):
        """Cleanup database connection"""
        if hasattr(self, 'db'):
            self.db.close_connection()

def main():
    """Main function"""
    try:
        scraper = NSERealTimeScraper()
        
        print("\n🚀 NSE Real-time Data Scraper")
        print("=" * 50)
        print("Available options:")
        print("1. 📊 Scrape all data once")
        print("2. 🔄 Continuous scraping (5 min interval)")
        print("3. ⏰ Continuous scraping (15 min interval)")
        print("4. 🎯 Custom interval")
        print("5. 📋 Show available scrapers")
        print("=" * 50)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            logger.info("🎯 Single scraping session selected")
            scraper.scrape_comprehensive_data()
            
        elif choice == "2":
            logger.info("🔄 Continuous scraping (5 min) selected")
            scraper.continuous_scraping(5)
            
        elif choice == "3":
            logger.info("⏰ Continuous scraping (15 min) selected")
            scraper.continuous_scraping(15)
            
        elif choice == "4":
            try:
                interval = int(input("Enter interval in minutes: "))
                if interval > 0:
                    logger.info(f"🎯 Custom interval ({interval} min) selected")
                    scraper.continuous_scraping(interval)
                else:
                    print("❌ Invalid interval. Using default 5 minutes.")
                    scraper.continuous_scraping(5)
            except ValueError:
                print("❌ Invalid interval. Using default 5 minutes.")
                scraper.continuous_scraping(5)
                
        elif choice == "5":
            print(f"\n📋 Available scrapers ({len(scraper.available_scrapers)}):")
            for scraper_name in scraper.available_scrapers:
                print(f"  • {scraper_name}")
            print(f"\n📊 Controllers loaded: {list(scraper.controllers.keys())}")
            
        else:
            print("❌ Invalid choice. Running single scrape...")
            scraper.scrape_comprehensive_data()
            
    except Exception as e:
        logger.error(f"❌ Main function failed: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
