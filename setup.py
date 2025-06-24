#!/usr/bin/env python3
"""
Bitaxe Monitor - Setup Script
Sets up the monitoring environment and configuration
"""
import os
import sys
import shutil
from pathlib import Path

def main():
    print("=== Bitaxe Monitor Setup ===\n")
    
    script_dir = Path(__file__).parent
    
    # Create config file if it doesn't exist
    config_path = script_dir / "config.yaml"
    example_config = script_dir / "examples" / "config.yaml"
    
    if not config_path.exists() and example_config.exists():
        print("Creating default configuration file...")
        shutil.copy2(example_config, config_path)
        print(f"✓ Created config.yaml from examples/config.yaml")
        print("⚠️  Please edit config.yaml to set your miner IP addresses!")
    elif config_path.exists():
        print("✓ Configuration file already exists")
    else:
        print("❌ No example configuration found!")
    
    # Create data directories
    data_dir = script_dir / "data"
    backups_dir = script_dir / "backups"
    
    for dir_path in [data_dir, backups_dir]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {dir_path.name}")
    
    # Check Python dependencies
    print("\nChecking dependencies...")
    try:
        import yaml
        import requests
        print("✓ All required dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Edit config.yaml with your miner IP addresses")
    print("2. Run: python monitor.py (to start collecting data)")
    print("3. Run: python viewer.py --summary (to view data)")
    print("4. Run: python viewer.py --live (for live dashboard)")
    
    print("\nProject structure:")
    print("├── monitor.py         # Start data collection")
    print("├── viewer.py          # View collected data")
    print("├── config.yaml        # Your configuration")
    print("├── src/               # Source code")
    print("├── tools/             # Utilities & repair tools")
    print("├── docs/              # Documentation")
    print("├── examples/          # Example configurations")
    print("├── data/              # Sample data files")
    print("└── backups/           # Automatic backups")

if __name__ == "__main__":
    main()
