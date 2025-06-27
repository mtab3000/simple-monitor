#!/usr/bin/env python3
"""
Bitaxe Monitor - Enhanced Collector
Simple launcher for the enhanced monitoring system
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    from enhanced_collector import main
    main()