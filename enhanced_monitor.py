#!/usr/bin/env python3
"""
Enhanced Monitor Launcher for Bitaxe Gamma Monitor
Launcher script for the enhanced database-powered monitoring system
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from src.enhanced_collector import main

if __name__ == "__main__":
    main()