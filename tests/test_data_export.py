"""Unit tests for the data export module."""

import pytest
import tempfile
import os
import csv
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data_export import DataExporter


class TestDataExporter:
    """Test suite for DataExporter class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test.db')
        
    def teardown_method(self):
        """Cleanup after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.data_export.BitaxeDatabase')
    def test_init(self, mock_db_class):
        """Test DataExporter initialization."""
        exporter = DataExporter(self.test_db_path)
        
        assert exporter.db_path == self.test_db_path
        mock_db_class.assert_called_once_with(self.test_db_path)
        assert exporter.db == mock_db_class.return_value
    
    def test_export_database_to_csv_success(self):
        """Test successful database export to CSV."""
        # Mock database connection and data
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Sample data that would come from database
        sample_data = [
            {
                'timestamp': '2023-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'hostname': 'bitaxe1',
                'status': 'online',
                'hashrate_ghs': 500.0,
                'expected_hashrate_ghs': 520.0,
                'hashrate_ratio_percent': 96.2,
                'efficiency_j_th': 0.025,
                'temp_asic_c': 65.0,
                'temp_vr_c': 62.0,
                'power_w': 12.5,
                'voltage_asic_set_v': 1.1,
                'voltage_asic_actual_v': 1.08,
                'voltage_device_v': 5.0,
                'frequency_set_mhz': 450,
                'current_a': 2.5,
                'shares_accepted': 1000,
                'shares_rejected': 5,
                'rejection_rate_percent': 0.5,
                'uptime_hours': 24.5,
                'wifi_rssi': -45,
                'fan_rpm': 3000,
                'connected_pool': 'stratum+tcp://pool.example.com:4444'
            }
        ]
        
        # Setup mocks
        mock_cursor.fetchall.return_value = [Mock(**data) for data in sample_data]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        # Create exporter with mocked database
        exporter = DataExporter(self.test_db_path)
        exporter.db = mock_db
        
        # Test export
        output_path = os.path.join(self.temp_dir, 'test_export.csv')
        result = exporter.export_database_to_csv(output_path)
        
        # Verify result
        assert result['success'] == True
        assert result['records_exported'] == 1
        assert result['output_path'] == output_path
        
        # Verify CSV file was created
        assert os.path.exists(output_path)
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['miner_ip'] == '192.168.1.45'
            assert rows[0]['hostname'] == 'bitaxe1'
            assert rows[0]['hashrate_ghs'] == '500.0'
    
    def test_export_database_to_csv_with_time_filter(self):
        """Test database export with time filter."""
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Setup mocks
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        # Create exporter with mocked database
        exporter = DataExporter(self.test_db_path)
        exporter.db = mock_db
        
        # Test export with time filter
        output_path = os.path.join(self.temp_dir, 'test_export.csv')
        result = exporter.export_database_to_csv(output_path, hours=24)
        
        # Verify the query was called with time filter
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args
        assert 'WHERE rm.timestamp >=' in call_args[0][0]
        assert len(call_args[0]) == 2  # Query and parameter
    
    def test_export_database_to_csv_no_data(self):
        """Test export when database has no data."""
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Setup mocks for empty result
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        # Create exporter with mocked database
        exporter = DataExporter(self.test_db_path)
        exporter.db = mock_db
        
        # Test export
        output_path = os.path.join(self.temp_dir, 'test_export.csv')
        result = exporter.export_database_to_csv(output_path)
        
        # Verify result
        assert result['success'] == False
        assert 'No data to export' in result['error']
    
    def test_export_database_to_csv_database_error(self):
        """Test export when database connection fails."""
        mock_db = Mock()
        mock_db.get_connection.side_effect = Exception("Database connection failed")
        
        # Create exporter with mocked database
        exporter = DataExporter(self.test_db_path)
        exporter.db = mock_db
        
        # Test export
        output_path = os.path.join(self.temp_dir, 'test_export.csv')
        result = exporter.export_database_to_csv(output_path)
        
        # Verify result
        assert result['success'] == False
        assert 'Database connection failed' in result['error']
    
    def test_export_database_to_csv_file_write_error(self):
        """Test export when file writing fails."""
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Sample data
        sample_data = [Mock(timestamp='2023-01-01 12:00:00', miner_ip='192.168.1.45')]
        mock_cursor.fetchall.return_value = sample_data
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_db.get_connection.return_value = mock_conn
        
        # Create exporter with mocked database
        exporter = DataExporter(self.test_db_path)
        exporter.db = mock_db
        
        # Test export to invalid path (should cause write error)
        invalid_path = '/invalid/path/test_export.csv'
        result = exporter.export_database_to_csv(invalid_path)
        
        # Verify result
        assert result['success'] == False
        assert 'error' in result


class TestDataExporterIntegration:
    """Integration tests for DataExporter."""
    
    @pytest.mark.integration
    def test_main_function_help(self):
        """Test the main function with help argument."""
        import subprocess
        import sys
        
        # Test help argument
        result = subprocess.run([
            sys.executable, '-m', 'src.data_export', '--help'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        assert result.returncode == 0
        assert 'Export database data to CSV format' in result.stdout
    
    @pytest.mark.integration  
    def test_main_function_with_nonexistent_db(self):
        """Test main function with non-existent database."""
        import subprocess
        import sys
        
        # Test with non-existent database
        result = subprocess.run([
            sys.executable, '-m', 'src.data_export', 
            '--db-path', '/tmp/nonexistent.db',
            '--output', '/tmp/test_output.csv'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        # Should fail with exit code 1
        assert result.returncode == 1
        assert 'Export failed' in result.stdout


@pytest.mark.unit
def test_data_exporter_imports():
    """Test that DataExporter can be imported without errors."""
    from src.data_export import DataExporter
    assert DataExporter is not None


@pytest.mark.unit
def test_main_function_exists():
    """Test that main function exists and is callable."""
    from src.data_export import main
    assert callable(main)