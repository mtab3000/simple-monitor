"""Unit tests for the utils module."""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    get_project_root, setup_logger, load_config, safe_path_join,
    ensure_directory, validate_ip_address, sanitize_filename,
    format_bytes, format_duration, ConfigValidationError, PathValidationError
)


class TestProjectRoot:
    """Test project root detection."""
    
    def test_get_project_root(self):
        """Test project root detection returns correct path."""
        root = get_project_root()
        assert isinstance(root, Path)
        # The project root should contain src and tests directories
        assert (root / 'src').exists()
        assert (root / 'tests').exists()


class TestLogger:
    """Test logger setup utilities."""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger('test_logger')
        assert logger.name == 'test_logger'
        assert logger.level == 20  # INFO level
    
    def test_setup_logger_with_level(self):
        """Test logger setup with custom level."""
        logger = setup_logger('test_debug', level='DEBUG')
        assert logger.level == 10  # DEBUG level
    
    def test_setup_logger_prevents_duplicates(self):
        """Test logger setup prevents duplicate handlers."""
        logger1 = setup_logger('test_dup')
        handler_count1 = len(logger1.handlers)
        
        logger2 = setup_logger('test_dup')
        handler_count2 = len(logger2.handlers)
        
        assert handler_count1 == handler_count2
        assert logger1 is logger2


class TestConfigLoading:
    """Test configuration loading utilities."""
    
    def test_load_config_success(self):
        """Test successful config loading."""
        config_content = "test_key: test_value\nminers: []"
        
        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('os.path.exists', return_value=True):
                config = load_config('test.yaml')
                
        assert config['test_key'] == 'test_value'
        assert 'miners' in config
    
    def test_load_config_file_not_found(self):
        """Test config loading with missing file."""
        with pytest.raises(FileNotFoundError):
            load_config('nonexistent.yaml')
    
    def test_load_config_invalid_yaml(self):
        """Test config loading with invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ValueError, match="Invalid YAML"):
                    load_config('test.yaml')
    
    def test_load_config_empty_file(self):
        """Test config loading with empty file."""
        with patch('builtins.open', mock_open(read_data="")):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ValueError, match="Configuration file is empty"):
                    load_config('test.yaml')
    
    def test_load_config_required_fields(self):
        """Test config validation with required fields."""
        config_content = "test_key: test_value"
        
        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('os.path.exists', return_value=True):
                # Should succeed with present field
                config = load_config('test.yaml', required_fields=['test_key'])
                assert config['test_key'] == 'test_value'
                
                # Should fail with missing field
                with pytest.raises(ValueError, match="Missing required configuration fields"):
                    load_config('test.yaml', required_fields=['missing_key'])


class TestPathSafety:
    """Test path safety utilities."""
    
    def test_safe_path_join_valid(self):
        """Test safe path joining with valid components."""
        path = safe_path_join('data', 'files', 'test.txt')
        assert isinstance(path, Path)
        assert str(path) == os.path.join('data', 'files', 'test.txt')
    
    def test_safe_path_join_invalid(self):
        """Test safe path joining with invalid components."""
        with pytest.raises(ValueError, match="Invalid path component"):
            safe_path_join('data', '../etc', 'passwd')
        
        with pytest.raises(ValueError, match="Invalid path component"):
            safe_path_join('/absolute', 'path')
    
    def test_ensure_directory(self):
        """Test directory creation utility."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / 'test_subdir'
            ensure_directory(test_dir)
            
            assert test_dir.exists()
            assert test_dir.is_dir()


class TestValidation:
    """Test validation utilities."""
    
    def test_validate_ip_address_valid(self):
        """Test IP address validation with valid addresses."""
        assert validate_ip_address('192.168.1.1') is True
        assert validate_ip_address('127.0.0.1') is True
        assert validate_ip_address('10.0.0.1') is True
        assert validate_ip_address('::1') is True  # IPv6
    
    def test_validate_ip_address_invalid(self):
        """Test IP address validation with invalid addresses."""
        assert validate_ip_address('256.256.256.256') is False
        assert validate_ip_address('not.an.ip.address') is False
        assert validate_ip_address('192.168.1') is False
        assert validate_ip_address('') is False
    
    def test_sanitize_filename_safe(self):
        """Test filename sanitization with safe names."""
        assert sanitize_filename('test.txt') == 'test.txt'
        assert sanitize_filename('valid_filename-123.csv') == 'valid_filename-123.csv'
    
    def test_sanitize_filename_dangerous(self):
        """Test filename sanitization with dangerous characters."""
        assert sanitize_filename('test<>file.txt') == 'test__file.txt'
        assert sanitize_filename('file|with:bad"chars.txt') == 'file_with_bad_chars.txt'
        assert sanitize_filename('../../../etc/passwd') == '______etc_passwd'
    
    def test_sanitize_filename_edge_cases(self):
        """Test filename sanitization edge cases."""
        # Leading/trailing dots and spaces
        assert sanitize_filename('  .file.  ') == 'file'
        
        # Long filename
        long_name = 'a' * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 255


class TestFormatting:
    """Test formatting utilities."""
    
    def test_format_bytes(self):
        """Test byte formatting utility."""
        assert format_bytes(0) == "0.0 B"
        assert format_bytes(512) == "512.0 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"
    
    def test_format_duration(self):
        """Test duration formatting utility."""
        assert format_duration(30.5) == "30.5s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3661) == "1h 1m"
        assert format_duration(90061) == "1d 1h 1m"
    
    def test_format_duration_edge_cases(self):
        """Test duration formatting edge cases."""
        assert format_duration(0) == "0.0s"
        assert format_duration(59.9) == "59.9s"
        assert format_duration(60) == "1m 0s"


class TestExceptions:
    """Test custom exception classes."""
    
    def test_config_validation_error(self):
        """Test ConfigValidationError exception."""
        with pytest.raises(ConfigValidationError):
            raise ConfigValidationError("Test error")
    
    def test_path_validation_error(self):
        """Test PathValidationError exception."""
        with pytest.raises(PathValidationError):
            raise PathValidationError("Test path error")


class TestUtilsIntegration:
    """Integration tests for utils module."""
    
    def test_full_workflow(self):
        """Test complete utility workflow."""
        # Get project root
        root = get_project_root()
        assert root.exists()
        
        # Setup logger
        logger = setup_logger('integration_test')
        assert logger is not None
        
        # Create safe paths
        safe_path = safe_path_join('data', 'test.txt')
        assert isinstance(safe_path, Path)
        
        # Validate IP addresses
        assert validate_ip_address('192.168.1.1')
        assert not validate_ip_address('invalid')
        
        # Test formatting
        formatted_bytes = format_bytes(1024)
        assert 'KB' in formatted_bytes
        
        formatted_duration = format_duration(3661)
        assert 'h' in formatted_duration