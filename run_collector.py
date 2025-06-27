#!/usr/bin/env python3
"""
Entry point script to run the collector from project root.
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from collector import main

if __name__ == "__main__":
    main()