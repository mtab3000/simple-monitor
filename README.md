# Simple BitAxe Monitor

A **simple, stable monitoring solution** for BitAxe mining devices with web dashboard and database storage.

## Features

- ✅ **Real-time monitoring** of BitAxe miners
- ✅ **SQLite database** for historical data
- ✅ **Web dashboard** with live metrics
- ✅ **Docker support** for easy deployment
- ✅ **Simple configuration** via YAML
- ✅ **Stable and lightweight** - no complex analytics

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/mtab3000/simple-monitor.git
cd simple-monitor
cp config.yaml.example config.yaml
# Edit config.yaml with your miner IPs
```

### 2. Docker Deployment (Recommended)

```bash
# Start monitoring
docker-compose up -d

# View logs
docker-compose logs -f

# Stop monitoring
docker-compose down
```

### 3. Native Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start monitoring
python enhanced_monitor.py

# Start web dashboard
python web_dashboard.py
```

## Usage

- **Monitor**: Access web dashboard at `http://localhost:8080`
- **API**: REST API available at `http://localhost:8080/api/`
- **Database**: SQLite database stored in `data/bitaxe_monitor.db`

## Configuration

Edit `config.yaml`:

```yaml
miners:
  - ip: "192.168.1.100"
    name: "Miner-1"
  - ip: "192.168.1.101" 
    name: "Miner-2"

poll_interval: 30
timeout: 10
database_path: "data/bitaxe_monitor.db"
```

## Requirements

- Python 3.11+
- BitAxe miners on local network
- Docker (optional but recommended)

## API Endpoints

- `GET /api/status` - Current miner status
- `GET /api/fleet` - Fleet statistics
- `GET /api/historical?hours=24` - Historical data

## License

MIT License - see LICENSE file for details.