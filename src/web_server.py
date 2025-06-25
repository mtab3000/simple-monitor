#!/usr/bin/env python3
"""
Web server module for Bitaxe Gamma Monitor
Provides a web interface to view monitoring data and statistics
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, jsonify, request
import yaml

from .cli_view import load_csv_data, get_latest_data_by_miner
from .database import BitaxeDatabase


class BitaxeWebServer:
    """Web server for displaying Bitaxe monitoring data."""
    
    def __init__(self, config_path: str = "config.yaml", host: str = "0.0.0.0", port: int = 80):
        """Initialize the web server."""
        self.config_path = config_path
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder='../web/templates', static_folder='../web/static')
        self.config = self.load_config()
        
        # Initialize database connection
        try:
            self.db = BitaxeDatabase('data/bitaxe_monitor.db')
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            self.db = None
        
        # Setup routes
        self.setup_routes()
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                print(f"Warning: Config file {self.config_path} not found, using defaults")
                return {
                    'csv_path': 'metrics.csv',
                    'miners': [],
                    'poll_interval': 30
                }
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                'csv_path': 'metrics.csv', 
                'miners': [],
                'poll_interval': 30
            }
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for current miner status."""
            try:
                data = self.get_current_data()
                return jsonify({
                    'success': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/history')
        def api_history():
            """API endpoint for historical data."""
            try:
                hours = request.args.get('hours', 24, type=int)
                # Input validation for security
                if hours < 1 or hours > 8760:  # Limit to 1 hour - 1 year
                    hours = 24
                data = self.get_historical_data(hours)
                return jsonify({
                    'success': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/fleet')
        def api_fleet():
            """API endpoint for fleet statistics."""
            try:
                stats = self.get_fleet_stats()
                return jsonify({
                    'success': True,
                    'data': stats,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def get_current_data(self) -> Dict:
        """Get current miner data from database (database-only mode)."""
        try:
            return self._get_data_from_database()
        except Exception as e:
            return {'miners': [], 'error': f'Database error: {str(e)}'}
    
    def _get_data_from_database(self) -> Dict:
        """Get current data from database as fallback."""
        try:
            with self.db.get_connection() as conn:
                # Get latest record for each miner from the optimized schema
                query = '''
                SELECT r.*, m.ip_address, m.hostname 
                FROM raw_metrics r
                JOIN miners m ON r.miner_id = m.id
                WHERE r.timestamp = (
                    SELECT MAX(timestamp) FROM raw_metrics r2 
                    WHERE r2.miner_id = r.miner_id
                )
                ORDER BY m.ip_address
                '''
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                
                miners = []
                for row in rows:
                    # New optimized schema mapping
                    miner_info = {
                        'ip': row['ip_address'],
                        'hostname': row['hostname'] if row['hostname'] else f'Miner-{row["ip_address"].split(".")[-1]}',
                        'status': row['status'],
                        'hashrate_ghs': float(row['hashrate_ghs']) if row['hashrate_ghs'] else 0,
                        'expected_hashrate_ghs': float(row['expected_hashrate_ghs']) if row['expected_hashrate_ghs'] else 0,
                        'hashrate_ratio_percent': float(row['hashrate_ratio_percent']) if row['hashrate_ratio_percent'] else 0,
                        'temp_asic_c': float(row['temp_asic_c']) if row['temp_asic_c'] else 0,
                        'temp_vr_c': float(row['temp_vr_c']) if row['temp_vr_c'] else 0,
                        'power_w': float(row['power_w']) if row['power_w'] else 0,
                        'efficiency_j_th': float(row['efficiency_j_th']) if row['efficiency_j_th'] else 0,
                        'uptime_hours': float(row['uptime_hours']) if row['uptime_hours'] else 0,
                        'shares_accepted': int(row['shares_accepted']) if row['shares_accepted'] else 0,
                        'shares_rejected': int(row['shares_rejected']) if row['shares_rejected'] else 0,
                        'rejection_rate_percent': float(row['rejection_rate_percent']) if row['rejection_rate_percent'] else 0,
                        'wifi_rssi': int(row['wifi_rssi']) if row['wifi_rssi'] else 0,
                        'timestamp': row['timestamp'],
                        'voltage_asic_actual_v': float(row['voltage_asic_actual_v']) if row['voltage_asic_actual_v'] else 0,
                        'voltage_asic_set_v': float(row['voltage_asic_set_v']) if row['voltage_asic_set_v'] else 0,
                        'frequency_set_mhz': float(row['frequency_set_mhz']) if row['frequency_set_mhz'] else 0,
                    }
                    
                    miners.append(miner_info)
                
                return {'miners': miners}
        except Exception as e:
            raise Exception(f'Database query failed: {str(e)}')
    
    def get_historical_data(self, hours: int = 24) -> Dict:
        """Get historical data for the specified number of hours."""
        csv_path = self.config.get('csv_path', 'metrics.csv')
        
        if not os.path.exists(csv_path):
            return {'data': [], 'message': 'No historical data available'}
        
        try:
            csv_data = load_csv_data(csv_path)
            if not csv_data:
                return {'data': [], 'message': 'No data in CSV file'}
            
            # Filter data by time range
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_data = []
            
            for row in csv_data:
                try:
                    timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if timestamp >= cutoff_time:
                        # Convert numeric fields
                        processed_row = row.copy()
                        numeric_fields = ['hashrate_ghs', 'temp_asic_c', 'temp_vr_c', 'power_w', 
                                        'efficiency_j_th', 'uptime_hours', 'shares_accepted', 
                                        'shares_rejected', 'wifi_rssi']
                        
                        for field in numeric_fields:
                            if field in processed_row:
                                try:
                                    processed_row[field] = float(processed_row[field])
                                except (ValueError, TypeError):
                                    processed_row[field] = 0
                        
                        filtered_data.append(processed_row)
                except ValueError:
                    continue  # Skip rows with invalid timestamps
            
            return {'data': filtered_data, 'hours': hours}
            
        except Exception as e:
            return {'data': [], 'error': f'Error processing historical data: {str(e)}'}
    
    def get_fleet_stats(self) -> Dict:
        """Calculate fleet-wide statistics."""
        current_data = self.get_current_data()
        miners = current_data.get('miners', [])
        
        if not miners:
            return {
                'total_miners': 0,
                'online_miners': 0,
                'total_hashrate_ghs': 0,
                'total_power_w': 0,
                'average_efficiency_j_th': 0,
                'average_temp_c': 0,
                'total_shares_accepted': 0,
                'total_shares_rejected': 0,
                'fleet_rejection_rate_percent': 0
            }
        
        # Calculate statistics
        online_miners = [m for m in miners if m['status'] == 'online']
        total_miners = len(miners)
        online_count = len(online_miners)
        
        total_hashrate = sum(m['hashrate_ghs'] for m in miners)
        total_power = sum(m['power_w'] for m in miners)
        total_shares_accepted = sum(m['shares_accepted'] for m in miners)
        total_shares_rejected = sum(m['shares_rejected'] for m in miners)
        
        # Calculate averages (only for online miners)
        if online_count > 0:
            avg_efficiency = sum(m['efficiency_j_th'] for m in online_miners) / online_count
            avg_temp = sum(m['temp_asic_c'] for m in online_miners) / online_count
        else:
            avg_efficiency = 0
            avg_temp = 0
        
        # Calculate fleet rejection rate
        total_shares = total_shares_accepted + total_shares_rejected
        fleet_rejection_rate = (total_shares_rejected / total_shares * 100) if total_shares > 0 else 0
        
        return {
            'total_miners': total_miners,
            'online_miners': online_count,
            'offline_miners': total_miners - online_count,
            'total_hashrate_ghs': round(total_hashrate, 2),
            'total_power_w': round(total_power, 2),
            'average_efficiency_j_th': round(avg_efficiency, 2),
            'average_temp_c': round(avg_temp, 1),
            'total_shares_accepted': total_shares_accepted,
            'total_shares_rejected': total_shares_rejected,
            'fleet_rejection_rate_percent': round(fleet_rejection_rate, 3)
        }
    
    def run(self, debug: bool = False):
        """Start the web server."""
        print(f"Starting Bitaxe Web Dashboard at http://{self.host}:{self.port}")
        print(f"Monitoring {len(self.config.get('miners', []))} miners")
        print(f"Data source: database")
        
        try:
            self.app.run(host=self.host, port=self.port, debug=debug)
        except KeyboardInterrupt:
            print("\nShutting down web server...")
        except Exception as e:
            print(f"Error starting web server: {e}")


def main():
    """Main entry point for the web server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bitaxe Web Dashboard')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=80, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and start web server
    server = BitaxeWebServer(
        config_path=args.config,
        host=args.host,
        port=args.port
    )
    
    server.run(debug=args.debug)


if __name__ == "__main__":
    main()