# Configuration Guide

## Basic Configuration

Edit `config.yaml` with your Bitaxe device settings:

```yaml
# Polling configuration
poll_interval: 30           # Seconds between polling cycles
csv_path: metrics.csv       # Data output file
timeout: 10                 # HTTP request timeout
retries: 3                  # Retry attempts
retry_delay: 1              # Delay between retries

# Miner configuration
miners:
  - ip: '192.168.1.45'
    expected_hashrate_ghs: 934.3
  - ip: '192.168.1.46'
    expected_hashrate_ghs: 944.5
```

## Advanced Configuration

### Monitoring Settings

```yaml
# Advanced polling options
poll_interval: 30
timeout: 10
retries: 3
retry_delay: 1

# Data storage
csv_path: metrics.csv
backup_enabled: true
backup_interval: 3600       # Backup every hour
```

### Web Dashboard Settings

```yaml
web:
  host: '0.0.0.0'           # Listen on all interfaces
  port: 80                  # Web server port
  auto_refresh: true        # Enable auto-refresh
  refresh_interval: 5       # Refresh every 5 seconds
  debug: false              # Disable debug mode
```

### Database Configuration

```yaml
database:
  enabled: true
  path: 'data/monitor.db'
  backup_enabled: true
  retention_days: 30
```

## Environment Variables

### UTF-8 Support
```bash
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Custom Paths
```bash
export BITAXE_CONFIG_PATH=/path/to/config.yaml
export BITAXE_DATA_PATH=/path/to/data
```

## Security Configuration

### Network Security
- Bind web interface to specific IP addresses
- Use firewall rules to restrict access
- Consider VPN for remote monitoring

### File Permissions
```bash
# Set proper permissions
chmod 600 config.yaml
chmod 755 data/
chmod 755 backups/
```

## Docker Configuration

### Environment Variables
```yaml
# docker-compose.yml
environment:
  - PYTHONIOENCODING=utf-8
  - LANG=en_US.UTF-8
  - LC_ALL=en_US.UTF-8
```

### Volume Mounts
```yaml
volumes:
  - ./config.yaml:/app/config.yaml:ro
  - ./data:/app/data
  - ./backups:/app/backups
```

## Validation

Test your configuration:
```bash
# Validate configuration file
python src/collector.py --validate-config

# Test miner connectivity
python src/collector.py --test-connections
```