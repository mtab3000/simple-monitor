#!/usr/bin/env python3
"""
Enhanced Collector for Bitaxe Gamma Monitor
Provides advanced data collection with database integration and analytics
"""

import time
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import threading

from collector import BitaxeCollector  # Import original collector
from database import BitaxeDatabase
from analytics import PerformanceAnalyzer, PredictiveAnalyzer


class EnhancedBitaxeCollector(BitaxeCollector):
    """Enhanced collector with database integration and analytics."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the enhanced collector."""
        # Initialize parent collector
        super().__init__(config_path)
        
        # Initialize database
        db_path = self.config.get('database_path', 'data/bitaxe_monitor.db')
        self.db = BitaxeDatabase(db_path)
        
        # Initialize analytics
        self.analyzer = PerformanceAnalyzer(self.db)
        self.predictor = PredictiveAnalyzer(self.db)
        
        # Enhanced configuration options
        self.config.update({
            'enable_database': self.config.get('enable_database', True),
            'enable_analytics': self.config.get('enable_analytics', True),
            'analytics_interval': self.config.get('analytics_interval', 3600),  # 1 hour
            'maintenance_interval': self.config.get('maintenance_interval', 86400),  # 24 hours
            'alert_thresholds': self.config.get('alert_thresholds', {
                'temp_critical': 90,
                'temp_warning': 85,
                'hashrate_drop_percent': 20,
                'rejection_rate_percent': 5,
                'efficiency_threshold': 20
            })
        })
        
        # Tracking variables
        self.last_analytics_run = 0
        self.last_maintenance_run = 0
        self.collection_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'start_time': time.time()
        }
        
        # Threading for background tasks
        self.analytics_thread = None
        self.maintenance_thread = None
        self.running = False
        
        # Setup enhanced logging
        self.setup_enhanced_logging()
        
        self.logger.info("Enhanced collector initialized with database and analytics")
    
    def setup_enhanced_logging(self):
        """Setup enhanced logging with performance metrics."""
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'data/collector.log')
        
        # Create log directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def collect_once(self):
        """Enhanced single collection cycle with database integration."""
        collection_start = time.time()
        self.collection_stats['total_collections'] += 1
        
        try:
            self.logger.info("Starting enhanced collection cycle")
            
            # Collect metrics from all miners
            all_metrics = []
            successful_miners = 0
            
            for miner_config in self.config['miners']:
                try:
                    metrics = self.fetch_miner_data(miner_config)
                    all_metrics.append(metrics)
                    
                    if metrics['status'] == 'online':
                        successful_miners += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to collect from {miner_config.get('ip', 'unknown')}: {e}")
                    # Create offline entry
                    offline_metrics = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'miner_ip': miner_config.get('ip', 'unknown'),
                        'hostname': 'Unknown',
                        'status': 'connection_failed',
                        'expected_hashrate_ghs': miner_config.get('expected_hashrate_ghs', 0)
                    }
                    all_metrics.append(offline_metrics)
            
            # Save to CSV (maintain backward compatibility)
            if self.config.get('enable_csv', True):
                csv_success = self.append_metrics_to_csv_safe(all_metrics)
                if not csv_success:
                    self.logger.warning("CSV write failed, but continuing with database storage")
            
            # Save to database
            if self.config.get('enable_database', True) and all_metrics:
                try:
                    self.db.insert_raw_metrics(all_metrics)
                    self.logger.debug(f"Inserted {len(all_metrics)} records to database")
                except Exception as e:
                    self.logger.error(f"Database insertion failed: {e}")
            
            # Update collection statistics
            collection_time = time.time() - collection_start
            self.collection_stats['successful_collections'] += 1
            
            # Log collection summary
            self.logger.info(f"Collection completed: {successful_miners}/{len(self.config['miners'])} miners online, "
                           f"took {collection_time:.2f}s")
            
            # Check if analytics should run
            self._check_analytics_schedule()
            
            # Check if maintenance should run
            self._check_maintenance_schedule()
            
        except Exception as e:
            self.collection_stats['failed_collections'] += 1
            self.logger.error(f"Collection cycle failed: {e}")
            raise
    
    def _check_analytics_schedule(self):
        """Check if analytics should be run based on schedule."""
        current_time = time.time()
        analytics_interval = self.config.get('analytics_interval', 3600)
        
        if (current_time - self.last_analytics_run) >= analytics_interval:
            if self.config.get('enable_analytics', True):
                self._run_analytics_background()
            self.last_analytics_run = current_time
    
    def _check_maintenance_schedule(self):
        """Check if maintenance should be run based on schedule."""
        current_time = time.time()
        maintenance_interval = self.config.get('maintenance_interval', 86400)
        
        if (current_time - self.last_maintenance_run) >= maintenance_interval:
            self._run_maintenance_background()
            self.last_maintenance_run = current_time
    
    def _run_analytics_background(self):
        """Run analytics in background thread."""
        if self.analytics_thread and self.analytics_thread.is_alive():
            self.logger.debug("Analytics already running, skipping")
            return
        
        self.analytics_thread = threading.Thread(target=self._analytics_worker, daemon=True)
        self.analytics_thread.start()
    
    def _run_maintenance_background(self):
        """Run maintenance in background thread."""
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            self.logger.debug("Maintenance already running, skipping")
            return
        
        self.maintenance_thread = threading.Thread(target=self._maintenance_worker, daemon=True)
        self.maintenance_thread.start()
    
    def _analytics_worker(self):
        """Background worker for analytics tasks."""
        try:
            self.logger.info("Running analytics tasks...")
            
            # Generate hourly statistics
            self.db.generate_hourly_stats()
            
            # Check each active miner for alerts
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, ip_address, hostname FROM miners WHERE is_active = 1")
                miners = cursor.fetchall()
            
            alert_count = 0
            for miner in miners:
                miner_id = miner['id']
                
                # Detect anomalies
                anomalies = self.analyzer.detect_anomalies(miner_id, hours=24)
                
                # Create alerts for significant anomalies
                for anomaly in anomalies:
                    if anomaly['severity'] in ['warning', 'critical']:
                        self._create_alert(miner_id, anomaly)
                        alert_count += 1
                
                # Check for predictive maintenance needs
                maintenance_prediction = self.predictor.predict_maintenance_needs(miner_id)
                if maintenance_prediction['maintenance_score'] > 70:
                    self._create_maintenance_alert(miner_id, maintenance_prediction)
                    alert_count += 1
            
            self.logger.info(f"Analytics completed, generated {alert_count} alerts")
            
        except Exception as e:
            self.logger.error(f"Analytics worker failed: {e}")
    
    def _maintenance_worker(self):
        """Background worker for maintenance tasks."""
        try:
            self.logger.info("Running maintenance tasks...")
            
            # Database maintenance
            self.db.maintenance_tasks()
            
            # Log collection statistics
            uptime = time.time() - self.collection_stats['start_time']
            success_rate = (self.collection_stats['successful_collections'] / 
                          max(self.collection_stats['total_collections'], 1)) * 100
            
            self.logger.info(f"Collection stats - Uptime: {uptime/3600:.1f}h, "
                           f"Success rate: {success_rate:.1f}%, "
                           f"Total collections: {self.collection_stats['total_collections']}")
            
        except Exception as e:
            self.logger.error(f"Maintenance worker failed: {e}")
    
    def _create_alert(self, miner_id: int, anomaly: Dict[str, Any]):
        """Create an alert in the database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO alerts (miner_id, alert_type, severity, message, value, threshold)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    miner_id,
                    anomaly['type'],
                    anomaly['severity'],
                    f"{anomaly['type'].replace('_', ' ').title()}: {anomaly.get('value', 'N/A')}",
                    anomaly.get('value'),
                    anomaly.get('threshold')
                ))
                
                conn.commit()
                self.logger.debug(f"Created alert for miner {miner_id}: {anomaly['type']}")
                
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
    
    def _create_maintenance_alert(self, miner_id: int, prediction: Dict[str, Any]):
        """Create a maintenance alert."""
        try:
            message = f"Maintenance recommended (score: {prediction['maintenance_score']})"
            if prediction['predicted_issues']:
                issues = [issue['description'] for issue in prediction['predicted_issues']]
                message += f" - Issues: {', '.join(issues[:2])}"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO alerts (miner_id, alert_type, severity, message, value)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    miner_id,
                    'maintenance_needed',
                    'warning' if prediction['maintenance_score'] < 85 else 'critical',
                    message,
                    prediction['maintenance_score']
                ))
                
                conn.commit()
                self.logger.info(f"Created maintenance alert for miner {miner_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to create maintenance alert: {e}")
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status and statistics."""
        uptime = time.time() - self.collection_stats['start_time']
        
        status = {
            'running': self.running,
            'uptime_hours': uptime / 3600,
            'total_collections': self.collection_stats['total_collections'],
            'successful_collections': self.collection_stats['successful_collections'],
            'failed_collections': self.collection_stats['failed_collections'],
            'success_rate_percent': (self.collection_stats['successful_collections'] / 
                                   max(self.collection_stats['total_collections'], 1)) * 100,
            'last_analytics_run': datetime.fromtimestamp(self.last_analytics_run).isoformat() if self.last_analytics_run else None,
            'last_maintenance_run': datetime.fromtimestamp(self.last_maintenance_run).isoformat() if self.last_maintenance_run else None,
            'analytics_running': self.analytics_thread and self.analytics_thread.is_alive(),
            'maintenance_running': self.maintenance_thread and self.maintenance_thread.is_alive()
        }
        
        return status
    
    def run_enhanced_monitoring(self):
        """Run the enhanced monitoring loop with graceful shutdown."""
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Starting enhanced monitoring loop...")
        self.logger.info(f"Configuration: {len(self.config['miners'])} miners, "
                        f"{self.config['poll_interval']}s interval, "
                        f"database: {self.config.get('enable_database', True)}, "
                        f"analytics: {self.config.get('enable_analytics', True)}")
        
        try:
            while self.running:
                cycle_start = time.time()
                
                try:
                    self.collect_once()
                except Exception as e:
                    self.logger.error(f"Collection failed: {e}")
                
                # Calculate sleep time
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, self.config['poll_interval'] - cycle_duration)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Collection took {cycle_duration:.1f}s, "
                                      f"longer than interval {self.config['poll_interval']}s")
        
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        finally:
            self._shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def _shutdown(self):
        """Perform graceful shutdown."""
        self.logger.info("Shutting down enhanced collector...")
        
        # Wait for background threads to complete
        if self.analytics_thread and self.analytics_thread.is_alive():
            self.logger.info("Waiting for analytics to complete...")
            self.analytics_thread.join(timeout=30)
        
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            self.logger.info("Waiting for maintenance to complete...")
            self.maintenance_thread.join(timeout=30)
        
        # Final statistics
        status = self.get_collection_status()
        self.logger.info(f"Final stats: {status['total_collections']} collections, "
                        f"{status['success_rate_percent']:.1f}% success rate, "
                        f"{status['uptime_hours']:.1f}h uptime")
        
        self.logger.info("Enhanced collector shutdown complete")


def main():
    """Main entry point for the enhanced collector."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Bitaxe Monitor Collector')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    parser.add_argument('--analytics-interval', type=int, default=3600,
                       help='Analytics interval in seconds')
    parser.add_argument('--maintenance-interval', type=int, default=86400,
                       help='Maintenance interval in seconds')
    
    args = parser.parse_args()
    
    # Create enhanced collector
    try:
        collector = EnhancedBitaxeCollector(args.config)
        
        # Override configuration with command line arguments
        collector.config['log_level'] = args.log_level
        collector.config['analytics_interval'] = args.analytics_interval
        collector.config['maintenance_interval'] = args.maintenance_interval
        
        # Re-setup logging with new level
        collector.setup_enhanced_logging()
        
        # Run monitoring
        collector.run_enhanced_monitoring()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()