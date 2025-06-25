#!/usr/bin/env python3
"""
Utility functions for Bitaxe Gamma Monitor
Common utilities for path handling, configuration, and logging
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


def get_project_root() -> Path:
    """Get the project root directory consistently across all modules.
    
    Returns:
        Path: The project root directory
    """
    return Path(__file__).parent.parent


def setup_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Set up a logger with consistent formatting across all modules.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: str, required_fields: Optional[list] = None) -> Dict[str, Any]:
    """Load and validate YAML configuration file consistently.
    
    Args:
        config_path: Path to configuration file
        required_fields: List of required configuration fields
        
    Returns:
        Dict[str, Any]: Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required fields are missing
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")
    
    if not config:
        raise ValueError("Configuration file is empty")
    
    # Validate required fields
    if required_fields:
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {missing_fields}")
    
    return config


def safe_path_join(*parts: str) -> Path:
    """Safely join path components with validation.
    
    Args:
        *parts: Path components to join
        
    Returns:
        Path: Validated path object
        
    Raises:
        ValueError: If path contains invalid characters
    """
    # Basic validation to prevent path traversal
    for part in parts:
        if '..' in part or part.startswith('/'):
            raise ValueError(f"Invalid path component: {part}")
    
    return Path(*parts)


def ensure_directory(directory: Path, permissions: int = 0o755) -> None:
    """Ensure directory exists with proper permissions.
    
    Args:
        directory: Directory path to create
        permissions: Directory permissions (default: 0o755)
    """
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(permissions)


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        bool: True if valid IP address format
    """
    try:
        import ipaddress
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace dangerous characters (but keep dots for extensions)
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Replace path separators and relative path indicators
    sanitized = sanitized.replace('..', '_')
    
    # Limit length and remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')[:255]
    
    return sanitized


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        str: Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds into human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration (e.g., "2h 30m 15s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds:.0f}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {minutes}m"
    
    days = hours // 24
    hours = hours % 24
    
    return f"{days}d {hours}h {minutes}m"


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""
    pass


class PathValidationError(Exception):
    """Exception raised for path validation errors."""
    pass