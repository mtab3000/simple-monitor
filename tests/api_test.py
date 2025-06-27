#!/usr/bin/env python3
"""
Test script to verify Bitaxe API connection and data format.
Run this before using the collector to check your miner connectivity.
"""
import requests
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from collector import load_config, validate_and_sanitize_metrics

def test_miner_api(miner_ip, timeout=10):
    """Test API connection to a single miner"""
    print(f"\nTesting connection to {miner_ip}...")
    
    try:
        response = requests.get(
            f"http://{miner_ip}/api/system/info",
            timeout=timeout,
            headers={'User-Agent': 'BitaxeMonitor/1.0'}
        )
        
        print(f"✓ HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response received ({len(data)} fields)")
            
            # Pretty print the JSON response
            print("\nAPI Response:")
            print(json.dumps(data, indent=2))
            
            # Check for expected fields
            expected_fields = ['hashRate', 'temp', 'power', 'uptimeSeconds', 
                             'sharesAccepted', 'sharesRejected']
            
            print("\nField Analysis:")
            for field in expected_fields:
                value = data.get(field, "NOT FOUND")
                print(f"  {field}: {value}")
            
            # Test data validation
            print("\nData Validation Test:")
            try:
                validated_metrics = validate_and_sanitize_metrics(data, miner_ip)
                print("✓ Data validation successful")
                print(f"  Sanitized hashrate: {validated_metrics['hashrate_gh']} GH/s")
                print(f"  Sanitized temperature: {validated_metrics['temperature']}°C")
                print(f"  Sanitized power: {validated_metrics['power_w']}W")
            except Exception as e:
                print(f"✗ Data validation failed: {e}")
            
            return True
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"✗ Timeout connecting to {miner_ip}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection failed to {miner_ip}")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    """Test all miners from config"""
    try:
        config = load_config()
        miners = config['miners']
        timeout = config.get('timeout', 10)
        
        print(f"Testing {len(miners)} miners from config.yaml...")
        print(f"Timeout: {timeout} seconds")
        
        success_count = 0
        for miner_ip in miners:
            if test_miner_api(miner_ip, timeout):
                success_count += 1
        
        print(f"\n=== Results ===")
        print(f"Successful connections: {success_count}/{len(miners)}")
        
        if success_count == len(miners):
            print("✓ All miners are reachable! You can now run collector.py")
        elif success_count > 0:
            print("⚠ Some miners are not reachable. Check IP addresses and network connectivity.")
        else:
            print("✗ No miners are reachable. Check configuration and network setup.")
            
    except FileNotFoundError:
        print("✗ config.yaml not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()