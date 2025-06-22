"""
Logging setup and utilities for the disk imaging app.

Provides robust error/debug logging configuration for all modules.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from .constants import LOG_FILE


def setup_logging(
    logfile: Optional[Path] = None, 
    level: int = logging.INFO,
    console_output: bool = True
) -> None:
    """
    Set up logging to file and optionally console for the app.
    
    Args:
        logfile: Path to log file, defaults to LOG_FILE
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to also log to console
    """
    if logfile is None:
        logfile = LOG_FILE
    
    # Ensure log directory exists
    logfile.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # File handler
    try:
        file_handler = logging.FileHandler(logfile, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}", file=sys.stderr)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
    
    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {logging.getLevelName(level)}, File: {logfile}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
