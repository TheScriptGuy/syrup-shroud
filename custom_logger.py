import logging
from typing import Optional

class CustomLogger:
    """Custom logging class to handle debug information throughout the application."""
    
    def __init__(self, name: str, level: Optional[str] = None):
        """Initialize the logger with a name and optional level.
        
        Args:
            name (str): Name of the logger
            level (Optional[str]): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if level is None else getattr(logging, level.upper()))
        
        # Create console handler with formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
