# 🚀 Bitaxe Monitor

A professional, enterprise-grade monitoring solution for Bitaxe Bitcoin miners featuring real-time data collection, robust error handling, and comprehensive visualization tools.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

### 🔌 **Real API Integration**
- Direct connection to Bitaxe miners via REST API
- Comprehensive metrics collection (32+ data points per miner)
- Smart status detection and health monitoring
- Automatic retry logic with configurable timeouts

### 🛡️ **Enterprise-Grade Reliability**
- **Robust CSV handling** with corruption prevention
- **Persistent hostname caching** for flaky network responses
- **Automatic backups** and data validation
- **Thread-safe operations** and atomic file writes
- **Self-healing system** that recovers from errors

### 📊 **Advanced Monitoring**
- **Real-time dashboard** with live updates
- **Fleet-wide statistics** and performance metrics
- **Mining efficiency calculations** (J/TH, GH/J)
- **Temperature monitoring** (ASIC + Voltage Regulator)
- **Network diagnostics** (WiFi signal, connectivity)

### 🔧 **Professional Tools**
- **CSV repair utility** for data recovery
- **Data validation** and integrity checking
- **Backup management** with automatic rotation
- **Configuration validation** and setup assistance

## 🏗️ Project Structure

```
bitaxe-monitor/
├── 📄 monitor.py          # Main launcher - start data collection
├── 📄 viewer.py           # Data viewer launcher
├── 📄 setup.py            # Setup and configuration tool
├── 📄 config.yaml         # Your configuration (created by setup)
├── 📁 src/                # Source code
│   ├── collector.py       # Enhanced data collector
│   └── cli_view.py        # Rich CLI viewer/dashboard
├── 📁 tools/              # Utilities and maintenance
│   ├── csv_repair.py      # CSV repair and recovery
│   ├── setup_improvements.py # Migration tools
│   └── collector_original_backup.py # Original version
├── 📁 docs/               # Documentation
│   └── IMPROVEMENTS.md    # Detailed improvement log
├── 📁 examples/           # Example configurations
│   └── config.yaml        # Template configuration
├── 📁 data/               # Sample and backup data
│   └── *.csv             # Sample data files
└── 📁 backups/           # Automatic backups (created at runtime)
```

## 🚀 Quick Start

### 1. **Setup**
```bash
# Clone the repository
git clone https://github.com/yourusername/bitaxe-monitor.git
cd bitaxe-monitor

# Install dependencies
pip install -r requirements.txt

# Run setup (creates config.yaml)
python setup.py
```

### 2. **Configure**
Edit `config.yaml` with your miner details:
```yaml
miners:
  - 192.168.1.45
  - 192.168.1.46
  - 192.168.1.47

poll_interval: 30           # Seconds between polls
csv_path: metrics.csv       # Data output file
timeout: 10                 # HTTP timeout
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

## 📊 Collected Metrics

### ⚡ **Core Mining Data**
| Metric | Description | Unit |
|--------|-------------|------|
| Hashrate | Current hashing performance | GH/s, TH/s |
| Temperature | ASIC and VR temperatures | °C |
| Power | Real-time consumption | Watts |
| Efficiency | Performance per watt | J/TH |
| Voltage | Input and core voltages | Volts |

### 🔍 **Advanced Diagnostics**
| Metric | Description | Purpose |
|--------|-------------|---------|
| WiFi RSSI | Signal strength | Network diagnostics |
| Share Stats | Accepted/rejected shares | Mining performance |
| Uptime | Operating time | Reliability tracking |
| Fan Control | Speed & RPM | Thermal management |
| Pool Info | Connected pool details | Mining setup |

### 🏥 **Health Monitoring**
- **🟢 Online**: Normal operation
- **🟡 Warning**: Performance issues
- **🔴 Critical**: Hardware problems
- **⚫ Offline**: Connection lost

## 🛠️ Advanced Features

### 🔧 **CSV Repair Tools**
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

### 🔄 **Backup Management**
- **Automatic backups** every 100 collection cycles
- **Backup rotation** (keeps last 10 files)
- **Manual backup tools** for data preservation
- **Recovery procedures** for data loss scenarios

### 🌐 **Network Resilience**
- **Hostname caching** survives network outages
- **Cached values** shown with `*` indicator
- **Automatic retry** with exponential backoff
- **Graceful degradation** when miners are offline

## 📈 Dashboard Features

### 🖥️ **Live Dashboard**
```bash
python viewer.py --live
```
- Real-time updates every 2 seconds
- Color-coded status indicators
- Fleet performance summary
- Individual miner details

### 📋 **Summary View**
```bash
python viewer.py --summary
```
- Quick overview of all miners
- Latest metrics and status
- Performance statistics
- Error summaries

### 🔍 **Detailed Mode**
```bash
python viewer.py --live --detailed
```
- Extended metrics display
- Additional diagnostic information
- Advanced performance indicators

## 🔧 Configuration Options

### Basic Configuration (`config.yaml`)
```yaml
# Miner IP addresses
miners:
  - 192.168.1.45
  - 192.168.1.46

# Timing settings
poll_interval: 30          # Polling frequency (seconds)
timeout: 10                # HTTP timeout (seconds)
retries: 3                 # Number of retries

# File settings
csv_path: metrics.csv      # Output file path
backup_frequency: 100      # Backup every N cycles
validate_csv: true         # Enable CSV validation

# Optional: Display names
aliases:
  - "Miner-01"
  - "Miner-02"
```

### Advanced Settings
- **Backup frequency**: Configure automatic backup intervals
- **Validation**: Enable/disable CSV integrity checking
- **Retry strategy**: Customize network retry behavior
- **File paths**: Relative or absolute path configurations

## 🐛 Troubleshooting

### Common Issues

**❌ "Connection failed" errors**
```bash
# Check miner connectivity
ping 192.168.1.45

# Verify API endpoint
curl http://192.168.1.45/api/system/info

# Check configuration
python setup.py
```

**❌ "CSV corruption detected"**
```bash
# Analyze the problem
python tools/csv_repair.py analyze metrics.csv

# Attempt repair
python tools/csv_repair.py repair metrics.csv metrics_fixed.csv
```

**❌ "No data in viewer"**
```bash
# Start data collection first
python monitor.py

# Check if CSV exists and has data
python tools/csv_repair.py stats metrics.csv
```

### Network Requirements
- ✅ Miners and monitoring computer on same network
- ✅ Port 80 (HTTP) access to miners
- ✅ Stable WiFi connection for miners
- ✅ Python 3.7+ with required packages

## 📊 Data Export & Integration

### CSV Format
The system generates CSV files with 32 columns including:
- Timestamps and miner identification
- Performance metrics (hashrate, power, efficiency)
- Thermal data (temperatures, fan control)
- Network diagnostics (WiFi, connectivity)
- Mining statistics (shares, uptime, pool info)

### Integration Options
- **Excel/Google Sheets**: Direct CSV import
- **Grafana**: Custom data source integration
- **InfluxDB**: Time series database import
- **Custom scripts**: Python pandas integration

## 🤝 Contributing

We welcome contributions! Areas for improvement:
- Additional miner model support
- Enhanced visualization features
- Database backend integration
- Web dashboard interface
- Mobile app development

### Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/bitaxe-monitor.git

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests (when available)
python -m pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Bitaxe Community** for hardware innovation
- **Python Community** for excellent libraries
- **Contributors** who helped improve reliability
- **Bitcoin Miners** worldwide for securing the network

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/bitaxe-monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/bitaxe-monitor/discussions)
- **Documentation**: See `docs/` folder for detailed guides

---

**Happy Mining!** ⛏️💎

*Monitor your Bitaxe fleet with enterprise-grade reliability and professional-quality tools.*
