#!/usr/bin/env python3
"""
main.py - Entry point for DiskImage application

Provides both CLI and GUI interfaces based on command line arguments.
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app_entry import run_app
from cli.main import main as cli_main


def main():
    """Main entry point - routes to CLI or GUI based on arguments."""
    # If no arguments provided, launch GUI
    if len(sys.argv) == 1:
        run_app()
        return
    
    # Check if first argument is a GUI-specific flag
    gui_flags = ['--gui', 'gui']
    if len(sys.argv) > 1 and sys.argv[1] in gui_flags:
        # Remove the GUI flag and launch GUI
        sys.argv.pop(1)
        run_app()
        return
    
    # Otherwise, use CLI
    cli_main()


if __name__ == "__main__":
    main()
