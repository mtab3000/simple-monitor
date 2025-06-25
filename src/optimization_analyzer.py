#!/usr/bin/env python3
"""
Mining Optimization Analyzer for Bitaxe Gamma Monitor
Analyzes voltage/frequency combinations to identify optimal settings for stability and efficiency
"""

import statistics
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
import json
import csv
from collections import defaultdict

from cli_view import load_csv_data


class MiningOptimizationAnalyzer:
    """Analyzes mining data to find optimal voltage/frequency combinations."""
    
    def __init__(self, csv_path: str = "metrics.csv"):
        """Initialize the optimization analyzer."""
        self.csv_path = csv_path
        self.logger = logging.getLogger(__name__)
        
        # Analysis parameters
        self.min_samples_per_setting = 10  # Minimum samples to consider a setting valid
        self.stability_window_minutes = 30  # Window for stability analysis
        self.benchmark_detection_threshold = 5  # Number of different settings to detect benchmarking
        
    def load_and_preprocess_data(self, hours: int = 24) -> pd.DataFrame:
        """Load CSV data and preprocess for analysis."""
        try:
            # Load raw CSV data
            raw_data = load_csv_data(self.csv_path)
            if not raw_data:
                self.logger.warning("No data found in CSV file")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(raw_data)
            
            # Filter by time window
            cutoff_time = datetime.now() - timedelta(hours=hours)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[df['timestamp'] >= cutoff_time]
            
            # Convert numeric columns
            numeric_columns = [
                'hashrate_ghs', 'expected_hashrate_ghs', 'hashrate_ratio_percent',
                'temp_asic_c', 'temp_vr_c', 'power_w', 'voltage_asic_set_v',
                'voltage_asic_actual_v', 'frequency_set_mhz', 'efficiency_j_th',
                'shares_accepted', 'shares_rejected', 'uptime_hours', 'wifi_rssi'
            ]
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove invalid data
            df = df.dropna(subset=['voltage_asic_set_v', 'frequency_set_mhz', 'hashrate_ghs'])
            df = df[df['voltage_asic_set_v'] > 0]
            df = df[df['frequency_set_mhz'] > 0]
            df = df[df['hashrate_ghs'] > 0]
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            self.logger.info(f"Loaded {len(df)} valid records for analysis")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def detect_benchmark_sessions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect benchmarking sessions where multiple settings are tested."""
        if df.empty:
            return []
        
        benchmark_sessions = []
        
        for miner_ip in df['miner_ip'].unique():
            miner_data = df[df['miner_ip'] == miner_ip].copy()
            
            # Group by time windows to detect setting changes
            miner_data['time_group'] = miner_data['timestamp'].dt.floor('30T')  # 30-minute windows
            
            for time_group, group_data in miner_data.groupby('time_group'):
                # Count unique voltage/frequency combinations
                settings_combinations = group_data.groupby(['voltage_asic_set_v', 'frequency_set_mhz']).size()
                
                if len(settings_combinations) >= self.benchmark_detection_threshold:
                    # This looks like a benchmarking session
                    session = {
                        'miner_ip': miner_ip,
                        'start_time': group_data['timestamp'].min(),
                        'end_time': group_data['timestamp'].max(),
                        'settings_tested': len(settings_combinations),
                        'total_samples': len(group_data),
                        'settings_details': [
                            {
                                'voltage': float(v),
                                'frequency': float(f),
                                'samples': int(count)
                            }
                            for (v, f), count in settings_combinations.items()
                        ]
                    }
                    benchmark_sessions.append(session)
        
        self.logger.info(f"Detected {len(benchmark_sessions)} benchmark sessions")
        return benchmark_sessions
    
    def analyze_setting_performance(self, df: pd.DataFrame, miner_ip: str = None) -> Dict[str, Any]:
        """Analyze performance for each voltage/frequency combination."""
        if df.empty:
            return {}
        
        # Filter by miner if specified
        if miner_ip:
            df = df[df['miner_ip'] == miner_ip]
        
        results = {}
        
        # Group by voltage and frequency settings
        setting_groups = df.groupby(['miner_ip', 'voltage_asic_set_v', 'frequency_set_mhz'])
        
        for (miner, voltage, frequency), group in setting_groups:
            if len(group) < self.min_samples_per_setting:
                continue  # Skip settings with insufficient data
            
            # Calculate performance metrics
            setting_key = f"{miner}_{voltage:.3f}V_{frequency:.0f}MHz"
            
            # Basic statistics
            hashrate_stats = {
                'mean': float(group['hashrate_ghs'].mean()),
                'std': float(group['hashrate_ghs'].std()),
                'min': float(group['hashrate_ghs'].min()),
                'max': float(group['hashrate_ghs'].max()),
                'cv': float(group['hashrate_ghs'].std() / group['hashrate_ghs'].mean() * 100)  # Coefficient of variation
            }
            
            efficiency_stats = {
                'mean': float(group['efficiency_j_th'].mean()),
                'std': float(group['efficiency_j_th'].std()),
                'min': float(group['efficiency_j_th'].min()),
                'max': float(group['efficiency_j_th'].max())
            }
            
            temperature_stats = {
                'mean': float(group['temp_asic_c'].mean()),
                'max': float(group['temp_asic_c'].max()),
                'std': float(group['temp_asic_c'].std())
            }
            
            power_stats = {
                'mean': float(group['power_w'].mean()),
                'std': float(group['power_w'].std())
            }
            
            # Calculate stability score (lower is better)
            hashrate_stability = hashrate_stats['cv']  # Coefficient of variation
            temp_stability = temperature_stats['std']
            efficiency_stability = efficiency_stats['std']
            
            # Overall stability score (weighted combination)
            stability_score = (
                hashrate_stability * 0.5 +  # Hashrate stability is most important
                temp_stability * 0.3 +      # Temperature stability
                efficiency_stability * 0.2   # Efficiency stability
            )
            
            # Performance score (higher is better)
            performance_score = (
                hashrate_stats['mean'] * 0.4 +           # Higher hashrate is better
                (20 - efficiency_stats['mean']) * 0.3 +   # Lower J/TH is better (normalized)
                (90 - temperature_stats['mean']) * 0.2 +  # Lower temp is better (normalized)
                (hashrate_stats['mean'] / power_stats['mean']) * 0.1  # Hashrate per watt
            )
            
            # Sweet spot score (combination of performance and stability)
            sweet_spot_score = performance_score / (1 + stability_score / 100)
            
            results[setting_key] = {
                'miner_ip': miner,
                'voltage': voltage,
                'frequency': frequency,
                'samples': len(group),
                'duration_hours': (group['timestamp'].max() - group['timestamp'].min()).total_seconds() / 3600,
                'hashrate': hashrate_stats,
                'efficiency': efficiency_stats,
                'temperature': temperature_stats,
                'power': power_stats,
                'stability_score': float(stability_score),
                'performance_score': float(performance_score),
                'sweet_spot_score': float(sweet_spot_score),
                'rejection_rate': float(group['shares_rejected'].sum() / (group['shares_accepted'].sum() + group['shares_rejected'].sum()) * 100) if (group['shares_accepted'].sum() + group['shares_rejected'].sum()) > 0 else 0
            }
        
        return results
    
    def find_optimal_settings(self, performance_data: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
        """Find the top N optimal settings based on sweet spot score."""
        if not performance_data:
            return []
        
        # Sort by sweet spot score (descending)
        sorted_settings = sorted(
            performance_data.values(),
            key=lambda x: x['sweet_spot_score'],
            reverse=True
        )
        
        return sorted_settings[:top_n]
    
    def analyze_stability_over_time(self, df: pd.DataFrame, voltage: float, frequency: float, miner_ip: str) -> Dict[str, Any]:
        """Analyze how hashrate and efficiency stability changes over time for a specific setting."""
        # Filter for specific setting
        setting_data = df[
            (df['miner_ip'] == miner_ip) &
            (df['voltage_asic_set_v'] == voltage) &
            (df['frequency_set_mhz'] == frequency)
        ].copy()
        
        if len(setting_data) < 10:
            return {}
        
        # Sort by timestamp
        setting_data = setting_data.sort_values('timestamp')
        
        # Create rolling windows for stability analysis
        window_size = min(20, len(setting_data) // 4)  # Adaptive window size
        
        stability_over_time = []
        
        for i in range(window_size, len(setting_data)):
            window_data = setting_data.iloc[i-window_size:i]
            
            hashrate_cv = window_data['hashrate_ghs'].std() / window_data['hashrate_ghs'].mean() * 100
            efficiency_std = window_data['efficiency_j_th'].std()
            temp_std = window_data['temp_asic_c'].std()
            
            stability_over_time.append({
                'timestamp': window_data['timestamp'].iloc[-1],
                'hashrate_cv': float(hashrate_cv),
                'efficiency_std': float(efficiency_std),
                'temp_std': float(temp_std),
                'mean_hashrate': float(window_data['hashrate_ghs'].mean()),
                'mean_efficiency': float(window_data['efficiency_j_th'].mean())
            })
        
        return {
            'voltage': voltage,
            'frequency': frequency,
            'miner_ip': miner_ip,
            'stability_timeline': stability_over_time,
            'overall_stability': float(np.mean([point['hashrate_cv'] for point in stability_over_time])),
            'stability_trend': self._calculate_trend([point['hashrate_cv'] for point in stability_over_time])
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if values are improving, degrading, or stable."""
        if len(values) < 3:
            return 'insufficient_data'
        
        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'degrading'  # Increasing CV means worse stability
        elif slope < -0.1:
            return 'improving'  # Decreasing CV means better stability
        else:
            return 'stable'
    
    def generate_optimization_report(self, miner_ip: str = None, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        self.logger.info(f"Generating optimization report for last {hours} hours")
        
        # Load data
        df = self.load_and_preprocess_data(hours)
        if df.empty:
            return {'error': 'No data available for analysis'}
        
        # Analyze performance for each setting
        performance_data = self.analyze_setting_performance(df, miner_ip)
        
        # Find optimal settings
        optimal_settings = self.find_optimal_settings(performance_data)
        
        # Detect benchmark sessions
        benchmark_sessions = self.detect_benchmark_sessions(df)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(optimal_settings, performance_data)
        
        report = {
            'analysis_period': {
                'hours': hours,
                'start_time': df['timestamp'].min().isoformat() if not df.empty else None,
                'end_time': df['timestamp'].max().isoformat() if not df.empty else None,
                'total_samples': len(df)
            },
            'miners_analyzed': list(df['miner_ip'].unique()) if not df.empty else [],
            'settings_tested': len(performance_data),
            'benchmark_sessions': benchmark_sessions,
            'optimal_settings': optimal_settings,
            'all_settings_performance': performance_data,
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self, optimal_settings: List[Dict], all_settings: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if not optimal_settings:
            recommendations.append("No optimal settings found. Collect more data with varied voltage/frequency combinations.")
            return recommendations
        
        best_setting = optimal_settings[0]
        
        # Voltage recommendations
        voltage_range = [s['voltage'] for s in optimal_settings]
        if len(voltage_range) > 1:
            recommendations.append(
                f"Optimal voltage range: {min(voltage_range):.3f}V - {max(voltage_range):.3f}V"
            )
        
        # Frequency recommendations
        freq_range = [s['frequency'] for s in optimal_settings]
        if len(freq_range) > 1:
            recommendations.append(
                f"Optimal frequency range: {min(freq_range):.0f}MHz - {max(freq_range):.0f}MHz"
            )
        
        # Stability recommendations
        if best_setting['stability_score'] > 5:
            recommendations.append(
                "Consider reducing frequency or voltage for better stability"
            )
        
        # Temperature recommendations
        if best_setting['temperature']['mean'] > 80:
            recommendations.append(
                "High temperatures detected. Improve cooling or reduce frequency"
            )
        
        # Efficiency recommendations
        if best_setting['efficiency']['mean'] > 16:
            recommendations.append(
                "Consider underclocking for better energy efficiency"
            )
        
        # Best setting recommendation
        recommendations.append(
            f"Recommended setting: {best_setting['voltage']:.3f}V @ {best_setting['frequency']:.0f}MHz "
            f"(Sweet spot score: {best_setting['sweet_spot_score']:.2f})"
        )
        
        return recommendations
    
    def export_analysis_results(self, report: Dict[str, Any], output_path: str = "optimization_analysis.json"):
        """Export analysis results to JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Analysis results exported to {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
    
    def create_settings_comparison_chart(self, performance_data: Dict[str, Any]) -> str:
        """Create a text-based comparison chart of different settings."""
        if not performance_data:
            return "No data available for comparison"
        
        # Sort by sweet spot score
        sorted_settings = sorted(
            performance_data.values(),
            key=lambda x: x['sweet_spot_score'],
            reverse=True
        )
        
        chart = "\n📊 VOLTAGE/FREQUENCY PERFORMANCE COMPARISON\n"
        chart += "=" * 70 + "\n"
        chart += f"{'Rank':<4} {'Voltage':<8} {'Freq':<7} {'Score':<7} {'Hashrate':<10} {'Efficiency':<8} {'Stability':<9}\n"
        chart += "-" * 70 + "\n"
        
        for i, setting in enumerate(sorted_settings[:10], 1):  # Top 10
            voltage = f"{setting['voltage']:.3f}V"
            frequency = f"{setting['frequency']:.0f}MHz"
            score = f"{setting['sweet_spot_score']:.2f}"
            hashrate = f"{setting['hashrate']['mean']:.1f} GH/s"
            efficiency = f"{setting['efficiency']['mean']:.1f} J/TH"
            stability = f"{setting['stability_score']:.1f}"
            
            chart += f"{i:<4} {voltage:<8} {frequency:<7} {score:<7} {hashrate:<10} {efficiency:<8} {stability:<9}\n"
        
        chart += "=" * 70 + "\n"
        chart += "💡 Lower stability score is better (less variation)\n"
        chart += "🎯 Higher sweet spot score indicates optimal balance\n"
        
        return chart


def main():
    """Command-line interface for the optimization analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mining Optimization Analyzer')
    parser.add_argument('--csv-path', default='metrics.csv', help='Path to CSV data file')
    parser.add_argument('--miner-ip', help='Analyze specific miner IP')
    parser.add_argument('--hours', type=int, default=24, help='Analysis time window in hours')
    parser.add_argument('--output', default='optimization_analysis.json', help='Output file path')
    parser.add_argument('--show-chart', action='store_true', help='Show comparison chart')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create analyzer
    analyzer = MiningOptimizationAnalyzer(args.csv_path)
    
    # Generate report
    print(f"🔍 Analyzing mining optimization data...")
    print(f"   Time window: {args.hours} hours")
    print(f"   Data source: {args.csv_path}")
    if args.miner_ip:
        print(f"   Miner filter: {args.miner_ip}")
    
    report = analyzer.generate_optimization_report(args.miner_ip, args.hours)
    
    if 'error' in report:
        print(f"❌ Error: {report['error']}")
        return
    
    # Display summary
    print(f"\n📈 ANALYSIS SUMMARY")
    print(f"   Miners analyzed: {len(report['miners_analyzed'])}")
    print(f"   Settings tested: {report['settings_tested']}")
    print(f"   Benchmark sessions: {len(report['benchmark_sessions'])}")
    print(f"   Optimal settings found: {len(report['optimal_settings'])}")
    
    # Show top recommendations
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # Show top settings
    if report['optimal_settings']:
        print(f"\n🏆 TOP OPTIMAL SETTINGS:")
        for i, setting in enumerate(report['optimal_settings'][:3], 1):
            print(f"   {i}. {setting['voltage']:.3f}V @ {setting['frequency']:.0f}MHz")
            print(f"      Score: {setting['sweet_spot_score']:.2f}, Hashrate: {setting['hashrate']['mean']:.1f} GH/s")
            print(f"      Stability: {setting['stability_score']:.1f}, Efficiency: {setting['efficiency']['mean']:.1f} J/TH")
    
    # Show comparison chart
    if args.show_chart and report['all_settings_performance']:
        chart = analyzer.create_settings_comparison_chart(report['all_settings_performance'])
        print(chart)
    
    # Export results
    analyzer.export_analysis_results(report, args.output)
    print(f"\n💾 Full analysis exported to: {args.output}")


if __name__ == "__main__":
    main()