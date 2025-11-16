#!/usr/bin/env python3
"""
Quick run script for BTC Smart Money Chart
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import main

if __name__ == "__main__":
    main()
