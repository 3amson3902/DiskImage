import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import platform
import subprocess
from datetime import datetime
import logging
import gui

# Initialize logging
logging.basicConfig(filename='diskimager_main.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s')

def main():
    gui.run_gui()

if __name__ == "__main__":
    main()
