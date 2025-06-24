#!/usr/bin/env python3
"""
Simple Bitaxe Gamma Monitor - Data Collector
Collects metrics from configured miners and logs to CSV
"""

import csv
import time
import random
import yaml
from datetime import datetime
import os
import sys

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("Error: config.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        sys.exit(1)

def simulate_miner_metrics(miner_ip):
    """Simulate collecting metrics from a Bitaxe Gamma miner"""
    # Simulate realistic mining metrics
    hashrate = random.uniform(450, 550)  # GH/s
    temperature = random.uniform(45, 75)  # Celsius    power = random.uniform(8, 15)  # Watts
    frequency = random.uniform(450, 500)  # MHz
    voltage = random.uniform(1.2, 1.4)  # Volts
    efficiency = hashrate / power if power > 0 else 0  # GH/J
    
    # Simulate some occasional errors or offline status
    status = "online" if random.random() > 0.05 else "offline"
    if status == "offline":
        hashrate = 0
        temperature = 0
        power = 0
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'miner_ip': miner_ip,
        'status': status,
        'hashrate_ghs': round(hashrate, 2),
        'temperature_c': round(temperature, 1),
        'power_w': round(power, 2),
        'frequency_mhz': round(frequency, 1),
        'voltage_v': round(voltage, 3),
        'efficiency_ghj': round(efficiency, 2)
    }

def write_csv_header(csv_path):
    """Write CSV header if file doesn't exist"""
    if not os.path.exists(csv_path):
        fieldnames = ['timestamp', 'miner_ip', 'status', 'hashrate_ghs', 
                     'temperature_c', 'power_w', 'frequency_mhz', 'voltage_v', 'efficiency_ghj']
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        print(f"Created new CSV file: {csv_path}")

def append_metrics_to_csv(metrics_list, csv_path):
    """Append metrics to CSV file"""
    fieldnames = ['timestamp', 'miner_ip', 'status', 'hashrate_ghs', 
                 'temperature_c', 'power_w', 'frequency_mhz', 'voltage_v', 'efficiency_ghj']
    
    with open(csv_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for metrics in metrics_list:
            writer.writerow(metrics)

def collect_all_miners(config):
    """Collect metrics from all configured miners"""
    print(f"Collecting metrics from {len(config['miners'])} miners...")
    all_metrics = []
    
    for miner_ip in config['miners']:
        print(f"  Polling {miner_ip}...", end=' ')
        try:
            metrics = simulate_miner_metrics(miner_ip)
            all_metrics.append(metrics)
            status_indicator = "OK" if metrics['status'] == 'online' else "ERR"
            print(f"{status_indicator} {metrics['status']} ({metrics['hashrate_ghs']} GH/s)")
        except Exception as e:
            print(f"ERR Error: {e}")
            # Add error entry
            error_metrics = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'miner_ip': miner_ip,
                'status': 'error',
                'hashrate_ghs': 0,
                'temperature_c': 0,
                'power_w': 0,
                'frequency_mhz': 0,
                'voltage_v': 0,
                'efficiency_ghj': 0
            }
            all_metrics.append(error_metrics)
    
    return all_metrics

def main():
    """Main collector loop"""
    print("=== Simple Bitaxe Gamma Monitor - Collector ===")
    
    # Load configuration
    config = load_config()
    csv_path = config['csv_path']
    poll_interval = config['poll_interval']
    
    print(f"Monitoring {len(config['miners'])} miners")
    print(f"Poll interval: {poll_interval} seconds")
    print(f"CSV output: {csv_path}")
    print(f"Press Ctrl+C to stop\n")
    
    # Initialize CSV file
    write_csv_header(csv_path)
    
    try:
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{timestamp}] Collection cycle started")
            
            # Collect metrics from all miners
            all_metrics = collect_all_miners(config)
            
            # Write to CSV
            append_metrics_to_csv(all_metrics, csv_path)
            print(f"Wrote {len(all_metrics)} records to {csv_path}")
            
            # Wait for next poll
            print(f"Waiting {poll_interval} seconds until next poll...")
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print("\n\nCollector stopped by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main()