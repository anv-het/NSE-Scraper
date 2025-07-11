import configparser
import os
from typing import Any, Optional
from Utils.logger import get_logger

logger = get_logger(__name__)

class ConfigReader:
    def __init__(self, config_file: str = 'config.ini'):
        # Get the project root directory (where config.ini should be)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = os.path.join(project_root, config_file)
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.error(f"Configuration file {self.config_file} not found")
                raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get configuration value as string"""
        try:
            value = self.config.get(section, key, fallback=fallback)
            return value
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logger.warning(f"Configuration key not found: [{section}] {key}")
            if fallback is not None:
                return fallback
            raise e
    
    def getint(self, section: str, key: str, fallback: Any = None) -> int:
        """Get configuration value as integer"""
        try:
            value = self.config.getint(section, key, fallback=fallback)
            return value
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logger.warning(f"Configuration key not found: [{section}] {key}")
            if fallback is not None:
                return fallback
            raise e
        except ValueError as e:
            logger.error(f"Invalid integer value for [{section}] {key}")
            raise e
    
    def getfloat(self, section: str, key: str, fallback: Any = None) -> float:
        """Get configuration value as float"""
        try:
            value = self.config.getfloat(section, key, fallback=fallback)
            return value
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logger.warning(f"Configuration key not found: [{section}] {key}")
            if fallback is not None:
                return fallback
            raise e
        except ValueError as e:
            logger.error(f"Invalid float value for [{section}] {key}")
            raise e
    
    def getboolean(self, section: str, key: str, fallback: Any = None) -> bool:
        """Get configuration value as boolean"""
        try:
            value = self.config.getboolean(section, key, fallback=fallback)
            return value
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logger.warning(f"Configuration key not found: [{section}] {key}")
            if fallback is not None:
                return fallback
            raise e
        except ValueError as e:
            logger.error(f"Invalid boolean value for [{section}] {key}")
            raise e
    
    def get_section(self, section: str) -> dict:
        """Get all configuration values from a section"""
        try:
            if self.config.has_section(section):
                return dict(self.config.items(section))
            else:
                logger.warning(f"Configuration section not found: {section}")
                return {}
        except Exception as e:
            logger.error(f"Error getting section {section}: {str(e)}")
            return {}
    
    def has_section(self, section: str) -> bool:
        """Check if section exists in configuration"""
        return self.config.has_section(section)
    
    def has_option(self, section: str, key: str) -> bool:
        """Check if option exists in configuration"""
        return self.config.has_option(section, key)
    
    def sections(self) -> list:
        """Get list of all sections"""
        return self.config.sections()
    
    def reload_config(self):
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        self._load_config()
    
    def set(self, section: str, key: str, value: str):
        """Set configuration value"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, key, str(value))
            logger.info(f"Configuration updated: [{section}] {key} = {value}")
        except Exception as e:
            logger.error(f"Error setting configuration: {str(e)}")
            raise
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise

# Global configuration instance
configure = ConfigReader()

def get_config() -> ConfigReader:
    """Get global configuration instance"""
    return configure

def reload_config():
    """Reload global configuration"""
    configure.reload_config()

def get_database_config() -> dict:
    """Get database configuration"""
    return configure.get_section('DB')

def get_server_config() -> dict:
    """Get server configuration"""
    return configure.get_section('SERVER')

def get_nse_config() -> dict:
    """Get NSE configuration"""
    return configure.get_section('NSE')

def get_scraping_config() -> dict:
    """Get scraping configuration"""
    return configure.get_section('SCRAPING')

def get_cron_config() -> dict:
    """Get cron configuration"""
    return configure.get_section('CRON')
