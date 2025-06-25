"""Unit tests for the health check module."""

import pytest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from health_check import HealthChecker


class TestHealthChecker:
    """Test suite for HealthChecker class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
    def teardown_method(self):
        """Cleanup after each test method."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test HealthChecker initialization."""
        checker = HealthChecker()
        
        assert checker.checks == []
        assert checker.warnings == []
        assert checker.errors == []
    
    def test_log_info(self):
        """Test logging info messages."""
        checker = HealthChecker()
        
        with patch('builtins.print') as mock_print:
            checker.log('INFO', 'Test message')
            
        mock_print.assert_called_once()
        assert 'INFO: Test message' in mock_print.call_args[0][0]
        assert len(checker.errors) == 0
        assert len(checker.warnings) == 0
    
    def test_log_warning(self):
        """Test logging warning messages."""
        checker = HealthChecker()
        
        with patch('builtins.print') as mock_print:
            checker.log('WARNING', 'Test warning')
            
        mock_print.assert_called_once()
        assert 'WARNING: Test warning' in mock_print.call_args[0][0]
        assert len(checker.warnings) == 1
        assert 'Test warning' in checker.warnings
    
    def test_log_error(self):
        """Test logging error messages."""
        checker = HealthChecker()
        
        with patch('builtins.print') as mock_print:
            checker.log('ERROR', 'Test error')
            
        mock_print.assert_called_once()
        assert 'ERROR: Test error' in mock_print.call_args[0][0]
        assert len(checker.errors) == 1
        assert 'Test error' in checker.errors
    
    @patch('health_check.BitaxeDatabase')
    def test_check_database_health_success(self, mock_db_class):
        """Test successful database health check."""
        # Setup mock database
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_db.get_connection.return_value = mock_conn
        mock_db.validate_data_quality.return_value = {
            'valid': True,
            'issues': [],
            'stats': {'total_miners': 3, 'total_metrics': 100, 'recent_metrics': 50}
        }
        mock_db_class.return_value = mock_db
        
        checker = HealthChecker()
        result = checker.check_database_health()
        
        assert result == True
        mock_db_class.assert_called_once_with('data/bitaxe_monitor.db')
        mock_db.get_connection.assert_called_once()
        mock_cursor.execute.assert_called_with("SELECT 1")
        mock_db.validate_data_quality.assert_called_once()
    
    @patch('health_check.BitaxeDatabase')
    def test_check_database_health_connection_failure(self, mock_db_class):
        """Test database health check with connection failure."""
        mock_db_class.side_effect = Exception("Database connection failed")
        
        checker = HealthChecker()
        result = checker.check_database_health()
        
        assert result == False
        assert len(checker.errors) == 1
        assert 'Database health check failed' in checker.errors[0]
    
    @patch('health_check.BitaxeDatabase')
    def test_check_database_health_data_quality_issues(self, mock_db_class):
        """Test database health check with data quality issues."""
        # Setup mock database with data quality issues
        mock_db = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_db.get_connection.return_value = mock_conn
        mock_db.validate_data_quality.return_value = {
            'valid': False,
            'issues': ['Found orphaned records', 'Stale miner data'],
            'stats': {'total_miners': 3, 'total_metrics': 100, 'recent_metrics': 50}
        }
        mock_db_class.return_value = mock_db
        
        checker = HealthChecker()
        result = checker.check_database_health()
        
        assert result == True  # Still passes but logs warnings
        assert len(checker.warnings) >= 1
        assert any('Data quality issues found' in warning for warning in checker.warnings)
    
    def test_check_file_permissions_success(self):
        """Test successful file permissions check."""
        checker = HealthChecker()
        
        # Create test database file
        with open('data/bitaxe_monitor.db', 'w') as f:
            f.write('test')
        
        result = checker.check_file_permissions()
        
        assert result == True
    
    def test_check_file_permissions_no_data_directory(self):
        """Test file permissions check when data directory doesn't exist."""
        # Remove data directory
        import shutil
        shutil.rmtree('data', ignore_errors=True)
        
        checker = HealthChecker()
        result = checker.check_file_permissions()
        
        assert result == False
        assert len(checker.errors) >= 1
        assert any('Data directory does not exist' in error for error in checker.errors)
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_success(self, mock_disk_usage):
        """Test successful disk space check."""
        # Mock sufficient disk space (500MB free)
        mock_disk_usage.return_value = (1000 * 1024 * 1024, 500 * 1024 * 1024, 500 * 1024 * 1024)
        
        checker = HealthChecker()
        result = checker.check_disk_space()
        
        assert result == True
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_low_warning(self, mock_disk_usage):
        """Test disk space check with low space warning."""
        # Mock low disk space (100MB free)
        mock_disk_usage.return_value = (1000 * 1024 * 1024, 900 * 1024 * 1024, 100 * 1024 * 1024)
        
        checker = HealthChecker()
        result = checker.check_disk_space()
        
        assert result == True  # Still passes but warns
        assert len(checker.warnings) >= 1
        assert any('Low disk space' in warning for warning in checker.warnings)
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_critical_error(self, mock_disk_usage):
        """Test disk space check with critically low space."""
        # Mock critically low disk space (30MB free)
        mock_disk_usage.return_value = (1000 * 1024 * 1024, 970 * 1024 * 1024, 30 * 1024 * 1024)
        
        checker = HealthChecker()
        result = checker.check_disk_space()
        
        assert result == False
        assert len(checker.errors) >= 1
        assert any('Critically low disk space' in error for error in checker.errors)
    
    def test_check_config_file_success(self):
        """Test successful config file check."""
        # Create valid config file
        config = {
            'miners': [
                {'ip': '192.168.1.45', 'expected_hashrate_ghs': 500}
            ],
            'poll_interval': 30
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        checker = HealthChecker()
        result = checker.check_config_file()
        
        assert result == True
    
    def test_check_config_file_missing(self):
        """Test config file check when file is missing."""
        checker = HealthChecker()
        result = checker.check_config_file()
        
        assert result == False
        assert len(checker.errors) >= 1
        assert any('Configuration file config.yaml not found' in error for error in checker.errors)
    
    def test_check_config_file_missing_fields(self):
        """Test config file check with missing required fields."""
        # Create config file missing required fields
        config = {'poll_interval': 30}  # Missing 'miners'
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        checker = HealthChecker()
        result = checker.check_config_file()
        
        assert result == False
        assert len(checker.errors) >= 1
        assert any('Required config field missing: miners' in error for error in checker.errors)
    
    def test_check_config_file_no_miners(self):
        """Test config file check with empty miners list."""
        # Create config file with empty miners list
        config = {
            'miners': [],
            'poll_interval': 30
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        checker = HealthChecker()
        result = checker.check_config_file()
        
        assert result == True  # Still passes but warns
        assert len(checker.warnings) >= 1
        assert any('No miners configured' in warning for warning in checker.warnings)
    
    @patch('requests.get')
    def test_check_web_server_success(self, mock_get):
        """Test successful web server check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        checker = HealthChecker()
        result = checker.check_web_server()
        
        assert result == True
        mock_get.assert_called_once_with('http://localhost:80/api/status', timeout=5)
    
    @patch('requests.get')
    def test_check_web_server_connection_error(self, mock_get):
        """Test web server check with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        checker = HealthChecker()
        result = checker.check_web_server()
        
        assert result == False
        assert len(checker.errors) >= 1
        assert any('Web server not responding' in error for error in checker.errors)
    
    @patch('requests.get')
    def test_check_web_server_bad_status(self, mock_get):
        """Test web server check with bad status code."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        checker = HealthChecker()
        result = checker.check_web_server()
        
        assert result == False
        assert len(checker.errors) >= 1
        assert any('Web server returned status 500' in error for error in checker.errors)
    
    def test_run_health_check_all_pass(self):
        """Test full health check when all checks pass."""
        checker = HealthChecker()
        
        # Mock all checks to return True
        checker.check_file_permissions = Mock(return_value=True)
        checker.check_disk_space = Mock(return_value=True)
        checker.check_config_file = Mock(return_value=True)
        checker.check_database_health = Mock(return_value=True)
        
        result = checker.run_health_check()
        
        assert result == True
        assert len(checker.errors) == 0
    
    def test_run_health_check_with_failures(self):
        """Test full health check when some checks fail."""
        checker = HealthChecker()
        
        # Mock some checks to fail
        checker.check_file_permissions = Mock(return_value=False)
        checker.check_disk_space = Mock(return_value=True)
        checker.check_config_file = Mock(return_value=False)
        checker.check_database_health = Mock(return_value=True)
        
        # Add some errors to simulate failures
        checker.errors = ['File permission error', 'Config error']
        
        result = checker.run_health_check()
        
        assert result == False
    
    def test_run_health_check_with_web_server(self):
        """Test full health check including web server check."""
        checker = HealthChecker()
        
        # Mock all checks to return True
        checker.check_file_permissions = Mock(return_value=True)
        checker.check_disk_space = Mock(return_value=True)
        checker.check_config_file = Mock(return_value=True)
        checker.check_database_health = Mock(return_value=True)
        checker.check_web_server = Mock(return_value=True)
        
        result = checker.run_health_check(check_web=True)
        
        assert result == True
        # Verify web server check was called
        checker.check_web_server.assert_called_once()


@pytest.mark.integration
def test_main_function_help():
    """Test the main function with help argument."""
    import subprocess
    import sys
    
    # Test help argument
    result = subprocess.run([
        sys.executable, 'health_check.py', '--help'
    ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
    
    assert result.returncode == 0
    assert 'Bitaxe Monitor Health Checker' in result.stdout


@pytest.mark.unit
def test_health_checker_imports():
    """Test that HealthChecker can be imported without errors."""
    from health_check import HealthChecker
    assert HealthChecker is not None


@pytest.mark.unit  
def test_main_function_exists():
    """Test that main function exists and is callable."""
    from health_check import main
    assert callable(main)