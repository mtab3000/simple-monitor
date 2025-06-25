#!/usr/bin/env python3
"""
Data Export Tool for Bitaxe Gamma Monitor
Exports data from SQLite database to CSV format for analysis
"""

import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging

from .database import BitaxeDatabase


class DataExporter:
    """Handles export from SQLite database to CSV format."""
    
    def __init__(self, db_path: str = "data/bitaxe_monitor.db"):
        """Initialize the data exporter."""
        self.db_path = db_path
        self.db = BitaxeDatabase(db_path)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def export_database_to_csv(self, output_path: str = "exported_metrics.csv", hours: int = None) -> Dict[str, Any]:
        """Export database data to CSV format for backup or analysis."""
        self.logger.info(f"Exporting database to CSV: {output_path}")
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query with optional time filter
                base_query = """
                    SELECT 
                        rm.timestamp,
                        m.ip_address as miner_ip,
                        m.hostname,
                        rm.status,
                        rm.hashrate_ghs,
                        rm.expected_hashrate_ghs,
                        rm.hashrate_ratio_percent,
                        rm.efficiency_j_th,
                        rm.temp_asic_c,
                        rm.temp_vr_c,
                        rm.power_w,
                        rm.voltage_asic_set_v,
                        rm.voltage_asic_actual_v,
                        rm.voltage_device_v,
                        rm.frequency_set_mhz,
                        rm.current_a,
                        rm.shares_accepted,
                        rm.shares_rejected,
                        rm.rejection_rate_percent,
                        rm.uptime_hours,
                        rm.wifi_rssi,
                        rm.fan_rpm,
                        rm.connected_pool
                    FROM raw_metrics rm
                    JOIN miners m ON rm.miner_id = m.id
                """
                
                if hours:
                    cutoff_time = datetime.now() - timedelta(hours=hours)
                    query = base_query + " WHERE rm.timestamp >= ? ORDER BY rm.timestamp"
                    cursor.execute(query, (cutoff_time.isoformat(),))
                else:
                    query = base_query + " ORDER BY rm.timestamp"
                    cursor.execute(query)
                
                records = cursor.fetchall()
                
                if not records:
                    return {'success': False, 'error': 'No data to export'}
                
                # Write to CSV
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'timestamp', 'miner_ip', 'hostname', 'status',
                        'hashrate_ghs', 'expected_hashrate_ghs', 'hashrate_ratio_percent',
                        'efficiency_j_th', 'temp_asic_c', 'temp_vr_c', 'power_w',
                        'voltage_asic_set_v', 'voltage_asic_actual_v', 'voltage_device_v',
                        'frequency_set_mhz', 'current_a', 'shares_accepted', 'shares_rejected',
                        'rejection_rate_percent', 'uptime_hours', 'wifi_rssi', 'fan_rpm', 'connected_pool'
                    ]
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for record in records:
                        # Convert SQLite Row to dictionary
                        row_dict = dict(record)
                        writer.writerow(row_dict)
                
                self.logger.info(f"Successfully exported {len(records)} records to {output_path}")
                return {
                    'success': True,
                    'records_exported': len(records),
                    'output_path': output_path
                }
                
        except Exception as e:
            self.logger.error(f"Error during export: {e}")
            return {'success': False, 'error': str(e)}


def main():
    """Command-line interface for data export."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export database data to CSV format')
    parser.add_argument('--db-path', default='data/bitaxe_monitor.db', help='Database file path')
    parser.add_argument('--output', default='exported_metrics.csv', help='Output CSV file path')
    parser.add_argument('--hours', type=int, help='Export only last N hours of data')
    
    args = parser.parse_args()
    
    exporter = DataExporter(args.db_path)
    result = exporter.export_database_to_csv(args.output, args.hours)
    
    if result['success']:
        print(f"✅ Export successful: {result['records_exported']} records exported to {result['output_path']}")
    else:
        print(f"❌ Export failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()