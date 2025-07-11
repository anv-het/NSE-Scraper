import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

class NSELogger:
    _loggers = {}
    
    def __init__(self):
        self.log_level = logging.INFO
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.date_format = '%Y-%m-%d %H:%M:%S'
        self.log_dir = 'logs'
        self.max_file_size = 10 * 1024 * 1024  # 10 MB
        self.backup_count = 5
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """
        Get or create a logger instance
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Logger instance
        """
        if name is None:
            name = 'nse_scraper'
            
        # Return existing logger if already created
        if name in self._loggers:
            return self._loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatter
        formatter = logging.Formatter(self.log_format, self.date_format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        log_filename = os.path.join(self.log_dir, f'{name}.log')
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error file handler (separate file for errors)
        error_log_filename = os.path.join(self.log_dir, f'{name}_error.log')
        error_file_handler = RotatingFileHandler(
            error_log_filename,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        logger.addHandler(error_file_handler)
        
        # Store logger
        self._loggers[name] = logger
        
        # Log initial message
        logger.info(f"Logger '{name}' initialized successfully")
        
        return logger
    
    def set_log_level(self, level: str):
        """
        Set logging level for all loggers
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.log_level = level_map[level.upper()]
            
            # Update existing loggers
            for logger in self._loggers.values():
                logger.setLevel(self.log_level)
                for handler in logger.handlers:
                    if not isinstance(handler, logging.FileHandler) or 'error' not in handler.baseFilename:
                        handler.setLevel(self.log_level)
        else:
            raise ValueError(f"Invalid log level: {level}")
    
    def create_daily_log_file(self, name: str) -> str:
        """
        Create a daily log file with timestamp
        
        Args:
            name: Base name for the log file
            
        Returns:
            Full path to the log file
        """
        timestamp = datetime.now().strftime('%Y%m%d')
        log_filename = f"{name}_{timestamp}.log"
        return os.path.join(self.log_dir, log_filename)
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up log files older than specified days
        
        Args:
            days: Number of days to keep logs
        """
        try:
            current_time = datetime.now()
            
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if (current_time - file_time).days > days:
                        os.remove(file_path)
                        print(f"Removed old log file: {filename}")
                        
        except Exception as e:
            print(f"Error cleaning up old logs: {str(e)}")

# Global logger instance
nse_logger = NSELogger()

def get_logger(name: str = None) -> logging.Logger:
    """
    Get logger instance - main function to use throughout the application
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return nse_logger.get_logger(name)

def set_log_level(level: str):
    """Set logging level globally"""
    nse_logger.set_log_level(level)

def cleanup_logs(days: int = 30):
    """Clean up old log files"""
    nse_logger.cleanup_old_logs(days)

# Configure logging based on config file if available
try:
    import configparser
    config = configparser.ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
        if config.has_section('PATH') and config.has_option('PATH', 'LOGGER_PATH'):
            nse_logger.log_dir = config.get('PATH', 'LOGGER_PATH')
            if not os.path.exists(nse_logger.log_dir):
                os.makedirs(nse_logger.log_dir)
except Exception:
    # If config reading fails, use default settings
    pass
