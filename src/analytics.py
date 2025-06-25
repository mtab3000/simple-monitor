#!/usr/bin/env python3
"""
Advanced Analytics Module for Bitaxe Gamma Monitor
Provides performance analysis, growth metrics, and predictive insights
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import math

from .database import BitaxeDatabase


class PerformanceAnalyzer:
    """Advanced performance analysis for Bitaxe miners."""
    
    def __init__(self, db: BitaxeDatabase):
        """Initialize with database connection."""
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def calculate_efficiency_score(self, miner_id: int, hours: int = 24) -> Dict[str, Any]:
        """Calculate comprehensive efficiency score for a miner."""
        trends = self.db.get_performance_trends(miner_id, hours)
        
        if not trends['hashrate']:
            return {'score': 0, 'factors': {}, 'recommendations': []}
        
        # Performance factors (weighted)
        factors = {}
        
        # Uptime factor (25% weight)
        avg_uptime = statistics.mean(trends['uptime']) if trends['uptime'] else 0
        factors['uptime'] = {
            'value': avg_uptime,
            'score': min(avg_uptime / 95.0, 1.0),  # 95% uptime is optimal
            'weight': 0.25
        }
        
        # Hashrate stability factor (30% weight)
        hashrates = [h for h in trends['hashrate'] if h > 0]
        if hashrates:
            hashrate_cv = statistics.stdev(hashrates) / statistics.mean(hashrates) if len(hashrates) > 1 else 0
            hashrate_stability = max(0, 1 - hashrate_cv * 2)  # Lower CV is better
        else:
            hashrate_stability = 0
        
        factors['hashrate_stability'] = {
            'value': hashrate_stability,
            'score': hashrate_stability,
            'weight': 0.30
        }
        
        # Temperature management factor (20% weight)
        temps = [t for t in trends['temperature'] if t > 0]
        if temps:
            avg_temp = statistics.mean(temps)
            max_temp = max(temps)
            # Optimal range: 60-75°C, penalty for >80°C
            temp_score = max(0, 1 - max(0, avg_temp - 75) / 20) * max(0, 1 - max(0, max_temp - 85) / 15)
        else:
            temp_score = 0
        
        factors['temperature'] = {
            'value': avg_temp if temps else 0,
            'score': temp_score,
            'weight': 0.20
        }
        
        # Energy efficiency factor (15% weight)
        efficiencies = [e for e in trends['efficiency'] if e > 0]
        if efficiencies:
            avg_efficiency = statistics.mean(efficiencies)
            # Lower J/TH is better, normalize around 15 J/TH
            efficiency_score = max(0, 1 - max(0, avg_efficiency - 12) / 10)
        else:
            efficiency_score = 0
        
        factors['efficiency'] = {
            'value': avg_efficiency if efficiencies else 0,
            'score': efficiency_score,
            'weight': 0.15
        }
        
        # Share rejection factor (10% weight)
        rejections = [r for r in trends['rejection_rate'] if r >= 0]
        if rejections:
            avg_rejection = statistics.mean(rejections)
            # Rejection rate should be <2%
            rejection_score = max(0, 1 - avg_rejection / 5)
        else:
            rejection_score = 0
        
        factors['rejection_rate'] = {
            'value': avg_rejection if rejections else 0,
            'score': rejection_score,
            'weight': 0.10
        }
        
        # Calculate weighted overall score
        overall_score = sum(factor['score'] * factor['weight'] for factor in factors.values())
        overall_score = min(overall_score * 100, 100)  # Convert to percentage
        
        # Generate recommendations
        recommendations = self._generate_recommendations(factors)
        
        return {
            'score': round(overall_score, 1),
            'grade': self._get_performance_grade(overall_score),
            'factors': factors,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, factors: Dict) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        # Uptime recommendations
        if factors['uptime']['score'] < 0.8:
            recommendations.append("Monitor network connectivity and power stability")
            recommendations.append("Check for frequent reboots or connection issues")
        
        # Hashrate stability recommendations
        if factors['hashrate_stability']['score'] < 0.7:
            recommendations.append("Review overclocking settings for stability")
            recommendations.append("Check for thermal throttling or power fluctuations")
        
        # Temperature recommendations
        if factors['temperature']['score'] < 0.8:
            recommendations.append("Improve cooling or reduce ambient temperature")
            recommendations.append("Consider reducing frequency to lower temperatures")
        
        # Efficiency recommendations
        if factors['efficiency']['score'] < 0.8:
            recommendations.append("Optimize voltage settings for better efficiency")
            recommendations.append("Consider underclocking for better J/TH ratio")
        
        # Rejection rate recommendations
        if factors['rejection_rate']['score'] < 0.8:
            recommendations.append("Check pool connection stability")
            recommendations.append("Verify network latency and quality")
        
        return recommendations
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 65:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def detect_anomalies(self, miner_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect performance anomalies using statistical analysis."""
        trends = self.db.get_performance_trends(miner_id, hours)
        anomalies = []
        
        # Hashrate anomalies
        hashrates = [h for h in trends['hashrate'] if h > 0]
        if len(hashrates) > 5:
            mean_hashrate = statistics.mean(hashrates)
            stdev_hashrate = statistics.stdev(hashrates)
            threshold = 2 * stdev_hashrate
            
            for i, hashrate in enumerate(hashrates):
                if abs(hashrate - mean_hashrate) > threshold:
                    anomalies.append({
                        'type': 'hashrate_anomaly',
                        'severity': 'warning' if abs(hashrate - mean_hashrate) < 3 * stdev_hashrate else 'critical',
                        'timestamp': trends['timestamps'][i],
                        'value': hashrate,
                        'expected': mean_hashrate,
                        'deviation': abs(hashrate - mean_hashrate) / stdev_hashrate
                    })
        
        # Temperature spikes
        temps = [t for t in trends['temperature'] if t > 0]
        if temps:
            for i, temp in enumerate(temps):
                if temp > 85:
                    severity = 'critical' if temp > 90 else 'warning'
                    anomalies.append({
                        'type': 'temperature_spike',
                        'severity': severity,
                        'timestamp': trends['timestamps'][i],
                        'value': temp,
                        'threshold': 85
                    })
        
        # Power consumption anomalies
        powers = [p for p in trends['power'] if p > 0]
        if len(powers) > 5:
            mean_power = statistics.mean(powers)
            stdev_power = statistics.stdev(powers)
            
            for i, power in enumerate(powers):
                if power > mean_power + 2 * stdev_power:
                    anomalies.append({
                        'type': 'power_anomaly',
                        'severity': 'warning',
                        'timestamp': trends['timestamps'][i],
                        'value': power,
                        'expected': mean_power,
                        'deviation': (power - mean_power) / stdev_power
                    })
        
        return anomalies
    
    def calculate_growth_metrics(self, miner_id: int, days: int = 30) -> Dict[str, Any]:
        """Calculate growth and trend metrics for a miner."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get daily averages for trend analysis
            cursor.execute("""
                SELECT 
                    DATE(hour_start) as date,
                    AVG(avg_hashrate_ghs) as daily_hashrate,
                    AVG(avg_power_w) as daily_power,
                    AVG(avg_efficiency_j_th) as daily_efficiency,
                    AVG(uptime_percent) as daily_uptime
                FROM hourly_stats
                WHERE miner_id = ? AND hour_start >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(hour_start)
                ORDER BY date
            """, (miner_id, days))
            
            daily_data = cursor.fetchall()
            
            if len(daily_data) < 7:
                return {'trend': 'insufficient_data', 'metrics': {}, 'period_days': days}
            
            # Calculate trends using linear regression
            dates = [(datetime.strptime(row['date'], '%Y-%m-%d') - datetime.strptime(daily_data[0]['date'], '%Y-%m-%d')).days for row in daily_data]
            
            trends = {}
            metrics = ['daily_hashrate', 'daily_power', 'daily_efficiency', 'daily_uptime']
            
            for metric in metrics:
                values = [row[metric] for row in daily_data if row[metric] is not None]
                if len(values) >= len(dates):
                    slope, _ = self._linear_regression(dates, values)
                    trend_direction = 'improving' if slope > 0 else 'declining' if slope < 0 else 'stable'
                    trends[metric] = {
                        'slope': slope,
                        'direction': trend_direction,
                        'current_value': values[-1] if values else 0,
                        'period_change': values[-1] - values[0] if len(values) >= 2 else 0
                    }
            
            # Overall trend assessment
            positive_trends = sum(1 for t in trends.values() if t['direction'] == 'improving')
            negative_trends = sum(1 for t in trends.values() if t['direction'] == 'declining')
            
            if positive_trends > negative_trends:
                overall_trend = 'improving'
            elif negative_trends > positive_trends:
                overall_trend = 'declining'
            else:
                overall_trend = 'stable'
            
            return {
                'trend': overall_trend,
                'metrics': trends,
                'period_days': days,
                'data_points': len(daily_data)
            }
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        """Simple linear regression to calculate slope and intercept."""
        n = len(x)
        if n < 2:
            return 0, 0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        # Calculate slope (m) and intercept (b)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept
    
    def generate_fleet_insights(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive fleet insights and recommendations."""
        analytics = self.db.get_fleet_analytics(days)
        
        insights = {
            'summary': analytics['fleet_stats'],
            'performance_insights': [],
            'operational_insights': [],
            'financial_insights': [],
            'recommendations': []
        }
        
        # Performance insights
        avg_uptime = analytics['fleet_stats']['avg_uptime']
        if avg_uptime < 95:
            insights['performance_insights'].append({
                'type': 'uptime_concern',
                'message': f"Fleet uptime ({avg_uptime:.1f}%) is below optimal (95%)",
                'impact': 'medium'
            })
        
        avg_efficiency = analytics['fleet_stats']['avg_efficiency']
        if avg_efficiency > 16:
            insights['performance_insights'].append({
                'type': 'efficiency_concern',
                'message': f"Fleet efficiency ({avg_efficiency:.1f} J/TH) could be improved",
                'impact': 'low'
            })
        
        # Operational insights
        if analytics['problem_miners']:
            insights['operational_insights'].append({
                'type': 'problem_miners',
                'message': f"{len(analytics['problem_miners'])} miners need attention",
                'details': analytics['problem_miners'],
                'impact': 'high'
            })
        
        # Financial insights (basic estimates)
        total_power = analytics['fleet_stats']['total_power']
        daily_power_cost = total_power * 24 * 0.10  # Assume $0.10/kWh
        
        insights['financial_insights'].append({
            'type': 'daily_power_cost',
            'message': f"Estimated daily power cost: ${daily_power_cost:.2f}",
            'value': daily_power_cost
        })
        
        # Generate recommendations
        if avg_uptime < 95:
            insights['recommendations'].append("Focus on improving network stability and power reliability")
        
        if analytics['problem_miners']:
            insights['recommendations'].append("Address issues with underperforming miners to improve fleet efficiency")
        
        if avg_efficiency > 15:
            insights['recommendations'].append("Consider optimizing voltage/frequency settings for better energy efficiency")
        
        return insights


class PredictiveAnalyzer:
    """Predictive analysis for maintenance and optimization."""
    
    def __init__(self, db: BitaxeDatabase):
        """Initialize with database connection."""
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def predict_maintenance_needs(self, miner_id: int) -> Dict[str, Any]:
        """Predict maintenance needs based on performance trends."""
        trends = self.db.get_performance_trends(miner_id, 168)  # 7 days
        
        predictions = {
            'maintenance_score': 0,  # 0-100, higher means more urgent
            'predicted_issues': [],
            'recommendations': [],
            'confidence': 0
        }
        
        if not trends['hashrate']:
            return predictions
        
        # Analyze temperature trends
        temps = [t for t in trends['temperature'] if t > 0]
        if temps:
            avg_temp = statistics.mean(temps)
            temp_trend = temps[-5:] if len(temps) >= 5 else temps
            temp_increasing = len(temp_trend) > 1 and temp_trend[-1] > temp_trend[0]
            
            if avg_temp > 80 or (temp_increasing and avg_temp > 75):
                predictions['predicted_issues'].append({
                    'type': 'thermal_stress',
                    'probability': 0.7 if temp_increasing else 0.5,
                    'timeframe': '1-2 weeks',
                    'description': 'Rising temperatures may indicate thermal paste degradation or fan issues'
                })
                predictions['recommendations'].append("Schedule thermal maintenance check")
        
        # Analyze hashrate degradation
        hashrates = [h for h in trends['hashrate'] if h > 0]
        if len(hashrates) >= 10:
            recent_hashrate = statistics.mean(hashrates[-5:])
            older_hashrate = statistics.mean(hashrates[:5])
            degradation = (older_hashrate - recent_hashrate) / older_hashrate
            
            if degradation > 0.05:  # 5% degradation
                predictions['predicted_issues'].append({
                    'type': 'performance_degradation',
                    'probability': 0.6,
                    'timeframe': '2-4 weeks',
                    'description': f'Hashrate has declined by {degradation:.1%} over monitoring period'
                })
                predictions['recommendations'].append("Investigate hardware health and settings")
        
        # Analyze efficiency trends
        efficiencies = [e for e in trends['efficiency'] if e > 0]
        if len(efficiencies) >= 10:
            recent_efficiency = statistics.mean(efficiencies[-5:])
            older_efficiency = statistics.mean(efficiencies[:5])
            efficiency_change = (recent_efficiency - older_efficiency) / older_efficiency
            
            if efficiency_change > 0.1:  # 10% worse efficiency
                predictions['predicted_issues'].append({
                    'type': 'efficiency_decline',
                    'probability': 0.5,
                    'timeframe': '1-3 weeks',
                    'description': 'Power efficiency declining, may indicate component wear'
                })
                predictions['recommendations'].append("Review power supply and component health")
        
        # Calculate overall maintenance score
        issue_scores = [issue['probability'] * 30 for issue in predictions['predicted_issues']]
        predictions['maintenance_score'] = min(sum(issue_scores), 100)
        predictions['confidence'] = min(len(trends['hashrate']) / 50, 1.0)  # More data = higher confidence
        
        return predictions
    
    def optimal_settings_recommendation(self, miner_id: int) -> Dict[str, Any]:
        """Recommend optimal settings based on performance analysis."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get recent performance data with settings
            cursor.execute("""
                SELECT 
                    voltage_asic_set_v,
                    frequency_set_mhz,
                    AVG(hashrate_ghs) as avg_hashrate,
                    AVG(power_w) as avg_power,
                    AVG(temp_asic_c) as avg_temp,
                    AVG(efficiency_j_th) as avg_efficiency,
                    COUNT(*) as samples
                FROM raw_metrics
                WHERE miner_id = ? AND timestamp >= datetime('now', '-7 days')
                  AND voltage_asic_set_v > 0 AND frequency_set_mhz > 0
                GROUP BY 
                    ROUND(voltage_asic_set_v, 3),
                    ROUND(frequency_set_mhz, 0)
                HAVING samples >= 10
                ORDER BY avg_efficiency ASC, avg_hashrate DESC
            """, (miner_id,))
            
            settings_data = cursor.fetchall()
            
            if not settings_data:
                return {'recommendation': 'insufficient_data'}
            
            # Find optimal settings based on efficiency and temperature
            best_settings = None
            best_score = 0
            
            for setting in settings_data:
                # Score based on efficiency (lower is better), hashrate (higher is better), and temperature (lower is better)
                efficiency_score = max(0, 1 - (setting['avg_efficiency'] - 12) / 10)  # Normalize around 12 J/TH
                hashrate_score = setting['avg_hashrate'] / 1000  # Normalize hashrate
                temp_score = max(0, 1 - max(0, setting['avg_temp'] - 70) / 20)  # Penalty above 70°C
                
                combined_score = (efficiency_score * 0.4 + hashrate_score * 0.4 + temp_score * 0.2)
                
                if combined_score > best_score and setting['avg_temp'] < 85:
                    best_score = combined_score
                    best_settings = setting
            
            if best_settings:
                return {
                    'recommendation': 'optimized_settings',
                    'voltage': round(best_settings['voltage_asic_set_v'], 3),
                    'frequency': int(best_settings['frequency_set_mhz']),
                    'expected_performance': {
                        'hashrate_ghs': round(best_settings['avg_hashrate'], 1),
                        'power_w': round(best_settings['avg_power'], 1),
                        'efficiency_j_th': round(best_settings['avg_efficiency'], 1),
                        'temperature_c': round(best_settings['avg_temp'], 1)
                    },
                    'confidence': min(best_settings['samples'] / 100, 1.0)
                }
            else:
                return {'recommendation': 'current_settings_optimal'}