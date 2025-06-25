#!/usr/bin/env python3
"""
Data Migration Tool for Bitaxe Gamma Monitor
Migrates data from CSV format to the new SQLite database
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from database import BitaxeDatabase
from cli_view import load_csv_data


class DataMigrator:
    """Handles migration from CSV to SQLite database."""
    
    def __init__(self, csv_path: str = "metrics.csv", db_path: str = "data/bitaxe_monitor.db"):
        """Initialize the data migrator."""
        self.csv_path = csv_path
        self.db_path = db_path
        self.db = BitaxeDatabase(db_path)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def migrate_csv_to_database(self) -> Dict[str, Any]:
        """Migrate all CSV data to the new database format."""
        self.logger.info("Starting CSV to database migration...")
        
        if not os.path.exists(self.csv_path):
            self.logger.error(f"CSV file not found: {self.csv_path}")
            return {'success': False, 'error': f'CSV file not found: {self.csv_path}'}
        
        try:
            # Load CSV data
            self.logger.info(f"Loading CSV data from {self.csv_path}")
            csv_data = load_csv_data(self.csv_path)
            
            if not csv_data:
                return {'success': False, 'error': 'No data found in CSV file'}
            
            self.logger.info(f"Found {len(csv_data)} records in CSV file")
            
            # Process data in batches
            batch_size = 1000
            total_records = len(csv_data)
            processed_records = 0
            
            for i in range(0, total_records, batch_size):
                batch = csv_data[i:i + batch_size]
                
                # Convert and insert batch
                converted_batch = self._convert_csv_records(batch)
                self.db.insert_raw_metrics(converted_batch)
                
                processed_records += len(batch)
                self.logger.info(f"Processed {processed_records}/{total_records} records ({processed_records/total_records*100:.1f}%)")
            
            # Generate aggregated statistics
            self.logger.info("Generating hourly statistics...")
            self.db.generate_hourly_stats(start_time=self._get_earliest_timestamp(csv_data))
            
            # Create backup of original CSV
            backup_path = f"{self.csv_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._backup_csv(backup_path)
            
            self.logger.info("Migration completed successfully!")
            
            return {
                'success': True,
                'total_records': total_records,
                'processed_records': processed_records,
                'backup_path': backup_path,
                'database_path': self.db_path
            }
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _convert_csv_records(self, csv_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert CSV records to database format."""
        converted_records = []
        
        for record in csv_records:
            # Clean and convert the record
            converted_record = {}
            
            # Required fields
            converted_record['timestamp'] = record.get('timestamp', '')
            converted_record['miner_ip'] = record.get('miner_ip', '')
            converted_record['status'] = record.get('status', 'unknown')
            converted_record['hostname'] = record.get('hostname', f"Miner-{record.get('miner_ip', '').split('.')[-1] if record.get('miner_ip') else 'unknown'}")
            
            # Numeric fields with defaults
            numeric_fields = {
                'hashrate_ghs': 0.0,
                'expected_hashrate_ghs': 0.0,
                'hashrate_ratio_percent': 0.0,
                'temp_asic_c': 0.0,
                'temp_vr_c': 0.0,
                'power_w': 0.0,
                'voltage_asic_set_v': 0.0,
                'voltage_asic_actual_v': 0.0,
                'voltage_device_v': 0.0,
                'frequency_set_mhz': 0.0,
                'efficiency_j_th': 0.0,
                'shares_accepted': 0,
                'shares_rejected': 0,
                'uptime_hours': 0.0,
                'wifi_rssi': 0,
                'fan_speed_percent': 0,
                'fan_rpm': 0,
                'free_heap_bytes': 0,
                'current_a': 0.0
            }
            
            for field, default_value in numeric_fields.items():
                try:
                    value = record.get(field, default_value)
                    if value == '' or value is None:
                        converted_record[field] = default_value
                    else:
                        if isinstance(default_value, int):
                            converted_record[field] = int(float(value))
                        else:
                            converted_record[field] = float(value)
                except (ValueError, TypeError):
                    converted_record[field] = default_value
            
            # Boolean fields
            converted_record['overclock_enabled'] = bool(record.get('overclock_enabled', False))
            
            # String fields
            converted_record['pool_user'] = record.get('pool_user', '')
            converted_record['best_session_diff'] = record.get('best_session_diff', '')
            
            converted_records.append(converted_record)
        
        return converted_records
    
    def _get_earliest_timestamp(self, csv_data: List[Dict[str, Any]]) -> datetime:
        """Get the earliest timestamp from CSV data."""
        timestamps = []
        for record in csv_data:
            try:
                timestamp = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                timestamps.append(timestamp)
            except (ValueError, KeyError):
                continue
        
        return min(timestamps) if timestamps else datetime.now()
    
    def _backup_csv(self, backup_path: str):
        """Create a backup of the original CSV file."""
        try:
            import shutil
            shutil.copy2(self.csv_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify the migration was successful by comparing record counts."""
        self.logger.info("Verifying migration...")
        
        # Count CSV records
        csv_count = 0
        if os.path.exists(self.csv_path):
            try:
                csv_data = load_csv_data(self.csv_path)
                csv_count = len(csv_data)
            except Exception as e:
                self.logger.error(f"Error reading CSV for verification: {e}")
        
        # Count database records
        db_count = 0
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM raw_metrics")
                db_count = cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error reading database for verification: {e}")
        
        # Get database statistics
        stats = {}
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Miner count
                cursor.execute("SELECT COUNT(*) FROM miners WHERE is_active = 1")
                stats['active_miners'] = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM raw_metrics")
                date_range = cursor.fetchone()
                stats['date_range'] = {
                    'start': date_range[0],
                    'end': date_range[1]
                }
                
                # Hourly stats count
                cursor.execute("SELECT COUNT(*) FROM hourly_stats")
                stats['hourly_stats'] = cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {e}")
        
        verification_result = {
            'csv_records': csv_count,
            'database_records': db_count,
            'migration_success': db_count > 0,
            'record_match': csv_count == db_count,
            'database_stats': stats
        }
        
        if verification_result['record_match']:
            self.logger.info("✅ Migration verified successfully - record counts match")
        elif verification_result['migration_success']:
            self.logger.warning(f"⚠️ Migration completed but record counts differ (CSV: {csv_count}, DB: {db_count})")
        else:
            self.logger.error("❌ Migration verification failed - no records in database")
        
        return verification_result
    
    def export_database_to_csv(self, output_path: str = "exported_metrics.csv") -> Dict[str, Any]:
        """Export database data back to CSV format for backup or analysis."""
        self.logger.info(f"Exporting database to CSV: {output_path}")
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all raw metrics with miner information
                cursor.execute("""
                    SELECT 
                        rm.timestamp,
                        m.ip_address as miner_ip,
                        m.hostname,
                        rm.status,
                        rm.hashrate_ghs,
                        rm.expected_hashrate_ghs,
                        rm.hashrate_ratio_percent,
                        rm.temp_asic_c,
                        rm.temp_vr_c,
                        rm.power_w,
                        rm.voltage_asic_set_v,
                        rm.voltage_asic_actual_v,
                        rm.voltage_device_v,
                        rm.frequency_set_mhz,
                        rm.efficiency_j_th,
                        rm.shares_accepted,
                        rm.shares_rejected,
                        rm.uptime_hours,
                        rm.wifi_rssi,
                        rm.fan_speed_percent,
                        rm.fan_rpm,
                        rm.free_heap_bytes,
                        rm.overclock_enabled,
                        rm.current_a,
                        rm.pool_user,
                        rm.best_session_diff
                    FROM raw_metrics rm
                    JOIN miners m ON rm.miner_id = m.id
                    ORDER BY rm.timestamp
                """)
                
                records = cursor.fetchall()
                
                if not records:
                    return {'success': False, 'error': 'No data to export'}
                
                # Write to CSV
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'timestamp', 'miner_ip', 'hostname', 'status',
                        'hashrate_ghs', 'expected_hashrate_ghs', 'hashrate_ratio_percent',
                        'temp_asic_c', 'temp_vr_c', 'power_w',
                        'voltage_asic_set_v', 'voltage_asic_actual_v', 'voltage_device_v',
                        'frequency_set_mhz', 'efficiency_j_th',
                        'shares_accepted', 'shares_rejected', 'uptime_hours',
                        'wifi_rssi', 'fan_speed_percent', 'fan_rpm', 'free_heap_bytes',
                        'overclock_enabled', 'current_a', 'pool_user', 'best_session_diff'
                    ]
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for record in records:
                        writer.writerow(dict(record))
                
                self.logger.info(f"Exported {len(records)} records to {output_path}")
                
                return {
                    'success': True,
                    'exported_records': len(records),
                    'output_path': output_path
                }
                
        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            return {'success': False, 'error': str(e)}


def main():
    """Command-line interface for data migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bitaxe Monitor Data Migration Tool')
    parser.add_argument('--csv-path', default='metrics.csv', help='Path to CSV file to migrate')
    parser.add_argument('--db-path', default='data/bitaxe_monitor.db', help='Path to SQLite database')
    parser.add_argument('--action', choices=['migrate', 'verify', 'export'], default='migrate',
                       help='Action to perform')
    parser.add_argument('--export-path', default='exported_metrics.csv',
                       help='Output path for CSV export')
    
    args = parser.parse_args()
    
    migrator = DataMigrator(args.csv_path, args.db_path)
    
    if args.action == 'migrate':
        result = migrator.migrate_csv_to_database()
        if result['success']:
            print(f"✅ Migration successful!")
            print(f"   Total records: {result['total_records']}")
            print(f"   Database: {result['database_path']}")
            print(f"   Backup: {result['backup_path']}")
            
            # Automatically verify
            verification = migrator.verify_migration()
            if verification['record_match']:
                print("✅ Verification passed - all records migrated successfully")
            else:
                print("⚠️ Verification warning - see logs for details")
        else:
            print(f"❌ Migration failed: {result['error']}")
            sys.exit(1)
    
    elif args.action == 'verify':
        result = migrator.verify_migration()
        print(f"CSV records: {result['csv_records']}")
        print(f"Database records: {result['database_records']}")
        print(f"Active miners: {result['database_stats'].get('active_miners', 'N/A')}")
        print(f"Date range: {result['database_stats'].get('date_range', {}).get('start', 'N/A')} to {result['database_stats'].get('date_range', {}).get('end', 'N/A')}")
        
        if result['record_match']:
            print("✅ Verification successful")
        else:
            print("⚠️ Verification failed - record counts don't match")
    
    elif args.action == 'export':
        result = migrator.export_database_to_csv(args.export_path)
        if result['success']:
            print(f"✅ Export successful!")
            print(f"   Exported records: {result['exported_records']}")
            print(f"   Output file: {result['output_path']}")
        else:
            print(f"❌ Export failed: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()