# 🚀 Bitaxe Monitor

A professional monitoring solution for Bitaxe Bitcoin miners featuring real-time data collection, robust error handling, and comprehensive visualization tools.

## ✨ Key Features

### 🔌 **Real API Integration**
- Direct connection to Bitaxe miners via REST API
- Comprehensive metrics collection (32+ data points per miner)
- Smart status detection and health monitoring
- Automatic retry logic with configurable timeouts

### 🛡️ **Robust & Reliable**
- **CSV corruption prevention** with atomic writes
- **Persistent hostname caching** for flaky network responses
- **Automatic backups** and data validation
- **Thread-safe operations** and error recovery
- **Self-healing system** that recovers from errors

### 📊 **Professional Monitoring**
- **Real-time dashboard** with live updates
- **Fleet-wide statistics** and performance metrics
- **Mining efficiency calculations** (J/TH)
- **Temperature monitoring** (ASIC + VR)
- **Network diagnostics** and connectivity status

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/bitaxe-monitor.git
cd bitaxe-monitor

# Install dependencies
pip install -r requirements.txt
```

### 2. **Setup Configuration**
```bash
# Run setup to create config.yaml
python setup.py
```
This creates `config.yaml` in the project root. Edit it with your miner IP addresses:

```yaml
miners:
  - 192.168.1.45
  - 192.168.1.46
  - 192.168.1.47

poll_interval: 30
csv_path: metrics.csv
timeout: 10
```

### 3. **Start Monitoring**
```bash
# Start data collection
python monitor.py

# View live dashboard (in another terminal)
python viewer.py --live

# View summary
python viewer.py --summary
```

## 📁 Project Structure

```
bitaxe-monitor/
├── monitor.py          # Main launcher - start data collection
├── viewer.py           # Data viewer - live dashboard and summaries
├── setup.py            # Setup tool - creates config.yaml
├── config.yaml         # Your configuration (created by setup.py)
├── metrics.csv         # Data output (created when monitoring starts)
├── hostname_cache.json # Hostname cache (created automatically)
├── src/                # Source code
│   ├── collector.py    # Data collector engine
│   └── cli_view.py     # CLI viewer/dashboard
├── tools/              # Utilities and maintenance
│   ├── csv_repair.py   # CSV repair and recovery tools
│   └── setup_improvements.py # Migration utilities
├── examples/           # Example configurations and templates
├── docs/               # Documentation
├── data/               # Sample data files
└── backups/            # Automatic backups (created at runtime)
```

## 📊 Collected Metrics

### Core Performance Data
- **Hashrate**: Current performance (GH/s, TH/s)
- **Temperature**: ASIC and voltage regulator temperatures
- **Power**: Real-time consumption (Watts)
- **Efficiency**: Performance per watt (J/TH)
- **Voltage**: Input and core voltages

### Mining Statistics
- **Shares**: Accepted and rejected share counts
- **Uptime**: Operating time tracking
- **Pool Info**: Connected pool details
- **Best Difficulty**: Highest difficulty achieved

### System Health
- **WiFi Signal**: RSSI strength monitoring
- **Fan Control**: Speed and RPM tracking
- **Status**: Comprehensive health assessment
- **Network**: Connectivity diagnostics

## 🔍 Status Indicators

The monitor provides intelligent status detection:

- **🟢 ONLINE**: Normal operation
- **🟡 NO HASH**: Zero hashrate detected  
- **🔴 HOT**: Overheating (>85°C)
- **🟠 WIFI**: WiFi connectivity issues
- **🔴 REJECT**: High share rejection rate (>10%)
- **🔴 TIMEOUT**: API request timeout
- **🔴 OFFLINE**: Connection failed

## 🖥️ Dashboard Features

### Live Dashboard (`python viewer.py --live`)
- Real-time updates every 2 seconds
- Color-coded status indicators  
- Fleet performance summary
- Individual miner details

### Summary View (`python viewer.py --summary`)
- Quick overview of all miners
- Latest metrics and status
- Performance statistics
- Fleet totals and averages

### Detailed Mode (`python viewer.py --summary --detailed`)
- Extended metrics display
- Additional diagnostic information
- Advanced performance indicators

## 🔧 Advanced Tools

### CSV Repair Utility
```bash
# Analyze file for corruption
python tools/csv_repair.py analyze metrics.csv

# Repair corrupted data
python tools/csv_repair.py repair corrupted_file.csv

# Get detailed statistics  
python tools/csv_repair.py stats metrics.csv

# Merge multiple files
python tools/csv_repair.py merge output.csv file1.csv file2.csv
```

### Backup Management
- **Automatic backups** every 100 collection cycles
- **Backup rotation** (keeps last 10 files)
- **Manual backup tools** for data preservation
- **Recovery procedures** for data loss scenarios

## ⚙️ Configuration

The `config.yaml` file (created by `python setup.py`) contains:

```yaml
# Miner IP addresses to monitor
miners:
  - 192.168.1.45
  - 192.168.1.46

# Polling settings
poll_interval: 30          # Seconds between polls
timeout: 10                # HTTP timeout
retries: 3                 # Number of retries

# File settings  
csv_path: metrics.csv      # Output file
backup_frequency: 100      # Backup every N cycles
validate_csv: true         # Enable validation

# Optional: Display names
aliases:
  - "Miner-01"
  - "Miner-02"
```

## 🐛 Troubleshooting

### Common Issues

**❌ "Connection failed" errors**
- Check miner IP addresses in `config.yaml`
- Verify miners are powered on and connected to WiFi
- Test connectivity: `ping 192.168.1.45`

**❌ "config.yaml not found"**
- Run `python setup.py` to create configuration file
- Edit the created `config.yaml` with your miner IPs

**❌ "No data in viewer"**
- Start data collection first: `python monitor.py`
- Let it run for a few cycles to generate data
- Check if `metrics.csv` exists and has data

**❌ CSV corruption detected**
- Use repair tools: `python tools/csv_repair.py analyze metrics.csv`
- Automatic backups available in `backups/` directory

### Network Requirements
- Miners and monitoring computer on same network
- Port 80 (HTTP) access to miners  
- Stable WiFi connection for miners
- Python 3.7+ with required packages

## 📈 Data Export

### CSV Format
Generated CSV files contain timestamped records with:
- Basic metrics (hashrate, temperature, power)
- Extended data (voltages, frequencies, efficiency)
- Mining stats (shares, uptime, pool info)
- System health (WiFi, fan, status)

### Integration
- **Excel/Sheets**: Direct CSV import
- **Grafana**: Custom data source
- **Python**: pandas DataFrame compatible
- **Custom apps**: Standard CSV format

## 🔄 Upgrades

### From Previous Versions
```bash
# Backup existing data
python tools/csv_repair.py stats old_metrics.csv

# Run new setup  
python setup.py

# Migrate configuration as needed
# Old data files are automatically compatible
```

## 🤝 Contributing

We welcome contributions! Areas for improvement:
- Additional miner model support
- Enhanced visualization features  
- Database integration
- Web interface development

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Support

- **Issues**: GitHub Issues for bug reports
- **Documentation**: See `docs/` folder
- **Examples**: Check `examples/` directory

---

**Start monitoring: `python setup.py` → `python monitor.py` → `python viewer.py --live`**
