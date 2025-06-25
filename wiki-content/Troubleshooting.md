# Troubleshooting

## Common Issues

### Unicode Display Issues

**Problem:** Strange characters or broken display in terminal

**Solution:**
```bash
# Set proper encoding
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# For optimization analyzer
PYTHONIOENCODING=utf-8 python src/optimization_analyzer.py
```

### Connection Problems

**Problem:** Cannot connect to Bitaxe devices

**Solutions:**
```bash
# Check network connectivity
ping 192.168.1.45

# Verify miner IPs are correct in config.yaml
# Increase timeout in config.yaml
timeout: 30

# Check firewall settings
sudo ufw status
```

### Docker Issues

**Problem:** Permission denied or container startup failures

**Solutions:**
```bash
# Fix permission issues
sudo chown -R $USER:$USER data/ backups/

# Check container logs
docker-compose logs -f bitaxe-monitor

# Restart services
docker-compose restart

# Rebuild containers
docker-compose build --no-cache
```

## Data Issues

### CSV Data Problems

**Problem:** Corrupted or missing CSV data

**Solutions:**
```bash
# Check backup directory
ls -la backups/

# Validate CSV file
python src/collector.py --validate-csv

# Restore from backup
cp backups/metrics_backup_latest.csv metrics.csv
```

### Database Issues

**Problem:** Database corruption or migration failures

**Solutions:**
```bash
# Database migration from CSV
python src/data_migration.py --action migrate

# Reset database
rm data/monitor.db
python src/data_migration.py --action migrate

# Check database integrity
python src/database.py --check-integrity
```

## Optimization Analyzer Issues

| Problem | Solution |
|---------|----------|
| 🚫 No data found | Check CSV path with `--csv-path` parameter |
| 📉 No benchmark sessions | Need 5+ different voltage/frequency combinations in 30min window |
| 🔢 Import errors | Install: `sudo apt install python3-pandas python3-numpy` |
| 🎯 Poor recommendations | Collect more data with varied settings |
| 📊 Chart display issues | Set `PYTHONIOENCODING=utf-8` |

## Web Dashboard Issues

### Cannot Access Web Interface

**Problem:** Web dashboard not accessible

**Solutions:**
```bash
# Check if service is running
docker-compose ps

# Check port binding
netstat -tlnp | grep 80

# Check firewall
sudo ufw allow 80

# Try different port
python web_dashboard.py --port 8081
```

### Slow Performance

**Problem:** Web dashboard loads slowly

**Solutions:**
```bash
# Reduce refresh interval
# Edit config.yaml:
web:
  refresh_interval: 10  # Increase from 5 seconds

# Check system resources
htop
df -h
```

## Network Issues

### Miners Going Offline

**Problem:** Miners frequently showing as offline

**Solutions:**
```bash
# Check network stability
ping -c 10 192.168.1.45

# Increase retry settings in config.yaml
retries: 5
retry_delay: 2
timeout: 15

# Check miner power and network cables
# Verify miner web interface accessibility
```

### High Rejection Rates

**Problem:** Miners showing high share rejection rates

**Solutions:**
- Check pool configuration on miners
- Verify network latency to pool
- Check for overclock stability
- Monitor temperature and power

## Performance Issues

### High CPU Usage

**Problem:** Monitoring software using too much CPU

**Solutions:**
```bash
# Increase polling interval
# Edit config.yaml:
poll_interval: 60  # Reduce frequency

# Disable detailed logging
# Use --profile basic instead of --profile enhanced
```

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
```bash
# Check available memory
free -h

# Clean up old data
python src/data_migration.py --action cleanup

# Reduce data retention
# Edit config.yaml:
database:
  retention_days: 7
```

## Getting Help

### Log Collection

```bash
# Collect logs for support
docker-compose logs > bitaxe-monitor-logs.txt

# System information
uname -a > system-info.txt
docker --version >> system-info.txt
docker-compose --version >> system-info.txt
```

### Configuration Validation

```bash
# Test configuration
python src/collector.py --validate-config

# Test connectivity
python src/collector.py --test-connections

# Generate diagnostic report
python src/utils.py --diagnostic
```

### Support Resources

- **GitHub Issues:** https://github.com/mtab3000/simple-monitor/issues
- **Documentation:** Check the [README](https://github.com/mtab3000/simple-monitor)
- **Wiki:** https://github.com/mtab3000/simple-monitor/wiki

When reporting issues, please include:
- Operating system and version
- Python version
- Docker version (if using Docker)
- Configuration file (remove sensitive IPs)
- Error messages and logs
- Steps to reproduce the issue