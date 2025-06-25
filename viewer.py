#!/usr/bin/env python3
"""
Bitaxe Monitor - Viewer Launcher
Runs the CLI viewer from the organized src/ directory
"""
import sys
import os

# Add src directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run viewer
if __name__ == "__main__":
    from cli_view import main
    main()
    