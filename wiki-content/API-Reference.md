# 🚀 Web Dashboard API Reference

## Overview

The Bitaxe Monitor provides a comprehensive REST API for accessing real-time mining data, fleet statistics, and historical analytics. All endpoints return JSON responses with consistent error handling.

**Base URL:** `http://localhost:80`

## 📊 API Endpoints

### GET /api/status

**Description:** Get current status of all miners with detailed metrics.

**Response Format:**
```json
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
        "voltage_asic_set_v": 1.003,
        "voltage_device_v": 4.938,
        "frequency_set_mhz": 458,
        "shares_accepted": 2847,
        "shares_rejected": 2,
        "rejection_rate_percent": 0.07,
        "wifi_rssi": -52,
        "uptime_hours": 12.4,
        "timestamp": "2024-01-01 12:00:00"
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Usage Examples:**
```bash
# Basic request
curl http://localhost:80/api/status

# Pretty-printed JSON
curl http://localhost:80/api/status | jq

# Extract specific miner data
curl -s http://localhost:80/api/status | jq '.data.miners[] | select(.ip=="192.168.1.45")'

# Check if any miners are offline
curl -s http://localhost:80/api/status | jq '.data.miners[] | select(.status!="online") | .ip'
```

### GET /api/fleet

**Description:** Get aggregated fleet statistics and performance metrics.

**Response Format:**
```json
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
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Usage Examples:**
```bash
# Fleet overview
curl http://localhost:80/api/fleet | jq

# Check fleet efficiency
curl -s http://localhost:80/api/fleet | jq '.data.average_efficiency_j_th'

# Monitor fleet hashrate
curl -s http://localhost:80/api/fleet | jq '.data.total_hashrate_ghs'

# Alert on offline miners
OFFLINE=$(curl -s http://localhost:80/api/fleet | jq '.data.offline_miners')
if [ "$OFFLINE" -gt 0 ]; then echo "Alert: $OFFLINE miners offline"; fi
```

### GET /api/history

**Description:** Get historical data for specified time range.

**Parameters:**
- `hours` (optional): Number of hours to retrieve (default: 24, max: 8760)

**Response Format:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "timestamp": "2024-01-01 12:00:00",
        "miner_ip": "192.168.1.45",
        "hostname": "bitaxe-001",
        "status": "online",
        "hashrate_ghs": 934.5,
        "temp_asic_c": 59.8,
        "power_w": 14.1,
        "efficiency_j_th": 15.1,
        "shares_accepted": 2847,
        "shares_rejected": 2,
        "wifi_rssi": -52,
        "uptime_hours": 12.4
      }
    ],
    "hours": 24
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Usage Examples:**
```bash
# Last 24 hours (default)
curl http://localhost:80/api/history

# Last week
curl "http://localhost:80/api/history?hours=168"

# Last hour only
curl "http://localhost:80/api/history?hours=1"

# Extract temperature trends
curl -s "http://localhost:80/api/history?hours=24" | jq '.data.data[] | {timestamp, ip: .miner_ip, temp: .temp_asic_c}'

# Calculate average hashrate over time
curl -s "http://localhost:80/api/history?hours=12" | jq '[.data.data[] | .hashrate_ghs] | add / length'
```

## 🔧 Integration Examples

### Python Integration

```python
import requests
import json
from datetime import datetime

class BitaxeAPI:
    def __init__(self, base_url="http://localhost:80"):
        self.base_url = base_url
    
    def get_status(self):
        """Get current miner status"""
        response = requests.get(f"{self.base_url}/api/status")
        return response.json()
    
    def get_fleet_stats(self):
        """Get fleet statistics"""
        response = requests.get(f"{self.base_url}/api/fleet")
        return response.json()
    
    def get_history(self, hours=24):
        """Get historical data"""
        response = requests.get(f"{self.base_url}/api/history", 
                              params={"hours": hours})
        return response.json()
    
    def get_miner_by_ip(self, ip):
        """Get specific miner data"""
        status = self.get_status()
        if status['success']:
            for miner in status['data']['miners']:
                if miner['ip'] == ip:
                    return miner
        return None
    
    def is_fleet_healthy(self, min_efficiency=15.0, max_temp=65.0):
        """Check if fleet is operating within parameters"""
        fleet = self.get_fleet_stats()
        if fleet['success']:
            data = fleet['data']
            return (data['average_efficiency_j_th'] <= min_efficiency and 
                   data['average_temp_c'] <= max_temp and
                   data['offline_miners'] == 0)
        return False

# Usage example
api = BitaxeAPI()

# Monitor fleet health
if not api.is_fleet_healthy():
    print("⚠️ Fleet health alert!")

# Get specific miner performance
miner = api.get_miner_by_ip("192.168.1.45")
if miner and miner['status'] == 'online':
    print(f"Miner {miner['hostname']}: {miner['hashrate_ghs']} GH/s")
```

### Bash Monitoring Script

```bash
#!/bin/bash
# Bitaxe Fleet Monitor Script

API_URL="http://localhost:80"
ALERT_EMAIL="admin@example.com"

# Function to send alerts
send_alert() {
    local message="$1"
    echo "$(date): $message" >> /var/log/bitaxe-alerts.log
    # echo "$message" | mail -s "Bitaxe Alert" "$ALERT_EMAIL"
    echo "🚨 ALERT: $message"
}

# Check fleet status
check_fleet() {
    local response=$(curl -s "${API_URL}/api/fleet")
    local offline=$(echo "$response" | jq -r '.data.offline_miners // 0')
    local temp=$(echo "$response" | jq -r '.data.average_temp_c // 0')
    local efficiency=$(echo "$response" | jq -r '.data.average_efficiency_j_th // 0')
    
    # Check for offline miners
    if [ "$offline" -gt 0 ]; then
        send_alert "Fleet has $offline offline miners"
    fi
    
    # Check temperature
    if (( $(echo "$temp > 70" | bc -l) )); then
        send_alert "Fleet average temperature high: ${temp}°C"
    fi
    
    # Check efficiency
    if (( $(echo "$efficiency > 18" | bc -l) )); then
        send_alert "Fleet efficiency degraded: ${efficiency} J/TH"
    fi
}

# Monitor individual miners
check_miners() {
    local response=$(curl -s "${API_URL}/api/status")
    echo "$response" | jq -r '.data.miners[] | select(.status != "online") | "Miner \(.ip) (\(.hostname)) is \(.status)"' | while read -r line; do
        if [ -n "$line" ]; then
            send_alert "$line"
        fi
    done
}

# Main monitoring loop
main() {
    echo "Starting Bitaxe monitoring..."
    while true; do
        check_fleet
        check_miners
        sleep 300  # Check every 5 minutes
    done
}

# Run if called directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
```

### Node.js Integration

```javascript
const axios = require('axios');

class BitaxeMonitor {
    constructor(baseUrl = 'http://localhost:80') {
        this.baseUrl = baseUrl;
    }
    
    async getStatus() {
        try {
            const response = await axios.get(`${this.baseUrl}/api/status`);
            return response.data;
        } catch (error) {
            console.error('Error fetching status:', error.message);
            return { success: false, error: error.message };
        }
    }
    
    async getFleetStats() {
        try {
            const response = await axios.get(`${this.baseUrl}/api/fleet`);
            return response.data;
        } catch (error) {
            console.error('Error fetching fleet stats:', error.message);
            return { success: false, error: error.message };
        }
    }
    
    async getHistory(hours = 24) {
        try {
            const response = await axios.get(`${this.baseUrl}/api/history`, {
                params: { hours }
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching history:', error.message);
            return { success: false, error: error.message };
        }
    }
    
    async monitorFleet() {
        setInterval(async () => {
            const fleet = await this.getFleetStats();
            if (fleet.success) {
                const { data } = fleet;
                console.log(`Fleet Status: ${data.online_miners}/${data.total_miners} online`);
                console.log(`Total Hashrate: ${data.total_hashrate_ghs} GH/s`);
                console.log(`Average Temp: ${data.average_temp_c}°C`);
                console.log(`Efficiency: ${data.average_efficiency_j_th} J/TH`);
                console.log('---');
            }
        }, 30000); // Every 30 seconds
    }
}

// Usage
const monitor = new BitaxeMonitor();
monitor.monitorFleet();
```

## 📈 Advanced Usage Patterns

### Real-time Data Streaming

```javascript
// WebSocket-style polling for real-time updates
function createRealTimeMonitor(callback, interval = 5000) {
    return setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            callback(data);
        } catch (error) {
            console.error('Monitor error:', error);
        }
    }, interval);
}

// Usage in web application
const monitor = createRealTimeMonitor((data) => {
    updateDashboard(data);
    checkAlerts(data);
}, 5000);
```

### Data Aggregation

```python
import pandas as pd
import requests

def collect_fleet_data(hours=24):
    """Collect and aggregate fleet data for analysis"""
    api_url = "http://localhost:80"
    
    # Get historical data
    response = requests.get(f"{api_url}/api/history", params={"hours": hours})
    data = response.json()
    
    if data['success']:
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data['data']['data'])
        
        # Calculate aggregated metrics
        summary = {
            'average_hashrate': df['hashrate_ghs'].mean(),
            'peak_hashrate': df['hashrate_ghs'].max(),
            'average_temp': df['temp_asic_c'].mean(),
            'max_temp': df['temp_asic_c'].max(),
            'total_accepted_shares': df['shares_accepted'].sum(),
            'average_efficiency': df['efficiency_j_th'].mean(),
            'uptime_percentage': (df['status'] == 'online').mean() * 100
        }
        
        return summary
    
    return None

# Generate daily report
daily_stats = collect_fleet_data(24)
print(f"Daily Fleet Report: {daily_stats}")
```

## 🔒 Security & Rate Limiting

### API Security Headers

The API includes standard security headers:
- `Content-Type: application/json`
- `X-Content-Type-Options: nosniff`
- Input validation on all parameters
- SQL injection protection

### Rate Limiting

**Recommended limits:**
- Status endpoint: Max 1 request per second
- History endpoint: Max 1 request per 10 seconds
- Fleet endpoint: Max 1 request per 5 seconds

### Access Control

For production deployments, consider:
```nginx
# Nginx reverse proxy configuration
location /api/ {
    proxy_pass http://localhost:80;
    
    # Rate limiting
    limit_req zone=api burst=10 nodelay;
    
    # IP whitelist
    allow 192.168.1.0/24;
    deny all;
    
    # CORS headers
    add_header Access-Control-Allow-Origin "https://your-domain.com";
}
```

## 🐛 Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Endpoint not found
- `500` - Internal Server Error
- `503` - Service Unavailable

### Retry Logic

```python
import time
import requests
from functools import wraps

def retry_api_call(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

@retry_api_call(max_retries=3, delay=1)
def get_fleet_status():
    response = requests.get("http://localhost:80/api/fleet", timeout=10)
    response.raise_for_status()
    return response.json()
```