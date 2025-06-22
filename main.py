import os
import sys
import platform
import subprocess
from datetime import datetime
import logging
import gui

# Initialize logging
logging.basicConfig(filename='diskimager_main.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

# --- Platform Agnostic Main Logic ---

def main():
    gui.run_gui()

if __name__ == "__main__":
    main()
