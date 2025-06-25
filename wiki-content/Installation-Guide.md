# Installation Guide

## 🐳 Docker Installation (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Network access to your Bitaxe devices

### Quick Start
```bash
# Clone repository
git clone https://github.com/mtab3000/simple-monitor.git
cd simple-monitor

# Create configuration
cp examples/config.example.yaml config.yaml
# Edit config.yaml with your Bitaxe IP addresses

# Start basic monitoring
docker-compose up -d

# Start with web dashboard
docker-compose --profile web up -d

# Start with enhanced analytics
docker-compose --profile enhanced up -d

# All features together
docker-compose --profile enhanced --profile web up -d
```

### Access Your Dashboard
```bash
# Terminal dashboard
docker-compose exec bitaxe-monitor python viewer.py --live

# Web dashboard (if using --profile web)
# Open http://localhost:80 in browser
```

## 🐍 Manual Python Installation

### System Requirements
- Python 3.8+
- Network access to Bitaxe devices
- UTF-8 terminal support

### Step-by-Step Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/mtab3000/simple-monitor.git
   cd simple-monitor
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Setup Script**
   ```bash
   python setup.py
   ```

4. **Configure Miners**
   ```bash
   cp examples/config.example.yaml config.yaml
   # Edit config.yaml with your settings
   ```

5. **Start Monitoring**
   ```bash
   # Basic monitoring
   python monitor.py
   
   # Enhanced monitoring with database
   python enhanced_monitor.py
   
   # Web dashboard
   python web_dashboard.py
   ```

6. **View Dashboard**
   ```bash
   # Terminal interface
   python viewer.py --live
   
   # Web interface
   # Open http://localhost:8080
   ```

## 📋 Dependencies

### Production Dependencies
- `requests>=2.28.0` - HTTP client
- `PyYAML>=6.0` - Configuration parsing
- `rich>=12.0.0` - Terminal interface
- `Flask>=2.3.0` - Web framework

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pylint>=2.15.0` - Code quality

## 🔧 Environment Setup

### UTF-8 Encoding (Linux/Mac)
```bash
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Windows PowerShell
```powershell
$env:PYTHONIOENCODING='utf-8'
```

## ✅ Verification

Test your installation:
```bash
# Check Python version
python --version

# Test basic functionality
python viewer.py --summary

# Test web dashboard
python web_dashboard.py --help
```

## Next Steps

- [➡️ Configuration Guide](Configuration)
- [➡️ Dashboard Usage](Dashboard-Usage)