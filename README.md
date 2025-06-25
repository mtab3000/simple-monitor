# ⚡ Bitaxe Gamma Monitor

<div align="center">

A **beautiful, real-time monitoring solution** for Bitaxe Gamma mining devices with professional-grade visualization, comprehensive fleet management, and **advanced mining optimization analytics**.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)
[![Tests](https://img.shields.io/badge/tests-146%20passing-brightgreen.svg)](tests/)
[![Code Quality](https://img.shields.io/badge/code%20quality-pylint-yellow.svg)](.pylintrc)
[![Security](https://img.shields.io/badge/security-CodeQL-purple.svg)](.github/workflows/codeql.yml)
[![Mining Optimization](https://img.shields.io/badge/optimization-sweet%20spot%20analysis-orange.svg)](src/optimization_analyzer.py)

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🎬 Quick Demo](#-quick-demo)
- [🚀 Quick Start](#-quick-start)
- [📖 Usage](#-usage)
- [📊 Dashboard Features](#-dashboard-features)
- [🎯 Mining Optimization Analyzer](#-mining-optimization-analyzer)
- [🔧 Advanced Configuration](#-advanced-configuration)
- [🛠️ Development](#-development)
- [📋 Requirements](#-requirements)
- [🐛 Troubleshooting](#-troubleshooting)
- [🔍 Quality Assurance](#-quality-assurance)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎯 **Real-time Monitoring**
- **Live dashboard** with auto-refresh every 5 seconds
- **Fleet overview** with health indicators and progress bars
- **Individual miner panels** with detailed metrics
- **Temperature monitoring** with overheating warnings
- **Performance tracking** with visual progress indicators

### ⚡ **Comprehensive Metrics**
- **Hashrate performance** with percentage of expected
- **Power consumption** and efficiency (J/TH) ratings
- **Voltage monitoring** (set, actual, device voltages)
- **Frequency settings** and overclock status
- **Temperature readings** (ASIC and VR temperatures)
- **Network connectivity** (WiFi signal strength)
- **System status** (fan speed, memory, uptime)
- **Mining statistics** (shares accepted/rejected, rejection rate)

### 🎯 **Mining Optimization** ⭐ **NEW**
- 🎯 **Sweet spot detection** for optimal voltage/frequency combinations
- 📊 **Benchmarking session detection** for automatic testing periods  
- 📈 **Stability scoring** using coefficient of variation analysis
- 🏆 **Performance rankings** with comprehensive comparison charts
- 💡 **Actionable recommendations** for optimal mining settings
- 📉 **Statistical analysis** of hashrate, efficiency, and temperature metrics
- ⚖️ **Advanced scoring algorithm** balancing performance vs stability
- 💾 **JSON export** for detailed analysis and historical tracking

</td>
<td width="50%">

### 🎨 **Beautiful Interface**
- **Web dashboard** with responsive design and real-time updates  
- **Terminal interface** with Unicode icons and color-coded status indicators
- **Progress bars** for visual performance assessment
- **Professional tables** with proper alignment
- **Fleet health ratings** with emoji indicators
- **Real-time timestamps** and graceful error handling

### 🏗️ **Enterprise Ready**
- 🐳 **Docker containerization** with docker-compose orchestration
- 🗄️ **Advanced database system** with SQLite for performance analytics
- 🔮 **Predictive analytics** with anomaly detection and maintenance alerts
- 🧪 **Comprehensive test suite** with 146+ tests and high coverage
- 🔄 **CI/CD pipeline** with automated code quality checks
- 🔒 **Security analysis** with CodeQL integration
- 💾 **Persistent data storage** with automatic backups
- 🛡️ **Robust error handling** and connection retry logic
- 🌐 **Hostname caching** for network resilience
- 📊 **CSV data export** for historical analysis

</td>
</tr>
</table>

## 🎬 Quick Demo

```bash
# 🔥 Start monitoring your Bitaxe fleet in 30 seconds
git clone https://github.com/mtab3000/simple-monitor.git
cd simple-monitor && cp examples/config.example.yaml config.yaml
# Edit config.yaml with your Bitaxe IPs, then:
docker-compose up -d
docker-compose exec bitaxe-monitor python viewer.py --live

# 🎯 Analyze mining optimization (NEW!)
PYTHONIOENCODING=utf-8 python src/optimization_analyzer.py --hours 24 --show-chart
```

---

## 🚀 Quick Start

### 🐳 Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mtab3000/simple-monitor.git
   cd simple-monitor
   ```

2. **Create your configuration:**
   ```bash
   cp examples/config.example.yaml config.yaml
   # Edit config.yaml with your Bitaxe IP addresses
   ```

3. **Start with Docker Compose:**
   ```bash
   # 🚀 ENHANCED MONITORING (DEFAULT - RECOMMENDED)
   # Includes: Advanced analytics, database, web dashboard, optimization analysis
   docker-compose up -d
   
   # 🔧 Basic monitoring only (minimal setup)
   docker-compose --profile basic up -d
   ```

4. **Access your dashboards:**
   ```bash
   # 🌐 Web Dashboard (DEFAULT)
   # Open http://localhost:80 in your browser
   
   # 📊 Terminal Dashboard
   docker-compose exec bitaxe-enhanced python viewer.py --live
   
   # 🎯 Mining Optimization Analysis
   docker-compose exec bitaxe-enhanced python src/optimization_analyzer.py --hours 24 --show-chart
   ```

### Manual Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your miners:**
   ```bash
   cp examples/config.example.yaml config.yaml
   # Edit config.yaml with your settings
   ```

3. **Start monitoring:**
   ```bash
   python monitor.py
   ```

4. **View the dashboard:**
   ```bash
   # Terminal interface
   python viewer.py --live
   
   # Enhanced monitoring with database and analytics
   python enhanced_monitor.py
   
   # Web interface (recommended)
   python web_dashboard.py
   ```

## 📖 Usage

### Configuration

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

### Viewing Options

**Live Dashboard (Recommended):**
```bash
python viewer.py --live
```

**Detailed View with Individual Panels:**
```bash
python viewer.py --live --detailed
```

**Static Summary:**
```bash
python viewer.py --summary
```

**Static Detailed Summary:**
```bash
python viewer.py --summary --detailed
```

### Enhanced Monitoring with Database & Analytics

**Start enhanced monitoring:**
```bash
python enhanced_monitor.py
```

**Database migration from CSV:**
```bash
python src/data_migration.py --action migrate
```

**Enhanced Features:**
- **SQLite database** for advanced data storage and analysis
- **Performance scoring** with A+ to F grades based on multiple factors
- **Anomaly detection** using statistical analysis
- **Predictive maintenance** alerts based on performance trends
- **Growth metrics** with trend analysis over time
- **Fleet analytics** with comparative performance insights
- **Automated alerts** for temperature, hashrate, and efficiency issues
- **Historical analysis** with hourly and daily aggregations

**See [Database & Analytics Documentation](docs/DATABASE_ANALYTICS.md) for detailed information.**

### Web Dashboard

**Start the web interface:**
```bash
python web_dashboard.py
```

**Custom host/port:**
```bash
python web_dashboard.py --host 0.0.0.0 --port 80
```

**Web Features:**
- **Responsive design** works on desktop, tablet, and mobile
- **Real-time updates** every 5 seconds
- **Fleet overview** with total statistics
- **Individual miner cards** with detailed metrics
- **Auto-refresh toggle** for manual control
- **REST API endpoints** for integration

### Mining Optimization Analysis

**Analyze voltage/frequency combinations for sweet spots:**
```bash
# Analyze voltage/frequency combinations for sweet spots
python src/optimization_analyzer.py --hours 24 --show-chart

# Analyze specific miner performance
python src/optimization_analyzer.py --miner-ip 192.168.1.45 --hours 48

# Export detailed analysis results  
python src/optimization_analyzer.py --hours 168 --output weekly_optimization.json

# Custom CSV path and time window
python src/optimization_analyzer.py --csv-path custom_metrics.csv --hours 72 --show-chart
```

### 🎯 **Advanced Optimization Analysis**

**Comprehensive sweet spot detection:**
```bash
# 📈 Weekly optimization analysis with detailed reporting
python src/optimization_analyzer.py --hours 168 --show-chart --output weekly_analysis.json

# 🎯 Miner-specific optimization (replace IP)
python src/optimization_analyzer.py --miner-ip 192.168.1.45 --hours 48 --detailed

# 📉 Performance comparison across fleet
python src/optimization_analyzer.py --hours 72 --compare-miners --export-csv

# 🔥 Real-time optimization monitoring
watch -n 300 'python src/optimization_analyzer.py --hours 6 --quick-summary'
```

**Understanding the analysis:**
```bash
# 🎢 Sweet Spot Algorithm Explanation:
# - Performance Score: Hashrate (40%) + Efficiency (30%) + Temperature (20%) + Power Ratio (10%)
# - Stability Score: Hashrate CV (50%) + Temp StdDev (30%) + Efficiency StdDev (20%)
# - Sweet Spot = Performance Score ÷ (1 + Stability Score/100)

# 📊 Benchmark Detection:
# - Automatically identifies testing sessions with 5+ voltage/frequency combinations
# - Analyzes 30-minute windows for optimal setting discovery
# - Provides stability metrics using coefficient of variation
```
### 🐳 Docker Commands

## 🚀 **Enhanced Monitoring Stack (DEFAULT)**

**Start complete monitoring solution:**
```bash
# 🎆 Full stack: Enhanced monitoring + Web dashboard + Analytics
docker-compose up -d

# 🔍 View all running services
docker-compose ps
```

**Access your monitoring:**
```bash
# 🌐 Web Dashboard (Primary Interface)
# Open http://localhost:80 in your browser

# 📊 Live Terminal Dashboard
docker-compose exec bitaxe-enhanced python viewer.py --live --detailed

# 🎯 Mining Optimization Analysis
docker-compose exec bitaxe-enhanced python src/optimization_analyzer.py --hours 24 --show-chart

# 📈 Database Analytics
docker-compose exec bitaxe-enhanced python src/analytics.py --report
```

## 🔧 **Minimal Setup (Basic Monitoring)**

**For resource-constrained environments:**
```bash
# Basic CSV-only monitoring
docker-compose --profile basic up -d

# Access basic monitoring
docker-compose exec bitaxe-monitor python viewer.py --live
```

## 🔍 **Service Management**

**Check service status:**
```bash
# View running containers
docker-compose ps

# Check service health
docker-compose exec bitaxe-enhanced python -c "import src.database; print('Database OK')"
```

**View logs:**
```bash
# Enhanced monitoring logs
docker-compose logs -f bitaxe-enhanced

# Web dashboard logs
docker-compose logs -f bitaxe-web

# All services
docker-compose logs -f
```

**Restart services:**
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart bitaxe-enhanced
docker-compose restart bitaxe-web
```

**Stop services:**
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: Deletes data)
docker-compose down -v
```

## 💾 **Data Management**

**Backup operations:**
```bash
# Manual backup
docker-compose exec bitaxe-enhanced python src/database.py --backup

# Export data
docker-compose exec bitaxe-enhanced python src/analytics.py --export-csv

# Access backup files
ls -la backups/
```

**Database operations:**
```bash
# Database migration from CSV
docker-compose exec bitaxe-enhanced python src/data_migration.py --action migrate

# Database integrity check
docker-compose exec bitaxe-enhanced python src/database.py --check-integrity

# View database stats
docker-compose exec bitaxe-enhanced python src/analytics.py --stats
```

## 🌐 **Web Dashboard API & Features**

### 🚀 **REST API Endpoints**

**Real-time data access:**
```bash
# Current miner status
curl http://localhost:80/api/status | jq

# Fleet statistics
curl http://localhost:80/api/fleet | jq

# Historical data (last 24 hours)
curl "http://localhost:80/api/history?hours=24" | jq

# Custom time range (last week)
curl "http://localhost:80/api/history?hours=168" | jq
```

**API Response examples:**
```json
// /api/status response
{
  "success": true,
  "data": {
    "miners": [
      {
        "ip": "192.168.1.45",
        "hostname": "bitaxe-001",
        "status": "online",
        "hashrate_ghs": 934.5,
        "expected_hashrate_ghs": 934.3,
        "hashrate_ratio_percent": 100.02,
        "temp_asic_c": 59.8,
        "temp_vr_c": 52.1,
        "power_w": 14.1,
        "efficiency_j_th": 15.1,
        "voltage_asic_actual_v": 0.981,
        "frequency_set_mhz": 458,
        "shares_accepted": 2847,
        "shares_rejected": 2,
        "rejection_rate_percent": 0.07,
        "wifi_rssi": -52,
        "uptime_hours": 12.4
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00"
}

// /api/fleet response
{
  "success": true,
  "data": {
    "total_miners": 3,
    "online_miners": 3,
    "offline_miners": 0,
    "total_hashrate_ghs": 2803.7,
    "total_power_w": 42.3,
    "average_efficiency_j_th": 15.08,
    "average_temp_c": 59.2,
    "total_shares_accepted": 8541,
    "total_shares_rejected": 7,
    "fleet_rejection_rate_percent": 0.082
  }
}
```

### 📋 **Web Dashboard Features**

**Professional monitoring interface:**
- 📊 **Real-time updates** every 5 seconds with auto-refresh
- 📈 **Fleet overview** with comprehensive statistics and health indicators
- 💰 **Individual miner cards** with detailed performance metrics
- 📱 **Responsive design** optimized for desktop, tablet, and mobile
- 🎨 **Visual indicators** with color-coded status and progress bars
- 🔄 **Auto-refresh toggle** for manual control and reduced bandwidth
- 🔗 **Deep linking** to specific miners and time ranges
- 📏 **CSV export** functionality for historical analysis

**Advanced visualizations:**
- 📉 **Performance trends** with hashrate and efficiency graphs
- 🌡️ **Temperature monitoring** with overheating alerts
- ⚡ **Power consumption** tracking and efficiency ratings
- 📆 **Share statistics** with acceptance/rejection rates
- 📡 **Network status** including WiFi signal strength
- 🕰️ **Uptime tracking** and availability metrics

## 📊 **Enhanced Analytics & Database Features**

### 📈 **Advanced Database Analytics**

**Automated performance analysis:**
```bash
# 🏆 Performance scoring (A+ to F grades)
python src/analytics.py --performance-report

# 🔍 Anomaly detection
python src/analytics.py --anomaly-detection --hours 24

# 🔮 Predictive maintenance alerts
python src/analytics.py --predictive-analysis

# 📈 Growth metrics and trends
python src/analytics.py --growth-analysis --days 7

# 🏢 Fleet analytics with comparative insights
python src/analytics.py --fleet-comparison
```

**Database features:**
- 💾 **SQLite database** for advanced data storage and querying
- 📅 **Automated hourly and daily aggregations** for trend analysis
- 🔄 **Automatic backup system** with configurable retention
- 📊 **Statistical analysis** with moving averages and variance calculations
- 🚨 **Alert system** for temperature, hashrate, and efficiency issues
- 📈 **Performance scoring** based on multiple weighted factors
- 🔍 **Anomaly detection** using statistical deviation analysis

### 🏆 **Fleet Dashboard**
- **Health Overview:** Visual fleet status with progress bars
- **Performance Metrics:** Total hashrate, power consumption, efficiency ratings
- **Temperature Monitoring:** Average ASIC and VR temperatures
- **Mining Statistics:** Shares accepted/rejected, rejection rates

### 💻 **Individual Miner Panels**
- **Performance Bars:** Visual hashrate percentage indicators
- **Comprehensive Metrics:** All voltage readings, frequency settings, power consumption
- **System Status:** Fan speed, memory usage, WiFi signal, uptime
- **Mining Stats:** Share statistics and best session difficulty

### Status Indicators
- 🟢 **Online:** Miner operating normally
- ⚠️ **No Hash:** Hashrate issues detected
- 🔥 **Overheating:** Temperature warnings
- 📶 **WiFi Issues:** Network connectivity problems
- ❌ **Rejected Shares:** High rejection rate alerts
- ⏰ **Timeout:** Connection timeouts
- 🔴 **Offline:** Miner unreachable

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Set UTF-8 encoding (handled automatically in Docker)
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Data Storage
- **CSV Data:** Stored in `metrics.csv` for historical analysis
- **Backups:** Automatic backups in `backups/` directory
- **Cache:** Hostname cache in `hostname_cache.json`
- **Persistence:** All data persisted between Docker restarts

### Customization
- Modify `poll_interval` for different update frequencies
- Adjust `expected_hashrate_ghs` for accurate performance monitoring
- Configure `timeout` and `retries` for network reliability

## 🛠️ Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py

# Run monitoring
python monitor.py

# View dashboard
python viewer.py --live
```

### Testing & Code Quality

**Run the complete test suite:**
```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run specific modules
pytest tests/test_database.py     # Database tests
pytest tests/test_analytics.py    # Analytics tests
pytest tests/test_web_server.py   # Web server tests

# Generate HTML coverage report
pytest --cov-report=html
```

**Code quality checks:**
```bash
# Run pylint code analysis
pylint src/

# Check for security issues (requires CodeQL CLI)
codeql database analyze
```

**Continuous Integration:**
- **Unit Tests:** Automated testing on push/PR across Python 3.8-3.11
- **Pylint:** Automated code quality checks on push/PR
- **CodeQL:** Security analysis runs weekly and on push
- **Test Coverage:** Minimum 80% coverage enforced with coverage reports

## 🎯 Mining Optimization Analyzer

<div align="center">

### 🚀 **The Ultimate Sweet Spot Finder for Bitaxe Mining** 🚀

*Automatically discover optimal voltage/frequency combinations that maximize both performance and stability*

[![Optimization](https://img.shields.io/badge/Algorithm-Sweet%20Spot%20Detection-orange.svg)](src/optimization_analyzer.py)
[![Tests](https://img.shields.io/badge/Tests-146%20Passing-brightgreen.svg)](tests/test_optimization_analyzer.py)
[![Analysis](https://img.shields.io/badge/Analysis-Statistical%20Methods-blue.svg)](README.md#sweet-spot-algorithm)

</div>

---

### 🔥 **Key Features**

<table>
<tr>
<td width="50%">

#### 🎯 **Smart Detection**
- 🎯 **Sweet Spot Discovery** - Find optimal voltage/frequency balance
- 🔍 **Benchmark Detection** - Auto-identifies testing sessions  
- 📊 **Statistical Analysis** - Uses coefficient of variation
- 🏆 **Performance Ranking** - Ranks all combinations

</td>
<td width="50%">

#### 💡 **Intelligent Analysis** 
- 📈 **Stability Scoring** - Measures hashrate consistency
- 🌡️ **Temperature Monitoring** - Thermal analysis & warnings
- ⚡ **Efficiency Metrics** - J/TH optimization tracking
- 📋 **Smart Recommendations** - Actionable improvement suggestions

</td>
</tr>
</table>

### 🧮 **Sweet Spot Algorithm**

<div align="center">

**🎯 Advanced multi-factor scoring system balancing performance with stability**

</div>

<table>
<tr>
<td width="33%">

#### 🚀 **Performance Score**
*Higher = Better*

```
📈 Hashrate (40%)
   └─ Higher average preferred

⚡ Efficiency (30%) 
   └─ Lower J/TH preferred

🌡️ Temperature (20%)
   └─ Lower temps preferred  

💪 Power Ratio (10%)
   └─ GH/s per watt
```

</td>
<td width="33%">

#### 📊 **Stability Score**  
*Lower = Better*

```
📈 Hashrate CV (50%)
   └─ Coefficient of variation

🌡️ Temp StdDev (30%)
   └─ Temperature consistency

⚡ Eff StdDev (20%)
   └─ Efficiency variation
```

</td>
<td width="34%">

#### 🎯 **Sweet Spot Formula**

```
🏆 Sweet Spot Score = 
   Performance Score ÷ 
   (1 + Stability Score/100)
```

**Perfect Balance:**
- High performance ✅
- Low variation ✅  
- Optimal efficiency ✅

</td>
</tr>
</table>

### 📊 **Analysis Output**

<div align="center">

**📈 Comprehensive reporting with actionable insights**

</div>

<table>
<tr>
<td width="50%">

#### 🏆 **Performance Reports**
- 📊 **Ranked Settings** by sweet spot score
- 📈 **Statistical Metrics** for each combination  
- 📋 **Visual Charts** in beautiful text format
- 🎯 **Optimal Ranges** for voltage/frequency
- 🔍 **Benchmark Detection** with detailed analysis

</td>
<td width="50%">

#### 💾 **Export & Integration**
- 📄 **JSON Export** for detailed analysis
- 📊 **CSV Compatibility** with existing data
- 🔗 **API Ready** for automation
- 📱 **Human Readable** summary reports
- ⚡ **Real-time Analysis** on live data

</td>
</tr>
</table>

---

### 🚀 **Usage Examples**

#### 🎯 **Quick Analysis**
```bash
# 📊 Basic analysis with beautiful comparison chart
PYTHONIOENCODING=utf-8 python src/optimization_analyzer.py --hours 24 --show-chart
```

#### 🔍 **Targeted Analysis**  
```bash
# 🎯 Weekly analysis for specific miner
python src/optimization_analyzer.py --miner-ip 192.168.1.45 --hours 168 --output miner_analysis.json

# 📁 Custom data source analysis  
python src/optimization_analyzer.py --csv-path backup_metrics.csv --hours 48
```

#### 📈 **Sample Output**
```
🔍 Analyzing mining optimization data...
   Time window: 24 hours
   Data source: metrics.csv

📈 ANALYSIS SUMMARY
   Miners analyzed: 3
   Settings tested: 3
   Optimal settings found: 3

🏆 TOP OPTIMAL SETTINGS:
   1. 1.003V @ 463MHz
      Score: 375.59, Hashrate: 952.2 GH/s
      Stability: 5.2, Efficiency: 15.1 J/TH

📊 VOLTAGE/FREQUENCY PERFORMANCE COMPARISON
======================================================================
Rank Voltage  Freq    Score   Hashrate   Efficiency Stability
----------------------------------------------------------------------
1    1.003V   463MHz  375.59  952.2 GH/s 15.1 J/TH  5.2      
2    1.003V   458MHz  370.41  941.6 GH/s 15.0 J/TH  5.5      
3    1.027V   452MHz  353.36  894.5 GH/s 15.0 J/TH  5.3      
======================================================================
💡 Lower stability score is better (less variation)
🎯 Higher sweet spot score indicates optimal balance
```

### File Structure
```
simple-monitor/
├── .github/
│   └── workflows/        # CI/CD workflows
│       ├── pylint.yml   # Code quality checks
│       └── codeql.yml   # Security analysis
├── src/
│   ├── collector.py      # Data collection and CSV handling
│   ├── cli_view.py       # Dashboard and visualization
│   ├── database.py       # SQLite database management
│   ├── analytics.py      # Performance analysis and predictions
│   ├── enhanced_collector.py # Enhanced monitoring with analytics
│   ├── data_migration.py # CSV to database migration tool
│   ├── web_server.py     # Web server and API endpoints
│   └── optimization_analyzer.py # Mining optimization analysis
├── docs/
│   └── DATABASE_ANALYTICS.md # Database and analytics documentation
├── web/
│   ├── templates/        # HTML templates
│   │   └── dashboard.html
│   └── static/          # CSS and JavaScript
│       ├── css/dashboard.css
│       └── js/dashboard.js
├── tests/
│   ├── __init__.py      # Test package initialization
│   ├── test_collector.py # Unit tests for collector
│   ├── test_cli_view.py # Unit tests for CLI viewer
│   ├── test_database.py # Unit tests for database module
│   ├── test_analytics.py # Unit tests for analytics module
│   ├── test_web_server.py # Unit tests for web server module
│   └── test_optimization_analyzer.py # Tests for optimization analyzer
├── examples/
│   └── config.example.yaml # Example configuration
├── data/                 # Runtime data directory
├── backups/             # Automatic backups
├── .gitignore          # Git ignore rules
├── .gitattributes      # Git attributes
├── .pylintrc          # Pylint configuration
├── pytest.ini        # Pytest configuration
├── docker-compose.yml # Docker orchestration
├── Dockerfile        # Container definition
├── requirements.txt  # Python dependencies
├── LICENSE          # MIT license
├── README.md       # This documentation
├── monitor.py     # Main monitoring script
├── enhanced_monitor.py # Enhanced monitoring with database
├── viewer.py     # Terminal dashboard launcher
├── web_dashboard.py # Web dashboard launcher
└── setup.py     # Installation and setup
```

## 📋 Requirements

### System Requirements
- **Python 3.8+**
- **Network access** to Bitaxe devices
- **UTF-8 terminal support** for Unicode display

### Python Dependencies

**Production:**
- `requests>=2.28.0` - HTTP client for API calls
- `PyYAML>=6.0` - Configuration file parsing
- `rich>=12.0.0` - Beautiful terminal interface
- `urllib3>=1.26.0` - HTTP library
- `Flask>=2.3.0` - Web interface framework

**Development & Testing:**
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Code coverage reporting
- `pylint>=2.15.0` - Code quality analyzer

### Hardware Requirements
- **RAM:** 100MB+ for data storage and processing
- **Storage:** 10MB+ for CSV data and backups
- **Network:** LAN access to Bitaxe devices

## 🐛 Troubleshooting

<div align="center">

**🔧 Quick fixes for common issues**

</div>

<table>
<tr>
<td width="50%">

### 🔤 **Unicode Display Issues**
```bash
# 🌐 Set proper encoding
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8

# For optimization analyzer
PYTHONIOENCODING=utf-8 python src/optimization_analyzer.py
```

### 🌐 **Connection Problems**
```bash
# ✅ Check network connectivity
ping 192.168.1.45

# ⚙️ Increase timeout in config.yaml
timeout: 30

# 🔍 Verify miner IPs are correct
```

</td>
<td width="50%">

### 🐳 **Docker Issues**
```bash
# 🔒 Fix permission issues
sudo chown -R $USER:$USER data/ backups/

# 📋 Check container logs
docker-compose logs -f bitaxe-monitor

# 🔄 Restart services
docker-compose restart
```

### 💾 **Data Issues**
```bash
# 📁 Check backup directory
ls -la backups/

# 🔧 Manual CSV repair (if needed)
python src/collector.py --validate-csv
```

</td>
</tr>
</table>

### 📊 **Optimization Analyzer Issues**

| Problem | Solution |
|---------|----------|
| 🚫 No data found | Check CSV path with `--csv-path` parameter |
| 📉 No benchmark sessions | Need 5+ different voltage/frequency combinations in 30min window |
| 🔢 Import errors | Install: `sudo apt install python3-pandas python3-numpy` |
| 🎯 Poor recommendations | Collect more data with varied settings |

## 🔒 Security

### Security Features

✅ **Code Security:**
- **CodeQL static analysis** in CI/CD pipeline
- **Dependabot** for automated dependency updates  
- **No hardcoded secrets** or credentials
- **Input validation** on all user inputs

✅ **Container Security:**
- **Non-root user** execution in Docker containers
- **Minimal attack surface** with slim base images
- **Security scanning** with Trivy vulnerability scanner
- **Proper file permissions** and isolation

✅ **Network Security:**
- **Local-only access** by default (no cloud dependencies)
- **Configurable network bindings** for web interface
- **Optional network isolation** with Docker networks
- **No unnecessary port exposures**

✅ **Data Protection:**
- **Local data storage** (no external data transmission)
- **Configurable data retention** policies
- **Automatic backup** capabilities
- **SQLite database** with file-level permissions

### Security Best Practices

**For Users:**
```bash
# Use firewall to restrict access to monitoring ports
sudo ufw allow from 192.168.1.0/24 to any port 80

# Run with minimal permissions
sudo chown -R $USER:$USER data/ backups/

# Use secure networks for Bitaxe devices
# Change default passwords on miners
# Keep monitoring software updated
```

**For Production Deployments:**
```bash
# Use reverse proxy with SSL/TLS
# Configure network-level access controls  
# Consider VPN access for remote monitoring
# Regular security updates via Dependabot
```

### Vulnerability Reporting

🚨 **Found a security issue?** Please report it responsibly:
- Use [GitHub Security Advisories](https://github.com/mtab3000/simple-monitor/security/advisories)
- **DO NOT** disclose publicly until addressed
- See our [Security Policy](SECURITY.md) for details

## 🔍 Quality Assurance

### Automated Testing
- **Comprehensive test suite** with unit and integration tests
- **Code coverage** tracking with minimum 80% requirement
- **Continuous testing** on multiple Python versions (3.8-3.11)
- **Test categories:** Unit tests, integration tests, edge case testing

### Code Quality
- **Pylint integration** with custom configuration
- **Automatic formatting** standards enforcement
- **Import optimization** and code organization
- **Docstring requirements** for all public functions

### Security & Compliance
- **CodeQL analysis** for vulnerability detection
- **Dependency scanning** for known security issues
- **Automated security updates** via GitHub workflows
- **MIT license** compliance and attribution

### CI/CD Pipeline
- **GitHub Actions** workflows for automation
- **Multi-platform testing** (Ubuntu, Windows, macOS compatible)
- **Automated unit testing** with 146+ comprehensive tests
- **Automated code review** with quality gates
- **Release automation** with proper versioning

## 🤝 Contributing

1. **Fork the repository** and clone your fork
2. **Create a feature branch:** `git checkout -b feature-name`
3. **Install development dependencies:** `pip install -r requirements.txt`
4. **Make your changes** following the existing code style
5. **Write tests** for new functionality (maintain 80%+ coverage)
6. **Run the test suite:** `pytest` (ensure all tests pass)
7. **Check code quality:** `pylint src/` (address any issues)
8. **Commit with descriptive messages** using conventional commit format
9. **Push to your fork** and submit a pull request

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Write comprehensive docstrings for all functions
- Add unit tests for new features and bug fixes
- Ensure backward compatibility when possible
- Update documentation for user-facing changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Bitaxe Community** for the amazing open-source mining hardware
- **Rich Library** for beautiful terminal interfaces
- **Python Community** for excellent tooling and libraries

---

<div align="center">

## 🎉 **Happy Mining!** 🎉

<table>
<tr>
<td align="center">
<img src="https://img.shields.io/badge/⚡-Bitaxe%20Optimized-orange?style=for-the-badge" />
</td>
<td align="center">
<img src="https://img.shields.io/badge/🎯-Sweet%20Spot%20Finder-brightgreen?style=for-the-badge" />
</td>
<td align="center">
<img src="https://img.shields.io/badge/🚀-Production%20Ready-blue?style=for-the-badge" />
</td>
</tr>
</table>

### 🔗 **Links & Support**

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/mtab3000/simple-monitor)
[![Issues](https://img.shields.io/badge/Support-Issues-red?style=for-the-badge&logo=github)](https://github.com/mtab3000/simple-monitor/issues)
[![Docs](https://img.shields.io/badge/Docs-README-blue?style=for-the-badge&logo=markdown)](README.md)

**Built with ❤️ for the Bitaxe community**

*Optimize your mining. Maximize your profits. Mine smarter, not harder.*

---

<sub>
🤖 Enhanced with advanced optimization analytics | 
📊 146+ comprehensive tests | 
🔒 Enterprise security | 
⚡ Real-time monitoring
</sub>

</div>