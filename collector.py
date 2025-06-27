#!/usr/bin/env python3
import csv
import time
import random
import yaml
from datetime import datetime
from pathlib import Path

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def collect_metrics(miner_ip):
    """
    Collect metrics from a Bitaxe Gamma miner.
    For now, this generates fake data for testing.
    Replace with actual API calls to your miners.
    """
    # Simulate realistic Bitaxe Gamma metrics
    return {
        'timestamp': datetime.now().isoformat(),
        'miner_ip': miner_ip,
        'hashrate_gh': round(random.uniform(450, 550), 2),  # GH/s
        'temperature': round(random.uniform(60, 85), 1),    # Celsius
        'power_w': round(random.uniform(15, 25), 1),        # Watts
        'uptime_s': random.randint(3600, 86400),            # Seconds
        'accepted_shares': random.randint(100, 1000),
        'rejected_shares': random.randint(0, 5),
        'pool_difficulty': random.randint(1000, 10000),
    }

def write_to_csv(data, csv_path):
    """Write metrics data to CSV file"""
    csv_file = Path(csv_path)
    file_exists = csv_file.exists()
    
    with open(csv_path, 'a', newline='') as f:
        fieldnames = ['timestamp', 'miner_ip', 'hashrate_gh', 'temperature', 
                     'power_w', 'uptime_s', 'accepted_shares', 'rejected_shares', 
                     'pool_difficulty']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)

def main():
    """Main collector loop"""
    config = load_config()
    
    print(f"Starting Bitaxe Gamma Monitor")
    print(f"Monitoring {len(config['miners'])} miners: {', '.join(config['miners'])}")
    print(f"Poll interval: {config['poll_interval']} seconds")
    print(f"CSV output: {config['csv_path']}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            for miner_ip in config['miners']:
                try:
                    metrics = collect_metrics(miner_ip)
                    write_to_csv(metrics, config['csv_path'])
                    print(f"✓ Collected metrics from {miner_ip} - {metrics['hashrate_gh']} GH/s")
                except Exception as e:
                    print(f"✗ Error collecting from {miner_ip}: {e}")
            
            time.sleep(config['poll_interval'])
            
    except KeyboardInterrupt:
        print("\nStopping collector...")

if __name__ == "__main__":
    main()