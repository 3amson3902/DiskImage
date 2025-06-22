"""
logging_utils.py - Logging setup and utilities for the disk imaging app.

Provides robust error/debug logging configuration for all modules.
LLM prompt: This module sets up and manages logging for the app and its submodules.
"""
import logging
import os

def setup_logging(logfile='diskimage.log', level=logging.INFO):
    """
    Set up logging to file and console for the app.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(logfile, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
