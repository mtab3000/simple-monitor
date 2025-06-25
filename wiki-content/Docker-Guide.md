# 🐳 Docker Deployment Guide

## 🚀 Enhanced Monitoring Stack (DEFAULT)

The Bitaxe Monitor now ships with **Enhanced Monitoring as the default configuration**, providing enterprise-grade analytics, database storage, and web dashboard out of the box.

### Quick Start

```bash
# Clone and configure
git clone https://github.com/mtab3000/simple-monitor.git
cd simple-monitor
cp examples/config.example.yaml config.yaml
# Edit config.yaml with your Bitaxe IP addresses

# 🎯 Start complete monitoring solution (DEFAULT)
docker-compose up -d
```

**What you get by default:**
- 🗄️ **SQLite database** for advanced analytics
- 🌐 **Web dashboard** at http://localhost:80
- 📊 **Performance scoring** and anomaly detection
- 🎯 **Mining optimization** analysis tools
- 📈 **Predictive maintenance** alerts
- 💾 **Automatic backups** and data retention

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Stack                        │
├─────────────────────────────────────────────────────────┤
│  🌐 bitaxe-web          │  📊 bitaxe-enhanced           │
│  ├─ Web Dashboard       │  ├─ Data Collection           │
│  ├─ REST API            │  ├─ Database Analytics        │
│  ├─ Real-time Updates   │  ├─ Performance Scoring       │
│  └─ Mobile Responsive   │  └─ Optimization Analysis     │
├─────────────────────────────────────────────────────────┤
│  💾 Persistent Storage                                  │
│  ├─ bitaxe-data/        │  📁 Configuration             │
│  ├─ bitaxe-backups/     │  ├─ config.yaml               │
│  ├─ metrics.csv         │  └─ hostname_cache.json       │
│  └─ monitor.db          │                               │
└─────────────────────────────────────────────────────────┘
```

## 🎛️ Service Configurations

### Enhanced Monitoring (bitaxe-enhanced)

**Default service providing:**
- Advanced data collection with database storage
- Performance analytics and scoring
- Anomaly detection and alerting
- Predictive maintenance insights
- Mining optimization analysis

```yaml
# Key features in docker-compose.yml
bitaxe-enhanced:
  command: ["python", "enhanced_monitor.py"]
  volumes:
    - bitaxe-data:/app/data          # Database storage
    - bitaxe-backups:/app/backups    # Automatic backups
```

### Web Dashboard (bitaxe-web)

**Professional web interface providing:**
- Real-time monitoring dashboard
- REST API endpoints
- Mobile-responsive design
- Fleet overview and individual miner details

```yaml
# Accessible at http://localhost:80
bitaxe-web:
  command: ["python", "web_dashboard.py", "--host", "0.0.0.0", "--port", "80"]
  ports:
    - "80:80"
```

## 🔧 Configuration Options

### Standard Deployment (Recommended)

```bash
# Full stack with all features
docker-compose up -d

# Services included:
# ✅ bitaxe-enhanced (data collection & analytics)  
# ✅ bitaxe-web (web dashboard & API)
```

### Minimal Deployment

```bash
# Basic monitoring only (CSV-based)
docker-compose --profile basic up -d

# Services included:
# ✅ bitaxe-monitor (basic CSV collection only)
```

### Custom Port Configuration

```bash
# Run web dashboard on custom port
docker-compose up -d
docker-compose exec bitaxe-web python web_dashboard.py --port 8080
```

## 📊 Data Management

### Persistent Storage

**Volumes automatically created:**
- `bitaxe-data/` - Database files and analytics data
- `bitaxe-backups/` - Automatic backup files
- `metrics.csv` - CSV data (for compatibility)
- `hostname_cache.json` - Network optimization cache

### Backup Operations

```bash
# Manual backup
docker-compose exec bitaxe-enhanced python src/database.py --backup

# View backups
ls -la backups/

# Restore from backup (if needed)
docker-compose exec bitaxe-enhanced python src/data_migration.py --restore backups/latest.db
```

### Data Export

```bash
# Export to CSV
docker-compose exec bitaxe-enhanced python src/analytics.py --export-csv

# Export optimization analysis
docker-compose exec bitaxe-enhanced python src/optimization_analyzer.py --hours 168 --output weekly.json

# Database statistics
docker-compose exec bitaxe-enhanced python src/analytics.py --stats
```

## 🔍 Monitoring & Troubleshooting

### Service Health Checks

```bash
# Check all services
docker-compose ps

# View service logs
docker-compose logs -f bitaxe-enhanced
docker-compose logs -f bitaxe-web

# Check database connectivity
docker-compose exec bitaxe-enhanced python -c "import src.database; print('Database OK')"

# Test web API
curl http://localhost:80/api/status | jq
```

### Performance Monitoring

```bash
# Container resource usage
docker stats

# Service restart if needed
docker-compose restart bitaxe-enhanced
docker-compose restart bitaxe-web

# Complete restart
docker-compose down && docker-compose up -d
```

### Log Analysis

```bash
# Enhanced monitoring logs
docker-compose logs -f bitaxe-enhanced | grep -E "(ERROR|WARNING|Performance)"

# Web server access logs
docker-compose logs -f bitaxe-web | grep -E "(GET|POST|ERROR)"

# Export logs for analysis
docker-compose logs > monitoring-logs-$(date +%Y%m%d).txt
```

## 🚀 Advanced Usage

### Development Mode

```bash
# Enable debug mode
docker-compose exec bitaxe-web python web_dashboard.py --debug

# Mount source code for live development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Scaling for Large Fleets

```bash
# Increase polling frequency for large fleets
# Edit config.yaml:
poll_interval: 15  # Reduced from 30 seconds

# Database optimization for large datasets
docker-compose exec bitaxe-enhanced python src/database.py --optimize

# Enable performance profiling
docker-compose exec bitaxe-enhanced python src/analytics.py --profile
```

### Integration with External Systems

```bash
# API integration examples
# Get JSON data for external monitoring
curl -s http://localhost:80/api/fleet | jq '.data.total_hashrate_ghs'

# Webhook notifications (custom implementation)
docker-compose exec bitaxe-enhanced python src/analytics.py --webhook-alerts

# Export to external databases
docker-compose exec bitaxe-enhanced python src/data_migration.py --export-influxdb
```

## 🔒 Security Considerations

### Network Security

```bash
# Bind to specific interface only
# docker-compose.yml modification:
ports:
  - "127.0.0.1:80:80"  # Localhost only

# Use reverse proxy for production
# Example nginx configuration provided
```

### Access Control

```bash
# File permissions
sudo chown -R $USER:$USER data/ backups/
chmod 600 config.yaml

# Firewall configuration
sudo ufw allow from 192.168.1.0/24 to any port 80
sudo ufw deny 80  # Block external access
```

## 📚 Additional Resources

- [Web Dashboard API Reference](API-Reference)
- [Mining Optimization Guide](Mining-Optimization)
- [Troubleshooting Guide](Troubleshooting)
- [Configuration Reference](Configuration)

## 🆘 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Web dashboard not accessible | Check `docker-compose ps`, restart `bitaxe-web` |
| Database errors | Run `docker-compose exec bitaxe-enhanced python src/database.py --check-integrity` |
| High memory usage | Reduce data retention in config.yaml |
| Poor performance | Increase `poll_interval` in config.yaml |
| Container won't start | Check logs with `docker-compose logs [service-name]` |