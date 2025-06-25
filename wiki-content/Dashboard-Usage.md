# Dashboard Usage

## Terminal Dashboard

### Live Dashboard
```bash
python viewer.py --live
```

### Detailed View with Individual Panels
```bash
python viewer.py --live --detailed
```

### Static Summary
```bash
python viewer.py --summary
```

### Static Detailed Summary
```bash
python viewer.py --summary --detailed
```

## Web Dashboard

### Starting the Web Interface
```bash
python web_dashboard.py
```

### Custom Host/Port
```bash
python web_dashboard.py --host 0.0.0.0 --port 80
```

### Web Features
- **Responsive design** works on desktop, tablet, and mobile
- **Real-time updates** every 5 seconds
- **Fleet overview** with total statistics
- **Individual miner cards** with detailed metrics
- **Auto-refresh toggle** for manual control
- **REST API endpoints** for integration

## Enhanced Monitoring

### Start Enhanced Monitoring
```bash
python enhanced_monitor.py
```

### Database Migration from CSV
```bash
python src/data_migration.py --action migrate
```

### Enhanced Features
- **SQLite database** for advanced data storage and analysis
- **Performance scoring** with A+ to F grades
- **Anomaly detection** using statistical analysis
- **Predictive maintenance** alerts
- **Growth metrics** with trend analysis
- **Fleet analytics** with comparative insights

## Status Indicators

### Miner Status
- 🟢 **Online** - Miner operating normally
- ⚠️ **No Hash** - Hashrate issues detected
- 🔥 **Overheating** - Temperature warnings
- 📶 **WiFi Issues** - Network connectivity problems
- ❌ **Rejected Shares** - High rejection rate alerts
- ⏰ **Timeout** - Connection timeouts
- 🔴 **Offline** - Miner unreachable

### Performance Indicators
- **Progress bars** for visual hashrate percentage
- **Temperature monitoring** with color coding
- **Efficiency ratings** (J/TH)
- **Network signal strength** indicators

## Fleet Dashboard Features

### Health Overview
- Visual fleet status with progress bars
- Performance metrics summary
- Total hashrate and power consumption
- Average temperatures (ASIC and VR)

### Individual Miner Panels
- **Performance bars** - Visual hashrate indicators
- **Comprehensive metrics** - All voltage readings, frequency settings
- **System status** - Fan speed, memory usage, WiFi signal, uptime
- **Mining statistics** - Share stats and best session difficulty

## Docker Dashboard Commands

### Basic Monitoring
```bash
docker-compose up -d
docker-compose exec bitaxe-monitor python viewer.py --live
```

### Enhanced Monitoring
```bash
docker-compose --profile enhanced up -d
docker-compose exec bitaxe-enhanced python viewer.py --live
```

### Web Dashboard
```bash
docker-compose --profile web up -d
# Access at http://localhost:80
```

### Check Logs
```bash
# Basic monitoring
docker-compose logs -f bitaxe-monitor

# Enhanced monitoring
docker-compose logs -f bitaxe-enhanced

# Web dashboard
docker-compose logs -f bitaxe-web
```