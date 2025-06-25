#!/usr/bin/env python3
"""
Smart Bitaxe Gamma Monitor - Improved Real API Collector
Features:
- Robust CSV handling with corruption prevention
- Persistent hostname caching for flaky network responses
- Enhanced error handling and recovery
- Automatic backup and validation
"""

import csv
import time
import yaml
import requests
import json
import tempfile
import shutil
import threading
from datetime import datetime
from pathlib import Path
import os
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# fcntl is Unix-only, not needed for Windows file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

class BitaxeCollector:
    def __init__(self, config_path=None):
        """Initialize the collector with configuration"""
        if config_path is None:
            # Look for config in parent directory (project root)
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            config_path = project_root / 'config.yaml'
            
            # Fallback to examples if no config exists
            if not config_path.exists():
                config_path = project_root / 'examples' / 'config.yaml'
        
        self.config = self.load_config(config_path)
        self.session = self.create_session()
        
        # Handle CSV path relative to project root
        csv_path = self.config['csv_path']
        if not os.path.isabs(csv_path):
            project_root = Path(__file__).parent.parent
            csv_path = project_root / csv_path
        self.csv_path = str(csv_path)
        
        # Handle cache and backup paths
        project_root = Path(__file__).parent.parent
        self.hostname_cache_path = project_root / 'hostname_cache.json'
        self.backup_dir = project_root / 'backups'
        
        # Thread lock for CSV operations
        self.csv_lock = threading.Lock()
        
        # Load persistent hostname cache
        self.hostname_cache = self.load_hostname_cache()
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
        
    def load_config(self, config_path):
        """Load configuration from YAML file with enhanced validation"""
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
            config.setdefault('backup_frequency', 100)  # Backup every N records
            config.setdefault('validate_csv', True)
            
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

    def load_hostname_cache(self):
        """Load persistent hostname cache from file"""
        try:
            if self.hostname_cache_path.exists():
                with open(self.hostname_cache_path, 'r') as f:
                    cache = json.load(f)
                print(f"Loaded hostname cache with {len(cache)} entries")
                return cache
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load hostname cache: {e}")
        
        return {}
    
    def save_hostname_cache(self):
        """Save hostname cache to persistent storage"""
        try:
            with open(self.hostname_cache_path, 'w') as f:
                json.dump(self.hostname_cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save hostname cache: {e}")
    
    def get_cached_hostname(self, miner_ip, current_hostname=None):
        """Get hostname with caching for flaky responses"""
        if current_hostname and current_hostname != 'Unknown':
            # Valid hostname received, cache it
            if self.hostname_cache.get(miner_ip) != current_hostname:
                self.hostname_cache[miner_ip] = current_hostname
                self.save_hostname_cache()
            return current_hostname
        else:
            # Flaky or missing hostname, use cached version
            cached = self.hostname_cache.get(miner_ip)
            if cached:
                return f"{cached}*"  # Asterisk indicates cached value
            else:
                return f"Miner-{miner_ip.split('.')[-1]}"  # Fallback based on IP

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
        """Fetch real data from a Bitaxe miner via API with enhanced error handling"""
        url = f"http://{miner_ip}/api/system/info"
        
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            data = response.json()
            
            # Validate response structure
            if not isinstance(data, dict):
                raise ValueError("Invalid API response format")
            
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
        except ValueError as e:
            return self.create_error_record(miner_ip, f"validation_error")
        except Exception as e:
            print(f"Unexpected error for {miner_ip}: {e}")
            return self.create_error_record(miner_ip, f"unknown_error")

    def parse_miner_response(self, miner_ip, data):
        """Parse the real API response from Bitaxe with enhanced validation"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Extract values with proper conversions and validation
            hashrate_gh = float(data.get('hashRate', 0))
            hashrate_th = hashrate_gh / 1000 if hashrate_gh else 0
            expected_hashrate_gh = float(data.get('expectedHashrate', 0))
            temp_asic = float(data.get('temp', 0))
            temp_vr = float(data.get('vrTemp', 0))
            power = float(data.get('power', 0))
            
            # Voltages (convert mV to V)
            voltage_device = float(data.get('voltage', 0)) / 1000 if data.get('voltage') else 0
            voltage_asic_actual = float(data.get('coreVoltageActual', 0)) / 1000 if data.get('coreVoltageActual') else 0
            current = float(data.get('current', 0)) / 1000 if data.get('current') else 0
            
            # Set values
            frequency_set = int(data.get('frequency', 0))
            voltage_asic_set = float(data.get('coreVoltage', 0)) / 1000 if data.get('coreVoltage') else 0
            
            # Mining statistics
            shares_accepted = int(data.get('sharesAccepted', 0))
            shares_rejected = int(data.get('sharesRejected', 0))
            best_diff = str(data.get('bestDiff', '0'))
            best_session_diff = str(data.get('bestSessionDiff', '0'))
            uptime_seconds = int(data.get('uptimeSeconds', 0))
            
            # Process rejection reasons with safe handling
            rejection_reasons = data.get('sharesRejectedReasons', [])
            rejection_summary = "None"
            if rejection_reasons and isinstance(rejection_reasons, list):
                try:
                    reasons = []
                    for reason in rejection_reasons:
                        if isinstance(reason, dict):
                            msg = str(reason.get('message', 'Unknown'))
                            count = int(reason.get('count', 0))
                            reasons.append(f"{msg}:{count}")
                    rejection_summary = "|".join(reasons) if reasons else "None"
                except Exception:
                    rejection_summary = "ParseError"
            
            # System info with cached hostname handling
            raw_hostname = data.get('hostname', 'Unknown')
            hostname = self.get_cached_hostname(miner_ip, raw_hostname)
            free_heap = int(data.get('freeHeap', 0))
            overclock_enabled = int(data.get('overclockEnabled', 0))
            
            # Network info
            wifi_rssi = int(data.get('wifiRSSI', 0))
            wifi_status = str(data.get('wifiStatus', 'Unknown'))
            
            # Fan control
            fan_speed = int(data.get('fanspeed', 0))
            fan_rpm = int(data.get('fanrpm', 0))
            
            # Pool info with safe string handling
            stratum_url = str(data.get('stratumURL', 'Unknown'))
            stratum_user = str(data.get('stratumUser', 'Unknown'))
            
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
            
        except (ValueError, TypeError) as e:
            print(f"Data parsing error for {miner_ip}: {e}")
            return self.create_error_record(miner_ip, "parse_error")

    def determine_status(self, data, hashrate, temp):
        """Determine miner status based on various metrics"""
        try:
            # Check for obvious issues
            if hashrate <= 0:
                return "no_hashrate"
            
            if temp >= 85:  # Overheating threshold for BM1370
                return "overheating"
                
            if temp <= 0:
                return "no_temp_sensor"
                
            # Check WiFi connection
            wifi_status = str(data.get('wifiStatus', '')).lower()
            if 'disconnected' in wifi_status or 'failed' in wifi_status:
                return "wifi_issues"
                
            # Check if shares are being rejected heavily
            accepted = int(data.get('sharesAccepted', 0))
            rejected = int(data.get('sharesRejected', 0))
            if accepted > 0 and rejected / (accepted + rejected) > 0.1:  # >10% rejection rate
                return "high_rejection"
                
            # Check power consumption (should be 15-25W for Gamma)
            power = float(data.get('power', 0))
            if power > 35:
                return "high_power"
            elif power < 5 and hashrate > 0:
                return "low_power"
                
            return "online"
        except Exception:
            return "status_error"

    def create_error_record(self, miner_ip, error_type):
        """Create error record when miner is unreachable with cached hostname"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Try to use cached hostname for error records
        hostname = self.get_cached_hostname(miner_ip)
        
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
            'hostname': hostname,
            'free_heap_bytes': 0,
            'overclock_enabled': 0,
            'stratum_url': 'Unknown',
            'pool_user': 'Unknown'
        }

    def validate_csv_file(self, csv_path):
        """Validate CSV file structure and integrity"""
        try:
            if not os.path.exists(csv_path):
                return True, "File doesn't exist yet"
            
            fieldnames = [
                'timestamp', 'miner_ip', 'status', 'hashrate_th', 'hashrate_ghs',
                'expected_hashrate_ghs', 'hashrate_ratio_percent', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                'voltage_device_v', 'voltage_asic_set_v', 'voltage_asic_actual_v', 'current_a', 'frequency_set_mhz', 
                'efficiency_j_th', 'shares_accepted', 'shares_rejected', 'rejection_reasons', 'best_diff', 
                'best_session_diff', 'uptime_seconds', 'uptime_hours', 'wifi_rssi', 'wifi_status', 
                'fan_speed_percent', 'fan_rpm', 'hostname', 'free_heap_bytes', 'overclock_enabled', 
                'stratum_url', 'pool_user'
            ]
            
            with open(csv_path, 'r', newline='') as csvfile:
                # Check first line (header)
                first_line = csvfile.readline().strip()
                expected_header = ','.join(fieldnames)
                if first_line != expected_header:
                    return False, f"Header mismatch: expected {len(fieldnames)} fields"
                
                # Validate some sample lines
                reader = csv.DictReader(csvfile, fieldnames=fieldnames)
                for i, row in enumerate(reader):
                    if i >= 10:  # Check first 10 data rows
                        break
                    if len(row) != len(fieldnames):
                        return False, f"Row {i+2} has {len(row)} fields, expected {len(fieldnames)}"
                        
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Validation error: {e}"

    def backup_csv_file(self):
        """Create a backup of the current CSV file"""
        try:
            if os.path.exists(self.csv_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.backup_dir / f"metrics_backup_{timestamp}.csv"
                shutil.copy2(self.csv_path, backup_path)
                print(f"Created backup: {backup_path}")
                
                # Keep only last 10 backups
                backups = sorted(self.backup_dir.glob("metrics_backup_*.csv"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                        
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")

    def write_csv_header(self):
        """Write CSV header if file doesn't exist with validation"""
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
            
            try:
                with open(self.csv_path, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                print(f"Created new CSV file: {self.csv_path}")
            except Exception as e:
                print(f"ERROR: Could not create CSV file: {e}")
                sys.exit(1)

    def append_metrics_to_csv_safe(self, metrics_list):
        """Safely append metrics to CSV file with corruption prevention"""
        with self.csv_lock:
            try:
                # Validate current file before writing
                if self.config.get('validate_csv', True):
                    is_valid, validation_msg = self.validate_csv_file(self.csv_path)
                    if not is_valid:
                        print(f"WARNING: CSV validation failed: {validation_msg}")
                        print("Creating backup and rebuilding CSV file...")
                        self.backup_csv_file()
                        self.write_csv_header()
                
                # Write to temporary file first
                temp_path = f"{self.csv_path}.tmp"
                
                fieldnames = [
                    'timestamp', 'miner_ip', 'status', 'hashrate_th', 'hashrate_ghs',
                    'expected_hashrate_ghs', 'hashrate_ratio_percent', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                    'voltage_device_v', 'voltage_asic_set_v', 'voltage_asic_actual_v', 'current_a', 'frequency_set_mhz', 
                    'efficiency_j_th', 'shares_accepted', 'shares_rejected', 'rejection_reasons', 'best_diff', 
                    'best_session_diff', 'uptime_seconds', 'uptime_hours', 'wifi_rssi', 'wifi_status', 
                    'fan_speed_percent', 'fan_rpm', 'hostname', 'free_heap_bytes', 'overclock_enabled', 
                    'stratum_url', 'pool_user'
                ]
                
                # Copy existing file to temp, then append new data
                if os.path.exists(self.csv_path):
                    shutil.copy2(self.csv_path, temp_path)
                else:
                    # Create header in temp file
                    with open(temp_path, 'w', newline='') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                
                # Append new metrics to temp file
                with open(temp_path, 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    for metrics in metrics_list:
                        # Validate each record before writing
                        validated_metrics = {}
                        for field in fieldnames:
                            if field in metrics:
                                validated_metrics[field] = metrics[field]
                            else:
                                print(f"WARNING: Missing field {field} in metrics")
                                validated_metrics[field] = 0 if field.replace('_', '').replace('percent', '').replace('mhz', '').replace('th', '').replace('ghs', '').replace('bytes', '').replace('seconds', '').replace('hours', '').isalpha() == False else 'Unknown'
                        
                        writer.writerow(validated_metrics)
                
                # Atomically replace the original file
                if os.name == 'nt':  # Windows
                    if os.path.exists(self.csv_path):
                        os.replace(temp_path, self.csv_path)
                    else:
                        os.rename(temp_path, self.csv_path)
                else:  # Unix-like
                    os.rename(temp_path, self.csv_path)
                
                return True
                
            except Exception as e:
                print(f"ERROR writing to CSV: {e}")
                # Clean up temp file
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError as cleanup_error:
                        print(f"Warning: Could not remove temporary file {temp_path}: {cleanup_error}")
                return False

    def collect_all_miners(self):
        """Collect metrics from all configured miners with enhanced error handling"""
        print(f"Polling {len(self.config['miners'])} miners...")
        all_metrics = []
        successful_polls = 0
        
        for miner_ip in self.config['miners']:
            print(f"  {miner_ip}...", end=' ', flush=True)
            
            try:
                metrics = self.get_miner_data(miner_ip)
                all_metrics.append(metrics)
                
                if metrics['status'] not in ['timeout', 'connection_failed', 'http_error', 'invalid_json', 'parse_error', 'unknown_error']:
                    successful_polls += 1
                
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
                    'low_power': 'LOPOWER',
                    'parse_error': 'PARSEERR',
                    'unknown_error': 'ERROR'
                }
                
                icon = status_icons.get(metrics['status'], 'ERROR')
                
                if metrics['status'] == 'online':
                    hostname_display = metrics['hostname']
                    if hostname_display.endswith('*'):
                        hostname_display = f"({hostname_display})"
                    print(f"{icon} {metrics['hashrate_ghs']:.1f}GH/s {hostname_display} {metrics['temp_asic_c']:.1f}°C {metrics['power_w']:.1f}W")
                else:
                    hostname_display = metrics['hostname']
                    print(f"{icon} {metrics['status']} {hostname_display}")
                    
            except Exception as e:
                print(f"CRITICAL ERROR processing {miner_ip}: {e}")
                # Still add an error record
                all_metrics.append(self.create_error_record(miner_ip, "critical_error"))
        
        print(f"Successfully polled: {successful_polls}/{len(self.config['miners'])}")
        return all_metrics

    def run_collector(self):
        """Main collector loop with enhanced robustness"""
        print(">>> Smart Bitaxe Gamma Monitor - Improved Real API Collector")
        print(f"Monitoring {len(self.config['miners'])} miners")
        print(f"Poll interval: {self.config['poll_interval']} seconds")
        print(f"CSV output: {self.csv_path}")
        print(f"Hostname cache: {self.hostname_cache_path}")
        print(f"Backup directory: {self.backup_dir}")
        print(f"CSV validation: {'enabled' if self.config.get('validate_csv', True) else 'disabled'}")
        print("Press Ctrl+C to stop\n")
        
        # Initialize CSV file
        self.write_csv_header()
        
        # Create initial backup
        self.backup_csv_file()
        
        collection_count = 0
        
        try:
            while True:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n[{timestamp}] Collection cycle #{collection_count + 1}")
                
                try:
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
                          f"ASIC:{avg_temp_asic:.1f}°C VR:{avg_temp_vr:.1f}°C, {fleet_efficiency:.1f}J/TH")
                    
                    # Write to CSV with safe method
                    if self.append_metrics_to_csv_safe(all_metrics):
                        print(f"Saved {len(all_metrics)} records to {self.csv_path}")
                    else:
                        print("WARNING: Failed to save to CSV - data may be lost!")
                    
                    collection_count += 1
                    
                    # Periodic backup
                    if collection_count % self.config.get('backup_frequency', 100) == 0:
                        print("Creating periodic backup...")
                        self.backup_csv_file()
                    
                except Exception as e:
                    print(f"ERROR in collection cycle: {e}")
                    print("Continuing to next cycle...")
                
                # Wait for next poll
                print(f"Next poll in {self.config['poll_interval']} seconds...")
                time.sleep(self.config['poll_interval'])
                
        except KeyboardInterrupt:
            print("\n\nCollector stopped by user")
            print("Saving final hostname cache...")
            self.save_hostname_cache()
            print("Creating final backup...")
            self.backup_csv_file()
            print("Check your data in the CSV file and view with:")
            print("   python cli_view.py --summary")
            print("   python cli_view.py --live")
        except Exception as e:
            print(f"\nCritical error: {e}")
            print("Saving hostname cache...")
            self.save_hostname_cache()
            print("Creating emergency backup...")
            self.backup_csv_file()

def main():
    """Main entry point"""
    collector = BitaxeCollector()
    collector.run_collector()

if __name__ == "__main__":
    main()
