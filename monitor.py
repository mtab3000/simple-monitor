#!/usr/bin/env python3
"""
Bitaxe Monitor - Main Launcher
Runs the collector from the organized src/ directory
"""
import sys
import os

# Add src directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run collector
if __name__ == "__main__":
    from collector import main
    main()
