# Changelog

All notable changes to the Bitaxe Monitor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-06-24

### 🚀 Major Release - Enterprise-Grade Reliability

This release represents a complete overhaul of the monitoring system with enterprise-grade features, robust error handling, and professional-quality tools.

### Added
- **Robust CSV handling** with corruption prevention and atomic writes
- **Persistent hostname caching** for flaky network responses
- **Automatic backup system** with configurable intervals
- **CSV repair and recovery tools** for data maintenance
- **Thread-safe operations** for concurrent access safety
- **Enhanced error handling** with graceful degradation
- **Professional project structure** with organized directories
- **Comprehensive documentation** and setup tools
- **Data validation** and integrity checking
- **Self-healing mechanisms** for error recovery

### Changed
- **Reduced polling interval** from 15s to 30s for better network efficiency
- **Reorganized project structure** into logical directories (`src/`, `tools/`, `docs/`, etc.)
- **Enhanced status reporting** with detailed error categorization
- **Improved configuration handling** with path resolution
- **Better user experience** with launcher scripts and setup tools

### Enhanced
- **CSV corruption prevention** using temporary files and atomic operations
- **Network resilience** with cached hostnames and retry mechanisms
- **Data persistence** with automatic backups and recovery procedures
- **Error visibility** with comprehensive logging and status indicators
- **Maintenance tools** for file repair and data analysis

### Fixed
- **CSV corruption issues** from concurrent writes and data merging
- **Hostname field losses** during network instability
- **Data validation errors** with improved type conversion
- **File system race conditions** with proper locking
- **Memory leaks** and resource management issues

### Tools Added
- `csv_repair.py` - Analyze, repair, and merge CSV data files
- `setup.py` - Interactive setup and configuration tool
- `monitor.py` - Main launcher with improved path handling
- `viewer.py` - Data visualization launcher
- Comprehensive backup and recovery utilities

### Documentation
- **Complete README rewrite** with professional formatting
- **Detailed improvement documentation** in `docs/IMPROVEMENTS.md`
- **Setup instructions** and troubleshooting guides
- **API documentation** and usage examples
- **Contributing guidelines** and development setup

### Performance
- **Reduced network load** with optimized polling intervals
- **Memory efficiency** improvements in data handling
- **Faster startup** with streamlined initialization
- **Better resource management** with proper cleanup

### Security
- **Input validation** for all configuration and data fields
- **Safe file operations** with proper error handling
- **Network timeout protection** against hanging connections
- **Data integrity verification** with checksum validation

## [1.0.0] - Previous Version

### Features
- Basic Bitaxe miner monitoring via REST API
- CSV data logging with timestamped metrics
- CLI viewer for data visualization
- Simple configuration via YAML file
- Real-time status monitoring

### Known Issues (Fixed in 2.0.0)
- CSV corruption from concurrent writes
- Missing hostname data during network issues
- Limited error handling and recovery
- Basic project structure
- No data validation or backup features

---

## Migration from 1.x to 2.0

### Automatic Migration
The new system includes migration tools that automatically:
- Backup existing data files
- Update configuration format
- Repair corrupted CSV files
- Preserve historical data

### Manual Steps Required
1. Run `python setup.py` to create new configuration
2. Update miner IP addresses in `config.yaml`
3. Use new launcher scripts: `python monitor.py` and `python viewer.py`
4. Check data integrity with `python tools/csv_repair.py stats metrics.csv`

### Breaking Changes
- Configuration file location moved to project root
- Script execution uses new launcher files
- Some CSV column names may have changed (automatic conversion provided)

### Compatibility
- Existing CSV data files are fully compatible
- Configuration files can be automatically migrated
- All original features remain available with enhancements

---

For detailed technical information about improvements, see `docs/IMPROVEMENTS.md`.
