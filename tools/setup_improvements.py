#!/usr/bin/env python3
"""
Setup script for improved Bitaxe Monitor
Helps transition from old collector to new improved version
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

def main():
    print("=== Bitaxe Monitor Improvement Setup ===\n")
    
    # Check if we're in the right directory
    if not os.path.exists('collector.py'):
        print("ERROR: This script should be run from the simple-monitor directory")
        print("Make sure you're in C:\\dev\\simple-monitor")
        sys.exit(1)
    
    print("1. Creating backup of original collector...")
    
    # Backup original collector
    if os.path.exists('collector.py'):
        backup_name = f"collector_original_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2('collector.py', backup_name)
        print(f"   Original collector saved as: {backup_name}")
    
    # Create backups directory if it doesn't exist
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    print(f"   Created backups directory: {backup_dir}")
    
    # Backup existing CSV files
    print("\n2. Backing up existing CSV files...")
    csv_files = ['metrics.csv', 'metrics_backup.csv', 'metrics_temp.csv']
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            backup_csv = backup_dir / f"{Path(csv_file).stem}_setup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            shutil.copy2(csv_file, backup_csv)
            print(f"   Backed up: {csv_file} -> {backup_csv}")
    
    # Replace collector.py with improved version
    print("\n3. Installing improved collector...")
    if os.path.exists('collector_improved.py'):
        shutil.copy2('collector_improved.py', 'collector.py')
        print("   ✓ Installed improved collector as collector.py")
    else:
        print("   ERROR: collector_improved.py not found!")
        sys.exit(1)
    
    # Check if corrupted CSV exists and suggest repair
    print("\n4. Checking for corrupted CSV files...")
    if os.path.exists('metrics_backup_corrupted.csv'):
        print("   Found corrupted CSV file: metrics_backup_corrupted.csv")
        print("   You can repair it using:")
        print("   python csv_repair.py analyze metrics_backup_corrupted.csv")
        print("   python csv_repair.py repair metrics_backup_corrupted.csv")
    
    # Show current config
    print("\n5. Current configuration:")
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r') as f:
            content = f.read()
            print("   config.yaml contents:")
            for line in content.split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    print(f"     {line}")
    
    print("\n=== SETUP COMPLETE ===")
    print("\nWhat's new in the improved collector:")
    print("  ✓ Reduced polling interval to 30 seconds")
    print("  ✓ Persistent hostname caching (survives network issues)")
    print("  ✓ Robust CSV handling with corruption prevention")
    print("  ✓ Automatic backups and validation")
    print("  ✓ Enhanced error handling and recovery")
    print("  ✓ CSV repair tools included")
    
    print("\nHow to use:")
    print("  Start monitoring: python collector.py")
    print("  Check CSV health: python csv_repair.py analyze metrics.csv")
    print("  Repair corruption: python csv_repair.py repair <corrupted_file>")
    print("  View statistics: python csv_repair.py stats metrics.csv")
    
    print("\nNew features:")
    print("  - Hostname cache file: hostname_cache.json")
    print("  - Backup directory: backups/")
    print("  - Automatic periodic backups every 100 collection cycles")
    print("  - Cached hostnames shown with * when network is flaky")
    
    print("\nIf you encounter issues:")
    print("  1. Check backups/ directory for recent copies")
    print("  2. Use csv_repair.py to analyze and fix corruption")
    print("  3. Hostname cache will rebuild automatically")
    
    print("\nReady to start improved monitoring!")

if __name__ == "__main__":
    main()
