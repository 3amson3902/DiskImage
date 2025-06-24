"""
Main application entry logic for DiskImage.
Handles GUI launch, QEMU extraction, and cleanup.
"""
import sys
import logging
from typing import NoReturn

from .qemu_manager import QemuManager
from .cleanup_utils import cleanup_all_tools
from .logging_utils import setup_logging
from .config_utils import AppConfig
from .thirdparty_downloader import ThirdPartyDownloader

logger = logging.getLogger(__name__)


def run_app() -> NoReturn:
    """
    Main entry point: launches the PyQt6 GUI.
    
    Sets up logging, initializes QEMU, runs the GUI, and handles cleanup.
    """
    # Setup logging first
    try:
        setup_logging()
        logger.info("DiskImage application starting")
    except Exception as e:
        print(f"Failed to setup logging: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration
    try:
        config = AppConfig.load()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        config = AppConfig()  # Use defaults
      # Initialize QEMU dependencies
    try:
        # Ensure third-party tools are available
        ThirdPartyDownloader.ensure_qemu()
        ThirdPartyDownloader.ensure_sevenzip()
        
        qemu_manager = QemuManager()
        qemu_manager.initialize()
        logger.info("QEMU dependencies initialized successfully")
    except Exception as e:
        logger.error(f"QEMU initialization failed: {e}")
        # Continue anyway - GUI can show error to user
    
    # Import and run GUI
    try:
        from gui.pyqt_app import run_pyqt_gui
        logger.info("Launching GUI")
        run_pyqt_gui()
        
    except ImportError as e:
        logger.error(f"Failed to import GUI module: {e}")
        print(f"GUI Error: {e}. Make sure PyQt6 is installed.", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        logger.exception("Fatal error in main application loop")
        print(f"Fatal error: {e}. See {config.__class__.__module__.split('.')[0]}_main.log for details.", file=sys.stderr)
        sys.exit(1)
        
    finally:
        # Cleanup on exit
        try:
            if config.cleanup_tools:
                logger.info("Performing cleanup on exit")
                cleanup_success = cleanup_all_tools()
                if cleanup_success:
                    logger.info("Cleanup completed successfully")
                else:
                    logger.warning("Some cleanup operations failed")
            else:
                logger.info("Cleanup skipped due to user configuration")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
        
        logger.info("DiskImage application exiting")
        sys.exit(0)
