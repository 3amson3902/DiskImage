#!/usr/bin/env python3
"""
diskimage - Command-line script for DiskImage
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli.main import main

if __name__ == "__main__":
    main()
