"""Tests for UI improvements and new functionality."""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.web_server import BitaxeWebServer


class TestUIImprovements:
    """Test suite for new UI improvements."""

    @pytest.fixture
    def mock_db_data(self):
        """Mock database data for testing."""
        return [
            {
                'ip_address': '192.168.1.45',
                'hostname': 'bitaxe1',
                'status': 'online',
                'hashrate_ghs': 934.5,
                'expected_hashrate_ghs': 934.3,
                'hashrate_ratio_percent': 100.0,
                'temp_asic_c': 60.0,
                'temp_vr_c': 55.0,
                'power_w': 14.0,
                'efficiency_j_th': 15.1,
                'uptime_hours': 3.1,
                'shares_accepted': 2285,
                'shares_rejected': 1,
                'rejection_rate_percent': 0.044,
                'wifi_rssi': -52,
                'timestamp': '2024-01-01 12:00:00',
                'voltage_asic_actual_v': 0.981,
                'voltage_asic_set_v': 1.003,
                'frequency_set_mhz': 458.0
            },
            {
                'ip_address': '192.168.1.46',
                'hostname': 'bitaxe2',
                'status': 'online',
                'hashrate_ghs': 944.5,
                'expected_hashrate_ghs': 944.5,
                'hashrate_ratio_percent': 100.0,
                'temp_asic_c': 59.5,
                'temp_vr_c': 54.0,
                'power_w': 14.2,
                'efficiency_j_th': 15.0,
                'uptime_hours': 3.1,
                'shares_accepted': 2366,
                'shares_rejected': 3,
                'rejection_rate_percent': 0.127,
                'wifi_rssi': -49,
                'timestamp': '2024-01-01 12:00:00',
                'voltage_asic_actual_v': 0.974,
                'voltage_asic_set_v': 1.003,
                'frequency_set_mhz': 463.0
            }
        ]

    @pytest.fixture
    def web_server(self):
        """Create a web server instance with mocked database."""
        with patch('src.web_server.BitaxeDatabase'):
            server = BitaxeWebServer()
            return server

    def test_fleet_stats_no_average_temp(self, web_server, mock_db_data):
        """Test that fleet stats no longer include average temperature."""
        # Mock the database query
        with patch.object(web_server, '_get_data_from_database') as mock_db:
            mock_db.return_value = {
                'miners': [
                    {
                        'ip': row['ip_address'],
                        'status': row['status'],
                        'hashrate_ghs': row['hashrate_ghs'],
                        'power_w': row['power_w'],
                        'efficiency_j_th': row['efficiency_j_th'],
                        'temp_asic_c': row['temp_asic_c'],
                        'shares_accepted': row['shares_accepted'],
                        'shares_rejected': row['shares_rejected']
                    } for row in mock_db_data
                ]
            }
            
            stats = web_server.get_fleet_stats()
            
            # Check that average_temp_c is NOT in the response
            assert 'average_temp_c' not in stats
            
            # Check that fleet efficiency IS in the response
            assert 'average_efficiency_j_th' in stats
            assert stats['average_efficiency_j_th'] == 15.05  # (15.1 + 15.0) / 2

    def test_individual_miner_required_fields(self, web_server, mock_db_data):
        """Test that individual miners have all required fields for new UI."""
        # Mock the database query
        with patch.object(web_server, '_get_data_from_database') as mock_db:
            miners_data = []
            for row in mock_db_data:
                miner_info = {
                    'ip': row['ip_address'],
                    'hostname': row['hostname'],
                    'status': row['status'],
                    'hashrate_ghs': row['hashrate_ghs'],
                    'expected_hashrate_ghs': row['expected_hashrate_ghs'],
                    'temp_asic_c': row['temp_asic_c'],
                    'temp_vr_c': row['temp_vr_c'],
                    'efficiency_j_th': row['efficiency_j_th'],
                    'voltage_asic_actual_v': row['voltage_asic_actual_v'],
                    'voltage_asic_set_v': row['voltage_asic_set_v'],
                    'power_w': row['power_w'],
                    'frequency_set_mhz': row['frequency_set_mhz'],
                    'shares_accepted': row['shares_accepted'],
                    'shares_rejected': row['shares_rejected'],
                    'uptime_hours': row['uptime_hours'],
                    'rejection_rate_percent': row['rejection_rate_percent']
                }
                miners_data.append(miner_info)
            
            mock_db.return_value = {'miners': miners_data}
            
            data = web_server.get_current_data()
            miners = data['miners']
            
            # Check that we have miners
            assert len(miners) == 2
            
            # Required fields for new UI improvements
            required_fields = [
                'temp_asic_c',           # ASIC temperature
                'temp_vr_c',             # VR temperature  
                'efficiency_j_th',       # Efficiency for charts
                'voltage_asic_actual_v', # ASIC voltage for charts
                'hashrate_ghs',          # Hashrate for charts
                'expected_hashrate_ghs'  # Expected hashrate for charts
            ]
            
            for miner in miners:
                for field in required_fields:
                    assert field in miner, f"Missing required field: {field}"
                    assert miner[field] is not None, f"Field {field} should not be None"

    def test_fleet_efficiency_calculation(self, web_server, mock_db_data):
        """Test that fleet efficiency is calculated correctly."""
        with patch.object(web_server, '_get_data_from_database') as mock_db:
            mock_db.return_value = {
                'miners': [
                    {
                        'ip': row['ip_address'],
                        'status': row['status'],
                        'hashrate_ghs': row['hashrate_ghs'],
                        'power_w': row['power_w'],
                        'efficiency_j_th': row['efficiency_j_th'],
                        'temp_asic_c': row['temp_asic_c'],
                        'shares_accepted': row['shares_accepted'],
                        'shares_rejected': row['shares_rejected']
                    } for row in mock_db_data
                ]
            }
            
            stats = web_server.get_fleet_stats()
            
            # Check fleet efficiency calculation
            expected_efficiency = (15.1 + 15.0) / 2  # Average of both miners
            assert stats['average_efficiency_j_th'] == expected_efficiency
            
            # Check other fleet stats
            assert stats['total_miners'] == 2
            assert stats['online_miners'] == 2
            assert stats['offline_miners'] == 0
            assert stats['total_hashrate_ghs'] == 1879.0  # 934.5 + 944.5
            assert stats['total_power_w'] == 28.2  # 14.0 + 14.2

    def test_dark_theme_variables(self):
        """Test that CSS contains dark theme color variables."""
        css_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'static', 'css', 'dashboard.css')
        
        if os.path.exists(css_path):
            with open(css_path, 'r') as f:
                css_content = f.read()
            
            # Check for dark blue primary color
            assert '--primary-color: #1e3a8a' in css_content
            
            # Check for darker background
            assert '--background: #0f1419' in css_content
            
            # Check for darker card background
            assert '--card-background: #1f2937' in css_content

    def test_api_fleet_endpoint_structure(self, web_server):
        """Test that the fleet API endpoint has the correct structure."""
        # Mock empty miners for basic structure test
        with patch.object(web_server, 'get_current_data') as mock_get_data:
            mock_get_data.return_value = {'miners': []}
            
            stats = web_server.get_fleet_stats()
            
            # Check required fields are present
            required_fields = [
                'total_miners',
                'online_miners', 
                'offline_miners',
                'total_hashrate_ghs',
                'total_power_w',
                'average_efficiency_j_th',  # Fleet efficiency
                'total_shares_accepted',
                'total_shares_rejected',
                'fleet_rejection_rate_percent'
            ]
            
            for field in required_fields:
                assert field in stats, f"Missing required field: {field}"
            
            # Check that average_temp_c is NOT present
            assert 'average_temp_c' not in stats

    def test_charts_data_availability(self, web_server, mock_db_data):
        """Test that data needed for charts is available."""
        with patch.object(web_server, '_get_data_from_database') as mock_db:
            miners_data = []
            for row in mock_db_data:
                miner_info = {
                    'ip': row['ip_address'],
                    'hashrate_ghs': row['hashrate_ghs'],
                    'expected_hashrate_ghs': row['expected_hashrate_ghs'],
                    'efficiency_j_th': row['efficiency_j_th'],
                    'voltage_asic_actual_v': row['voltage_asic_actual_v'],
                    'status': row['status']
                }
                miners_data.append(miner_info)
            
            mock_db.return_value = {'miners': miners_data}
            
            data = web_server.get_current_data()
            miners = data['miners']
            
            # Check chart data availability for each miner
            for miner in miners:
                # Hashrate chart data
                assert 'hashrate_ghs' in miner
                assert 'expected_hashrate_ghs' in miner
                assert isinstance(miner['hashrate_ghs'], (int, float))
                assert isinstance(miner['expected_hashrate_ghs'], (int, float))
                
                # Efficiency & voltage chart data
                assert 'efficiency_j_th' in miner
                assert 'voltage_asic_actual_v' in miner
                assert isinstance(miner['efficiency_j_th'], (int, float))
                assert isinstance(miner['voltage_asic_actual_v'], (int, float))