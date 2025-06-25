# 🛡️ Robustness & Reliability Features

## Overview

The Bitaxe Monitor has been enhanced with enterprise-grade robustness and reliability features to ensure continuous operation in production environments.

## 🔧 Database Robustness

### Startup Health Checks
- **Integrity validation**: Database integrity check on startup
- **Disk space monitoring**: Warns when free space < 100MB
- **Connection testing**: Validates database connectivity
- **Schema validation**: Ensures all required tables exist
- **Data quality checks**: Detects orphaned records and stale data

### Enhanced Connection Management
- **WAL mode**: Write-Ahead Logging for better concurrency
- **Busy timeout**: 30-second timeout for locked database operations
- **Connection pooling**: Optimized connection reuse
- **Automatic retry**: Retry logic for transient failures

### Data Quality Monitoring
```python
# Run data quality check
quality_report = db.validate_data_quality()
if not quality_report['valid']:
    print(f"Issues found: {quality_report['issues']}")
```

## ⚡ Collector Resilience

### Circuit Breaker Pattern
- **Failure threshold**: Stops collection after 10 consecutive failures
- **Reset timer**: Automatically resets after 5 minutes
- **Graceful degradation**: Continues other operations during circuit breaker

### Exponential Backoff
- **Dynamic intervals**: Increases polling interval on failures
- **Maximum backoff**: Caps at 5 minutes maximum interval
- **Automatic recovery**: Returns to normal interval on success

### Error Recovery
```python
# Example of automatic recovery
if self.failure_count >= self.max_consecutive_failures:
    self.circuit_breaker_open = True
    self.logger.critical("Circuit breaker activated")
```

## 🐳 Container Health Monitoring

### Comprehensive Health Checks
```bash
# Manual health check
python health_check.py --web --exit-code

# Container health (automatic)
docker-compose ps  # Shows health status
```

### Health Check Components
- **File permissions**: Validates read/write access
- **Disk space**: Monitors available storage
- **Configuration**: Validates config file structure
- **Database health**: Tests connectivity and integrity
- **Web server**: Validates API responsiveness (when enabled)

### Docker Integration
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
    CMD python health_check.py --exit-code
```

## 📊 Data Export & Backup

### Database Export
```bash
# Export last 24 hours
python -m src.data_export --hours 24 --output backup.csv

# Export all data
python -m src.data_export --output full_backup.csv
```

### Export Features
- **Time filtering**: Export specific time ranges
- **CSV format**: Standard format for analysis tools
- **Complete schema**: All database fields included
- **Error handling**: Graceful failure handling

## 🔄 Automatic Maintenance

### Background Tasks
- **Data cleanup**: Removes old records (configurable retention)
- **Database vacuum**: Optimizes database file size
- **Analytics generation**: Creates hourly statistics
- **Restart detection**: Monitors miner uptime patterns

### Configuration
```yaml
# config.yaml
analytics_interval: 1800    # 30 minutes
maintenance_interval: 43200 # 12 hours
```

## 🚨 Monitoring & Alerting

### Log Levels
```python
# Logging configuration
logging.basicConfig(level=logging.INFO)

# Critical errors trigger circuit breaker
self.logger.critical("Circuit breaker activated")

# Warnings for data quality issues
self.logger.warning("Data quality issues found")
```

### Key Metrics
- **Collection success rate**: Tracks successful vs failed collections
- **Database performance**: Monitors query execution times
- **Disk usage**: Tracks storage consumption
- **Miner connectivity**: Monitors individual miner health

## 🔧 Configuration

### Robustness Settings
```yaml
# Enhanced collector settings
max_consecutive_failures: 10    # Circuit breaker threshold
max_backoff: 300                # Maximum backoff time (seconds)
analytics_interval: 1800        # Background analytics frequency
maintenance_interval: 43200     # Database maintenance frequency
```

### Health Check Settings
```bash
# Health check options
--web          # Include web server check
--exit-code    # Exit with error code on failure
```

## 📈 Performance Optimization

### Database Optimizations
- **Prepared statements**: Reduces query parsing overhead
- **Batch operations**: Groups multiple insertions
- **Index optimization**: Optimized for common queries
- **Connection reuse**: Minimizes connection overhead

### Memory Management
- **Bounded queues**: Prevents memory leaks
- **Garbage collection**: Proper cleanup of resources
- **Connection pooling**: Reuses database connections

## 🛠️ Troubleshooting

### Common Issues

**Circuit Breaker Activated**
```
CRITICAL: Circuit breaker activated - too many failures (10)
```
- Check network connectivity to miners
- Verify miner IP addresses in config
- Wait 5 minutes for automatic reset

**Database Locked**
```
WARNING: Database locked, retrying...
```
- Multiple processes accessing database
- Check for zombie processes
- Restart containers if persistent

**Low Disk Space**
```
WARNING: Low disk space: 50MB available
```
- Clean up old log files
- Increase disk allocation
- Configure shorter data retention

### Diagnostic Commands
```bash
# Full health check
python health_check.py --web

# Database integrity
python -c "from src.database import BitaxeDatabase; db = BitaxeDatabase(); print(db.validate_data_quality())"

# Container status
docker-compose ps
docker-compose logs bitaxe-enhanced --tail=50
```