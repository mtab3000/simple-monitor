#!/usr/bin/env python3
"""
Web Dashboard Launcher for Bitaxe Gamma Monitor
Simple launcher script for the web interface
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from web_server import main

if __name__ == "__main__":
    main()