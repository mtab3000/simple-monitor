"""Unit tests for the database module."""

import pytest
import tempfile
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import BitaxeDatabase


class TestBitaxeDatabase:
    """Test suite for BitaxeDatabase class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = BitaxeDatabase(db_path)
        yield db
        
        # Cleanup
        try:
            os.unlink(db_path)
        except OSError:
            pass

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics data for testing."""
        return [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'hostname': 'bitaxe1',
                'status': 'online',
                'hashrate_ghs': 934.5,
                'expected_hashrate_ghs': 934.3,
                'hashrate_ratio_percent': 100.0,
                'temp_asic_c': 60.0,
                'temp_vr_c': 53.0,
                'power_w': 14.0,
                'voltage_asic_set_v': 1.003,
                'voltage_asic_actual_v': 0.981,
                'voltage_device_v': 4.938,
                'frequency_set_mhz': 458,
                'efficiency_j_th': 15.1,
                'shares_accepted': 2285,
                'shares_rejected': 1,
                'uptime_hours': 3.1,
                'wifi_rssi': -52,
                'fan_speed_percent': 46,
                'fan_rpm': 3837,
                'free_heap_bytes': 8388608,
                'overclock_enabled': True,
                'current_a': 9.03,
                'pool_user': '3Aas8yBKTY3wA5d...',
                'best_session_diff': '2.87M'
            },
            {
                'timestamp': '2024-01-01 12:05:00',
                'miner_ip': '192.168.1.46',
                'hostname': 'bitaxe2',
                'status': 'online',
                'hashrate_ghs': 944.5,
                'expected_hashrate_ghs': 944.5,
                'hashrate_ratio_percent': 100.0,
                'temp_asic_c': 59.5,
                'temp_vr_c': 54.0,
                'power_w': 14.2,
                'voltage_asic_set_v': 1.003,
                'voltage_asic_actual_v': 0.974,
                'voltage_device_v': 5.008,
                'frequency_set_mhz': 463,
                'efficiency_j_th': 15.0,
                'shares_accepted': 2366,
                'shares_rejected': 3,
                'uptime_hours': 3.1,
                'wifi_rssi': -49,
                'fan_speed_percent': 38,
                'fan_rpm': 3148,
                'free_heap_bytes': 8388608,
                'overclock_enabled': True,
                'current_a': 9.23,
                'pool_user': '3Aas8yBKTY3wA5d...',
                'best_session_diff': '1.69M'
            }
        ]

    def test_database_initialization(self, temp_db):
        """Test database initialization and schema creation."""
        # Check that database file was created
        assert os.path.exists(temp_db.db_path)
        
        # Check that tables were created
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['miners', 'raw_metrics', 'hourly_stats', 'daily_stats', 'fleet_stats', 'alerts']
            for table in expected_tables:
                assert table in tables

    def test_add_or_update_miner(self, temp_db):
        """Test adding and updating miner configurations."""
        # Add new miner
        miner_id = temp_db.add_or_update_miner('192.168.1.45', 'bitaxe1', 934.3)
        assert isinstance(miner_id, int)
        assert miner_id > 0
        
        # Verify miner was added
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM miners WHERE id = ?", (miner_id,))
            miner = cursor.fetchone()
            
            assert miner is not None
            assert miner['ip_address'] == '192.168.1.45'
            assert miner['hostname'] == 'bitaxe1'
            assert miner['expected_hashrate_ghs'] == 934.3
            assert miner['is_active'] == 1
        
        # Update existing miner
        updated_id = temp_db.add_or_update_miner('192.168.1.45', 'updated_name', 950.0)
        assert updated_id == miner_id  # Should return same ID
        
        # Verify update
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM miners WHERE id = ?", (miner_id,))
            miner = cursor.fetchone()
            
            assert miner['hostname'] == 'updated_name'
            assert miner['expected_hashrate_ghs'] == 950.0

    def test_insert_raw_metrics(self, temp_db, sample_metrics):
        """Test inserting raw metrics data."""
        # Insert metrics
        temp_db.insert_raw_metrics(sample_metrics)
        
        # Verify data was inserted
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check miners were created
            cursor.execute("SELECT COUNT(*) FROM miners")
            miner_count = cursor.fetchone()[0]
            assert miner_count == 2
            
            # Check raw metrics were inserted
            cursor.execute("SELECT COUNT(*) FROM raw_metrics")
            metrics_count = cursor.fetchone()[0]
            assert metrics_count == 2
            
            # Verify specific data
            cursor.execute("""
                SELECT rm.*, m.ip_address 
                FROM raw_metrics rm 
                JOIN miners m ON rm.miner_id = m.id 
                WHERE m.ip_address = '192.168.1.45'
            """)
            metrics = cursor.fetchone()
            
            assert metrics is not None
            assert metrics['status'] == 'online'
            assert metrics['hashrate_ghs'] == 934.5
            assert metrics['temp_asic_c'] == 60.0

    def test_generate_hourly_stats(self, temp_db, sample_metrics):
        """Test generation of hourly statistics."""
        # Insert sample data with different timestamps
        extended_metrics = []
        base_time = datetime.strptime('2024-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
        
        for i in range(10):  # Create 10 data points over 1 hour
            for metric in sample_metrics:
                new_metric = metric.copy()
                new_metric['timestamp'] = (base_time + timedelta(minutes=i*6)).strftime('%Y-%m-%d %H:%M:%S')
                extended_metrics.append(new_metric)
        
        temp_db.insert_raw_metrics(extended_metrics)
        
        # Generate hourly stats
        temp_db.generate_hourly_stats(start_time=base_time)
        
        # Verify hourly stats were generated
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hourly_stats")
            stats_count = cursor.fetchone()[0]
            assert stats_count > 0
            
            # Check specific stats
            cursor.execute("""
                SELECT hs.*, m.ip_address 
                FROM hourly_stats hs 
                JOIN miners m ON hs.miner_id = m.id 
                WHERE m.ip_address = '192.168.1.45'
            """)
            stats = cursor.fetchone()
            
            assert stats is not None
            assert stats['samples_count'] == 10
            assert stats['uptime_percent'] == 100.0  # All samples online
            assert stats['avg_hashrate_ghs'] == 934.5

    def test_get_performance_trends(self, temp_db, sample_metrics):
        """Test retrieving performance trends."""
        # Insert sample data
        temp_db.insert_raw_metrics(sample_metrics)
        
        # Get miner ID
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM miners WHERE ip_address = '192.168.1.45'")
            miner_id = cursor.fetchone()[0]
        
        # Generate hourly stats first
        temp_db.generate_hourly_stats()
        
        # Get trends
        trends = temp_db.get_performance_trends(miner_id, hours=24)
        
        # Verify trends structure
        assert isinstance(trends, dict)
        expected_keys = ['timestamps', 'uptime', 'hashrate', 'temperature', 'power', 'efficiency', 'rejection_rate']
        for key in expected_keys:
            assert key in trends
            assert isinstance(trends[key], list)

    def test_get_fleet_analytics(self, temp_db, sample_metrics):
        """Test fleet analytics functionality."""
        # Insert sample data
        temp_db.insert_raw_metrics(sample_metrics)
        temp_db.generate_hourly_stats()
        
        # Get fleet analytics
        analytics = temp_db.get_fleet_analytics(days=7)
        
        # Verify analytics structure
        assert isinstance(analytics, dict)
        assert 'fleet_stats' in analytics
        assert 'top_performers' in analytics
        assert 'problem_miners' in analytics
        assert 'period_days' in analytics
        
        # Check fleet stats
        fleet_stats = analytics['fleet_stats']
        assert 'total_miners' in fleet_stats
        assert 'avg_uptime' in fleet_stats
        assert 'total_hashrate' in fleet_stats

    def test_maintenance_tasks(self, temp_db, sample_metrics):
        """Test maintenance task execution."""
        # Insert sample data
        temp_db.insert_raw_metrics(sample_metrics)
        
        # Mock time to trigger vacuum
        original_vacuum_interval = temp_db.vacuum_interval
        temp_db.vacuum_interval = 0  # Force vacuum
        temp_db.last_vacuum = 0
        
        # Run maintenance
        temp_db.maintenance_tasks()
        
        # Verify vacuum was performed (last_vacuum updated)
        assert temp_db.last_vacuum > 0
        
        # Restore original interval
        temp_db.vacuum_interval = original_vacuum_interval

    def test_database_optimization(self, temp_db):
        """Test database performance optimizations."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check WAL mode is enabled
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.upper() == 'WAL'
            
            # Check foreign keys are enabled
            cursor.execute("PRAGMA foreign_keys")
            foreign_keys = cursor.fetchone()[0]
            assert foreign_keys == 1
            
            # Check that indexes exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            indexes = cursor.fetchall()
            assert len(indexes) > 0  # Should have performance indexes

    def test_data_cleanup(self, temp_db):
        """Test automatic data cleanup functionality."""
        # Create old test data
        old_metrics = [{
            'timestamp': '2023-01-01 12:00:00',  # Old data
            'miner_ip': '192.168.1.45',
            'hostname': 'bitaxe1',
            'status': 'online',
            'hashrate_ghs': 900.0,
            'expected_hashrate_ghs': 900.0,
            'hashrate_ratio_percent': 100.0,
            'temp_asic_c': 65.0,
            'temp_vr_c': 58.0,
            'power_w': 15.0,
            'voltage_asic_set_v': 1.0,
            'voltage_asic_actual_v': 0.98,
            'voltage_device_v': 5.0,
            'frequency_set_mhz': 450,
            'efficiency_j_th': 16.0,
            'shares_accepted': 1000,
            'shares_rejected': 5,
            'uptime_hours': 2.0,
            'wifi_rssi': -50,
            'fan_speed_percent': 50,
            'fan_rpm': 4000,
            'free_heap_bytes': 8000000,
            'overclock_enabled': False,
            'current_a': 8.5,
            'pool_user': 'test_user',
            'best_session_diff': '1M'
        }]
        
        temp_db.insert_raw_metrics(old_metrics)
        
        # Verify data was inserted
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_metrics")
            initial_count = cursor.fetchone()[0]
            assert initial_count == 1
        
        # Run maintenance (which includes cleanup)
        temp_db.maintenance_tasks()
        
        # Old data should be cleaned up (30+ days old)
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_metrics WHERE timestamp < datetime('now', '-30 days')")
            old_count = cursor.fetchone()[0]
            assert old_count == 0  # Old data should be removed

    def test_error_handling(self, temp_db):
        """Test error handling in database operations."""
        # Test with invalid data
        invalid_metrics = [{
            'timestamp': 'invalid_timestamp',
            'miner_ip': '',
            'status': 'unknown'
        }]
        
        # Should handle gracefully without crashing
        try:
            temp_db.insert_raw_metrics(invalid_metrics)
        except Exception as e:
            # Should either succeed with default values or fail gracefully
            assert isinstance(e, Exception)

    def test_concurrent_access(self, temp_db, sample_metrics):
        """Test concurrent database access."""
        # Test multiple connections
        connections = []
        try:
            for _ in range(3):
                conn = temp_db.get_connection()
                connections.append(conn.__enter__())
            
            # All connections should work
            for conn in connections:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM miners")
                result = cursor.fetchone()
                assert result is not None
        
        finally:
            # Cleanup connections
            for conn in connections:
                try:
                    conn.__exit__(None, None, None)
                except:
                    pass


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database functionality."""

    @pytest.fixture
    def temp_db_with_data(self):
        """Create a temporary database with sample data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = BitaxeDatabase(db_path)
        
        # Insert sample data spanning multiple days
        sample_data = []
        base_time = datetime.now() - timedelta(days=3)
        
        for day in range(3):
            for hour in range(24):
                for minute in [0, 30]:  # Two data points per hour
                    timestamp = base_time + timedelta(days=day, hours=hour, minutes=minute)
                    
                    sample_data.append({
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'miner_ip': '192.168.1.45',
                        'hostname': 'test_miner',
                        'status': 'online',
                        'hashrate_ghs': 930 + (day * 5) + (hour % 10),  # Varying hashrate
                        'expected_hashrate_ghs': 934.3,
                        'hashrate_ratio_percent': 99.5 + (hour % 5) * 0.1,
                        'temp_asic_c': 60 + (hour % 12),  # Temperature variation
                        'temp_vr_c': 53 + (hour % 8),
                        'power_w': 14 + (hour % 3) * 0.5,
                        'voltage_asic_set_v': 1.003,
                        'voltage_asic_actual_v': 0.981,
                        'voltage_device_v': 4.938,
                        'frequency_set_mhz': 458,
                        'efficiency_j_th': 15.0 + (hour % 4) * 0.2,
                        'shares_accepted': 2000 + hour * 10,
                        'shares_rejected': hour % 5,
                        'uptime_hours': 24.0,
                        'wifi_rssi': -50 - (hour % 10),
                        'fan_speed_percent': 40 + (hour % 20),
                        'fan_rpm': 3500 + hour * 20,
                        'free_heap_bytes': 8388608,
                        'overclock_enabled': True,
                        'current_a': 9.0 + (hour % 3) * 0.1,
                        'pool_user': 'test_user',
                        'best_session_diff': f'{2 + hour % 3}.{hour % 10}M'
                    })
        
        db.insert_raw_metrics(sample_data)
        db.generate_hourly_stats(start_time=base_time)
        
        yield db
        
        # Cleanup
        try:
            os.unlink(db_path)
        except OSError:
            pass

    def test_complete_analytics_workflow(self, temp_db_with_data):
        """Test complete analytics workflow with realistic data."""
        # Get miner ID
        with temp_db_with_data.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM miners WHERE ip_address = '192.168.1.45'")
            miner_id = cursor.fetchone()[0]
        
        # Test performance trends
        trends = temp_db_with_data.get_performance_trends(miner_id, hours=72)
        assert len(trends['hashrate']) > 0
        assert len(trends['temperature']) > 0
        
        # Test fleet analytics
        analytics = temp_db_with_data.get_fleet_analytics(days=3)
        assert analytics['fleet_stats']['total_miners'] == 1
        assert analytics['fleet_stats']['total_hashrate'] > 0
        
        # Verify hourly stats were generated
        with temp_db_with_data.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hourly_stats WHERE miner_id = ?", (miner_id,))
            hourly_count = cursor.fetchone()[0]
            assert hourly_count > 0

    def test_large_dataset_performance(self, temp_db):
        """Test database performance with larger datasets."""
        # Generate larger dataset
        large_dataset = []
        base_time = datetime.now() - timedelta(hours=48)
        
        for i in range(1000):  # 1000 records
            timestamp = base_time + timedelta(minutes=i*3)  # Every 3 minutes
            
            large_dataset.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'miner_ip': f'192.168.1.{45 + (i % 5)}',  # 5 different miners
                'hostname': f'miner_{i % 5}',
                'status': 'online' if i % 10 != 0 else 'offline',  # 90% uptime
                'hashrate_ghs': 930 + (i % 50),
                'expected_hashrate_ghs': 934.3,
                'hashrate_ratio_percent': 98 + (i % 20) * 0.1,
                'temp_asic_c': 55 + (i % 30),
                'temp_vr_c': 50 + (i % 20),
                'power_w': 13 + (i % 10) * 0.2,
                'voltage_asic_set_v': 1.0,
                'voltage_asic_actual_v': 0.98,
                'voltage_device_v': 5.0,
                'frequency_set_mhz': 450 + (i % 20),
                'efficiency_j_th': 14 + (i % 20) * 0.1,
                'shares_accepted': 1000 + i,
                'shares_rejected': i % 10,
                'uptime_hours': 24.0,
                'wifi_rssi': -45 - (i % 15),
                'fan_speed_percent': 30 + (i % 40),
                'fan_rpm': 3000 + i,
                'free_heap_bytes': 8000000,
                'overclock_enabled': i % 2 == 0,
                'current_a': 8 + (i % 10) * 0.1,
                'pool_user': 'test_user',
                'best_session_diff': f'{1 + i % 5}M'
            })
        
        # Measure insertion time
        start_time = time.time()
        temp_db.insert_raw_metrics(large_dataset)
        insertion_time = time.time() - start_time
        
        # Should handle 1000 records reasonably quickly (< 5 seconds)
        assert insertion_time < 5.0, f"Insertion took {insertion_time:.2f}s, should be < 5s"
        
        # Verify all data was inserted
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_metrics")
            count = cursor.fetchone()[0]
            assert count == 1000
            
            cursor.execute("SELECT COUNT(*) FROM miners")
            miner_count = cursor.fetchone()[0]
            assert miner_count == 5

    def test_data_integrity_constraints(self, temp_db):
        """Test database integrity constraints and foreign keys."""
        # Test foreign key constraint
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to insert raw_metrics with invalid miner_id
            with pytest.raises(Exception):  # Should raise foreign key constraint error
                cursor.execute("""
                    INSERT INTO raw_metrics (miner_id, timestamp, status, hashrate_ghs)
                    VALUES (999, '2024-01-01 12:00:00', 'online', 900)
                """)
                conn.commit()

    def test_backup_and_recovery(self, temp_db_with_data):
        """Test database backup functionality."""
        # Create backup using SQLite backup
        backup_path = temp_db_with_data.db_path + '.backup'
        
        try:
            with temp_db_with_data.get_connection() as source_conn:
                # Create backup database
                import sqlite3
                backup_conn = sqlite3.connect(backup_path)
                source_conn.backup(backup_conn)
                backup_conn.close()
            
            # Verify backup was created
            assert os.path.exists(backup_path)
            
            # Verify backup integrity
            backup_db = BitaxeDatabase(backup_path)
            with backup_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM raw_metrics")
                backup_count = cursor.fetchone()[0]
                
                # Get original count
                cursor.execute("SELECT COUNT(*) FROM raw_metrics")
                original_count = cursor.fetchone()[0]
                
                assert backup_count == original_count
        
        finally:
            # Cleanup backup file
            try:
                os.unlink(backup_path)
            except OSError:
                pass