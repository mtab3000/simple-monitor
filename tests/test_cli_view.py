"""Unit tests for the CLI viewer module."""

import pytest
import tempfile
import csv
import os
from unittest.mock import Mock, patch, mock_open
from io import StringIO

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cli_view import (
    load_config, load_csv_data, get_latest_data_by_miner,
    create_main_table, get_status_display, create_fleet_stats_panel,
    create_individual_panels
)


class TestCliView:
    """Test suite for CLI viewer functions."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return {
            'csv_path': 'test_metrics.csv',
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 934.3},
                {'ip': '192.168.1.46', 'expected_hashrate_ghs': 944.5}
            ]
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

    def test_load_config_success(self, mock_config):
        """Test successful configuration loading."""
        config_content = """
csv_path: 'test_metrics.csv'
miners:
  - ip: '192.168.1.45'
    expected_hashrate_ghs: 934.3
"""
        
        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('yaml.safe_load', return_value=mock_config):
                result = load_config()
                assert result == mock_config

    def test_load_config_file_not_found(self):
        """Test configuration loading with missing file."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', side_effect=FileNotFoundError):
                with pytest.raises(SystemExit):
                    load_config()

    def test_load_csv_data_success(self, temp_csv_file, sample_csv_data):
        """Test successful CSV data loading."""
        result = load_csv_data(temp_csv_file)
        
        assert len(result) == 2
        assert result[0]['miner_ip'] == '192.168.1.45'
        assert result[1]['miner_ip'] == '192.168.1.46'
        
        # Check that numeric fields are converted
        assert isinstance(result[0]['hashrate_ghs'], float)
        assert isinstance(result[0]['temp_asic_c'], float)

    def test_load_csv_data_file_not_found(self):
        """Test CSV loading with missing file."""
        with pytest.raises(SystemExit):
            load_csv_data('nonexistent_file.csv')

    def test_load_csv_data_empty_file(self):
        """Test CSV loading with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pass  # Create empty file
        
        try:
            result = load_csv_data(f.name)
            assert result == []
        finally:
            os.unlink(f.name)

    def test_get_latest_data_by_miner(self, sample_csv_data):
        """Test getting latest data for each miner."""
        # Add older data for the same miner
        older_data = sample_csv_data[0].copy()
        older_data['timestamp'] = '2024-01-01 11:55:00'
        older_data['hashrate_ghs'] = '900.0'
        
        test_data = [older_data] + sample_csv_data
        
        result = get_latest_data_by_miner(test_data)
        
        assert len(result) == 2
        assert result['192.168.1.45']['timestamp'] == '2024-01-01 12:00:00'
        assert result['192.168.1.45']['hashrate_ghs'] == '934.5'

    def test_get_status_display(self):
        """Test status display formatting."""
        test_cases = [
            ('online', '🟢 ONLINE'),
            ('no_hashrate', '⚠️  NO HASH'),
            ('overheating', '🔥 HOT'),
            ('wifi_issues', '📶 WIFI'),
            ('high_rejection', '❌ REJECT'),
            ('timeout', '⏰ TIMEOUT'),
            ('connection_failed', '🔴 OFFLINE'),
            ('unknown_status', '❓ UNKNOWN_STATUS')
        ]
        
        for status, expected in test_cases:
            result = get_status_display(status)
            assert expected in result

    def test_create_main_table_summary(self, sample_csv_data):
        """Test main table creation in summary mode."""
        # Convert sample data to proper format
        latest_data = {}
        for row in sample_csv_data:
            # Convert string values to floats
            processed_row = row.copy()
            for key, value in processed_row.items():
                if key in ['hashrate_ghs', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                          'voltage_asic_actual_v', 'efficiency_j_th', 'uptime_hours']:
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = 0.0
            latest_data[row['miner_ip']] = processed_row
        
        table = create_main_table(latest_data, show_detailed=False)
        
        assert table is not None
        assert table.title == "⚡ Bitaxe Gamma Fleet Summary"

    def test_create_main_table_detailed(self, sample_csv_data):
        """Test main table creation in detailed mode."""
        # Convert sample data to proper format
        latest_data = {}
        for row in sample_csv_data:
            processed_row = row.copy()
            for key, value in processed_row.items():
                if key in ['hashrate_ghs', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                          'voltage_asic_actual_v', 'efficiency_j_th', 'uptime_hours']:
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = 0.0
            latest_data[row['miner_ip']] = processed_row
        
        table = create_main_table(latest_data, show_detailed=True)
        
        assert table is not None
        assert table.title == "⚡ Fleet Summary"

    def test_create_fleet_stats_panel(self, sample_csv_data):
        """Test fleet statistics panel creation."""
        # Convert sample data to proper format
        latest_data = {}
        for row in sample_csv_data:
            processed_row = row.copy()
            for key, value in processed_row.items():
                if key in ['hashrate_ghs', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                          'shares_accepted', 'shares_rejected']:
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = 0.0
            latest_data[row['miner_ip']] = processed_row
        
        panel = create_fleet_stats_panel(latest_data)
        
        assert panel is not None
        assert "Fleet Dashboard" in str(panel.title)

    def test_create_individual_panels(self, sample_csv_data):
        """Test individual miner panels creation."""
        # Convert sample data to proper format
        latest_data = {}
        for row in sample_csv_data:
            processed_row = row.copy()
            for key, value in processed_row.items():
                if key in ['hashrate_ghs', 'hashrate_ratio_percent', 'temp_asic_c', 
                          'temp_vr_c', 'power_w', 'current_a', 'voltage_asic_set_v',
                          'voltage_asic_actual_v', 'voltage_device_v', 'frequency_set_mhz',
                          'efficiency_j_th', 'shares_accepted', 'shares_rejected',
                          'free_heap_bytes', 'overclock_enabled', 'fan_speed_percent',
                          'fan_rpm', 'wifi_rssi', 'uptime_hours']:
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = 0.0
            latest_data[row['miner_ip']] = processed_row
        
        panels = create_individual_panels(latest_data)
        
        assert len(panels) == 2
        assert all(panel is not None for panel in panels)

    def test_create_individual_panels_with_temperature_warning(self):
        """Test individual panels with temperature warnings."""
        hot_data = {
            '192.168.1.45': {
                'status': 'online',
                'hostname': 'bitaxe1',
                'hashrate_ghs': 934.5,
                'hashrate_ratio_percent': 100.0,
                'expected_hashrate_ghs': 934.3,
                'temp_asic_c': 85.0,  # High temperature
                'temp_vr_c': 82.0,    # High temperature
                'power_w': 14.0,
                'current_a': 9.03,
                'voltage_asic_set_v': 1.003,
                'voltage_asic_actual_v': 0.981,
                'voltage_device_v': 4.938,
                'frequency_set_mhz': 458.0,
                'efficiency_j_th': 15.1,
                'shares_accepted': 2285.0,
                'shares_rejected': 1.0,
                'best_session_diff': '2.87M',
                'fan_speed_percent': 46.0,
                'fan_rpm': 3837.0,
                'free_heap_bytes': 8388608.0,
                'wifi_rssi': -52.0,
                'uptime_hours': 3.1,
                'overclock_enabled': 1.0,
                'pool_user': '3Aas8yBKTY3wA5d...'
            }
        }
        
        panels = create_individual_panels(hot_data)
        
        assert len(panels) == 1
        # Check for temperature warning emoji in panel content
        panel_content = str(panels[0].renderable)
        assert "🔥" in panel_content


class TestCliViewIntegration:
    """Integration tests for CLI viewer functionality."""

    @pytest.mark.integration
    def test_full_viewer_workflow(self, temp_csv_file, sample_csv_data):
        """Test complete viewer workflow from CSV to display."""
        # Load data
        data = load_csv_data(temp_csv_file)
        assert len(data) == 2
        
        # Get latest data
        latest_data = get_latest_data_by_miner(data)
        assert len(latest_data) == 2
        
        # Create displays
        summary_table = create_main_table(latest_data, show_detailed=False)
        detailed_table = create_main_table(latest_data, show_detailed=True)
        fleet_panel = create_fleet_stats_panel(latest_data)
        individual_panels = create_individual_panels(latest_data)
        
        # Verify all components were created
        assert summary_table is not None
        assert detailed_table is not None
        assert fleet_panel is not None
        assert len(individual_panels) == 2

    @pytest.mark.integration
    def test_viewer_with_offline_miners(self, temp_csv_file):
        """Test viewer behavior with offline miners."""
        offline_data = [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'hostname': 'bitaxe1',
                'status': 'connection_failed',
                'hashrate_ghs': '0',
                'temp_asic_c': '0',
                'temp_vr_c': '0',
                'power_w': '0',
                'shares_accepted': '0',
                'shares_rejected': '0'
            }
        ]
        
        # Write offline data to CSV
        with open(temp_csv_file, 'w', newline='') as f:
            if offline_data:
                writer = csv.DictWriter(f, fieldnames=offline_data[0].keys())
                writer.writeheader()
                writer.writerows(offline_data)
        
        data = load_csv_data(temp_csv_file)
        latest_data = get_latest_data_by_miner(data)
        
        # Verify offline status is handled
        assert latest_data['192.168.1.45']['status'] == 'connection_failed'
        
        # Test that panels can be created even with offline miners
        panels = create_individual_panels(latest_data)
        assert len(panels) == 1

    @pytest.mark.integration 
    def test_viewer_with_mixed_status_miners(self, temp_csv_file):
        """Test viewer with miners in different statuses."""
        mixed_data = [
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.45',
                'hostname': 'bitaxe1',
                'status': 'online',
                'hashrate_ghs': '934.5',
                'temp_asic_c': '60.0',
                'temp_vr_c': '53.0',
                'power_w': '14.0',
                'shares_accepted': '2285',
                'shares_rejected': '1'
            },
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.46',
                'hostname': 'bitaxe2',
                'status': 'overheating',
                'hashrate_ghs': '944.5',
                'temp_asic_c': '90.0',  # Overheating
                'temp_vr_c': '85.0',
                'power_w': '14.2',
                'shares_accepted': '2366',
                'shares_rejected': '3'
            },
            {
                'timestamp': '2024-01-01 12:00:00',
                'miner_ip': '192.168.1.47',
                'hostname': 'bitaxe3',
                'status': 'connection_failed',
                'hashrate_ghs': '0',
                'temp_asic_c': '0',
                'temp_vr_c': '0',
                'power_w': '0',
                'shares_accepted': '0',
                'shares_rejected': '0'
            }
        ]
        
        # Write mixed data to CSV
        with open(temp_csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=mixed_data[0].keys())
            writer.writeheader()
            writer.writerows(mixed_data)
        
        data = load_csv_data(temp_csv_file)
        latest_data = get_latest_data_by_miner(data)
        
        # Test fleet stats with mixed statuses
        fleet_panel = create_fleet_stats_panel(latest_data)
        assert fleet_panel is not None
        
        # Verify different statuses are represented
        statuses = [miner['status'] for miner in latest_data.values()]
        assert 'online' in statuses
        assert 'overheating' in statuses
        assert 'connection_failed' in statuses


@pytest.mark.unit
class TestCliViewEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_data = {}
        
        table = create_main_table(empty_data, show_detailed=False)
        fleet_panel = create_fleet_stats_panel(empty_data)
        individual_panels = create_individual_panels(empty_data)
        
        assert table is not None
        assert fleet_panel is not None
        assert individual_panels == []

    def test_malformed_data_handling(self):
        """Test handling of malformed data."""
        malformed_data = {
            '192.168.1.45': {
                'status': 'online',
                'hostname': None,  # Malformed
                'hashrate_ghs': 'invalid',  # Invalid number
                'temp_asic_c': None,
                'power_w': ''
            }
        }
        
        # Should not raise exceptions
        table = create_main_table(malformed_data, show_detailed=False)
        fleet_panel = create_fleet_stats_panel(malformed_data)
        individual_panels = create_individual_panels(malformed_data)
        
        assert table is not None
        assert fleet_panel is not None
        assert len(individual_panels) == 1

    def test_very_long_hostnames(self):
        """Test handling of very long hostnames."""
        long_hostname_data = {
            '192.168.1.45': {
                'status': 'online',
                'hostname': 'this-is-a-very-long-hostname-that-should-be-truncated',
                'hashrate_ghs': 934.5,
                'temp_asic_c': 60.0,
                'power_w': 14.0
            }
        }
        
        individual_panels = create_individual_panels(long_hostname_data)
        assert len(individual_panels) == 1