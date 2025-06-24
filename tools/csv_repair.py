#!/usr/bin/env python3
"""
CSV Recovery and Repair Utility for Bitaxe Monitor
Helps fix corrupted CSV files and recover missing data
"""

import csv
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import json

class CSVRepairTool:
    def __init__(self, csv_path='metrics.csv'):
        self.csv_path = Path(csv_path)
        self.backup_dir = self.csv_path.parent / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        self.expected_fieldnames = [
            'timestamp', 'miner_ip', 'status', 'hashrate_th', 'hashrate_ghs',
            'expected_hashrate_ghs', 'hashrate_ratio_percent', 'temp_asic_c', 'temp_vr_c', 'power_w', 
            'voltage_device_v', 'voltage_asic_set_v', 'voltage_asic_actual_v', 'current_a', 'frequency_set_mhz', 
            'efficiency_j_th', 'shares_accepted', 'shares_rejected', 'rejection_reasons', 'best_diff', 
            'best_session_diff', 'uptime_seconds', 'uptime_hours', 'wifi_rssi', 'wifi_status', 
            'fan_speed_percent', 'fan_rpm', 'hostname', 'free_heap_bytes', 'overclock_enabled', 
            'stratum_url', 'pool_user'
        ]
    
    def analyze_csv(self, file_path):
        """Analyze CSV file for corruption and issues"""
        print(f"\nAnalyzing {file_path}...")
        
        if not os.path.exists(file_path):
            print("ERROR: File does not exist!")
            return False
        
        issues = []
        total_lines = 0
        valid_records = 0
        corrupted_lines = []
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Check header
                first_line = csvfile.readline().strip()
                total_lines += 1
                
                expected_header = ','.join(self.expected_fieldnames)
                if first_line != expected_header:
                    issues.append(f"Header mismatch - got {len(first_line.split(','))} fields, expected {len(self.expected_fieldnames)}")
                
                # Analyze data lines
                line_num = 1
                for line in csvfile:
                    line_num += 1
                    total_lines += 1
                    
                    # Check for obvious corruption (data merged without newlines)
                    if len(line.strip()) > 500:  # Suspiciously long line
                        corrupted_lines.append((line_num, "Line too long", line[:100] + "..."))
                        continue
                    
                    # Count fields
                    fields = line.strip().split(',')
                    if len(fields) != len(self.expected_fieldnames):
                        corrupted_lines.append((line_num, f"Wrong field count: {len(fields)}", line.strip()[:100]))
                        continue
                    
                    # Basic validation
                    try:
                        timestamp = fields[0]
                        if len(timestamp) < 19:  # Should be YYYY-MM-DD HH:MM:SS
                            corrupted_lines.append((line_num, "Invalid timestamp", line.strip()[:100]))
                            continue
                        
                        valid_records += 1
                        
                    except Exception as e:
                        corrupted_lines.append((line_num, f"Parse error: {e}", line.strip()[:100]))
                        
        except Exception as e:
            print(f"ERROR reading file: {e}")
            return False
        
        # Report results
        print(f"Total lines: {total_lines}")
        print(f"Valid records: {valid_records}")
        print(f"Corrupted lines: {len(corrupted_lines)}")
        
        if corrupted_lines:
            print("\nCORRUPTED LINES FOUND:")
            for line_num, reason, content in corrupted_lines[:10]:  # Show first 10
                print(f"  Line {line_num}: {reason}")
                print(f"    Content: {content}")
            
            if len(corrupted_lines) > 10:
                print(f"    ... and {len(corrupted_lines) - 10} more")
        
        if issues:
            print("\nISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        
        return len(corrupted_lines) == 0 and len(issues) == 0
    
    def repair_csv(self, input_path, output_path=None):
        """Attempt to repair a corrupted CSV file"""
        input_path = Path(input_path)
        
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_repaired{input_path.suffix}"
        else:
            output_path = Path(output_path)
        
        print(f"\nRepairing {input_path} -> {output_path}")
        
        # Create backup
        backup_path = self.backup_dir / f"{input_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        shutil.copy2(input_path, backup_path)
        print(f"Created backup: {backup_path}")
        
        repaired_records = 0
        skipped_records = 0
        
        try:
            with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
                 open(output_path, 'w', newline='', encoding='utf-8') as outfile:
                
                writer = csv.DictWriter(outfile, fieldnames=self.expected_fieldnames)
                writer.writeheader()
                
                line_num = 0
                buffer = ""
                
                for line in infile:
                    line_num += 1
                    
                    if line_num == 1:  # Skip header
                        continue
                    
                    buffer += line.strip()
                    
                    # Try to parse what we have in buffer
                    while True:
                        # Look for complete record pattern
                        parts = buffer.split(',')
                        
                        if len(parts) < len(self.expected_fieldnames):
                            # Not enough fields, need more data
                            break
                        
                        if len(parts) == len(self.expected_fieldnames):
                            # Perfect match, process this record
                            record = self.create_record_dict(parts)
                            if record:
                                writer.writerow(record)
                                repaired_records += 1
                            else:
                                skipped_records += 1
                            buffer = ""
                            break
                        
                        # Too many fields, try to find record boundary
                        # Look for timestamp pattern at field positions
                        found_boundary = False
                        for i in range(len(self.expected_fieldnames), len(parts)):
                            if self.looks_like_timestamp(parts[i]):
                                # Found start of next record
                                record_parts = parts[:len(self.expected_fieldnames)]
                                remaining_parts = parts[len(self.expected_fieldnames):]
                                
                                record = self.create_record_dict(record_parts)
                                if record:
                                    writer.writerow(record)
                                    repaired_records += 1
                                else:
                                    skipped_records += 1
                                
                                # Continue with remaining data
                                buffer = ','.join(remaining_parts)
                                found_boundary = True
                                break
                        
                        if not found_boundary:
                            # Can't find boundary, skip this corrupted data
                            print(f"Skipping corrupted data at line {line_num}")
                            skipped_records += 1
                            buffer = ""
                            break
                
                # Process any remaining buffer
                if buffer.strip():
                    parts = buffer.split(',')
                    if len(parts) == len(self.expected_fieldnames):
                        record = self.create_record_dict(parts)
                        if record:
                            writer.writerow(record)
                            repaired_records += 1
                        else:
                            skipped_records += 1
        
        except Exception as e:
            print(f"ERROR during repair: {e}")
            return False
        
        print(f"Repair complete!")
        print(f"Repaired records: {repaired_records}")
        print(f"Skipped records: {skipped_records}")
        
        return True
    
    def looks_like_timestamp(self, text):
        """Check if text looks like a timestamp"""
        if len(text) < 19:
            return False
        
        # Look for YYYY-MM-DD HH:MM:SS pattern
        parts = text.split(' ')
        if len(parts) != 2:
            return False
        
        date_part, time_part = parts
        if len(date_part) != 10 or date_part.count('-') != 2:
            return False
        
        if len(time_part) != 8 or time_part.count(':') != 2:
            return False
        
        return True
    
    def create_record_dict(self, field_values):
        """Create a record dictionary from field values"""
        if len(field_values) != len(self.expected_fieldnames):
            return None
        
        try:
            record = {}
            for i, fieldname in enumerate(self.expected_fieldnames):
                value = field_values[i].strip()
                
                # Basic validation and cleanup
                if fieldname == 'timestamp':
                    if not self.looks_like_timestamp(value):
                        return None
                elif fieldname in ['miner_ip', 'status', 'hostname', 'wifi_status', 'stratum_url', 'pool_user', 'rejection_reasons', 'best_diff', 'best_session_diff']:
                    # String fields
                    value = value.strip('"\'')
                else:
                    # Numeric fields
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        value = 0
                
                record[fieldname] = value
            
            return record
            
        except Exception:
            return None
    
    def merge_csv_files(self, file_list, output_path):
        """Merge multiple CSV files into one"""
        print(f"\nMerging {len(file_list)} files into {output_path}")
        
        all_records = []
        
        for file_path in file_list:
            print(f"Reading {file_path}...")
            try:
                with open(file_path, 'r', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        all_records.append(row)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        # Sort by timestamp
        all_records.sort(key=lambda x: x.get('timestamp', ''))
        
        # Write merged file
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.expected_fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        
        print(f"Merged {len(all_records)} records to {output_path}")
    
    def show_statistics(self, file_path):
        """Show statistics about the CSV file"""
        print(f"\nStatistics for {file_path}:")
        
        try:
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                total_records = 0
                status_counts = {}
                miners = set()
                date_range = []
                
                for row in reader:
                    total_records += 1
                    
                    status = row.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    miners.add(row.get('miner_ip', 'unknown'))
                    
                    timestamp = row.get('timestamp', '')
                    if timestamp:
                        date_range.append(timestamp)
                
                print(f"Total records: {total_records:,}")
                print(f"Unique miners: {len(miners)}")
                
                if date_range:
                    print(f"Date range: {min(date_range)} to {max(date_range)}")
                
                print("\nStatus distribution:")
                for status, count in sorted(status_counts.items()):
                    percentage = (count / total_records) * 100
                    print(f"  {status}: {count:,} ({percentage:.1f}%)")
                
                print(f"\nMiners found:")
                for miner in sorted(miners):
                    print(f"  {miner}")
                    
        except Exception as e:
            print(f"Error reading file: {e}")

def main():
    if len(sys.argv) < 2:
        print("CSV Repair Tool for Bitaxe Monitor")
        print("\nUsage:")
        print("  python csv_repair.py analyze <csv_file>")
        print("  python csv_repair.py repair <csv_file> [output_file]")
        print("  python csv_repair.py merge <output_file> <file1> <file2> ...")
        print("  python csv_repair.py stats <csv_file>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    tool = CSVRepairTool()
    
    if command == 'analyze':
        if len(sys.argv) < 3:
            print("Error: Please specify CSV file to analyze")
            sys.exit(1)
        tool.analyze_csv(sys.argv[2])
    
    elif command == 'repair':
        if len(sys.argv) < 3:
            print("Error: Please specify CSV file to repair")
            sys.exit(1)
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        tool.repair_csv(input_file, output_file)
    
    elif command == 'merge':
        if len(sys.argv) < 4:
            print("Error: Please specify output file and input files")
            sys.exit(1)
        output_file = sys.argv[2]
        input_files = sys.argv[3:]
        tool.merge_csv_files(input_files, output_file)
    
    elif command == 'stats':
        if len(sys.argv) < 3:
            print("Error: Please specify CSV file")
            sys.exit(1)
        tool.show_statistics(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
