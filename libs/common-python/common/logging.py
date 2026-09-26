"""
Shared Logging Configuration Module

Provides standardized structured JSON / console logging setup across all homelab Python services.

Intended Usage:
    from common.logging import setup_logging
    logger = setup_logging(service_name="bus-scraper", level="INFO")
    logger.info("Scraper execution started", extra={"days": 21})
"""

import logging
import os
import sys

def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """Configures structured log formatting for a given service.
    
    Args:
        service_name: Name of the service emitting log records.
        level: Minimum log level string (DEBUG, INFO, WARNING, ERROR).
        
    Returns:
        Configured standard library logger instance.
    """
    logger = logging.getLogger(service_name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            f"[%(asctime)s] [%(levelname)s] [{service_name}] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
