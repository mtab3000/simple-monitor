"""Unit tests for the BitaxeCollector class."""

import pytest
import tempfile
import json
import csv
import os
import requests
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from collector import BitaxeCollector


class TestBitaxeCollector:
    """Test suite for BitaxeCollector class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return {
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3},
                {'ip': '192.168.1.46', 'expected_hashrate_ghs': 944.5}
            ],
            'poll_interval': 30,
            'csv_path': 'test_metrics.csv',
            'timeout': 10,
            'retries': 3,
            'retry_delay': 1,
            'backup_frequency': 100,
            'validate_csv': True
        }

    @pytest.fixture
    def mock_api_response(self):
        """Create a mock API response from Bitaxe."""
        return {
            'hostname': 'bitaxe1',
            'hashRate': 934.5,  # 934.5 GH/s
            'temp': 60.0,
            'vrTemp': 53.0,
            'power': 14.0,
            'voltage': 0.981,
            'asicVoltage': 1.003,
            'frequency': 458.0,
            'shares': {'accepted': 2285, 'rejected': 1},
            'uptimeSeconds': 11160,
            'freeHeap': 8388608,
            'wifiStatus': {'rssi': -52},
            'fanSpeed': 46,
            'fanRpm': 3837,
            'boardTemp': 45.0,
            'poolUser': '3Aas8yBKTY3wA5d...',
            'bestDiff': '2.87M'
        }

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def collector(self, mock_config, temp_dir):
        """Create a BitaxeCollector instance for testing."""
        config_path = os.path.join(temp_dir, 'config.yaml')
        
        with patch('collector.BitaxeCollector.load_config') as mock_load:
            mock_load.return_value = mock_config
            with patch.object(Path, 'parent', new_callable=lambda: Path(temp_dir)):
                collector = BitaxeCollector(config_path)
                collector.csv_path = os.path.join(temp_dir, 'test_metrics.csv')
                collector.hostname_cache_path = Path(temp_dir) / 'hostname_cache.json'
                collector.backup_dir = Path(temp_dir) / 'backups'
                collector.backup_dir.mkdir(exist_ok=True)
                return collector

    def test_init(self, collector, mock_config):
        """Test collector initialization."""
        assert collector.config == mock_config
        assert collector.config['poll_interval'] == 30
        assert collector.config['timeout'] == 10

    def test_load_config_success(self, temp_dir):
        """Test successful configuration loading."""
        config_data = {
            'miners': [{'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3}],
            'poll_interval': 30,
            'csv_path': 'metrics.csv',
            'timeout': 10
        }
        config_path = os.path.join(temp_dir, 'config.yaml')
        
        with patch('builtins.open', mock_open(read_data='miners:\n  - ip: "192.168.1.45"\n')):
            with patch('yaml.safe_load', return_value=config_data):
                collector = BitaxeCollector.__new__(BitaxeCollector)
                result = collector.load_config(config_path)
                
        assert result['miners'] == config_data['miners']
        assert result['timeout'] == 10
        assert result['retries'] == 3  # Default value

    def test_load_config_missing_fields(self, temp_dir):
        """Test configuration loading with missing required fields."""
        config_data = {'poll_interval': 30}  # Missing 'miners'
        config_path = os.path.join(temp_dir, 'config.yaml')
        
        with patch('builtins.open', mock_open()):
            with patch('yaml.safe_load', return_value=config_data):
                collector = BitaxeCollector.__new__(BitaxeCollector)
                with pytest.raises(SystemExit):
                    collector.load_config(config_path)

    def test_hostname_cache_operations(self, collector):
        """Test hostname caching functionality."""
        # Test saving and loading hostname cache
        test_cache = {'192.168.1.45': 'bitaxe1'}
        
        collector.hostname_cache = test_cache
        collector.save_hostname_cache()
        
        # Clear cache and reload
        collector.hostname_cache = {}
        loaded_cache = collector.load_hostname_cache()
        
        assert loaded_cache == test_cache

    def test_get_cached_hostname_with_valid_hostname(self, collector):
        """Test hostname caching with valid hostname."""
        miner_ip = '192.168.1.45'
        hostname = 'bitaxe1'
        
        result = collector.get_cached_hostname(miner_ip, hostname)
        
        assert result == hostname
        assert collector.hostname_cache[miner_ip] == hostname

    def test_get_cached_hostname_with_cached_value(self, collector):
        """Test hostname retrieval from cache when current is invalid."""
        miner_ip = '192.168.1.45'
        collector.hostname_cache[miner_ip] = 'bitaxe1'
        
        result = collector.get_cached_hostname(miner_ip, 'Unknown')
        
        assert result == 'bitaxe1*'  # Asterisk indicates cached value

    def test_get_cached_hostname_fallback(self, collector):
        """Test hostname fallback when no cache exists."""
        miner_ip = '192.168.1.45'
        
        result = collector.get_cached_hostname(miner_ip, 'Unknown')
        
        assert result == 'Miner-45'  # Fallback based on IP

    @patch('requests.Session.get')
    def test_fetch_miner_data_success(self, mock_get, collector, mock_api_response):
        """Test successful miner data fetching."""
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        miner_config = {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3}
        result = collector.get_miner_data(miner_config['ip'])
        
        assert result['status'] == 'online'
        assert result['miner_ip'] == '192.168.1.45'
        assert result['hashrate_ghs'] == 934.5
        assert result['temp_asic_c'] == 60.0

    @patch('requests.Session.get')
    def test_fetch_miner_data_timeout(self, mock_get, collector):
        """Test miner data fetching with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        miner_config = {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3}
        result = collector.get_miner_data(miner_config['ip'])
        
        assert result['status'] == 'timeout'
        assert result['miner_ip'] == '192.168.1.45'

    def test_determine_status_online(self, collector):
        """Test status determination for online miner."""
        data = {
            'hashRate': 934500000000,  # Raw API format
            'temp': 60.0,
            'power': 14.0,
            'sharesRejected': 1,
            'sharesAccepted': 2285,
            'wifiRSSI': -52,
            'wifiStatus': 'connected'
        }
        
        status = collector.determine_status(data, data['hashRate'] / 1000000000, data['temp'])
        assert status == 'online'

    def test_determine_status_no_hashrate(self, collector):
        """Test status determination for no hashrate."""
        data = {
            'hashRate': 0,
            'temp': 60.0,
            'power': 14.0,
            'sharesRejected': 1,
            'sharesAccepted': 2285,
            'wifiRSSI': -52,
            'wifiStatus': 'connected'
        }
        
        status = collector.determine_status(data, data['hashRate'], data['temp'])
        assert status == 'no_hashrate'

    def test_determine_status_overheating(self, collector):
        """Test status determination for overheating."""
        data = {
            'hashRate': 934500000000,
            'temp': 90.0,  # Overheating
            'power': 14.0,
            'sharesRejected': 1,
            'sharesAccepted': 2285,
            'wifiRSSI': -52,
            'wifiStatus': 'connected'
        }
        
        status = collector.determine_status(data, data['hashRate'] / 1000000000, data['temp'])
        assert status == 'overheating'

    def test_determine_status_high_rejection(self, collector):
        """Test status determination for high rejection rate."""
        data = {
            'hashRate': 934500000000,
            'temp': 60.0,
            'power': 14.0,
            'sharesRejected': 250,  # High rejection
            'sharesAccepted': 2000,
            'wifiRSSI': -52,
            'wifiStatus': 'connected'
        }
        
        status = collector.determine_status(data, data['hashRate'] / 1000000000, data['temp'])
        assert status == 'high_rejection'

    def test_csv_initialization(self, collector):
        """Test CSV file initialization."""
        collector.write_csv_header()
        
        assert os.path.exists(collector.csv_path)
        
        # Check headers
        with open(collector.csv_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert 'timestamp' in headers
            assert 'miner_ip' in headers
            assert 'hashrate_ghs' in headers

    def test_append_metrics_to_csv(self, collector):
        """Test appending metrics to CSV."""
        collector.write_csv_header()
        
        test_metrics = [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'status': 'online',
                'hashrate_ghs': 934.5,
                'temp_asic_c': 60.0,
                'power_w': 14.0,
                'hostname': 'bitaxe1'
            }
        ]
        
        result = collector.append_metrics_to_csv_safe(test_metrics)
        assert result is True
        
        # Verify data was written
        with open(collector.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['miner_ip'] == '192.168.1.45'

    def test_backup_creation(self, collector):
        """Test backup file creation."""
        collector.write_csv_header()
        
        # Add some data
        test_metrics = [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'status': 'online',
                'hashrate_ghs': 934.5
            }
        ]
        collector.append_metrics_to_csv_safe(test_metrics)
        
        # Create backup
        collector.backup_csv_file()
        
        # Check that a backup was created in the backup directory
        backups = list(collector.backup_dir.glob("metrics_backup_*.csv"))
        assert len(backups) > 0
        assert backups[0].exists()

    def test_validate_csv_structure_valid(self, collector):
        """Test CSV validation with valid file."""
        collector.write_csv_header()
        
        is_valid, message = collector.validate_csv_file(collector.csv_path)
        assert is_valid is True
        assert "File is valid" in message

    def test_validate_csv_structure_missing_file(self, collector):
        """Test CSV validation with missing file."""
        # Don't initialize CSV
        is_valid, message = collector.validate_csv_file(collector.csv_path)
        assert is_valid is True
        assert "File doesn't exist yet" in message


class TestCollectorIntegration:
    """Integration tests for the collector."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.mark.integration
    def test_full_collection_cycle(self, temp_dir):
        """Test a complete collection cycle."""
        config = {
            'miners': ['192.168.1.45'],
            'poll_interval': 1,
            'csv_path': os.path.join(temp_dir, 'metrics.csv'),
            'timeout': 5,
            'retries': 1,
            'retry_delay': 1
        }
        
        with patch('collector.BitaxeCollector.load_config', return_value=config):
            with patch.object(Path, 'parent', new_callable=lambda: Path(temp_dir)):
                collector = BitaxeCollector()
                collector.csv_path = config['csv_path']
                
                # Mock a successful API response
                mock_response = {
                    'hostname': 'bitaxe1',
                    'hashRate': 934500000000,
                    'temp': 60.0,
                    'vrTemp': 53.0,
                    'power': 14.0
                }
                
                with patch.object(collector, 'get_miner_data') as mock_fetch:
                    mock_fetch.return_value = {
                        'status': 'online',
                        'miner_ip': '192.168.1.45',
                        'hashrate_ghs': 934.5,
                        'temp_asic_c': 60.0,
                        'temp_vr_c': 53.0,
                        'power_w': 14.0,
                        'hostname': 'bitaxe1',
                        'timestamp': '2024-01-01 12:00:00'
                    }
                    
                    # Run one collection cycle
                    collector.write_csv_header()
                    all_metrics = collector.collect_all_miners()
                    collector.append_metrics_to_csv_safe(all_metrics)
                    
                    # Verify data was collected
                    assert os.path.exists(collector.csv_path)
                    with open(collector.csv_path, 'r') as f:
                        content = f.read()
                        assert '192.168.1.45' in content
                        assert 'online' in content


@pytest.mark.unit
class TestCollectorHelperFunctions:
    """Test helper functions and utilities."""

    def test_create_session(self):
        """Test HTTP session creation."""
        config = {'retries': 3, 'retry_delay': 1}
        
        with patch('collector.BitaxeCollector.load_config', return_value=config):
            collector = BitaxeCollector.__new__(BitaxeCollector)
            collector.config = config
            session = collector.create_session()
            
            assert session is not None
            # Verify retry configuration is applied
            assert hasattr(session, 'adapters')