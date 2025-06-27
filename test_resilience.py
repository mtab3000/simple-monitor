#!/usr/bin/env python3
"""
Test script to verify resilience features of the collector.
Tests various edge cases and error conditions.
"""
import json
import tempfile
import os
from collector import (
    validate_numeric_value, 
    validate_and_sanitize_metrics,
    write_to_csv,
    load_config
)

def test_numeric_validation():
    """Test numeric value validation"""
    print("Testing numeric validation...")
    
    # Test cases: (value, field_name, min_val, max_val, expected_result)
    test_cases = [
        (42.5, "test", None, None, 42.5),
        ("42.5", "test", None, None, 42.5),
        (None, "test", None, None, 0.0),
        ("invalid", "test", None, None, 0.0),
        (float('nan'), "test", None, None, 0.0),
        (float('inf'), "test", None, None, 0.0),
        (-10, "test", 0, 100, 0),  # Below minimum
        (150, "test", 0, 100, 100),  # Above maximum
        (50, "test", 0, 100, 50),  # Within range
    ]
    
    for value, field, min_val, max_val, expected in test_cases:
        result = validate_numeric_value(value, field, min_val, max_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {field}={value} -> {result} (expected {expected})")
    
    print()

def test_data_sanitization():
    """Test data sanitization with various API response formats"""
    print("Testing data sanitization...")
    
    test_cases = [
        # Normal case
        {
            "name": "Normal API response",
            "data": {
                "hashRate": 1200.0,  # MH/s
                "temp": 75.5,
                "power": 20.3,
                "uptimeSeconds": 86400,
                "sharesAccepted": 150,
                "sharesRejected": 2,
                "stratumDifficulty": 5000
            }
        },
        # Alternative field names
        {
            "name": "Alternative field names",
            "data": {
                "currentHashrate": 1.2,  # Already in GH/s
                "temperature": 80.0,
                "powerConsumption": 18.5,
                "uptime": 7200,
                "acceptedShares": 100,
                "rejectedShares": 1,
                "difficulty": 3000
            }
        },
        # Missing fields
        {
            "name": "Missing fields",
            "data": {
                "hashRate": 500.0,
                "temp": 70.0
                # Other fields missing
            }
        },
        # Invalid values
        {
            "name": "Invalid values",
            "data": {
                "hashRate": "invalid",
                "temp": float('nan'),
                "power": -5.0,  # Negative power
                "uptimeSeconds": "not_a_number",
                "sharesAccepted": float('inf'),
                "sharesRejected": -1,  # Negative shares
                "stratumDifficulty": None
            }
        },
        # Extreme values
        {
            "name": "Extreme values",
            "data": {
                "hashRate": 50000.0,  # Very high hashrate
                "temp": 200.0,       # Very high temperature
                "power": 1000.0,     # Very high power
                "uptimeSeconds": 86400 * 365,  # One year
                "sharesAccepted": 1000000,
                "sharesRejected": 50000,
                "stratumDifficulty": 100000000
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"  Testing: {test_case['name']}")
        try:
            result = validate_and_sanitize_metrics(test_case['data'], "test-miner")
            print(f"    ✓ Sanitized successfully")
            print(f"      Hashrate: {result['hashrate_gh']} GH/s")
            print(f"      Temperature: {result['temperature']}°C")
            print(f"      Power: {result['power_w']}W")
        except Exception as e:
            print(f"    ✗ Failed: {e}")
    
    print()

def test_csv_writing():
    """Test CSV writing with various scenarios"""
    print("Testing CSV writing...")
    
    # Test with temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Test data
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'miner_ip': '192.168.1.100',
            'hashrate_gh': 1.2,
            'temperature': 75.0,
            'power_w': 20.0,
            'uptime_s': 3600,
            'accepted_shares': 100,
            'rejected_shares': 2,
            'pool_difficulty': 5000
        }
        
        # Test normal write
        success = write_to_csv(test_data, tmp_path)
        if success:
            print("  ✓ Normal CSV write successful")
        else:
            print("  ✗ Normal CSV write failed")
        
        # Test append
        success = write_to_csv(test_data, tmp_path)
        if success:
            print("  ✓ CSV append successful")
        else:
            print("  ✗ CSV append failed")
        
        # Check file contents
        if os.path.exists(tmp_path):
            with open(tmp_path, 'r') as f:
                lines = f.readlines()
                if len(lines) == 3:  # Header + 2 data rows
                    print("  ✓ CSV file has correct number of lines")
                else:
                    print(f"  ✗ CSV file has {len(lines)} lines, expected 3")
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    # Test write to non-existent directory
    non_existent_path = "/tmp/non_existent_dir/test.csv"
    success = write_to_csv(test_data, non_existent_path)
    if success:
        print("  ✓ CSV write to non-existent directory (created automatically)")
        # Clean up
        if os.path.exists(non_existent_path):
            os.unlink(non_existent_path)
            os.rmdir(os.path.dirname(non_existent_path))
    else:
        print("  ✗ CSV write to non-existent directory failed")
    
    print()

def test_config_validation():
    """Test configuration validation"""
    print("Testing configuration validation...")
    
    # Save original config
    original_config_path = 'config.yaml'
    backup_path = 'config.yaml.backup'
    
    if os.path.exists(original_config_path):
        os.rename(original_config_path, backup_path)
    
    try:
        # Test missing config file
        try:
            load_config()
            print("  ✗ Should have failed with missing config file")
        except FileNotFoundError:
            print("  ✓ Correctly detected missing config file")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
        
        # Test invalid YAML
        with open(original_config_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        try:
            load_config()
            print("  ✗ Should have failed with invalid YAML")
        except ValueError:
            print("  ✓ Correctly detected invalid YAML")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
        
        # Test missing required fields
        with open(original_config_path, 'w') as f:
            f.write("poll_interval: 10\\n")  # Missing miners and csv_path
        
        try:
            load_config()
            print("  ✗ Should have failed with missing required fields")
        except ValueError:
            print("  ✓ Correctly detected missing required fields")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
        
        # Test invalid values
        with open(original_config_path, 'w') as f:
            f.write("""
miners: []
poll_interval: -5
csv_path: test.csv
""")
        
        try:
            load_config()
            print("  ✗ Should have failed with invalid values")
        except ValueError:
            print("  ✓ Correctly detected invalid values")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            
    finally:
        # Restore original config
        if os.path.exists(original_config_path):
            os.unlink(original_config_path)
        if os.path.exists(backup_path):
            os.rename(backup_path, original_config_path)
    
    print()

def main():
    """Run all resilience tests"""
    print("=== Collector Resilience Tests ===\\n")
    
    test_numeric_validation()
    test_data_sanitization()
    test_csv_writing()
    test_config_validation()
    
    print("=== Test Suite Complete ===")

if __name__ == "__main__":
    main()