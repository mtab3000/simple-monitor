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
            # For miner-specific analysis, group by settings only
            setting_groups = df.groupby(['voltage_asic_set_v', 'frequency_set_mhz'])
        else:
            # For fleet analysis, group by miner and settings
            setting_groups = df.groupby(['miner_ip', 'voltage_asic_set_v', 'frequency_set_mhz'])
        
        results = {}
        
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
                'voltage': float(voltage),
                'frequency': float(frequency),
                'samples': len(group),
                'duration_hours': (group['timestamp'].max() - group['timestamp'].min()).total_seconds() / 3600,
                'hashrate': hashrate_stats,
                'efficiency': efficiency_stats,
                'temperature': temperature_stats,
                'power': power_stats,
                'stability_score': float(stability_score),
                'performance_score': float(performance_score),
                'sweet_spot_score': float(sweet_spot_score),
                'rejection_rate': float(group['shares_rejected'].sum() / (group['shares_accepted'].sum() + group['shares_rejected'].sum()) * 100) if (group['shares_accepted'].sum() + group['shares_rejected'].sum()) > 0 else 0,
                'analysis_type': 'miner_specific' if miner_ip else 'fleet'
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
    
    def generate_fleet_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate fleet-wide optimization summary."""
        if df.empty:
            return {}
        
        fleet_summary = {
            'total_miners': len(df['miner_ip'].unique()),
            'miners': {},
            'fleet_optimal_settings': {},
            'fleet_performance_stats': {}
        }
        
        # Analyze each miner individually
        for miner_ip in df['miner_ip'].unique():
            miner_data = df[df['miner_ip'] == miner_ip]
            miner_performance = self.analyze_setting_performance(miner_data, miner_ip)
            miner_optimal = self.find_optimal_settings(miner_performance, top_n=3)
            
            fleet_summary['miners'][miner_ip] = {
                'settings_tested': len(miner_performance),
                'optimal_settings': miner_optimal,
                'best_performance': miner_optimal[0] if miner_optimal else None,
                'analysis_period': {
                    'samples': len(miner_data),
                    'duration_hours': (miner_data['timestamp'].max() - miner_data['timestamp'].min()).total_seconds() / 3600
                }
            }
        
        # Find fleet-wide optimal settings (settings that work well across multiple miners)
        all_settings = df.groupby(['voltage_asic_set_v', 'frequency_set_mhz'])
        for (voltage, frequency), group in all_settings:
            miners_with_setting = group['miner_ip'].nunique()
            if miners_with_setting >= 2:  # Setting tested on at least 2 miners
                fleet_performance = self.analyze_setting_performance(group)
                if fleet_performance:
                    avg_sweet_spot = sum(p['sweet_spot_score'] for p in fleet_performance.values()) / len(fleet_performance)
                    fleet_summary['fleet_optimal_settings'][f"{voltage:.3f}V_{frequency:.0f}MHz"] = {
                        'voltage': float(voltage),
                        'frequency': float(frequency),
                        'miners_tested': miners_with_setting,
                        'average_sweet_spot_score': float(avg_sweet_spot),
                        'individual_results': fleet_performance
                    }
        
        return fleet_summary
    
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
        if miner_ip:
            return self._generate_miner_specific_report(miner_ip, hours)
        else:
            return self._generate_fleet_report(hours)
    
    def _generate_miner_specific_report(self, miner_ip: str, hours: int = 24) -> Dict[str, Any]:
        """Generate detailed report for a specific miner."""
        self.logger.info(f"Generating miner-specific optimization report for {miner_ip} (last {hours} hours)")
        
        # Load data
        df = self.load_and_preprocess_data(hours)
        if df.empty:
            return {'error': 'No data available for analysis'}
        
        # Filter for specific miner
        miner_df = df[df['miner_ip'] == miner_ip]
        if miner_df.empty:
            return {'error': f'No data available for miner {miner_ip}'}
        
        # Analyze performance for this specific miner
        performance_data = self.analyze_setting_performance(miner_df, miner_ip)
        
        # Find optimal settings
        optimal_settings = self.find_optimal_settings(performance_data)
        
        # Detect benchmark sessions for this miner
        benchmark_sessions = self.detect_benchmark_sessions(miner_df)
        
        # Generate miner-specific recommendations
        recommendations = self._generate_recommendations(optimal_settings, performance_data)
        
        report = {
            'analysis_type': 'miner_specific',
            'miner_ip': miner_ip,
            'analysis_period': {
                'hours': hours,
                'start_time': miner_df['timestamp'].min().isoformat(),
                'end_time': miner_df['timestamp'].max().isoformat(),
                'total_samples': len(miner_df)
            },
            'settings_tested': len(performance_data),
            'benchmark_sessions': benchmark_sessions,
            'optimal_settings': optimal_settings,
            'all_settings_performance': performance_data,
            'recommendations': recommendations,
            'miner_stats': {
                'current_performance': self._get_current_performance(miner_df),
                'performance_trend': self._analyze_performance_trend(miner_df),
                'stability_analysis': self._analyze_overall_stability(miner_df)
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_fleet_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate fleet-wide optimization summary."""
        self.logger.info(f"Generating fleet optimization report (last {hours} hours)")
        
        # Load data
        df = self.load_and_preprocess_data(hours)
        if df.empty:
            return {'error': 'No data available for analysis'}
        
        # Generate fleet summary
        fleet_summary = self.generate_fleet_summary(df)
        
        # Detect fleet-wide benchmark sessions
        benchmark_sessions = self.detect_benchmark_sessions(df)
        
        # Find settings that work well across the fleet
        fleet_optimal = []
        if fleet_summary.get('fleet_optimal_settings'):
            fleet_optimal = sorted(
                fleet_summary['fleet_optimal_settings'].values(),
                key=lambda x: x['average_sweet_spot_score'],
                reverse=True
            )[:5]
        
        report = {
            'analysis_type': 'fleet',
            'analysis_period': {
                'hours': hours,
                'start_time': df['timestamp'].min().isoformat(),
                'end_time': df['timestamp'].max().isoformat(),
                'total_samples': len(df)
            },
            'fleet_summary': fleet_summary,
            'benchmark_sessions': benchmark_sessions,
            'fleet_optimal_settings': fleet_optimal,
            'miner_comparisons': self._generate_miner_comparisons(df),
            'fleet_recommendations': self._generate_fleet_recommendations(fleet_summary),
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
    
    def _get_current_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get current performance metrics for a miner."""
        if df.empty:
            return {}
        
        # Get most recent data
        recent_data = df.sort_values('timestamp').tail(10)  # Last 10 measurements
        
        return {
            'current_hashrate': float(recent_data['hashrate_ghs'].mean()),
            'current_efficiency': float(recent_data['efficiency_j_th'].mean()),
            'current_temperature': float(recent_data['temp_asic_c'].mean()),
            'current_voltage': float(recent_data['voltage_asic_set_v'].iloc[-1]),
            'current_frequency': float(recent_data['frequency_set_mhz'].iloc[-1])
        }
    
    def _analyze_performance_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance trend over time."""
        if len(df) < 20:
            return {'trend': 'insufficient_data'}
        
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Calculate trend for hashrate and efficiency
        x = np.arange(len(df_sorted))
        hashrate_slope = np.polyfit(x, df_sorted['hashrate_ghs'].values, 1)[0]
        efficiency_slope = np.polyfit(x, df_sorted['efficiency_j_th'].values, 1)[0]
        
        return {
            'hashrate_trend': 'improving' if hashrate_slope > 0.1 else 'degrading' if hashrate_slope < -0.1 else 'stable',
            'efficiency_trend': 'improving' if efficiency_slope < -0.01 else 'degrading' if efficiency_slope > 0.01 else 'stable',
            'samples_analyzed': len(df_sorted)
        }
    
    def _analyze_overall_stability(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall stability metrics for a miner."""
        if df.empty:
            return {}
        
        hashrate_cv = df['hashrate_ghs'].std() / df['hashrate_ghs'].mean() * 100
        temp_std = df['temp_asic_c'].std()
        efficiency_std = df['efficiency_j_th'].std()
        
        # Overall stability score
        stability_score = hashrate_cv * 0.5 + temp_std * 0.3 + efficiency_std * 0.2
        
        return {
            'hashrate_cv_percent': float(hashrate_cv),
            'temperature_std': float(temp_std),
            'efficiency_std': float(efficiency_std),
            'overall_stability_score': float(stability_score),
            'stability_rating': 'excellent' if stability_score < 5 else 'good' if stability_score < 10 else 'poor'
        }
    
    def _generate_miner_comparisons(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comparisons between miners in the fleet."""
        comparisons = {}
        
        for miner_ip in df['miner_ip'].unique():
            miner_data = df[df['miner_ip'] == miner_ip]
            comparisons[miner_ip] = {
                'average_hashrate': float(miner_data['hashrate_ghs'].mean()),
                'average_efficiency': float(miner_data['efficiency_j_th'].mean()),
                'average_temperature': float(miner_data['temp_asic_c'].mean()),
                'stability_score': float(miner_data['hashrate_ghs'].std() / miner_data['hashrate_ghs'].mean() * 100),
                'settings_tested': len(miner_data.groupby(['voltage_asic_set_v', 'frequency_set_mhz'])),
                'samples': len(miner_data)
            }
        
        return comparisons
    
    def _generate_fleet_recommendations(self, fleet_summary: Dict[str, Any]) -> List[str]:
        """Generate fleet-wide recommendations."""
        recommendations = []
        
        if not fleet_summary:
            return ['Insufficient data for fleet recommendations']
        
        # Analyze fleet performance
        miners = fleet_summary.get('miners', {})
        if len(miners) > 1:
            best_performers = sorted(
                miners.items(),
                key=lambda x: x[1]['best_performance']['sweet_spot_score'] if x[1]['best_performance'] else 0,
                reverse=True
            )
            
            if best_performers:
                best_miner, best_data = best_performers[0]
                recommendations.append(f"Best performing miner: {best_miner} with sweet spot score {best_data['best_performance']['sweet_spot_score']:.2f}")
                
                if best_data['best_performance']:
                    voltage = best_data['best_performance']['voltage']
                    frequency = best_data['best_performance']['frequency']
                    recommendations.append(f"Consider applying {voltage:.3f}V @ {frequency:.0f}MHz to other miners")
        
        # Fleet optimization recommendations
        fleet_settings = fleet_summary.get('fleet_optimal_settings', {})
        if fleet_settings:
            best_fleet_setting = max(fleet_settings.values(), key=lambda x: x['average_sweet_spot_score'])
            recommendations.append(f"Fleet-wide optimal setting: {best_fleet_setting['voltage']:.3f}V @ {best_fleet_setting['frequency']:.0f}MHz")
            recommendations.append(f"This setting tested on {best_fleet_setting['miners_tested']} miners with avg score {best_fleet_setting['average_sweet_spot_score']:.2f}")
        
        return recommendations
    
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
    parser.add_argument('--miner-ip', help='Analyze specific miner IP (for miner-specific analysis)')
    parser.add_argument('--fleet', action='store_true', help='Perform fleet-wide analysis (default when no miner-ip specified)')
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
        print(f"   Analysis type: Miner-specific ({args.miner_ip})")
    else:
        print(f"   Analysis type: Fleet-wide summary")
    
    report = analyzer.generate_optimization_report(args.miner_ip, args.hours)
    
    if 'error' in report:
        print(f"❌ Error: {report['error']}")
        return
    
    # Display summary based on analysis type
    analysis_type = report.get('analysis_type', 'unknown')
    
    if analysis_type == 'miner_specific':
        print(f"\n📈 MINER-SPECIFIC ANALYSIS SUMMARY ({report['miner_ip']})")
        print(f"   Settings tested: {report['settings_tested']}")
        print(f"   Benchmark sessions: {len(report['benchmark_sessions'])}")
        print(f"   Optimal settings found: {len(report['optimal_settings'])}")
        
        # Show current performance
        current = report.get('miner_stats', {}).get('current_performance', {})
        if current:
            print(f"\n🎯 CURRENT PERFORMANCE")
            print(f"   Hashrate: {current.get('current_hashrate', 0):.1f} GH/s")
            print(f"   Efficiency: {current.get('current_efficiency', 0):.1f} J/TH")
            print(f"   Temperature: {current.get('current_temperature', 0):.1f}°C")
            print(f"   Settings: {current.get('current_voltage', 0):.3f}V @ {current.get('current_frequency', 0):.0f}MHz")
    
    elif analysis_type == 'fleet':
        fleet_summary = report.get('fleet_summary', {})
        print(f"\n📈 FLEET ANALYSIS SUMMARY")
        print(f"   Total miners: {fleet_summary.get('total_miners', 0)}")
        print(f"   Fleet-wide settings: {len(report.get('fleet_optimal_settings', []))}")
        print(f"   Benchmark sessions: {len(report['benchmark_sessions'])}")
        
        # Show miner comparison
        comparisons = report.get('miner_comparisons', {})
        if comparisons:
            print(f"\n🏆 MINER PERFORMANCE RANKING")
            ranked_miners = sorted(
                comparisons.items(),
                key=lambda x: x[1]['average_hashrate'],
                reverse=True
            )
            for i, (miner_ip, stats) in enumerate(ranked_miners[:3], 1):
                print(f"   {i}. {miner_ip}: {stats['average_hashrate']:.1f} GH/s, {stats['average_efficiency']:.1f} J/TH")
    
    else:
        # Fallback for legacy format
        miners_analyzed = report.get('miners_analyzed', [])
        print(f"\n📈 ANALYSIS SUMMARY")
        print(f"   Miners analyzed: {len(miners_analyzed)}")
        print(f"   Settings tested: {report.get('settings_tested', 0)}")
        print(f"   Benchmark sessions: {len(report.get('benchmark_sessions', []))}")
        print(f"   Optimal settings found: {len(report.get('optimal_settings', []))}")
    
    # Show recommendations based on analysis type
    recommendations = report.get('recommendations', []) or report.get('fleet_recommendations', [])
    if recommendations:
        recommendation_title = "💡 MINER RECOMMENDATIONS" if analysis_type == 'miner_specific' else "💡 FLEET RECOMMENDATIONS"
        print(f"\n{recommendation_title}:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # Show optimal settings based on analysis type
    if analysis_type == 'miner_specific':
        optimal_settings = report.get('optimal_settings', [])
        if optimal_settings:
            print(f"\n🏆 TOP OPTIMAL SETTINGS FOR {report['miner_ip']}:")
            for i, setting in enumerate(optimal_settings[:3], 1):
                print(f"   {i}. {setting['voltage']:.3f}V @ {setting['frequency']:.0f}MHz")
                print(f"      Score: {setting['sweet_spot_score']:.2f}, Hashrate: {setting['hashrate']['mean']:.1f} GH/s")
                print(f"      Stability: {setting['stability_score']:.1f}, Efficiency: {setting['efficiency']['mean']:.1f} J/TH")
    
    elif analysis_type == 'fleet':
        fleet_optimal = report.get('fleet_optimal_settings', [])
        if fleet_optimal:
            print(f"\n🏆 TOP FLEET-WIDE OPTIMAL SETTINGS:")
            for i, setting in enumerate(fleet_optimal[:3], 1):
                print(f"   {i}. {setting['voltage']:.3f}V @ {setting['frequency']:.0f}MHz")
                print(f"      Miners tested: {setting['miners_tested']}, Avg score: {setting['average_sweet_spot_score']:.2f}")
    
    else:
        # Fallback for legacy format
        optimal_settings = report.get('optimal_settings', [])
        if optimal_settings:
            print(f"\n🏆 TOP OPTIMAL SETTINGS:")
            for i, setting in enumerate(optimal_settings[:3], 1):
                print(f"   {i}. {setting['voltage']:.3f}V @ {setting['frequency']:.0f}MHz")
                print(f"      Score: {setting['sweet_spot_score']:.2f}, Hashrate: {setting['hashrate']['mean']:.1f} GH/s")
                print(f"      Stability: {setting['stability_score']:.1f}, Efficiency: {setting['efficiency']['mean']:.1f} J/TH")
    
    # Show comparison chart
    chart_data = report.get('all_settings_performance')
    if not chart_data and analysis_type == 'fleet':
        # For fleet analysis, try to get chart data from fleet summary
        fleet_summary = report.get('fleet_summary', {})
        if fleet_summary.get('fleet_optimal_settings'):
            chart_data = fleet_summary['fleet_optimal_settings']
    
    if args.show_chart and chart_data:
        chart = analyzer.create_settings_comparison_chart(chart_data)
        print(chart)
    
    # Export results
    analyzer.export_analysis_results(report, args.output)
    print(f"\n💾 Full analysis exported to: {args.output}")


if __name__ == "__main__":
    main()