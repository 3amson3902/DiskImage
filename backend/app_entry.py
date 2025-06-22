"""
app_entry.py - Main application entry logic for DiskImage.
Handles GUI launch, QEMU extraction, and cleanup.
"""
import logging
from backend.qemu_utils import init_qemu
from backend.cleanup_utils import cleanup_qemu_files
from backend.logging_utils import setup_logging
from backend.config_utils import load_config

def run_app():
    """Main entry point: launches the PyQt6 GUI. Add CLI entry here if needed."""
    setup_logging()
    try:
        init_qemu()
        logging.info("QEMU dependencies extracted at startup.")
    except Exception as e:
        logging.error(f"QEMU extraction failed at startup: {e}")
    from gui.pyqt_app import run_pyqt_gui
    import sys
    try:
        run_pyqt_gui()
    except Exception as e:
        logging.exception("Fatal error in main application loop")
        print(f"Fatal error: {e}. See diskimager_main.log for details.")
        sys.exit(1)
    finally:
        config = load_config()
        if config.get('cleanup_tools', True):
            cleanup_qemu_files()
            logging.info("QEMU dependencies cleaned up on exit.")
        else:
            logging.info("QEMU cleanup skipped due to user config.")
