#!/usr/bin/env python3
"""
Smart Bitaxe Gamma Monitor - Real API Collector
Connects to actual Bitaxe Gamma miners via their REST API
"""

import csv
import time
import yaml
import requests
import json
from datetime import datetime
import os
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BitaxeCollector:
    def __init__(self, config_path='config.yaml'):
        """Initialize the collector with configuration"""
        self.config = self.load_config(config_path)
        self.session = self.create_session()
        self.csv_path = self.config['csv_path']
        
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            # Validate required fields
            required_fields = ['miners', 'poll_interval', 'csv_path']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required config field: {field}")
                    
            # Set defaults
            config.setdefault('timeout', 10)
            config.setdefault('retries', 3)
            config.setdefault('retry_delay', 1)
            
            return config
        except FileNotFoundError:
            print(f"ERROR: Configuration file '{config_path}' not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"ERROR parsing configuration: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)

    def create_session(self):
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config['retries'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=self.config['retry_delay']
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def get_miner_data(self, miner_ip):
        """Fetch real data from a Bitaxe miner via API"""
        url = f"http://{miner_ip}/api/system/info"
        
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            data = response.json()
            
            # Extract and normalize data from the API response
            return self.parse_miner_response(miner_ip, data)
            
        except requests.exceptions.Timeout:
            return self.create_error_record(miner_ip, "timeout")
        except requests.exceptions.ConnectionError:
            return self.create_error_record(miner_ip, "connection_failed")
        except requests.exceptions.HTTPError as e:
            return self.create_error_record(miner_ip, f"http_error_{e.response.status_code}")
        except json.JSONDecodeError:
            return self.create_error_record(miner_ip, "invalid_json")
        except Exception as e:
            return self.create_error_record(miner_ip, f"unknown_error")

    def parse_miner_response(self, miner_ip, data):
        """Parse the real API response from Bitaxe"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Extract values with proper conversions
        hashrate_gh = data.get('hashRate', 0)  # Already in GH/s
        hashrate_th = hashrate_gh / 1000 if hashrate_gh else 0  # Convert to TH/s
        expected_hashrate_gh = data.get('expectedHashrate', 0)  # Expected hashrate
        temp_asic = data.get('temp', 0)  # ASIC temperature
        temp_vr = data.get('vrTemp', 0)  # VR temperature  
        power = data.get('power', 0)  # Already in Watts
        
        # Voltages (convert mV to V)
        voltage_device = data.get('voltage', 0) / 1000 if data.get('voltage') else 0  # Device voltage
        voltage_asic_actual = data.get('coreVoltageActual', 0) / 1000 if data.get('coreVoltageActual') else 0  # Actual ASIC voltage
        current = data.get('current', 0) / 1000 if data.get('current') else 0  # Convert mA to A
        
        # Set values
        frequency_set = data.get('frequency', 0)  # Set frequency in MHz
        voltage_asic_set = data.get('coreVoltage', 0) / 1000 if data.get('coreVoltage') else 0  # Set ASIC voltage in V
        
        # Mining statistics
        shares_accepted = data.get('sharesAccepted', 0)
        shares_rejected = data.get('sharesRejected', 0)
        best_diff = data.get('bestDiff', '0')
        best_session_diff = data.get('bestSessionDiff', '0')  # NEW: Session best
        uptime_seconds = data.get('uptimeSeconds', 0)
        
        # Process rejection reasons (NEW: Detailed rejection analysis)
        rejection_reasons = data.get('sharesRejectedReasons', [])
        rejection_summary = ""
        if rejection_reasons:
            reasons = []
            for reason in rejection_reasons:
                if isinstance(reason, dict):
                    msg = reason.get('message', 'Unknown')
                    count = reason.get('count', 0)
                    reasons.append(f"{msg}:{count}")
            rejection_summary = "|".join(reasons) if reasons else "None"
        else:
            rejection_summary = "None"
        
        # System info (NEW: Hardware identification and monitoring)
        hostname = data.get('hostname', 'Unknown')
        free_heap = data.get('freeHeap', 0)  # Memory monitoring
        overclock_enabled = data.get('overclockEnabled', 0)  # Configuration tracking
        
        # Network info
        wifi_rssi = data.get('wifiRSSI', 0)
        wifi_status = data.get('wifiStatus', 'Unknown')
        
        # Fan control
        fan_speed = data.get('fanspeed', 0)
        fan_rpm = data.get('fanrpm', 0)
        
        # Pool info
        stratum_url = data.get('stratumURL', 'Unknown')
        stratum_user = data.get('stratumUser', 'Unknown')
        
        # Calculate efficiency in J/TH (Joules per Terahash)
        efficiency_j_th = power / hashrate_th if hashrate_th > 0 else 0
        
        # Calculate performance ratio (actual vs expected)
        hashrate_ratio = (hashrate_gh / expected_hashrate_gh * 100) if expected_hashrate_gh > 0 else 0
        
        # Determine status
        status = self.determine_status(data, hashrate_gh, temp_asic)
        
        return {
            'timestamp': timestamp,
            'miner_ip': miner_ip,
            'status': status,
            'hashrate_th': round(hashrate_th, 3),
            'hashrate_ghs': round(hashrate_gh, 2),
            'expected_hashrate_ghs': round(expected_hashrate_gh, 2),
            'hashrate_ratio_percent': round(hashrate_ratio, 1),
            'temp_asic_c': round(temp_asic, 1),
            'temp_vr_c': round(temp_vr, 1),
            'power_w': round(power, 2),
            'voltage_device_v': round(voltage_device, 3),
            'voltage_asic_set_v': round(voltage_asic_set, 3),
            'voltage_asic_actual_v': round(voltage_asic_actual, 3),
            'current_a': round(current, 3),
            'frequency_set_mhz': frequency_set,
            'efficiency_j_th': round(efficiency_j_th, 2),
            'shares_accepted': shares_accepted,
            'shares_rejected': shares_rejected,
            'rejection_reasons': rejection_summary,
            'best_diff': best_diff,
            'best_session_diff': best_session_diff,
            'uptime_seconds': uptime_seconds,
            'uptime_hours': round(uptime_seconds / 3600, 1),
            'wifi_rssi': wifi_rssi,
            'wifi_status': wifi_status,
            'fan_speed_percent': fan_speed,
            'fan_rpm': fan_rpm,
            'hostname': hostname,
            'free_heap_bytes': free_heap,
            'overclock_enabled': overclock_enabled,
            'stratum_url': stratum_url,
            'pool_user': stratum_user.split('.')[0] if '.' in stratum_user else stratum_user[:20]
        }

    def determine_status(self, data, hashrate, temp):
        """Determine miner status based on various metrics"""
        # Check for obvious issues
        if hashrate <= 0:
            return "no_hashrate"
        
        if temp >= 85:  # Overheating threshold for BM1370
            return "overheating"
            
        if temp <= 0:
            return "no_temp_sensor"
            
        # Check WiFi connection
        wifi_status = data.get('wifiStatus', '').lower()
        if 'disconnected' in wifi_status or 'failed' in wifi_status:
            return "wifi_issues"
            
        # Check if shares are being rejected heavily
        accepted = data.get('sharesAccepted', 0)
        rejected = data.get('sharesRejected', 0)
        if accepted > 0 and rejected / (accepted + rejected) > 0.1:  # >10% rejection rate
            return "high_rejection"
            
        # Check power consumption (should be 15-25W for Gamma)
        power = data.get('power', 0)
        if power > 35:
            return "high_power"
        elif power < 5 and hashrate > 0:
            return "low_power"
            
        return "online"

    def create_error_record(self, miner_ip, error_type):
        """Create error record when miner is unreachable"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'timestamp': timestamp,
            'miner_ip': miner_ip,
            'status': error_type,
            'hashrate_th': 0,
            'hashrate_ghs': 0,
            'expected_hashrate_ghs': 0,
            'hashrate_ratio_percent': 0,
            'temp_asic_c': 0,
            'temp_vr_c': 0,
            'power_w': 0,
            'voltage_device_v': 0,
            'voltage_asic_set_v': 0,
            'voltage_asic_actual_v': 0,
            'current_a': 0,
            'frequency_set_mhz': 0,
            'efficiency_j_th': 0,
            'shares_accepted': 0,
            'shares_rejected': 0,
            'rejection_reasons': 'None',
            'best_diff': '0',
            'best_session_diff': '0',
            'uptime_seconds': 0,
            'uptime_hours': 0,
            'wifi_rssi': 0,
            'wifi_status': 'Unknown',
            'fan_speed_percent': 0,
            'fan_rpm': 0,
            'hostname': 'Unknown',
            'free_heap_bytes': 0,
            'overclock_enabled': 0,
            'stratum_url': 'Unknown',
            'pool_user': 'Unknown'
        }

    def write_csv_header(self):
        """Write CSV header if file doesn't exist"""
        if not os.path.exists(self.csv_path):
            fieldnames = [
                'timestamp', 'miner_ip', 'status', 'hashrate_th', 'hashrate_ghs',
                'expected_hashrate_ghs', 'hashrate_ratio_percent', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                'voltage_device_v', 'voltage_asic_set_v', 'voltage_asic_actual_v', 'current_a', 'frequency_set_mhz', 
                'efficiency_j_th', 'shares_accepted', 'shares_rejected', 'rejection_reasons', 'best_diff', 
                'best_session_diff', 'uptime_seconds', 'uptime_hours', 'wifi_rssi', 'wifi_status', 
                'fan_speed_percent', 'fan_rpm', 'hostname', 'free_heap_bytes', 'overclock_enabled', 
                'stratum_url', 'pool_user'
            ]
            
            with open(self.csv_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            print(f"Created new CSV file: {self.csv_path}")

    def append_metrics_to_csv(self, metrics_list):
        """Append metrics to CSV file"""
        fieldnames = [
            'timestamp', 'miner_ip', 'status', 'hashrate_th', 'hashrate_ghs',
            'expected_hashrate_ghs', 'hashrate_ratio_percent', 'temp_asic_c', 'temp_vr_c', 'power_w', 
            'voltage_device_v', 'voltage_asic_set_v', 'voltage_asic_actual_v', 'current_a', 'frequency_set_mhz', 
            'efficiency_j_th', 'shares_accepted', 'shares_rejected', 'rejection_reasons', 'best_diff', 
            'best_session_diff', 'uptime_seconds', 'uptime_hours', 'wifi_rssi', 'wifi_status', 
            'fan_speed_percent', 'fan_rpm', 'hostname', 'free_heap_bytes', 'overclock_enabled', 
            'stratum_url', 'pool_user'
        ]
        
        with open(self.csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for metrics in metrics_list:
                writer.writerow(metrics)

    def collect_all_miners(self):
        """Collect metrics from all configured miners"""
        print(f"Polling {len(self.config['miners'])} miners...")
        all_metrics = []
        
        for miner_ip in self.config['miners']:
            print(f"  {miner_ip}...", end=' ', flush=True)
            
            metrics = self.get_miner_data(miner_ip)
            all_metrics.append(metrics)
            
            # Status display with appropriate symbol
            status_icons = {
                'online': 'OK',
                'no_hashrate': 'WARN',
                'overheating': 'HOT',
                'wifi_issues': 'WIFI',
                'high_rejection': 'REJECT',
                'timeout': 'TIMEOUT',
                'connection_failed': 'OFFLINE',
                'high_power': 'HIPOWER',
                'low_power': 'LOPOWER'
            }
            
            icon = status_icons.get(metrics['status'], 'ERROR')
            
            if metrics['status'] == 'online':
                print(f"{icon} {metrics['hashrate_ghs']:.1f} GH/s, ASIC:{metrics['temp_asic_c']:.1f}C VR:{metrics['temp_vr_c']:.1f}C, {metrics['power_w']:.1f}W, {metrics['efficiency_j_th']:.1f}J/TH")
            else:
                print(f"{icon} {metrics['status']}")
        
        return all_metrics

    def run_collector(self):
        """Main collector loop"""
        print(">>> Smart Bitaxe Gamma Monitor - Real API Collector")
        print(f"Monitoring {len(self.config['miners'])} miners")
        print(f"Poll interval: {self.config['poll_interval']} seconds")
        print(f"CSV output: {self.csv_path}")
        print(f"API timeout: {self.config['timeout']} seconds")
        print(f"Retries: {self.config['retries']}")
        print("Press Ctrl+C to stop\n")
        
        # Initialize CSV file
        self.write_csv_header()
        
        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n[{timestamp}] Collection cycle started")
                
                # Collect metrics from all miners
                all_metrics = self.collect_all_miners()
                
                # Calculate fleet summary
                online_miners = [m for m in all_metrics if m['status'] == 'online']
                total_hashrate = sum(m['hashrate_ghs'] for m in online_miners)
                total_power = sum(m['power_w'] for m in online_miners)
                avg_temp_asic = sum(m['temp_asic_c'] for m in online_miners) / len(online_miners) if online_miners else 0
                avg_temp_vr = sum(m['temp_vr_c'] for m in online_miners) / len(online_miners) if online_miners else 0
                fleet_efficiency = total_power / (total_hashrate / 1000) if total_hashrate > 0 else 0  # J/TH
                
                print(f"Fleet: {len(online_miners)}/{len(all_metrics)} online, "
                      f"{total_hashrate:.1f} GH/s, {total_power:.1f}W, "
                      f"ASIC:{avg_temp_asic:.1f}C VR:{avg_temp_vr:.1f}C, {fleet_efficiency:.1f}J/TH")
                
                # Write to CSV
                self.append_metrics_to_csv(all_metrics)
                print(f"Saved {len(all_metrics)} records to {self.csv_path}")
                
                # Wait for next poll
                print(f"Next poll in {self.config['poll_interval']} seconds...")
                time.sleep(self.config['poll_interval'])
                
        except KeyboardInterrupt:
            print("\n\nCollector stopped by user")
            print("Check your data in the CSV file and view with:")
            print("   python cli_view.py --summary")
            print("   python cli_view.py --live")
        except Exception as e:
            print(f"\nUnexpected error: {e}")

def main():
    """Main entry point"""
    collector = BitaxeCollector()
    collector.run_collector()

if __name__ == "__main__":
    main()