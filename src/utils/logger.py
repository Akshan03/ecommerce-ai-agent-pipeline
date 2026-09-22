"""
Standardized logging configuration module.
Provides a setup function to create loggers that output to both console and file.
"""
import logging
import sys
from config.settings import settings, BASE_DIR

def setup_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger instance.
    
    Args:
        name (str): The name of the module (usually __name__).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times if instantiated repeatedly
    if logger.hasHandlers():
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_file = BASE_DIR / "pipeline.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger