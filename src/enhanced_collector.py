#!/usr/bin/env python3
"""
Enhanced Database-Only Collector for Bitaxe Gamma Monitor
Complete rewrite for pure database operation with miner restart detection
"""

import time
import signal
import sys
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yaml

from .database import BitaxeDatabase


class EnhancedBitaxeCollector:
    """Database-only enhanced collector with optimized data flow."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the enhanced collector."""
        self.config_path = config_path
        self.config = self.load_config()
        self.running = False
        
        # Initialize database
        db_path = self.config.get('database_path', 'data/bitaxe_monitor.db')
        self.db = BitaxeDatabase(db_path)
        
        # Analytics removed for simplicity
        
        # Setup HTTP session with retries
        self.session = self.create_session()
        
        # Setup logging
        self.setup_logging()
        
        # Collection statistics
        self.collection_stats = {
            'start_time': time.time(),
            'successful_collections': 0,
            'failed_collections': 0,
            'total_collections': 0,
            'miners_online': 0,
            'miners_total': len(self.config.get('miners', []))
        }
        
        # Simplified - no complex analytics
        
        self.logger.info("Enhanced collector initialized - Database-only mode")
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Set defaults
            config.setdefault('poll_interval', 30)
            config.setdefault('timeout', 10)
            config.setdefault('retries', 3)
            
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def create_session(self):
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.get('retries', 3),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def setup_logging(self):
        """Setup enhanced logging."""
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'data/collector.log')
        
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def collect_miner_data(self, miner_config: Dict) -> Dict:
        """Collect data from a single miner."""
        miner_ip = miner_config.get('ip')
        expected_hashrate = miner_config.get('expected_hashrate_ghs', 0)
        
        try:
            # Make API call
            response = self.session.get(
                f"http://{miner_ip}/api/system/info", 
                timeout=self.config.get('timeout', 10)
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            data = response.json()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Parse and calculate metrics
            uptime_seconds = int(data.get('uptimeSeconds', 0))
            uptime_hours = round(uptime_seconds / 3600, 2)
            
            hashrate_ghs = float(data.get('hashRate', 0))
            power_w = float(data.get('power', 0))
            efficiency_j_th = round((power_w * 1000) / (hashrate_ghs * 1000), 2) if hashrate_ghs > 0 else 0
            
            shares_accepted = int(data.get('sharesAccepted', 0))
            shares_rejected = int(data.get('sharesRejected', 0))
            
            # Create optimized metrics record
            metrics = {
                'timestamp': timestamp,
                'miner_ip': miner_ip,
                'hostname': data.get('hostname', f'miner-{miner_ip.split(".")[-1]}'),
                'status': 'online',
                'hashrate_ghs': hashrate_ghs,
                'expected_hashrate_ghs': expected_hashrate,
                'hashrate_ratio_percent': round((hashrate_ghs / expected_hashrate) * 100, 1) if expected_hashrate > 0 else 0,
                'efficiency_j_th': efficiency_j_th,
                'temp_asic_c': float(data.get('temp', 0)),
                'temp_vr_c': float(data.get('vrTemp', 0)),
                'power_w': power_w,
                'voltage_asic_set_v': float(data.get('coreVoltage', 0)) / 1000,  # mV to V
                'voltage_asic_actual_v': float(data.get('coreVoltageActual', 0)) / 1000,
                'voltage_device_v': float(data.get('voltage', 0)) / 1000,
                'frequency_set_mhz': float(data.get('frequency', 0)),
                'current_a': float(data.get('current', 0)) / 1000,  # mA to A
                'shares_accepted': shares_accepted,
                'shares_rejected': shares_rejected,
                'uptime_hours': uptime_hours,
                'wifi_rssi': int(data.get('wifiRSSI', 0)),
                'fan_rpm': int(data.get('fanrpm', 0)),
                'connected_pool': data.get('stratumURL', ''),
            }
            
            self.logger.debug(f"✓ {miner_ip}: {uptime_hours:.1f}h uptime, {hashrate_ghs:.1f} GH/s")
            return metrics
            
        except Exception as e:
            self.logger.warning(f"Failed to collect from {miner_ip}: {e}")
            # Return offline record
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'miner_ip': miner_ip,
                'hostname': f'miner-{miner_ip.split(".")[-1]}',
                'status': 'connection_failed',
                'hashrate_ghs': 0,
                'expected_hashrate_ghs': expected_hashrate,
                'hashrate_ratio_percent': 0,
                'efficiency_j_th': 0,
                'temp_asic_c': 0,
                'temp_vr_c': 0,
                'power_w': 0,
                'voltage_asic_set_v': 0,
                'voltage_asic_actual_v': 0,
                'voltage_device_v': 0,
                'frequency_set_mhz': 0,
                'current_a': 0,
                'shares_accepted': 0,
                'shares_rejected': 0,
                'uptime_hours': 0,
                'wifi_rssi': 0,
                'fan_rpm': 0,
                'connected_pool': '',
            }
    
    def collect_once(self):
        """Single collection cycle - database only."""
        collection_start = time.time()
        self.collection_stats['total_collections'] += 1
        
        try:
            self.logger.info("Starting collection cycle")
            
            # Collect from all miners
            all_metrics = []
            online_count = 0
            
            for miner_config in self.config['miners']:
                metrics = self.collect_miner_data(miner_config)
                all_metrics.append(metrics)
                
                if metrics['status'] == 'online':
                    online_count += 1
            
            # Store in database only
            if all_metrics:
                try:
                    # Insert to database first
                    self.db.insert_raw_metrics(all_metrics)
                    
                    # Check for miner restarts after successful insertion
                    for metrics in all_metrics:
                        if metrics['status'] == 'online' and metrics['uptime_hours'] > 0:
                            try:
                                self.db.handle_miner_restart(metrics['miner_ip'], metrics['uptime_hours'])
                            except Exception as restart_error:
                                self.logger.warning(f"Restart detection failed for {metrics['miner_ip']}: {restart_error}")
                    
                    self.collection_stats['successful_collections'] += 1
                    self.collection_stats['miners_online'] = online_count
                    
                    collection_time = time.time() - collection_start
                    self.logger.info(f"✓ Collection complete: {online_count}/{len(self.config['miners'])} online, "
                                   f"{collection_time:.2f}s, {len(all_metrics)} records stored")
                    
                except Exception as e:
                    self.logger.error(f"Database storage failed: {e}")
                    self.collection_stats['failed_collections'] += 1
                    import traceback
                    traceback.print_exc()
            
            # Simple collection - no complex background tasks
            
        except Exception as e:
            self.logger.error(f"Collection cycle failed: {e}")
            self.collection_stats['failed_collections'] += 1
    
    def run(self):
        """Main collection loop."""
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"Starting enhanced collector - monitoring {len(self.config['miners'])} miners")
        
        while self.running:
            try:
                self.collect_once()
                
                if self.running:  # Check if still running after collection
                    time.sleep(self.config.get('poll_interval', 30))
                    
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(10)  # Wait before retry
        
        self.logger.info("Enhanced collector stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status."""
        uptime = time.time() - self.collection_stats['start_time']
        total_collections = self.collection_stats['total_collections']
        
        return {
            'running': self.running,
            'uptime_hours': uptime / 3600,
            'total_collections': total_collections,
            'successful_collections': self.collection_stats['successful_collections'],
            'failed_collections': self.collection_stats['failed_collections'],
            'success_rate': (self.collection_stats['successful_collections'] / max(total_collections, 1)) * 100,
            'miners_online': self.collection_stats['miners_online'],
            'miners_total': self.collection_stats['miners_total']
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Bitaxe Collector - Database Only')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--test', action='store_true', help='Run single collection test')
    
    args = parser.parse_args()
    
    collector = EnhancedBitaxeCollector(args.config)
    
    if args.test:
        print("Running single collection test...")
        collector.collect_once()
        status = collector.get_status()
        print(f"Test complete: {status}")
    else:
        collector.run()


if __name__ == "__main__":
    main()