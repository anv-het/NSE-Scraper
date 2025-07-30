#!/usr/bin/env python3
"""
NSE Scraper Main Entry Point
Starts the FastAPI server with automated cron jobs for data collection
"""

import sys
import os
import threading
import time
import signal
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from Utils.config_reader import configure
from Utils.logger import get_logger
from Loader.server import create_application
from Services.cron_jobs import NSEDataCronJobs

logger = get_logger(__name__)

class NSEScraperApp:
    """Main application class for NSE Scraper with integrated cron jobs"""
    
    def __init__(self):
        self.cron_manager = None
        self.cron_thread = None
        self.is_running = False
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
        
    def start_cron_jobs(self):
        """Start cron jobs in a separate thread"""
        try:
            logger.info("Starting NSE data collection cron jobs...")
            self.cron_manager = NSEDataCronJobs()
            
            # Test database connection first
            if not self.cron_manager.db_manager.test_connection():
                logger.error("Database connection failed! Cron jobs will not start.")
                return False
                
            logger.info("Database connection successful")
            
            # Start cron jobs in background
            self.cron_manager.setup_cron_schedules()
            
            # Run initial cookie refresh
            self.cron_manager.job_cookie_refresh()
            
            # Start cron job loop
            self.is_running = True
            while self.is_running:
                try:
                    import schedule
                    schedule.run_pending()
                    time.sleep(30)  # Check every 30 seconds
                    
                    # Print statistics every 10 minutes
                    if datetime.now().minute % 10 == 0:
                        self.cron_manager.print_job_statistics()
                        
                except Exception as e:
                    logger.error(f"Error in cron job loop: {str(e)}")
                    time.sleep(60)  # Wait before retrying
                    
            logger.info("Cron jobs stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start cron jobs: {str(e)}")
            return False
            
    def start_cron_jobs_thread(self):
        """Start cron jobs in a separate thread"""
        self.cron_thread = threading.Thread(target=self.start_cron_jobs, daemon=True)
        self.cron_thread.start()
        
    def create_app(self):
        """Create FastAPI application"""
        try:
            app = create_application()
            logger.info("FastAPI application created successfully")
            return app
        except Exception as e:
            logger.error(f"Failed to create FastAPI application: {str(e)}")
            return None
            
    def shutdown(self):
        """Graceful shutdown"""
        logger.info(" Shutting down NSE Scraper...")
        
        # Stop cron jobs
        self.is_running = False
        
        # Close database connections
        if self.cron_manager:
            self.cron_manager.db_manager.close_connection()
            
        logger.info("Shutdown complete")
        sys.exit(0)
        
    def run(self):
        """Main run method"""
        print("=" * 80)
        print("NSE SCRAPER - COMPLETE DATA COLLECTION SYSTEM")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Features:")
        print("   • FastAPI Server for data access")
        print("   • Automated NSE data scraping (every minute)")
        print("   • MongoDB storage with data formatting")
        print("   • Real-time data collection and cleanup")
        print("   • Comprehensive logging and monitoring")
        print("=" * 80)
        
        try:
            # Start cron jobs in background
            logger.info("Starting background cron jobs...")
            self.start_cron_jobs_thread()
            time.sleep(2)  # Give cron jobs time to start
            
            # Create FastAPI app
            app = self.create_app()
            if not app:
                logger.error("Failed to create application")
                return
                
            # Get server configuration
            host = configure.get("SERVER", "HOST", fallback="0.0.0.0")
            port = configure.getint("SERVER", "PORT", fallback=8000)
            
            print(f"API Server starting on http://{host}:{port}")
            print(f"API Documentation: http://{host}:{port}/docs")
            print(f"Cron Jobs: Running every minute (testing mode)")
            print(f"Database: MongoDB data storage active")
            print("Press Ctrl+C to stop")
            print("=" * 80)
            
            # Start the FastAPI server
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
        except KeyboardInterrupt:
            logger.info(" Application stopped by user")
            self.shutdown()
        except Exception as e:
            logger.error(f" Application error: {str(e)}")
            self.shutdown()

def main():
    """Main entry point"""
    app = NSEScraperApp()
    app.run()

if __name__ == "__main__":
    main()

