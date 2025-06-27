#!/usr/bin/env python3
import csv
import time
import yaml
import requests
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def load_config():
    """Load and validate configuration from config.yaml"""
    config_path = 'config.yaml'
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading config file: {e}")
    
    # Validate required fields
    required_fields = ['miners', 'poll_interval', 'csv_path']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field '{field}' in config")
    
    # Validate miners list
    if not isinstance(config['miners'], list) or len(config['miners']) == 0:
        raise ValueError("'miners' must be a non-empty list of IP addresses")
    
    # Validate poll_interval
    if not isinstance(config['poll_interval'], (int, float)) or config['poll_interval'] <= 0:
        raise ValueError("'poll_interval' must be a positive number")
    
    # Set defaults for optional fields
    config.setdefault('timeout', 10)
    config.setdefault('max_retries', 3)
    config.setdefault('retry_delay', 2)
    config.setdefault('data_validation', True)
    
    return config

def validate_numeric_value(value: Any, field_name: str, min_val: float = None, max_val: float = None, default: float = 0.0) -> float:
    """Validate and sanitize numeric values"""
    if value is None:
        return default
    
    try:
        num_value = float(value)
        
        # Check for invalid values
        if not (isinstance(num_value, (int, float)) and not (isinstance(num_value, bool))):
            raise ValueError(f"Invalid numeric type for {field_name}")
        
        # Check for NaN or infinity
        if not (num_value == num_value):  # NaN check
            raise ValueError(f"NaN value for {field_name}")
        
        if abs(num_value) == float('inf'):
            raise ValueError(f"Infinite value for {field_name}")
        
        # Range validation
        if min_val is not None and num_value < min_val:
            print(f"Warning: {field_name} value {num_value} below minimum {min_val}, using minimum")
            return min_val
        
        if max_val is not None and num_value > max_val:
            print(f"Warning: {field_name} value {num_value} above maximum {max_val}, using maximum")
            return max_val
        
        return num_value
        
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid {field_name} value '{value}': {e}. Using default {default}")
        return default

def validate_and_sanitize_metrics(data: Dict[str, Any], miner_ip: str) -> Dict[str, Any]:
    """Validate and sanitize metrics data"""
    # Handle different field name variations
    hashrate_raw = data.get('hashRate', data.get('hashrateGHs', data.get('currentHashrate', 0)))
    
    # Convert hashrate units if necessary
    hashrate_validated = validate_numeric_value(hashrate_raw, 'hashrate_raw', 0, None, 0)
    if hashrate_validated > 1000:  # Likely in MH/s, convert to GH/s
        hashrate_gh = validate_numeric_value(hashrate_validated / 1000, 'hashrate_gh', 0, 10000, 0)
    else:  # Already in GH/s
        hashrate_gh = validate_numeric_value(hashrate_validated, 'hashrate_gh', 0, 10000, 0)
    
    # Validate and sanitize all metrics
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'miner_ip': str(miner_ip),
        'hashrate_gh': round(hashrate_gh, 2),
        'temperature': round(validate_numeric_value(
            data.get('temp', data.get('temperature', 0)), 
            'temperature', -50, 150, 0
        ), 1),
        'power_w': round(validate_numeric_value(
            data.get('power', data.get('powerConsumption', 0)), 
            'power_w', 0, 1000, 0
        ), 1),
        'uptime_s': int(validate_numeric_value(
            data.get('uptimeSeconds', data.get('uptime', 0)), 
            'uptime_s', 0, None, 0
        )),
        'accepted_shares': int(validate_numeric_value(
            data.get('sharesAccepted', data.get('acceptedShares', 0)), 
            'accepted_shares', 0, None, 0
        )),
        'rejected_shares': int(validate_numeric_value(
            data.get('sharesRejected', data.get('rejectedShares', 0)), 
            'rejected_shares', 0, None, 0
        )),
        'pool_difficulty': int(validate_numeric_value(
            data.get('stratumDifficulty', data.get('difficulty', 0)), 
            'pool_difficulty', 0, None, 0
        )),
    }
    
    return metrics

def collect_metrics(miner_ip: str, timeout: int = 10, validate_data: bool = True) -> Dict[str, Any]:
    """
    Collect metrics from a Bitaxe Gamma miner via API.
    """
    try:
        # Make API request to /api/system/info endpoint
        response = requests.get(
            f"http://{miner_ip}/api/system/info",
            timeout=timeout,
            headers={'User-Agent': 'BitaxeMonitor/1.0'}
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Validate and sanitize metrics data
        if validate_data:
            metrics = validate_and_sanitize_metrics(data, miner_ip)
        else:
            # Basic extraction without validation (fallback mode)
            hashrate_raw = data.get('hashRate', data.get('hashrateGHs', data.get('currentHashrate', 0)))
            if hashrate_raw > 1000:
                hashrate_gh = round(hashrate_raw / 1000, 2)
            else:
                hashrate_gh = round(hashrate_raw, 2)
                
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'miner_ip': miner_ip,
                'hashrate_gh': hashrate_gh,
                'temperature': round(data.get('temp', data.get('temperature', 0)), 1),
                'power_w': round(data.get('power', data.get('powerConsumption', 0)), 1),
                'uptime_s': data.get('uptimeSeconds', data.get('uptime', 0)),
                'accepted_shares': data.get('sharesAccepted', data.get('acceptedShares', 0)),
                'rejected_shares': data.get('sharesRejected', data.get('rejectedShares', 0)),
                'pool_difficulty': data.get('stratumDifficulty', data.get('difficulty', 0)),
            }
        
        return metrics
        
    except requests.exceptions.Timeout:
        raise Exception(f"Timeout connecting to {miner_ip}")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Connection failed to {miner_ip}")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error {e.response.status_code} from {miner_ip}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")
    except (KeyError, ValueError) as e:
        raise Exception(f"Invalid data format: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")

def collect_metrics_with_retry(miner_ip: str, max_retries: int = 3, retry_delay: int = 2, **kwargs) -> Optional[Dict[str, Any]]:
    """Collect metrics with retry logic"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return collect_metrics(miner_ip, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed for {miner_ip}: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"All {max_retries} attempts failed for {miner_ip}: {e}")
    
    return None

def write_to_csv(data: Dict[str, Any], csv_path: str) -> bool:
    """Write metrics data to CSV file with error handling"""
    try:
        csv_file = Path(csv_path)
        file_exists = csv_file.exists()
        
        # Ensure directory exists
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'miner_ip', 'hashrate_gh', 'temperature', 
                         'power_w', 'uptime_s', 'accepted_shares', 'rejected_shares', 
                         'pool_difficulty']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(data)
            f.flush()  # Ensure data is written immediately
            
        return True
        
    except PermissionError:
        print(f"Permission denied writing to {csv_path}")
        return False
    except OSError as e:
        print(f"OS error writing to {csv_path}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error writing to {csv_path}: {e}")
        return False

def validate_startup_conditions(config: Dict[str, Any]) -> bool:
    """Validate startup conditions and connectivity"""
    print("Performing startup validation...")
    
    # Test CSV write permissions
    csv_path = config['csv_path']
    try:
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'miner_ip': 'test',
            'hashrate_gh': 0.0,
            'temperature': 0.0,
            'power_w': 0.0,
            'uptime_s': 0,
            'accepted_shares': 0,
            'rejected_shares': 0,
            'pool_difficulty': 0
        }
        
        # Try to write test data and then remove it
        csv_file = Path(csv_path)
        temp_file = csv_file.with_suffix('.tmp')
        
        if write_to_csv(test_data, str(temp_file)):
            temp_file.unlink(missing_ok=True)
            print(f"✓ CSV write permissions OK for {csv_path}")
        else:
            print(f"✗ Cannot write to CSV file {csv_path}")
            return False
            
    except Exception as e:
        print(f"✗ CSV validation failed: {e}")
        return False
    
    # Test network connectivity to miners
    reachable_miners = []
    unreachable_miners = []
    
    for miner_ip in config['miners']:
        print(f"Testing connectivity to {miner_ip}...")
        try:
            # Quick connectivity test
            response = requests.get(
                f"http://{miner_ip}/api/system/info",
                timeout=config['timeout'],
                headers={'User-Agent': 'BitaxeMonitor/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and len(data) > 0:
                    reachable_miners.append(miner_ip)
                    print(f"✓ {miner_ip} is reachable and responding")
                else:
                    unreachable_miners.append(miner_ip)
                    print(f"⚠ {miner_ip} responded but returned empty/invalid data")
            else:
                unreachable_miners.append(miner_ip)
                print(f"⚠ {miner_ip} returned HTTP {response.status_code}")
                
        except Exception as e:
            unreachable_miners.append(miner_ip)
            print(f"✗ {miner_ip} is not reachable: {e}")
    
    print(f"\nConnectivity Summary:")
    print(f"  Reachable miners: {len(reachable_miners)}/{len(config['miners'])}")
    
    if len(reachable_miners) == 0:
        print("✗ No miners are reachable. Please check network configuration.")
        return False
    elif len(unreachable_miners) > 0:
        print(f"⚠ {len(unreachable_miners)} miners are not reachable. Monitoring will continue with available miners.")
        print(f"  Unreachable: {', '.join(unreachable_miners)}")
    
    print("✓ Startup validation completed successfully")
    return True

def main():
    """Main collector loop with enhanced error handling"""
    try:
        config = load_config()
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        sys.exit(1)
    
    # Perform startup validation
    if not validate_startup_conditions(config):
        print("\n✗ Startup validation failed. Please fix the issues above and try again.")
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            sys.exit(1)
        print("⚠ Continuing with degraded functionality...")
    
    print(f"Starting Bitaxe Gamma Monitor")
    print(f"Monitoring {len(config['miners'])} miners: {', '.join(config['miners'])}")
    print(f"Poll interval: {config['poll_interval']} seconds")
    print(f"CSV output: {config['csv_path']}")
    print("Press Ctrl+C to stop")
    
    # Main collection loop with enhanced error handling
    consecutive_failures = {}
    max_consecutive_failures = 5
    
    try:
        while True:
            success_count = 0
            
            for miner_ip in config['miners']:
                try:
                    metrics = collect_metrics_with_retry(
                        miner_ip, 
                        max_retries=config.get('max_retries', 3),
                        retry_delay=config.get('retry_delay', 2),
                        timeout=config.get('timeout', 10),
                        validate_data=config.get('data_validation', True)
                    )
                    
                    if metrics:
                        if write_to_csv(metrics, config['csv_path']):
                            print(f"✓ {miner_ip}: {metrics['hashrate_gh']} GH/s, {metrics['temperature']}°C, {metrics['power_w']}W")
                            success_count += 1
                            consecutive_failures[miner_ip] = 0  # Reset failure count
                        else:
                            print(f"✗ Failed to write data for {miner_ip}")
                    else:
                        consecutive_failures[miner_ip] = consecutive_failures.get(miner_ip, 0) + 1
                        if consecutive_failures[miner_ip] >= max_consecutive_failures:
                            print(f"⚠ {miner_ip} has failed {consecutive_failures[miner_ip]} consecutive times")
                        
                except Exception as e:
                    consecutive_failures[miner_ip] = consecutive_failures.get(miner_ip, 0) + 1
                    print(f"✗ Error with {miner_ip}: {e}")
            
            if success_count == 0:
                print("⚠ No successful collections this cycle")
            
            time.sleep(config['poll_interval'])
            
    except KeyboardInterrupt:
        print("\nGracefully stopping collector...")
    except Exception as e:
        print(f"\n✗ Unexpected error in main loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()