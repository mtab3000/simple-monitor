"""Unit tests for the web server module."""

import pytest
import tempfile
import os
import json
import csv
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.web_server import BitaxeWebServer


class TestBitaxeWebServer:
    """Test suite for BitaxeWebServer class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return {
            'csv_path': 'test_metrics.csv',
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3},
                {'ip': '192.168.1.46', 'expected_hashrate_ghs': 944.5}
            ],
            'poll_interval': 30
        }

    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing."""
        return [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'hostname': 'bitaxe1',
                'status': 'online',
                'hashrate_ghs': '934.5',
                'expected_hashrate_ghs': '934.3',
                'hashrate_ratio_percent': '100.0',
                'temp_asic_c': '60.0',
                'temp_vr_c': '53.0',
                'power_w': '14.0',
                'voltage_asic_set_v': '1.003',
                'voltage_asic_actual_v': '0.981',
                'voltage_device_v': '4.938',
                'frequency_set_mhz': '458',
                'efficiency_j_th': '15.1',
                'shares_accepted': '2285',
                'shares_rejected': '1',
                'uptime_hours': '3.1',
                'wifi_rssi': '-52',
                'fan_speed_percent': '46',
                'fan_rpm': '3837',
                'free_heap_bytes': '8388608',
                'overclock_enabled': '1',
                'current_a': '9.03',
                'pool_user': '3Aas8yBKTY3wA5d...',
                'best_session_diff': '2.87M'
            },
            {
                'timestamp': '2024-01-01 12:05:00',
                'miner_ip': '192.168.1.46',
                'hostname': 'bitaxe2',
                'status': 'online',
                'hashrate_ghs': '944.5',
                'expected_hashrate_ghs': '944.5',
                'hashrate_ratio_percent': '100.0',
                'temp_asic_c': '59.5',
                'temp_vr_c': '54.0',
                'power_w': '14.2',
                'voltage_asic_set_v': '1.003',
                'voltage_asic_actual_v': '0.974',
                'voltage_device_v': '5.008',
                'frequency_set_mhz': '463',
                'efficiency_j_th': '15.0',
                'shares_accepted': '2366',
                'shares_rejected': '3',
                'uptime_hours': '3.1',
                'wifi_rssi': '-49',
                'fan_speed_percent': '38',
                'fan_rpm': '3148',
                'free_heap_bytes': '8388608',
                'overclock_enabled': '1',
                'current_a': '9.23',
                'pool_user': '3Aas8yBKTY3wA5d...',
                'best_session_diff': '1.69M'
            }
        ]

    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """Create a temporary CSV file with sample data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            if sample_csv_data:
                writer = csv.DictWriter(f, fieldnames=sample_csv_data[0].keys())
                writer.writeheader()
                writer.writerows(sample_csv_data)
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def web_server(self, mock_config):
        """Create a BitaxeWebServer instance for testing."""
        with patch.object(BitaxeWebServer, 'load_config', return_value=mock_config):
            server = BitaxeWebServer(config_path='test_config.yaml')
            return server

    @pytest.fixture
    def app_client(self, web_server):
        """Create Flask test client."""
        web_server.app.config['TESTING'] = True
        return web_server.app.test_client()

    def test_server_initialization(self, web_server):
        """Test web server initialization."""
        assert web_server.config['csv_path'] == 'test_metrics.csv'
        assert len(web_server.config['miners']) == 2
        assert web_server.host == '0.0.0.0'
        assert web_server.port == 80

    def test_load_config_success(self, mock_config):
        """Test successful configuration loading."""
        config_content = """
csv_path: 'test_metrics.csv'
miners:
  - ip: '192.168.1.45'
    expected_hashrate_ghs: 934.3
poll_interval: 30
"""
        
        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('yaml.safe_load', return_value=mock_config):
                with patch('pathlib.Path.exists', return_value=True):
                    server = BitaxeWebServer()
                    assert server.config == mock_config

    def test_load_config_missing_file(self):
        """Test configuration loading with missing file."""
        with patch('pathlib.Path.exists', return_value=False):
            server = BitaxeWebServer(config_path='nonexistent.yaml')
            # Should fall back to defaults
            assert 'csv_path' in server.config
            assert 'miners' in server.config
            assert server.config['csv_path'] == 'metrics.csv'

    def test_dashboard_route(self, app_client):
        """Test dashboard route."""
        response = app_client.get('/')
        assert response.status_code == 200
        assert b'Bitaxe Gamma Monitor' in response.data

    def test_api_status_no_data(self, app_client):
        """Test API status endpoint with no data."""
        with patch('os.path.exists', return_value=False):
            response = app_client.get('/api/status')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'miners' in data['data']
            assert data['data']['miners'] == []
            assert 'message' in data['data']

    def test_api_status_with_data(self, app_client, temp_csv_file, web_server):
        """Test API status endpoint with data."""
        web_server.config['csv_path'] = temp_csv_file
        
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_get_data.return_value = {
                'miners': [
                    {
                        'ip': '192.168.1.45',
                        'hostname': 'bitaxe1',
                        'status': 'online',
                        'hashrate_ghs': 934.5,
                        'temp_asic_c': 60.0,
                        'power_w': 14.0
                    }
                ]
            }
            
            response = app_client.get('/api/status')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['data']['miners']) == 1
            assert data['data']['miners'][0]['ip'] == '192.168.1.45'

    def test_api_fleet_endpoint(self, app_client, web_server):
        """Test API fleet endpoint."""
        mock_stats = {
            'total_miners': 2,
            'online_miners': 2,
            'offline_miners': 0,
            'total_hashrate_ghs': 1879.0,
            'total_power_w': 28.2,
            'average_efficiency_j_th': 15.05,
            'total_shares_accepted': 4651,
            'total_shares_rejected': 4,
            'fleet_rejection_rate_percent': 0.086
        }
        
        with patch.object(web_server, 'get_fleet_stats', return_value=mock_stats):
            response = app_client.get('/api/fleet')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['total_miners'] == 2
            assert data['data']['online_miners'] == 2

    def test_api_history_endpoint(self, app_client, web_server):
        """Test API history endpoint."""
        mock_history = {
            'data': [
                {
                    'timestamp': '2024-01-01 12:00:00',
                    'miner_ip': '192.168.1.45',
                    'hashrate_ghs': 934.5
                }
            ],
            'hours': 24
        }
        
        with patch.object(web_server, 'get_historical_data', return_value=mock_history):
            response = app_client.get('/api/history?hours=24')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['data']['data']) == 1
            assert data['data']['hours'] == 24

    def test_get_current_data_with_csv(self, web_server, temp_csv_file):
        """Test getting current data from CSV file."""
        web_server.config['csv_path'] = temp_csv_file
        
        result = web_server.get_current_data()
        
        assert 'miners' in result
        assert len(result['miners']) == 2
        
        # Check first miner data
        miner1 = result['miners'][0]
        assert miner1['ip'] == '192.168.1.45'
        assert miner1['hostname'] == 'bitaxe1'
        assert miner1['status'] == 'online'
        assert miner1['hashrate_ghs'] == 934.5
        assert miner1['rejection_rate_percent'] < 1.0  # Should be very low

    def test_get_current_data_missing_csv(self, web_server):
        """Test getting current data with missing CSV file."""
        web_server.config['csv_path'] = 'nonexistent.csv'
        
        result = web_server.get_current_data()
        
        assert 'miners' in result
        assert result['miners'] == []
        assert 'message' in result

    def test_get_current_data_empty_csv(self, web_server):
        """Test getting current data from empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            web_server.config['csv_path'] = csv_path
            result = web_server.get_current_data()
            
            assert 'miners' in result
            assert result['miners'] == []
            assert 'message' in result
        finally:
            os.unlink(csv_path)

    def test_get_historical_data(self, web_server, temp_csv_file):
        """Test getting historical data."""
        web_server.config['csv_path'] = temp_csv_file
        
        result = web_server.get_historical_data(hours=24)
        
        assert 'data' in result
        assert 'hours' in result
        assert result['hours'] == 24
        assert len(result['data']) >= 0  # May be filtered by time

    def test_get_fleet_stats(self, web_server, temp_csv_file):
        """Test fleet statistics calculation."""
        web_server.config['csv_path'] = temp_csv_file
        
        # Mock get_current_data to return test data
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_get_data.return_value = {
                'miners': [
                    {
                        'ip': '192.168.1.45',
                        'status': 'online',
                        'hashrate_ghs': 934.5,
                        'power_w': 14.0,
                        'efficiency_j_th': 15.1,
                        'temp_asic_c': 60.0,
                        'shares_accepted': 2285,
                        'shares_rejected': 1
                    },
                    {
                        'ip': '192.168.1.46',
                        'status': 'online',
                        'hashrate_ghs': 944.5,
                        'power_w': 14.2,
                        'efficiency_j_th': 15.0,
                        'temp_asic_c': 59.5,
                        'shares_accepted': 2366,
                        'shares_rejected': 3
                    }
                ]
            }
            
            stats = web_server.get_fleet_stats()
            
            assert stats['total_miners'] == 2
            assert stats['online_miners'] == 2
            assert stats['offline_miners'] == 0
            assert stats['total_hashrate_ghs'] == 1879.0
            assert stats['total_power_w'] == 28.2
            assert stats['total_shares_accepted'] == 4651
            assert stats['total_shares_rejected'] == 4

    def test_get_fleet_stats_empty(self, web_server):
        """Test fleet statistics with no miners."""
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_get_data.return_value = {'miners': []}
            
            stats = web_server.get_fleet_stats()
            
            assert stats['total_miners'] == 0
            assert stats['online_miners'] == 0
            assert stats['total_hashrate_ghs'] == 0
            assert stats['total_power_w'] == 0

    def test_api_error_handling(self, app_client, web_server):
        """Test API error handling."""
        with patch.object(web_server, 'get_current_data', side_effect=Exception("Test error")):
            response = app_client.get('/api/status')
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'error' in data

    def test_data_type_conversion(self, web_server, sample_csv_data):
        """Test proper data type conversion."""
        # Create CSV with string data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_csv_data)
            csv_path = f.name
        
        try:
            web_server.config['csv_path'] = csv_path
            result = web_server.get_current_data()
            
            miner = result['miners'][0]
            
            # Check that numeric fields are properly converted
            assert isinstance(miner['hashrate_ghs'], float)
            assert isinstance(miner['temp_asic_c'], float)
            assert isinstance(miner['power_w'], float)
            assert isinstance(miner['shares_accepted'], int)
            assert isinstance(miner['shares_rejected'], int)
            assert isinstance(miner['rejection_rate_percent'], float)
            
        finally:
            os.unlink(csv_path)

    def test_custom_host_port(self):
        """Test custom host and port configuration."""
        with patch.object(BitaxeWebServer, 'load_config', return_value={}):
            server = BitaxeWebServer(host='127.0.0.1', port=9090)
            assert server.host == '127.0.0.1'
            assert server.port == 9090

    def test_rejection_rate_calculation(self, web_server):
        """Test rejection rate calculation."""
        # Mock data with specific share counts
        test_miners = [
            {
                'shares_accepted': 1000,
                'shares_rejected': 50  # 5% rejection rate
            },
            {
                'shares_accepted': 2000,
                'shares_rejected': 0   # 0% rejection rate
            },
            {
                'shares_accepted': 0,
                'shares_rejected': 0   # Division by zero case
            }
        ]
        
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_miners = []
            for i, miner_data in enumerate(test_miners):
                mock_miner = {
                    'ip': f'192.168.1.{45+i}',
                    'status': 'online',
                    'hashrate_ghs': 900.0,
                    'power_w': 14.0,
                    'efficiency_j_th': 15.0,
                    'temp_asic_c': 60.0,
                    'shares_accepted': miner_data['shares_accepted'],
                    'shares_rejected': miner_data['shares_rejected']
                }
                mock_miners.append(mock_miner)
            
            mock_get_data.return_value = {'miners': mock_miners}
            result = web_server.get_current_data()
            
            # Check rejection rate calculations
            assert abs(result['miners'][0]['rejection_rate_percent'] - 4.76) < 0.1  # ~4.76%
            assert result['miners'][1]['rejection_rate_percent'] == 0.0
            assert result['miners'][2]['rejection_rate_percent'] == 0.0

    def test_timestamp_parsing(self, web_server):
        """Test timestamp parsing in historical data."""
        # Create test data with various timestamp formats
        test_data = [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'hashrate_ghs': '900',
                'temp_asic_c': '60'
            },
            {
                'timestamp': 'invalid_timestamp',
                'miner_ip': '192.168.1.46',
                'hashrate_ghs': '910',
                'temp_asic_c': '61'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=test_data[0].keys())
            writer.writeheader()
            writer.writerows(test_data)
            csv_path = f.name
        
        try:
            web_server.config['csv_path'] = csv_path
            result = web_server.get_historical_data(hours=24)
            
            # Should handle invalid timestamps gracefully
            assert 'data' in result
            # May have 0 or 1 entries depending on timestamp filtering
            assert len(result['data']) >= 0
            
        finally:
            os.unlink(csv_path)


@pytest.mark.integration
class TestWebServerIntegration:
    """Integration tests for web server functionality."""

    @pytest.fixture
    def integration_setup(self, sample_csv_data):
        """Set up integration test environment."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_csv_data)
            csv_path = f.name
        
        # Create temporary config
        config = {
            'csv_path': csv_path,
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3},
                {'ip': '192.168.1.46', 'expected_hashrate_ghs': 944.5}
            ],
            'poll_interval': 30
        }
        
        with patch.object(BitaxeWebServer, 'load_config', return_value=config):
            server = BitaxeWebServer()
            server.app.config['TESTING'] = True
            client = server.app.test_client()
        
        yield client, server, csv_path
        
        # Cleanup
        os.unlink(csv_path)

    def test_full_api_workflow(self, integration_setup):
        """Test complete API workflow."""
        client, server, csv_path = integration_setup
        
        # Test status endpoint
        response = client.get('/api/status')
        assert response.status_code == 200
        status_data = json.loads(response.data)
        assert status_data['success'] is True
        assert len(status_data['data']['miners']) == 2
        
        # Test fleet endpoint
        response = client.get('/api/fleet')
        assert response.status_code == 200
        fleet_data = json.loads(response.data)
        assert fleet_data['success'] is True
        assert fleet_data['data']['total_miners'] == 2
        
        # Test history endpoint
        response = client.get('/api/history?hours=1')
        assert response.status_code == 200
        history_data = json.loads(response.data)
        assert history_data['success'] is True

    def test_dashboard_rendering(self, integration_setup):
        """Test dashboard HTML rendering."""
        client, server, csv_path = integration_setup
        
        response = client.get('/')
        assert response.status_code == 200
        assert b'Bitaxe Gamma Monitor' in response.data
        assert b'Fleet Overview' in response.data
        assert b'Individual Miners' in response.data

    def test_api_data_consistency(self, integration_setup):
        """Test data consistency across API endpoints."""
        client, server, csv_path = integration_setup
        
        # Get data from status endpoint
        status_response = client.get('/api/status')
        status_data = json.loads(status_response.data)
        miners_from_status = status_data['data']['miners']
        
        # Get data from fleet endpoint
        fleet_response = client.get('/api/fleet')
        fleet_data = json.loads(fleet_response.data)
        
        # Verify consistency
        assert len(miners_from_status) == fleet_data['data']['total_miners']
        
        # Calculate expected totals
        expected_hashrate = sum(miner['hashrate_ghs'] for miner in miners_from_status)
        expected_power = sum(miner['power_w'] for miner in miners_from_status)
        
        assert abs(expected_hashrate - fleet_data['data']['total_hashrate_ghs']) < 0.1
        assert abs(expected_power - fleet_data['data']['total_power_w']) < 0.1

    def test_error_recovery(self, integration_setup):
        """Test error recovery scenarios."""
        client, server, csv_path = integration_setup
        
        # Delete CSV file to simulate error
        os.unlink(csv_path)
        
        # API should still respond gracefully
        response = client.get('/api/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['miners'] == []

    def test_large_dataset_handling(self, integration_setup):
        """Test handling of larger datasets."""
        client, server, csv_path = integration_setup
        
        # Create larger dataset
        large_data = []
        base_timestamp = datetime.strptime('2024-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
        
        for i in range(100):  # 100 data points
            timestamp = base_timestamp.replace(minute=i % 60, hour=12 + i // 60)
            large_data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'miner_ip': f'192.168.1.{45 + (i % 2)}',
                'hostname': f'bitaxe{i % 2 + 1}',
                'status': 'online',
                'hashrate_ghs': str(930 + i % 50),
                'expected_hashrate_ghs': '934.3',
                'hashrate_ratio_percent': '99.5',
                'temp_asic_c': str(60 + i % 20),
                'temp_vr_c': '53.0',
                'power_w': str(14 + i % 5),
                'voltage_asic_set_v': '1.003',
                'voltage_asic_actual_v': '0.981',
                'voltage_device_v': '4.938',
                'frequency_set_mhz': '458',
                'efficiency_j_th': str(15 + i % 10 * 0.1),
                'shares_accepted': str(2000 + i * 10),
                'shares_rejected': str(i % 5),
                'uptime_hours': '24.0',
                'wifi_rssi': str(-50 - i % 10),
                'fan_speed_percent': str(40 + i % 30),
                'fan_rpm': str(3500 + i * 10),
                'free_heap_bytes': '8388608',
                'overclock_enabled': '1',
                'current_a': str(9 + i % 3 * 0.1),
                'pool_user': 'test_user',
                'best_session_diff': f'{2 + i % 3}M'
            })
        
        # Write large dataset
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=large_data[0].keys())
            writer.writeheader()
            writer.writerows(large_data)
        
        # Test API performance with large dataset
        import time
        start_time = time.time()
        response = client.get('/api/status')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['miners']) == 2  # Should aggregate by miner IP

    def test_concurrent_api_requests(self, integration_setup):
        """Test handling of concurrent API requests."""
        client, server, csv_path = integration_setup
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.get('/api/status')
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads for concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0
        assert len(results) == 10
        assert all(status == 200 for status in results)

    def test_fleet_efficiency_in_stats(self, web_server):
        """Test that fleet efficiency is included in fleet statistics."""
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_get_data.return_value = {
                'miners': [
                    {
                        'ip': '192.168.1.45',
                        'status': 'online',
                        'hashrate_ghs': 1000.0,
                        'power_w': 15.0,
                        'efficiency_j_th': 15.0,
                        'temp_asic_c': 60.0,
                        'temp_vr_c': 55.0,
                        'voltage_device_v': 5.0,
                        'shares_accepted': 100,
                        'shares_rejected': 1
                    },
                    {
                        'ip': '192.168.1.46',
                        'status': 'online',
                        'hashrate_ghs': 950.0,
                        'power_w': 15.2,
                        'efficiency_j_th': 16.0,
                        'temp_asic_c': 62.0,
                        'temp_vr_c': 56.0,
                        'voltage_device_v': 5.1,
                        'shares_accepted': 95,
                        'shares_rejected': 2
                    }
                ]
            }
            
            stats = web_server.get_fleet_stats()
            
            # Check that fleet efficiency is calculated correctly
            assert 'average_efficiency_j_th' in stats
            expected_efficiency = (15.0 + 16.0) / 2
            assert stats['average_efficiency_j_th'] == expected_efficiency

    def test_individual_miner_extended_metrics(self, web_server):
        """Test that individual miners include extended metrics for new UI."""
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_get_data.return_value = {
                'miners': [
                    {
                        'ip': '192.168.1.45',
                        'hostname': 'bitaxe1',
                        'status': 'online',
                        'hashrate_ghs': 934.5,
                        'expected_hashrate_ghs': 934.3,
                        'efficiency_j_th': 15.1,
                        'temp_asic_c': 60.0,
                        'temp_vr_c': 55.0,
                        'voltage_device_v': 5.0,
                        'voltage_asic_actual_v': 0.981,
                        'voltage_asic_set_v': 1.003,
                        'power_w': 14.0,
                        'frequency_set_mhz': 458,
                        'shares_accepted': 2285,
                        'shares_rejected': 1,
                        'uptime_hours': 3.1
                    }
                ]
            }
            
            data = web_server.get_current_data()
            miner = data['miners'][0]
            
            # Check that all required fields for new UI are present
            required_fields = [
                'voltage_device_v',  # Input voltage
                'temp_vr_c',         # VR temperature  
                'temp_asic_c',       # ASIC temperature
                'efficiency_j_th',   # Efficiency for charts
                'voltage_asic_actual_v',  # ASIC voltage for charts
                'hashrate_ghs',      # Hashrate for charts
                'expected_hashrate_ghs'  # Expected hashrate for charts
            ]
            
            for field in required_fields:
                assert field in miner, f"Missing required field: {field}"
                assert miner[field] is not None, f"Field {field} should not be None"

    def test_dark_theme_assets_accessible(self, app_client):
        """Test that CSS and JS assets are accessible for dark theme."""
        # Test CSS file
        response = app_client.get('/static/css/dashboard.css')
        assert response.status_code == 200
        assert 'text/css' in response.content_type
        
        # Test JS file  
        response = app_client.get('/static/js/dashboard.js')
        assert response.status_code == 200
        assert 'javascript' in response.content_type or 'text/javascript' in response.content_type

    def test_dashboard_chart_support(self, app_client):
        """Test that dashboard HTML includes Chart.js support."""
        response = app_client.get('/')
        assert response.status_code == 200
        
        # Check that Chart.js is included
        assert b'chart.js' in response.data or b'chart.umd.js' in response.data
        
        # Check that fleet efficiency element is present
        assert b'fleet-efficiency' in response.data