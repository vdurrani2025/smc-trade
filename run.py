#!/usr/bin/env python3
"""
Simple script to run the Streamlit trading bot
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(script_dir, "smc_trader", "main.py")
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", main_file])

