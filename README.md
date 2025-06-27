# Simple Bitaxe Gamma Monitor

This tool collects metrics from Bitaxe Gamma miners via API and logs them to a CSV file with comprehensive resilience features. View live stats in your terminal using the CLI viewer.

## Project Structure

```
simple-monitor/
├── src/                    # Source code
│   ├── collector.py        # Main data collector with API integration
│   └── cli_view.py         # Terminal-based viewer with live updates
├── config/                 # Configuration files
│   └── config.yaml         # Miner settings and collection parameters
├── data/                   # Data storage
│   └── metrics.csv         # Collected metrics (auto-generated)
├── tests/                  # Test utilities
│   ├── api_test.py         # Connectivity and API response testing
│   └── test_resilience.py  # Resilience feature validation
├── docs/                   # Documentation
├── run_collector.py        # Collector entry point
├── run_viewer.py           # Viewer entry point
└── requirements.txt        # Python dependencies
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure miners:**
   Edit `config/config.yaml` with your Bitaxe IP addresses

3. **Test connectivity:**
   ```bash
   python tests/api_test.py
   ```

4. **Start collecting:**
   ```bash
   python run_collector.py
   ```

5. **View live data:**
   ```bash
   python run_viewer.py --live
   python run_viewer.py --summary
   ```

## Features

- **Real API Integration**: Connects to Bitaxe `/api/system/info` endpoint
- **Comprehensive Resilience**: Data validation, retry logic, error recovery
- **Startup Validation**: Network connectivity and configuration checks
- **Flexible Configuration**: Timeout, retry, and validation settings
- **Live Monitoring**: Rich terminal interface with real-time updates
- **Data Quality**: Sanitization, range checking, and unit conversion