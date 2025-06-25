#!/usr/bin/env python3
"""
Health Check Script for Bitaxe Monitor Containers
Validates system health, database connectivity, and data quality
"""

import sys
import os
import time
import requests
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import BitaxeDatabase


class HealthChecker:
    """Comprehensive health checker for Bitaxe Monitor containers."""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def log(self, level: str, message: str):
        """Log a message with appropriate level."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
        
        if level == 'ERROR':
            self.errors.append(message)
        elif level == 'WARNING':
            self.warnings.append(message)
    
    def check_database_health(self) -> bool:
        """Check database connectivity and health."""
        try:
            self.log('INFO', 'Checking database health...')
            
            db = BitaxeDatabase('data/bitaxe_monitor.db')
            
            # Test basic connection
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result[0] != 1:
                    self.log('ERROR', 'Database connection test failed')
                    return False
            
            # Validate data quality
            quality_report = db.validate_data_quality()
            
            if not quality_report['valid']:
                self.log('WARNING', f"Data quality issues found: {quality_report['issues']}")
            
            stats = quality_report['stats']
            self.log('INFO', f"Database stats - Miners: {stats.get('total_miners', 0)}, "
                            f"Metrics: {stats.get('total_metrics', 0)}, "
                            f"Recent: {stats.get('recent_metrics', 0)}")
            
            return True
            
        except Exception as e:
            self.log('ERROR', f'Database health check failed: {e}')
            return False
    
    def check_file_permissions(self) -> bool:
        """Check file and directory permissions."""
        try:
            self.log('INFO', 'Checking file permissions...')
            
            # Check data directory
            data_dir = Path('data')
            if not data_dir.exists():
                self.log('ERROR', 'Data directory does not exist')
                return False
            
            if not os.access(data_dir, os.R_OK | os.W_OK):
                self.log('ERROR', 'Data directory is not readable/writable')
                return False
            
            # Check database file if it exists
            db_file = data_dir / 'bitaxe_monitor.db'
            if db_file.exists():
                if not os.access(db_file, os.R_OK | os.W_OK):
                    self.log('ERROR', 'Database file is not readable/writable')
                    return False
            
            self.log('INFO', 'File permissions OK')
            return True
            
        except Exception as e:
            self.log('ERROR', f'File permission check failed: {e}')
            return False
    
    def check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            self.log('INFO', 'Checking disk space...')
            
            import shutil
            total, used, free = shutil.disk_usage('.')
            free_mb = free // (1024 * 1024)
            total_mb = total // (1024 * 1024)
            
            self.log('INFO', f'Disk space - Total: {total_mb}MB, Free: {free_mb}MB')
            
            if free_mb < 50:
                self.log('ERROR', f'Critically low disk space: {free_mb}MB')
                return False
            elif free_mb < 200:
                self.log('WARNING', f'Low disk space: {free_mb}MB')
            
            return True
            
        except Exception as e:
            self.log('ERROR', f'Disk space check failed: {e}')
            return False
    
    def check_config_file(self) -> bool:
        """Check configuration file availability and validity."""
        try:
            self.log('INFO', 'Checking configuration file...')
            
            config_file = Path('config.yaml')
            if not config_file.exists():
                self.log('ERROR', 'Configuration file config.yaml not found')
                return False
            
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ['miners', 'poll_interval']
            for field in required_fields:
                if field not in config:
                    self.log('ERROR', f'Required config field missing: {field}')
                    return False
            
            miners = config.get('miners', [])
            if not miners:
                self.log('WARNING', 'No miners configured')
            else:
                self.log('INFO', f'Configuration OK - {len(miners)} miners configured')
            
            return True
            
        except Exception as e:
            self.log('ERROR', f'Configuration check failed: {e}')
            return False
    
    def check_web_server(self, port: int = 80) -> bool:
        """Check if web server is responding (for web container)."""
        try:
            self.log('INFO', f'Checking web server on port {port}...')
            
            response = requests.get(f'http://localhost:{port}/api/status', timeout=5)
            
            if response.status_code == 200:
                self.log('INFO', 'Web server responding correctly')
                return True
            else:
                self.log('ERROR', f'Web server returned status {response.status_code}')
                return False
                
        except requests.exceptions.ConnectionError:
            self.log('ERROR', 'Web server not responding')
            return False
        except Exception as e:
            self.log('ERROR', f'Web server check failed: {e}')
            return False
    
    def run_health_check(self, check_web: bool = False) -> bool:
        """Run all health checks."""
        self.log('INFO', '=== Starting Health Check ===')
        
        checks = [
            ('File Permissions', self.check_file_permissions),
            ('Disk Space', self.check_disk_space),
            ('Configuration', self.check_config_file),
            ('Database Health', self.check_database_health),
        ]
        
        if check_web:
            checks.append(('Web Server', self.check_web_server))
        
        all_passed = True
        
        for check_name, check_func in checks:
            self.log('INFO', f'Running {check_name} check...')
            if not check_func():
                all_passed = False
        
        # Summary
        self.log('INFO', '=== Health Check Summary ===')
        self.log('INFO', f'Errors: {len(self.errors)}')
        self.log('INFO', f'Warnings: {len(self.warnings)}')
        
        if self.errors:
            self.log('ERROR', 'Health check FAILED')
            for error in self.errors:
                self.log('ERROR', f'  - {error}')
        else:
            self.log('INFO', 'Health check PASSED')
            
        if self.warnings:
            for warning in self.warnings:
                self.log('WARNING', f'  - {warning}')
        
        return all_passed


def main():
    """Command-line interface for health checker."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bitaxe Monitor Health Checker')
    parser.add_argument('--web', action='store_true', help='Include web server check')
    parser.add_argument('--exit-code', action='store_true', help='Exit with non-zero code on failure')
    
    args = parser.parse_args()
    
    checker = HealthChecker()
    success = checker.run_health_check(check_web=args.web)
    
    if args.exit_code and not success:
        sys.exit(1)
    
    return success


if __name__ == "__main__":
    main()