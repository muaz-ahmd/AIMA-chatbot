import logging
import os
from datetime import datetime

from config import ChatbotConfig


class ChatbotLogger:
    """Advanced logging utility"""
    
    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('AmmaarBhaiChatBot')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Clear existing handlers
        logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config.log_level))
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler
        if self.config.log_to_file:
            os.makedirs(os.path.dirname(self.config.log_file_path), exist_ok=True)
            
            file_handler = logging.FileHandler(self.config.log_file_path)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        return logger
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        self.logger.error(message, exc_info=exc_info)
