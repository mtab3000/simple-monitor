#!/usr/bin/env python3
"""
Enhanced Database Model for Bitaxe Gamma Monitor
Provides advanced data storage, analytics, and performance tracking
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import logging


class BitaxeDatabase:
    """Advanced database model for Bitaxe monitoring data."""
    
    def __init__(self, db_path: str = "data/bitaxe_monitor.db"):
        """Initialize the database connection and schema."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database schema
        self.init_schema()
        
        # Performance optimization settings
        self.batch_size = 100
        self.vacuum_interval = 24 * 60 * 60  # 24 hours
        self.last_vacuum = time.time()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with optimization."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=60.0)
            
            # Enable performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            yield conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                self.logger.warning("Database locked, retrying...")
                time.sleep(0.1)
                raise e
            else:
                raise e
        finally:
            if conn:
                conn.close()
    
    def init_schema(self):
        """Initialize database schema with all required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Miners configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS miners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    hostname TEXT,
                    expected_hashrate_ghs REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Raw metrics table - optimized for mining performance tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    miner_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    -- Core mining performance
                    hashrate_ghs REAL,
                    expected_hashrate_ghs REAL,
                    hashrate_ratio_percent REAL,
                    efficiency_j_th REAL,
                    -- Temperature monitoring
                    temp_asic_c REAL,
                    temp_vr_c REAL,
                    -- Power and electrical
                    power_w REAL,
                    voltage_asic_set_v REAL,
                    voltage_asic_actual_v REAL,
                    voltage_device_v REAL,
                    frequency_set_mhz REAL,
                    current_a REAL,
                    -- Mining statistics
                    shares_accepted INTEGER,
                    shares_rejected INTEGER,
                    rejection_rate_percent REAL,
                    -- System status
                    uptime_hours REAL,
                    wifi_rssi INTEGER,
                    fan_rpm INTEGER,
                    -- Pool connection (simplified)
                    connected_pool TEXT,
                    FOREIGN KEY (miner_id) REFERENCES miners (id) ON DELETE CASCADE
                )
            """)
            
            # Hourly aggregated data for performance analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hourly_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    miner_id INTEGER NOT NULL,
                    hour_start TIMESTAMP NOT NULL,
                    samples_count INTEGER NOT NULL,
                    uptime_percent REAL,
                    avg_hashrate_ghs REAL,
                    min_hashrate_ghs REAL,
                    max_hashrate_ghs REAL,
                    avg_temp_asic_c REAL,
                    max_temp_asic_c REAL,
                    avg_power_w REAL,
                    max_power_w REAL,
                    avg_efficiency_j_th REAL,
                    total_shares_accepted INTEGER,
                    total_shares_rejected INTEGER,
                    rejection_rate_percent REAL,
                    avg_wifi_rssi INTEGER,
                    status_distribution TEXT,  -- JSON: {"online": 50, "offline": 10}
                    FOREIGN KEY (miner_id) REFERENCES miners (id) ON DELETE CASCADE,
                    UNIQUE(miner_id, hour_start)
                )
            """)
            
            # Daily aggregated data for growth analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    miner_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    total_samples INTEGER NOT NULL,
                    uptime_percent REAL,
                    avg_hashrate_ghs REAL,
                    peak_hashrate_ghs REAL,
                    avg_temp_asic_c REAL,
                    peak_temp_asic_c REAL,
                    total_power_wh REAL,
                    avg_efficiency_j_th REAL,
                    total_shares_accepted INTEGER,
                    total_shares_rejected INTEGER,
                    rejection_rate_percent REAL,
                    revenue_estimate_sats INTEGER,  -- Estimated earnings in satoshis
                    FOREIGN KEY (miner_id) REFERENCES miners (id) ON DELETE CASCADE,
                    UNIQUE(miner_id, date)
                )
            """)
            
            # Fleet-wide performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fleet_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    total_miners INTEGER NOT NULL,
                    online_miners INTEGER NOT NULL,
                    total_hashrate_ghs REAL NOT NULL,
                    total_power_w REAL NOT NULL,
                    avg_efficiency_j_th REAL,
                    fleet_uptime_percent REAL,
                    total_shares_accepted INTEGER,
                    total_shares_rejected INTEGER,
                    fleet_rejection_rate_percent REAL
                )
            """)
            
            # Performance alerts and anomalies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    miner_id INTEGER,
                    alert_type TEXT NOT NULL,  -- 'temp_high', 'hashrate_low', 'offline', etc.
                    severity TEXT NOT NULL,   -- 'info', 'warning', 'critical'
                    message TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    is_resolved BOOLEAN DEFAULT 0,
                    FOREIGN KEY (miner_id) REFERENCES miners (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_raw_metrics_miner_timestamp ON raw_metrics (miner_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_raw_metrics_timestamp ON raw_metrics (timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_hourly_stats_miner_hour ON hourly_stats (miner_id, hour_start)",
                "CREATE INDEX IF NOT EXISTS idx_daily_stats_miner_date ON daily_stats (miner_id, date)",
                "CREATE INDEX IF NOT EXISTS idx_fleet_stats_timestamp ON fleet_stats (timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_miner_timestamp ON alerts (miner_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_type_severity ON alerts (alert_type, severity)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            self.logger.info("Database schema initialized successfully")
    
    def add_or_update_miner(self, ip_address: str, hostname: str = None, 
                           expected_hashrate_ghs: float = 0) -> int:
        """Add or update miner configuration."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to update existing miner
            cursor.execute("""
                UPDATE miners 
                SET hostname = COALESCE(?, hostname),
                    expected_hashrate_ghs = COALESCE(?, expected_hashrate_ghs),
                    updated_at = CURRENT_TIMESTAMP,
                    is_active = 1
                WHERE ip_address = ?
            """, (hostname, expected_hashrate_ghs if expected_hashrate_ghs > 0 else None, ip_address))
            
            if cursor.rowcount == 0:
                # Insert new miner
                cursor.execute("""
                    INSERT INTO miners (ip_address, hostname, expected_hashrate_ghs)
                    VALUES (?, ?, ?)
                """, (ip_address, hostname or f"Miner-{ip_address.split('.')[-1]}", expected_hashrate_ghs))
                miner_id = cursor.lastrowid
            else:
                # Get existing miner ID
                cursor.execute("SELECT id FROM miners WHERE ip_address = ?", (ip_address,))
                miner_id = cursor.fetchone()[0]
            
            conn.commit()
            return miner_id
    
    def insert_raw_metrics(self, metrics_batch: List[Dict[str, Any]]):
        """Insert batch of raw metrics data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for metrics in metrics_batch:
                # Get or create miner (inline to avoid nested connections)
                ip_address = metrics['miner_ip']
                hostname = metrics.get('hostname')
                expected_hashrate_ghs = float(metrics.get('expected_hashrate_ghs', 0))
                
                # Try to update existing miner
                cursor.execute("""
                    UPDATE miners 
                    SET hostname = COALESCE(?, hostname),
                        expected_hashrate_ghs = COALESCE(?, expected_hashrate_ghs),
                        updated_at = CURRENT_TIMESTAMP,
                        is_active = 1
                    WHERE ip_address = ?
                """, (hostname, expected_hashrate_ghs if expected_hashrate_ghs > 0 else None, ip_address))
                
                if cursor.rowcount == 0:
                    # Insert new miner
                    cursor.execute("""
                        INSERT INTO miners (ip_address, hostname, expected_hashrate_ghs)
                        VALUES (?, ?, ?)
                    """, (ip_address, hostname or f"Miner-{ip_address.split('.')[-1]}", expected_hashrate_ghs))
                    miner_id = cursor.lastrowid
                else:
                    # Get existing miner ID
                    cursor.execute("SELECT id FROM miners WHERE ip_address = ?", (ip_address,))
                    miner_id = cursor.fetchone()[0]
                
                # Calculate rejection rate
                shares_accepted = int(metrics.get('shares_accepted', 0))
                shares_rejected = int(metrics.get('shares_rejected', 0))
                total_shares = shares_accepted + shares_rejected
                rejection_rate = (shares_rejected / total_shares * 100) if total_shares > 0 else 0
                
                # Prepare optimized data for insertion
                insert_data = (
                    miner_id,
                    metrics['timestamp'],
                    metrics['status'],
                    # Core mining performance
                    float(metrics.get('hashrate_ghs', 0)),
                    float(metrics.get('expected_hashrate_ghs', 0)),
                    float(metrics.get('hashrate_ratio_percent', 0)),
                    float(metrics.get('efficiency_j_th', 0)),
                    # Temperature monitoring
                    float(metrics.get('temp_asic_c', 0)),
                    float(metrics.get('temp_vr_c', 0)),
                    # Power and electrical
                    float(metrics.get('power_w', 0)),
                    float(metrics.get('voltage_asic_set_v', 0)),
                    float(metrics.get('voltage_asic_actual_v', 0)),
                    float(metrics.get('voltage_device_v', 0)),
                    float(metrics.get('frequency_set_mhz', 0)),
                    float(metrics.get('current_a', 0)),
                    # Mining statistics
                    shares_accepted,
                    shares_rejected,
                    rejection_rate,
                    # System status
                    float(metrics.get('uptime_hours', 0)),
                    int(metrics.get('wifi_rssi', 0)),
                    int(metrics.get('fan_rpm', 0)),
                    # Pool connection (simplified)
                    metrics.get('stratum_url', '')
                )
                
                cursor.execute("""
                    INSERT INTO raw_metrics (
                        miner_id, timestamp, status, 
                        hashrate_ghs, expected_hashrate_ghs, hashrate_ratio_percent, efficiency_j_th,
                        temp_asic_c, temp_vr_c, 
                        power_w, voltage_asic_set_v, voltage_asic_actual_v, voltage_device_v, 
                        frequency_set_mhz, current_a,
                        shares_accepted, shares_rejected, rejection_rate_percent,
                        uptime_hours, wifi_rssi, fan_rpm, connected_pool
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)
            
            conn.commit()
            self.logger.info(f"Inserted {len(metrics_batch)} raw metrics records")
    
    def handle_miner_restart(self, miner_ip: str, current_uptime: float):
        """Handle data hygiene when a miner restart is detected."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get miner ID
            cursor.execute("SELECT id FROM miners WHERE ip_address = ?", (miner_ip,))
            result = cursor.fetchone()
            if not result:
                return
            
            miner_id = result[0]
            
            # Get the last recorded uptime for this miner
            cursor.execute("""
                SELECT uptime_hours FROM raw_metrics 
                WHERE miner_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (miner_id,))
            
            last_uptime_result = cursor.fetchone()
            if not last_uptime_result:
                return
                
            last_uptime = last_uptime_result[0]
            
            # If current uptime is significantly less than last uptime, 
            # this indicates a restart (reduced threshold for tuning process)
            if last_uptime and current_uptime < (last_uptime - 0.1):  # 6 minute threshold for tuning
                self.logger.info(f"Miner restart detected for {miner_ip}: "
                               f"uptime dropped from {last_uptime:.2f}h to {current_uptime:.2f}h")
                
                # Mark a restart event in the database
                cursor.execute("""
                    INSERT INTO alerts (miner_id, alert_type, severity, message, 
                                      value, threshold, timestamp, is_resolved)
                    VALUES (?, 'restart', 'info', 'Miner restart detected', ?, ?, ?, 1)
                """, (miner_id, current_uptime, last_uptime, datetime.now().isoformat()))
                
                conn.commit()
                self.logger.info(f"Logged restart event for miner {miner_ip}")
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """Clean up old raw metrics data to maintain database performance."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete old raw metrics
            cursor.execute("""
                DELETE FROM raw_metrics 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            
            # Delete resolved alerts older than 30 days
            alert_cutoff = datetime.now() - timedelta(days=30)
            cursor.execute("""
                DELETE FROM alerts 
                WHERE timestamp < ? AND is_resolved = 1
            """, (alert_cutoff.isoformat(),))
            
            conn.commit()
            self.logger.info(f"Cleaned up {deleted_count} old raw metrics records")
            
            # Vacuum database to reclaim space
            conn.execute("VACUUM")
            self.logger.info("Database vacuum completed")
    
    def generate_hourly_stats(self, start_time: Optional[datetime] = None):
        """Generate hourly aggregated statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Default to last 25 hours if no start time specified
            if start_time is None:
                start_time = datetime.now() - timedelta(hours=25)
            
            # Get all miners
            cursor.execute("SELECT id, ip_address FROM miners WHERE is_active = 1")
            miners = cursor.fetchall()
            
            for miner in miners:
                miner_id = miner['id']
                
                # Process each hour
                current_hour = start_time.replace(minute=0, second=0, microsecond=0)
                end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
                
                while current_hour < end_time:
                    hour_end = current_hour + timedelta(hours=1)
                    
                    # Get metrics for this hour
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as samples_count,
                            AVG(CASE WHEN status = 'online' THEN 1.0 ELSE 0.0 END) * 100 as uptime_percent,
                            AVG(hashrate_ghs) as avg_hashrate_ghs,
                            MIN(hashrate_ghs) as min_hashrate_ghs,
                            MAX(hashrate_ghs) as max_hashrate_ghs,
                            AVG(temp_asic_c) as avg_temp_asic_c,
                            MAX(temp_asic_c) as max_temp_asic_c,
                            AVG(power_w) as avg_power_w,
                            MAX(power_w) as max_power_w,
                            AVG(efficiency_j_th) as avg_efficiency_j_th,
                            SUM(shares_accepted) as total_shares_accepted,
                            SUM(shares_rejected) as total_shares_rejected,
                            AVG(wifi_rssi) as avg_wifi_rssi,
                            status
                        FROM raw_metrics 
                        WHERE miner_id = ? AND timestamp >= ? AND timestamp < ?
                        GROUP BY status
                    """, (miner_id, current_hour.isoformat(), hour_end.isoformat()))
                    
                    stats = cursor.fetchall()
                    
                    if stats:
                        # Aggregate status distribution
                        status_dist = {}
                        total_samples = 0
                        combined_stats = {
                            'samples_count': 0,
                            'uptime_percent': 0,
                            'avg_hashrate_ghs': 0,
                            'min_hashrate_ghs': float('inf'),
                            'max_hashrate_ghs': 0,
                            'avg_temp_asic_c': 0,
                            'max_temp_asic_c': 0,
                            'avg_power_w': 0,
                            'max_power_w': 0,
                            'avg_efficiency_j_th': 0,
                            'total_shares_accepted': 0,
                            'total_shares_rejected': 0,
                            'avg_wifi_rssi': 0
                        }
                        
                        for stat in stats:
                            status_dist[stat['status']] = stat['samples_count']
                            total_samples += stat['samples_count']
                            
                            # Weight averages by sample count
                            weight = stat['samples_count']
                            combined_stats['samples_count'] += weight
                            combined_stats['uptime_percent'] += stat['uptime_percent'] * weight
                            combined_stats['avg_hashrate_ghs'] += (stat['avg_hashrate_ghs'] or 0) * weight
                            combined_stats['min_hashrate_ghs'] = min(combined_stats['min_hashrate_ghs'], stat['min_hashrate_ghs'] or float('inf'))
                            combined_stats['max_hashrate_ghs'] = max(combined_stats['max_hashrate_ghs'], stat['max_hashrate_ghs'] or 0)
                            combined_stats['avg_temp_asic_c'] += (stat['avg_temp_asic_c'] or 0) * weight
                            combined_stats['max_temp_asic_c'] = max(combined_stats['max_temp_asic_c'], stat['max_temp_asic_c'] or 0)
                            combined_stats['avg_power_w'] += (stat['avg_power_w'] or 0) * weight
                            combined_stats['max_power_w'] = max(combined_stats['max_power_w'], stat['max_power_w'] or 0)
                            combined_stats['avg_efficiency_j_th'] += (stat['avg_efficiency_j_th'] or 0) * weight
                            combined_stats['total_shares_accepted'] += stat['total_shares_accepted'] or 0
                            combined_stats['total_shares_rejected'] += stat['total_shares_rejected'] or 0
                            combined_stats['avg_wifi_rssi'] += (stat['avg_wifi_rssi'] or 0) * weight
                        
                        # Normalize weighted averages
                        if total_samples > 0:
                            for key in ['uptime_percent', 'avg_hashrate_ghs', 'avg_temp_asic_c', 
                                       'avg_power_w', 'avg_efficiency_j_th', 'avg_wifi_rssi']:
                                combined_stats[key] /= total_samples
                        
                        if combined_stats['min_hashrate_ghs'] == float('inf'):
                            combined_stats['min_hashrate_ghs'] = 0
                        
                        # Calculate rejection rate
                        total_shares = combined_stats['total_shares_accepted'] + combined_stats['total_shares_rejected']
                        rejection_rate = (combined_stats['total_shares_rejected'] / total_shares * 100) if total_shares > 0 else 0
                        
                        # Insert or update hourly stats
                        cursor.execute("""
                            INSERT OR REPLACE INTO hourly_stats (
                                miner_id, hour_start, samples_count, uptime_percent,
                                avg_hashrate_ghs, min_hashrate_ghs, max_hashrate_ghs,
                                avg_temp_asic_c, max_temp_asic_c, avg_power_w, max_power_w,
                                avg_efficiency_j_th, total_shares_accepted, total_shares_rejected,
                                rejection_rate_percent, avg_wifi_rssi, status_distribution
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            miner_id, current_hour.isoformat(), combined_stats['samples_count'],
                            combined_stats['uptime_percent'], combined_stats['avg_hashrate_ghs'],
                            combined_stats['min_hashrate_ghs'], combined_stats['max_hashrate_ghs'],
                            combined_stats['avg_temp_asic_c'], combined_stats['max_temp_asic_c'],
                            combined_stats['avg_power_w'], combined_stats['max_power_w'],
                            combined_stats['avg_efficiency_j_th'], combined_stats['total_shares_accepted'],
                            combined_stats['total_shares_rejected'], rejection_rate,
                            combined_stats['avg_wifi_rssi'], json.dumps(status_dist)
                        ))
                    
                    current_hour = hour_end
            
            conn.commit()
            self.logger.info("Generated hourly statistics")
    
    def get_performance_trends(self, miner_id: int, hours: int = 24) -> Dict[str, List]:
        """Get performance trends for a specific miner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get hourly data for trends
            cursor.execute("""
                SELECT 
                    hour_start,
                    uptime_percent,
                    avg_hashrate_ghs,
                    avg_temp_asic_c,
                    avg_power_w,
                    avg_efficiency_j_th,
                    rejection_rate_percent
                FROM hourly_stats
                WHERE miner_id = ? AND hour_start >= datetime('now', '-' || ? || ' hours')
                ORDER BY hour_start
            """, (miner_id, hours))
            
            data = cursor.fetchall()
            
            trends = {
                'timestamps': [],
                'uptime': [],
                'hashrate': [],
                'temperature': [],
                'power': [],
                'efficiency': [],
                'rejection_rate': []
            }
            
            for row in data:
                trends['timestamps'].append(row['hour_start'])
                trends['uptime'].append(row['uptime_percent'])
                trends['hashrate'].append(row['avg_hashrate_ghs'])
                trends['temperature'].append(row['avg_temp_asic_c'])
                trends['power'].append(row['avg_power_w'])
                trends['efficiency'].append(row['avg_efficiency_j_th'])
                trends['rejection_rate'].append(row['rejection_rate_percent'])
            
            return trends
    
    def get_fleet_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive fleet analytics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get overall fleet performance
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT m.id) as total_miners,
                    AVG(hs.uptime_percent) as avg_uptime,
                    SUM(hs.avg_hashrate_ghs) as total_hashrate,
                    SUM(hs.avg_power_w) as total_power,
                    AVG(hs.avg_efficiency_j_th) as avg_efficiency,
                    AVG(hs.avg_temp_asic_c) as avg_temperature,
                    AVG(hs.rejection_rate_percent) as avg_rejection_rate
                FROM miners m
                JOIN hourly_stats hs ON m.id = hs.miner_id
                WHERE hs.hour_start >= datetime('now', '-' || ? || ' days')
                  AND m.is_active = 1
            """, (days,))
            
            fleet_stats = dict(cursor.fetchone())
            
            # Get top performers
            cursor.execute("""
                SELECT 
                    m.ip_address,
                    m.hostname,
                    AVG(hs.uptime_percent) as avg_uptime,
                    AVG(hs.avg_hashrate_ghs) as avg_hashrate,
                    AVG(hs.avg_efficiency_j_th) as avg_efficiency
                FROM miners m
                JOIN hourly_stats hs ON m.id = hs.miner_id
                WHERE hs.hour_start >= datetime('now', '-' || ? || ' days')
                  AND m.is_active = 1
                GROUP BY m.id
                ORDER BY avg_uptime DESC, avg_hashrate DESC
                LIMIT 5
            """, (days,))
            
            top_performers = [dict(row) for row in cursor.fetchall()]
            
            # Get problem miners
            cursor.execute("""
                SELECT 
                    m.ip_address,
                    m.hostname,
                    AVG(hs.uptime_percent) as avg_uptime,
                    AVG(hs.avg_hashrate_ghs) as avg_hashrate,
                    AVG(hs.rejection_rate_percent) as avg_rejection_rate,
                    COUNT(a.id) as alert_count
                FROM miners m
                JOIN hourly_stats hs ON m.id = hs.miner_id
                LEFT JOIN alerts a ON m.id = a.miner_id 
                  AND a.timestamp >= datetime('now', '-' || ? || ' days')
                WHERE hs.hour_start >= datetime('now', '-' || ? || ' days')
                  AND m.is_active = 1
                  AND (hs.uptime_percent < 95 OR hs.rejection_rate_percent > 5)
                GROUP BY m.id
                ORDER BY avg_uptime ASC, alert_count DESC
                LIMIT 5
            """, (days, days))
            
            problem_miners = [dict(row) for row in cursor.fetchall()]
            
            return {
                'fleet_stats': fleet_stats,
                'top_performers': top_performers,
                'problem_miners': problem_miners,
                'period_days': days
            }
    
    def maintenance_tasks(self):
        """Perform routine maintenance tasks."""
        current_time = time.time()
        
        # Vacuum database if needed
        if current_time - self.last_vacuum > self.vacuum_interval:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                self.last_vacuum = current_time
                self.logger.info("Database vacuum completed")
        
        # Clean old raw data (keep only last 30 days)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM raw_metrics 
                WHERE timestamp < datetime('now', '-30 days')
            """)
            deleted_rows = cursor.rowcount
            conn.commit()
            
            if deleted_rows > 0:
                self.logger.info(f"Cleaned {deleted_rows} old raw metrics records")
        
        # Generate hourly stats for recent data
        self.generate_hourly_stats()
        
        self.logger.info("Maintenance tasks completed")