"""Tests for the main monitor.py launcher."""

import pytest
import sys
import os
from unittest.mock import patch, Mock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestMainLauncher:
    """Test suite for the main launcher script."""

    def test_monitor_script_exists(self):
        """Test that monitor.py exists and is readable."""
        monitor_path = os.path.join(os.path.dirname(__file__), '..', 'monitor.py')
        assert os.path.exists(monitor_path), "monitor.py launcher script not found"
        assert os.access(monitor_path, os.R_OK), "monitor.py is not readable"

    def test_monitor_script_imports(self):
        """Test that monitor.py can import required modules."""
        # Mock the main function to avoid actually running the collector
        with patch('sys.argv', ['monitor.py']):
            with patch('enhanced_collector.main') as mock_main:
                # Import and run the script
                import monitor
                
                # The import should succeed without errors
                assert hasattr(monitor, 'main') is False  # It's a launcher, not a module

    def test_path_setup(self):
        """Test that the path setup in monitor.py works correctly."""
        monitor_path = os.path.join(os.path.dirname(__file__), '..', 'monitor.py')
        
        # Read the script content
        with open(monitor_path, 'r') as f:
            content = f.read()
        
        # Check that it sets up the path correctly
        assert 'sys.path.insert' in content
        assert 'src' in content
        assert 'from enhanced_collector import main' in content

    def test_docker_command_structure(self):
        """Test that Docker command structure is valid."""
        dockerfile_path = os.path.join(os.path.dirname(__file__), '..', 'Dockerfile')
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check that it uses the correct module command
        assert 'python", "-m", "src.enhanced_collector"' in content

    def test_docker_compose_structure(self):
        """Test that docker-compose.yml has correct structure."""
        compose_path = os.path.join(os.path.dirname(__file__), '..', 'docker-compose.yml')
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check that it only has one service
        assert 'bitaxe-collector:' in content
        assert 'bitaxe-monitor:' not in content  # Legacy removed
        assert 'bitaxe-web:' not in content      # Web interface removed

    def test_requirements_simplified(self):
        """Test that requirements.txt has been simplified."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        
        with open(req_path, 'r') as f:
            content = f.read()
        
        # Should have core dependencies
        assert 'requests' in content
        assert 'PyYAML' in content
        assert 'pandas' in content
        assert 'numpy' in content
        
        # Should not have web dependencies
        assert 'Flask' not in content
        assert 'rich' not in content