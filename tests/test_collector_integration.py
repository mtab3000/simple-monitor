"""Integration tests for the simplified collector system."""

import pytest
import tempfile
import os
import sys
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_collector import EnhancedBitaxeCollector


class TestCollectorIntegration:
    """Test suite for the simplified collector system."""

    @pytest.fixture
    def test_config(self):
        """Create a test configuration."""
        return {
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3},
                {'ip': '192.168.1.46', 'expected_hashrate_ghs': 944.5}
            ],
            'poll_interval': 30,
            'csv_path': 'metrics.csv',
            'timeout': 10,
            'retries': 3,
            'retry_delay': 1,
            'database_path': 'test_db.db'
        }

    @pytest.fixture
    def temp_config_file(self, test_config):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        yield config_path
        try:
            os.unlink(config_path)
        except OSError:
            pass

    def test_collector_initialization(self, temp_config_file):
        """Test collector initialization with minimal setup."""
        collector = EnhancedBitaxeCollector(temp_config_file)
        
        # Basic checks
        assert collector.config is not None
        assert len(collector.config['miners']) == 2
        assert collector.config['poll_interval'] == 30
        assert hasattr(collector, 'db')
        assert hasattr(collector, 'session')

    def test_efficiency_calculation_correct(self):
        """Test that efficiency calculation is correct."""
        # Test the corrected efficiency formula
        test_cases = [
            (900, 20, 22.22),   # 900 GH/s, 20W -> 22.22 J/TH
            (500, 15, 30.0),    # 500 GH/s, 15W -> 30.0 J/TH
            (1000, 25, 25.0),   # 1000 GH/s, 25W -> 25.0 J/TH
            (0, 20, 0),         # 0 GH/s, 20W -> 0 J/TH (safety check)
        ]
        
        for hashrate_ghs, power_w, expected in test_cases:
            efficiency = round(power_w / (hashrate_ghs / 1000), 2) if hashrate_ghs > 0 else 0
            assert efficiency == expected, f"Hashrate {hashrate_ghs} GH/s, Power {power_w}W: expected {expected} J/TH, got {efficiency} J/TH"

    def test_miner_data_collection_structure(self, temp_config_file):
        """Test the structure of miner data collection."""
        with patch('requests.Session.get') as mock_get:
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'hashRate': 900,
                'power': 20,
                'boardTemp': 45,
                'chipTemp': 60,
                'vrTemp': 55,
                'sharesAccepted': 1000,
                'sharesRejected': 5,
                'uptimeSeconds': 3600,
                'voltage': 1.0,
                'frequency': 500
            }
            mock_get.return_value = mock_response
            
            collector = EnhancedBitaxeCollector(temp_config_file)
            miner_config = {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3}
            
            result = collector.collect_miner_data(miner_config)
            
            # Check required fields are present
            required_fields = [
                'timestamp', 'miner_ip', 'status', 'hashrate_ghs',
                'power_w', 'efficiency_j_th', 'temp_asic_c'
            ]
            for field in required_fields:
                assert field in result, f"Required field '{field}' missing from collection result"
            
            # Check efficiency calculation
            assert result['efficiency_j_th'] == 22.22  # 20W / (900GH/s / 1000)

    def test_config_loading_validation(self, temp_config_file):
        """Test configuration loading and validation."""
        collector = EnhancedBitaxeCollector(temp_config_file)
        
        # Check all required config keys
        required_keys = ['miners', 'poll_interval', 'timeout', 'retries']
        for key in required_keys:
            assert key in collector.config, f"Required config key '{key}' missing"
        
        # Check miners configuration
        assert isinstance(collector.config['miners'], list)
        assert len(collector.config['miners']) > 0
        
        for miner in collector.config['miners']:
            assert 'ip' in miner
            assert 'expected_hashrate_ghs' in miner

    def test_database_initialization(self, temp_config_file):
        """Test database initialization."""
        # Use a temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            # Update config to use temp database
            with open(temp_config_file, 'r') as f:
                config = yaml.safe_load(f)
            config['database_path'] = db_path
            
            with open(temp_config_file, 'w') as f:
                yaml.dump(config, f)
            
            collector = EnhancedBitaxeCollector(temp_config_file)
            
            # Check database exists and has tables
            assert os.path.exists(db_path)
            assert collector.db is not None
            
            # Try a simple database operation
            with collector.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                # Should have at least the raw_metrics table
                table_names = [table[0] for table in tables]
                assert 'raw_metrics' in table_names
                
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass

    def test_error_handling_network_failure(self, temp_config_file):
        """Test error handling for network failures."""
        with patch('requests.Session.get') as mock_get:
            # Mock network failure
            mock_get.side_effect = Exception("Network error")
            
            collector = EnhancedBitaxeCollector(temp_config_file)
            miner_config = {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3}
            
            result = collector.collect_miner_data(miner_config)
            
            # Should return failed connection record
            assert result['status'] == 'connection_failed'
            assert result['miner_ip'] == '192.168.1.45'
            assert result['efficiency_j_th'] == 0

    def test_module_imports(self):
        """Test that all required modules can be imported."""
        try:
            from enhanced_collector import EnhancedBitaxeCollector
            from database import BitaxeDatabase
            from analytics import PerformanceAnalyzer, PredictiveAnalyzer
            from utils import setup_logger
        except ImportError as e:
            pytest.fail(f"Failed to import required module: {e}")