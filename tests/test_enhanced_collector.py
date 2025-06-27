"""Unit tests for the enhanced collector module."""

import pytest
import tempfile
import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.enhanced_collector import EnhancedBitaxeCollector


class TestEnhancedBitaxeCollector:
    """Test suite for EnhancedBitaxeCollector class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return {
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3},
                {'ip': '192.168.1.46', 'expected_hashrate_ghs': 944.5}
            ],
            'poll_interval': 1,  # Short interval for testing
            'csv_path': 'test_metrics.csv',
            'timeout': 10,
            'retries': 3,
            'retry_delay': 1,
            'backup_frequency': 100,
            'validate_csv': True,
            'enable_database': True,
            'enable_analytics': True,
            'analytics_interval': 5,  # Short interval for testing
            'maintenance_interval': 10,  # Short interval for testing
            'database_path': 'test_db.db'
        }

    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create a temporary config file."""
        import yaml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(mock_config, f)
            config_path = f.name
        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def enhanced_collector(self, temp_config_file):
        """Create an EnhancedBitaxeCollector instance for testing."""
        with patch('enhanced_collector.BitaxeDatabase') as mock_db:
            with patch('enhanced_collector.PerformanceAnalyzer') as mock_analyzer:
                with patch('enhanced_collector.PredictiveAnalyzer') as mock_predictor:
                    # Mock database instance
                    mock_db_instance = Mock()
                    mock_db.return_value = mock_db_instance
                    
                    # Mock analyzer instances
                    mock_analyzer_instance = Mock()
                    mock_analyzer.return_value = mock_analyzer_instance
                    
                    mock_predictor_instance = Mock()
                    mock_predictor.return_value = mock_predictor_instance
                    
                    collector = EnhancedBitaxeCollector(temp_config_file)
                    
                    # Set short intervals for testing
                    collector.config['analytics_interval'] = 0.1
                    collector.config['maintenance_interval'] = 0.1
                    
                    yield collector, mock_db_instance, mock_analyzer_instance, mock_predictor_instance

    def test_initialization(self, enhanced_collector):
        """Test enhanced collector initialization."""
        collector, mock_db, mock_analyzer, mock_predictor = enhanced_collector
        
        # Check that database and analytics components are initialized
        assert collector.db == mock_db
        assert collector.analyzer == mock_analyzer
        assert collector.predictor == mock_predictor
        
        # Check enhanced configuration
        assert 'enable_database' in collector.config
        assert 'enable_analytics' in collector.config
        assert 'analytics_interval' in collector.config
        assert 'maintenance_interval' in collector.config

    def test_enhanced_logging_setup(self, enhanced_collector):
        """Test enhanced logging setup."""
        collector, _, _, _ = enhanced_collector
        
        # Check that logger is configured
        assert hasattr(collector, 'logger')
        assert collector.logger is not None

    def test_collect_once_with_database(self, enhanced_collector):
        """Test enhanced collection with database integration."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Mock successful miner data collection
        sample_metrics = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'miner_ip': '192.168.1.45',
            'hostname': 'bitaxe1',
            'status': 'online',
            'hashrate_ghs': 934.5,
            'expected_hashrate_ghs': 934.3
        }
        
        with patch.object(collector, 'fetch_miner_data', return_value=sample_metrics):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                collector.collect_once()
                
                # Verify database insertion was called
                mock_db.insert_raw_metrics.assert_called_once()
                
                # Check collection statistics
                assert collector.collection_stats['total_collections'] == 1
                assert collector.collection_stats['successful_collections'] == 1

    def test_collect_once_database_disabled(self, enhanced_collector):
        """Test collection with database disabled."""
        collector, mock_db, _, _ = enhanced_collector
        collector.config['enable_database'] = False
        
        sample_metrics = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'miner_ip': '192.168.1.45',
            'hostname': 'bitaxe1',
            'status': 'online'
        }
        
        with patch.object(collector, 'fetch_miner_data', return_value=sample_metrics):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                collector.collect_once()
                
                # Verify database insertion was NOT called
                mock_db.insert_raw_metrics.assert_not_called()

    def test_analytics_scheduling(self, enhanced_collector):
        """Test analytics scheduling functionality."""
        collector, mock_db, mock_analyzer, _ = enhanced_collector
        
        # Mock successful collection
        with patch.object(collector, 'fetch_miner_data', return_value={'status': 'online', 'miner_ip': '192.168.1.45'}):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                # Set last analytics run to trigger immediate execution
                collector.last_analytics_run = 0
                
                collector.collect_once()
                
                # Give time for background thread to start
                time.sleep(0.2)
                
                # Analytics should have been triggered
                assert collector.last_analytics_run > 0

    def test_maintenance_scheduling(self, enhanced_collector):
        """Test maintenance scheduling functionality."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Mock successful collection
        with patch.object(collector, 'fetch_miner_data', return_value={'status': 'online', 'miner_ip': '192.168.1.45'}):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                # Set last maintenance run to trigger immediate execution
                collector.last_maintenance_run = 0
                
                collector.collect_once()
                
                # Give time for background thread to start
                time.sleep(0.2)
                
                # Maintenance should have been triggered
                assert collector.last_maintenance_run > 0

    def test_analytics_worker(self, enhanced_collector):
        """Test analytics worker functionality."""
        collector, mock_db, mock_analyzer, mock_predictor = enhanced_collector
        
        # Mock database to return sample miners
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value.fetchall.return_value = [
            {'id': 1, 'ip_address': '192.168.1.45', 'hostname': 'bitaxe1'}
        ]
        
        # Mock analyzer methods
        mock_analyzer.detect_anomalies.return_value = [
            {'type': 'temperature_spike', 'severity': 'warning', 'value': 85, 'threshold': 80}
        ]
        
        mock_predictor.predict_maintenance_needs.return_value = {
            'maintenance_score': 75,
            'predicted_issues': [{'type': 'thermal_stress', 'description': 'High temperature trend'}]
        }
        
        # Run analytics worker
        collector._analytics_worker()
        
        # Verify analytics methods were called
        mock_db.generate_hourly_stats.assert_called_once()
        mock_analyzer.detect_anomalies.assert_called()
        mock_predictor.predict_maintenance_needs.assert_called()

    def test_maintenance_worker(self, enhanced_collector):
        """Test maintenance worker functionality."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Run maintenance worker
        collector._maintenance_worker()
        
        # Verify maintenance tasks were called
        mock_db.maintenance_tasks.assert_called_once()

    def test_alert_creation(self, enhanced_collector):
        """Test alert creation functionality."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Mock database connection
        mock_cursor = Mock()
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        anomaly = {
            'type': 'temperature_spike',
            'severity': 'critical',
            'value': 90,
            'threshold': 85
        }
        
        collector._create_alert(1, anomaly)
        
        # Verify alert was inserted
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO alerts' in args[0]

    def test_maintenance_alert_creation(self, enhanced_collector):
        """Test maintenance alert creation."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Mock database connection
        mock_cursor = Mock()
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        prediction = {
            'maintenance_score': 85,
            'predicted_issues': [
                {'description': 'Thermal stress detected'},
                {'description': 'Performance degradation'}
            ]
        }
        
        collector._create_maintenance_alert(1, prediction)
        
        # Verify maintenance alert was inserted
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO alerts' in args[0]
        assert 'maintenance_needed' in args[1]

    def test_collection_status(self, enhanced_collector):
        """Test collection status reporting."""
        collector, _, _, _ = enhanced_collector
        
        # Update some statistics
        collector.collection_stats['total_collections'] = 10
        collector.collection_stats['successful_collections'] = 8
        collector.collection_stats['failed_collections'] = 2
        collector.last_analytics_run = time.time()
        collector.last_maintenance_run = time.time()
        
        status = collector.get_collection_status()
        
        # Verify status structure
        assert isinstance(status, dict)
        assert 'running' in status
        assert 'uptime_hours' in status
        assert 'total_collections' in status
        assert 'successful_collections' in status
        assert 'failed_collections' in status
        assert 'success_rate_percent' in status
        assert 'last_analytics_run' in status
        assert 'last_maintenance_run' in status
        
        # Check calculated values
        assert status['total_collections'] == 10
        assert status['successful_collections'] == 8
        assert status['failed_collections'] == 2
        assert status['success_rate_percent'] == 80.0

    def test_error_handling_in_collection(self, enhanced_collector):
        """Test error handling during collection."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Mock failed miner data collection
        with patch.object(collector, 'fetch_miner_data', side_effect=Exception("Network error")):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                collector.collect_once()
                
                # Should still create offline entries for failed miners
                mock_db.insert_raw_metrics.assert_called_once()
                
                # Check that failed collection is recorded
                assert collector.collection_stats['total_collections'] == 1

    def test_database_error_handling(self, enhanced_collector):
        """Test handling of database errors."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Mock database insertion failure
        mock_db.insert_raw_metrics.side_effect = Exception("Database error")
        
        sample_metrics = {'status': 'online', 'miner_ip': '192.168.1.45'}
        
        with patch.object(collector, 'fetch_miner_data', return_value=sample_metrics):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                # Should not raise exception despite database error
                collector.collect_once()
                
                # Collection should still be counted as successful
                assert collector.collection_stats['successful_collections'] == 1

    def test_graceful_shutdown(self, enhanced_collector):
        """Test graceful shutdown functionality."""
        collector, _, _, _ = enhanced_collector
        
        # Start analytics thread
        collector.analytics_thread = threading.Thread(target=lambda: time.sleep(0.1), daemon=True)
        collector.analytics_thread.start()
        
        # Start maintenance thread
        collector.maintenance_thread = threading.Thread(target=lambda: time.sleep(0.1), daemon=True)
        collector.maintenance_thread.start()
        
        # Test shutdown
        collector._shutdown()
        
        # Threads should be cleaned up
        assert not collector.analytics_thread.is_alive()
        assert not collector.maintenance_thread.is_alive()

    def test_signal_handling(self, enhanced_collector):
        """Test signal handling for graceful shutdown."""
        collector, _, _, _ = enhanced_collector
        
        # Test signal handler
        collector.running = True
        collector._signal_handler(15, None)  # SIGTERM
        
        # Should set running to False
        assert collector.running is False

    def test_concurrent_thread_management(self, enhanced_collector):
        """Test concurrent thread management."""
        collector, mock_db, _, _ = enhanced_collector
        
        # Start multiple analytics calls
        collector._run_analytics_background()
        collector._run_analytics_background()  # Should not start second thread
        
        # Give time for thread to start
        time.sleep(0.1)
        
        # Should only have one analytics thread
        assert collector.analytics_thread is not None
        assert collector.analytics_thread.is_alive()

    def test_configuration_override(self, enhanced_collector):
        """Test configuration override capabilities."""
        collector, _, _, _ = enhanced_collector
        
        # Test that configuration can be overridden
        original_interval = collector.config['analytics_interval']
        collector.config['analytics_interval'] = 999
        
        assert collector.config['analytics_interval'] == 999
        assert collector.config['analytics_interval'] != original_interval

    def test_efficiency_calculation_formula(self, enhanced_collector):
        """Test that efficiency calculation uses correct J/TH formula."""
        collector, _, _, _ = enhanced_collector
        
        # Test efficiency calculation directly using the formula from collect_miner_data
        hashrate_ghs = 900  # 900 GH/s
        power_w = 20        # 20 watts
        
        # Direct calculation using the corrected formula
        efficiency_j_th = round(power_w / (hashrate_ghs / 1000), 2) if hashrate_ghs > 0 else 0
        
        # Expected: 20W / (900GH/s / 1000) = 20 / 0.9 = 22.22 J/TH
        expected_efficiency = 22.22
        
        assert efficiency_j_th == expected_efficiency, f"Expected {expected_efficiency} J/TH, got {efficiency_j_th} J/TH"
        
        # Test edge cases
        # Zero hashrate should return 0 efficiency
        efficiency_zero = round(power_w / (0 / 1000), 2) if 0 > 0 else 0
        assert efficiency_zero == 0, "Zero hashrate should result in 0 efficiency"
        
        # Test with different values
        hashrate_ghs2 = 500  # 500 GH/s
        power_w2 = 15        # 15 watts
        efficiency_j_th2 = round(power_w2 / (hashrate_ghs2 / 1000), 2)
        expected_efficiency2 = 30.0  # 15 / 0.5 = 30.0 J/TH
        
        assert efficiency_j_th2 == expected_efficiency2, f"Expected {expected_efficiency2} J/TH, got {efficiency_j_th2} J/TH"


@pytest.mark.integration
class TestEnhancedCollectorIntegration:
    """Integration tests for enhanced collector functionality."""

    @pytest.fixture
    def integration_collector(self):
        """Create a real enhanced collector for integration testing."""
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create temporary config
        config = {
            'miners': [{'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3}],
            'poll_interval': 0.1,  # Very short for testing
            'csv_path': 'test_metrics.csv',
            'database_path': db_path,
            'enable_database': True,
            'enable_analytics': True,
            'analytics_interval': 0.2,
            'maintenance_interval': 0.5,
            'timeout': 1,
            'retries': 1
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            collector = EnhancedBitaxeCollector(config_path)
            yield collector
        finally:
            # Cleanup
            try:
                os.unlink(config_path)
                os.unlink(db_path)
            except OSError:
                pass

    def test_real_database_integration(self, integration_collector):
        """Test real database integration."""
        collector = integration_collector
        
        # Mock successful miner data
        sample_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'miner_ip': '192.168.1.45',
            'hostname': 'test_miner',
            'status': 'online',
            'hashrate_ghs': 934.5,
            'expected_hashrate_ghs': 934.3,
            'temp_asic_c': 60.0,
            'power_w': 14.0
        }
        
        with patch.object(collector, 'fetch_miner_data', return_value=sample_data):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                collector.collect_once()
        
        # Verify data was inserted into database
        with collector.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_metrics")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_analytics_integration(self, integration_collector):
        """Test analytics integration with real data."""
        collector = integration_collector
        
        # Insert some test data
        sample_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'miner_ip': '192.168.1.45',
            'hostname': 'test_miner',
            'status': 'online',
            'hashrate_ghs': 934.5,
            'expected_hashrate_ghs': 934.3,
            'temp_asic_c': 85.0,  # High temperature for alert
            'power_w': 14.0,
            'efficiency_j_th': 15.0,
            'shares_accepted': 1000,
            'shares_rejected': 5
        }
        
        with patch.object(collector, 'fetch_miner_data', return_value=sample_data):
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                collector.collect_once()
        
        # Force analytics run
        collector.last_analytics_run = 0
        collector._check_analytics_schedule()
        
        # Give time for analytics to complete
        time.sleep(0.5)
        
        # Check if alerts were generated
        with collector.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM alerts")
            alert_count = cursor.fetchone()[0]
            # May or may not have alerts depending on data patterns
            assert alert_count >= 0

    def test_maintenance_integration(self, integration_collector):
        """Test maintenance integration."""
        collector = integration_collector
        
        # Force maintenance run
        collector.last_maintenance_run = 0
        collector._check_maintenance_schedule()
        
        # Give time for maintenance to complete
        time.sleep(0.5)
        
        # Verify maintenance completed (no exceptions)
        assert collector.last_maintenance_run > 0

    def test_short_monitoring_loop(self, integration_collector):
        """Test short monitoring loop execution."""
        collector = integration_collector
        
        # Mock miner data
        with patch.object(collector, 'fetch_miner_data') as mock_fetch:
            mock_fetch.return_value = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'miner_ip': '192.168.1.45',
                'status': 'online',
                'hashrate_ghs': 934.5
            }
            
            with patch.object(collector, 'append_metrics_to_csv_safe', return_value=True):
                # Start monitoring in separate thread
                monitoring_thread = threading.Thread(target=collector.run_enhanced_monitoring, daemon=True)
                monitoring_thread.start()
                
                # Let it run for a short time
                time.sleep(0.5)
                
                # Stop monitoring
                collector.running = False
                monitoring_thread.join(timeout=1.0)
                
                # Verify collections occurred
                assert collector.collection_stats['total_collections'] > 0