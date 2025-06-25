# ⚡ Bitaxe Gamma Monitor

A beautiful, real-time monitoring solution for Bitaxe Gamma mining devices with professional-grade visualization and comprehensive fleet management.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Tests](https://img.shields.io/badge/tests-pytest-green.svg)
![Code Quality](https://img.shields.io/badge/code%20quality-pylint-yellow.svg)
![Security](https://img.shields.io/badge/security-CodeQL-purple.svg)

## ✨ Features

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

### 🎨 **Beautiful Interface**
- **Web dashboard** with responsive design and real-time updates
- **Terminal interface** with Unicode icons and color-coded status indicators
- **Progress bars** for visual performance assessment
- **Professional tables** with proper alignment
- **Fleet health ratings** with emoji indicators
- **Real-time timestamps** and graceful error handling

### 🏗️ **Enterprise Ready**
- **Docker containerization** with docker-compose orchestration
- **Comprehensive test suite** with 80%+ code coverage
- **CI/CD pipeline** with automated code quality checks
- **Security analysis** with CodeQL integration
- **Persistent data storage** with automatic backups
- **Robust error handling** and connection retry logic
- **Hostname caching** for network resilience
- **CSV data export** for historical analysis

## 🚀 Quick Start

### Using Docker (Recommended)

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
   docker-compose up -d
   ```

4. **View the monitoring dashboard:**
   ```bash
   docker-compose exec bitaxe-monitor python viewer.py --live
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

### Web Dashboard

**Start the web interface:**
```bash
python web_dashboard.py
```

**Custom host/port:**
```bash
python web_dashboard.py --host 0.0.0.0 --port 8080
```

**Web Features:**
- **Responsive design** works on desktop, tablet, and mobile
- **Real-time updates** every 5 seconds
- **Fleet overview** with total statistics
- **Individual miner cards** with detailed metrics
- **Auto-refresh toggle** for manual control
- **REST API endpoints** for integration

### Docker Commands

**Start monitoring in background:**
```bash
docker-compose up -d
```

**View live dashboard:**
```bash
docker-compose exec bitaxe-monitor python viewer.py --live
```

**Check logs:**
```bash
docker-compose logs -f bitaxe-monitor
```

**Stop monitoring:**
```bash
docker-compose down
```

## 📊 Dashboard Features

### Fleet Dashboard
- **Health Overview:** Visual fleet status with progress bars
- **Performance Metrics:** Total hashrate, power consumption, efficiency ratings
- **Temperature Monitoring:** Average ASIC and VR temperatures
- **Mining Statistics:** Shares accepted/rejected, rejection rates

### Individual Miner Panels
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
- **Pylint:** Automated code quality checks on push/PR
- **CodeQL:** Security analysis runs weekly and on push
- **Test Coverage:** Minimum 80% coverage enforced

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
│   └── web_server.py     # Web server and API endpoints
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
│   └── test_web_server.py # Unit tests for web server module
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

### Common Issues

**Unicode Display Problems:**
```bash
# Set environment variables
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
```

**Connection Timeouts:**
- Check network connectivity to Bitaxe devices
- Increase `timeout` value in config.yaml
- Verify IP addresses are correct

**Docker Permission Issues:**
```bash
# Fix permissions
sudo chown -R $USER:$USER data/ backups/
```

**CSV Corruption:**
- Check `backups/` directory for recent backups
- Automatic corruption detection and repair included

### Logging
- Monitor Docker logs: `docker-compose logs -f`
- Check for network issues in console output
- Automatic retry logic handles temporary failures

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

⚡ **Happy Mining!** ⚡

For support and updates, visit the [GitHub repository](https://github.com/mtab3000/simple-monitor).