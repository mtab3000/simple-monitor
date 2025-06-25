"""Unit tests for the analytics module."""

import pytest
import tempfile
import os
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database import BitaxeDatabase
from src.analytics import PerformanceAnalyzer, PredictiveAnalyzer


class TestPerformanceAnalyzer:
    """Test suite for PerformanceAnalyzer class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with sample data for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = BitaxeDatabase(db_path)
        
        # Insert sample miner and data
        miner_id = db.add_or_update_miner('192.168.1.45', 'test_miner', 934.3)
        
        # Insert hourly stats for testing
        sample_stats = []
        base_time = datetime.now() - timedelta(hours=48)
        
        for i in range(48):  # 48 hours of data
            hour_start = base_time + timedelta(hours=i)
            sample_stats.append({
                'miner_id': miner_id,
                'hour_start': hour_start.strftime('%Y-%m-%d %H:%M:%S'),
                'samples_count': 10,
                'uptime_percent': 95.0 + (i % 10),  # Varying uptime
                'avg_hashrate_ghs': 930 + (i % 20),  # Varying hashrate
                'min_hashrate_ghs': 920 + (i % 15),
                'max_hashrate_ghs': 940 + (i % 25),
                'avg_temp_asic_c': 60 + (i % 15),  # Varying temperature
                'max_temp_asic_c': 65 + (i % 20),
                'avg_power_w': 14 + (i % 5) * 0.2,
                'max_power_w': 15 + (i % 8) * 0.1,
                'avg_efficiency_j_th': 15 + (i % 10) * 0.1,
                'total_shares_accepted': 1000 + i * 10,
                'total_shares_rejected': i % 5,
                'rejection_rate_percent': (i % 5) / 10,  # Low rejection rate
                'avg_wifi_rssi': -50 - (i % 10),
                'status_distribution': '{"online": 10}'
            })
        
        # Insert hourly stats directly
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for stats in sample_stats:
                cursor.execute("""
                    INSERT INTO hourly_stats (
                        miner_id, hour_start, samples_count, uptime_percent,
                        avg_hashrate_ghs, min_hashrate_ghs, max_hashrate_ghs,
                        avg_temp_asic_c, max_temp_asic_c, avg_power_w, max_power_w,
                        avg_efficiency_j_th, total_shares_accepted, total_shares_rejected,
                        rejection_rate_percent, avg_wifi_rssi, status_distribution
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stats['miner_id'], stats['hour_start'], stats['samples_count'],
                    stats['uptime_percent'], stats['avg_hashrate_ghs'], stats['min_hashrate_ghs'],
                    stats['max_hashrate_ghs'], stats['avg_temp_asic_c'], stats['max_temp_asic_c'],
                    stats['avg_power_w'], stats['max_power_w'], stats['avg_efficiency_j_th'],
                    stats['total_shares_accepted'], stats['total_shares_rejected'],
                    stats['rejection_rate_percent'], stats['avg_wifi_rssi'], stats['status_distribution']
                ))
            conn.commit()
        
        yield db, miner_id
        
        # Cleanup
        try:
            os.unlink(db_path)
        except OSError:
            pass

    @pytest.fixture
    def analyzer(self, temp_db):
        """Create a PerformanceAnalyzer instance for testing."""
        db, miner_id = temp_db
        return PerformanceAnalyzer(db), miner_id

    def test_calculate_efficiency_score(self, analyzer):
        """Test efficiency score calculation."""
        analyzer_instance, miner_id = analyzer
        
        # Calculate efficiency score
        score_result = analyzer_instance.calculate_efficiency_score(miner_id, hours=24)
        
        # Verify result structure
        assert isinstance(score_result, dict)
        assert 'score' in score_result
        assert 'grade' in score_result
        assert 'factors' in score_result
        assert 'recommendations' in score_result
        
        # Check score is within valid range
        assert 0 <= score_result['score'] <= 100
        
        # Check grade is valid
        valid_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']
        assert score_result['grade'] in valid_grades
        
        # Check factors structure
        factors = score_result['factors']
        expected_factors = ['uptime', 'hashrate_stability', 'temperature', 'efficiency', 'rejection_rate']
        
        for factor in expected_factors:
            assert factor in factors
            assert 'value' in factors[factor]
            assert 'score' in factors[factor]
            assert 'weight' in factors[factor]
            assert 0 <= factors[factor]['score'] <= 1
        
        # Check recommendations is a list
        assert isinstance(score_result['recommendations'], list)

    def test_detect_anomalies(self, analyzer):
        """Test anomaly detection functionality."""
        analyzer_instance, miner_id = analyzer
        
        # Detect anomalies
        anomalies = analyzer_instance.detect_anomalies(miner_id, hours=24)
        
        # Verify result structure
        assert isinstance(anomalies, list)
        
        # Check anomaly structure if any found
        for anomaly in anomalies:
            assert isinstance(anomaly, dict)
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert 'timestamp' in anomaly
            assert anomaly['severity'] in ['warning', 'critical']

    def test_calculate_growth_metrics(self, analyzer):
        """Test growth metrics calculation."""
        analyzer_instance, miner_id = analyzer
        
        # Calculate growth metrics
        growth_result = analyzer_instance.calculate_growth_metrics(miner_id, days=2)
        
        # Verify result structure
        assert isinstance(growth_result, dict)
        assert 'trend' in growth_result
        assert 'metrics' in growth_result
        assert 'period_days' in growth_result
        
        if growth_result['trend'] != 'insufficient_data':
            assert growth_result['trend'] in ['improving', 'declining', 'stable']
            
            # Check metrics structure
            metrics = growth_result['metrics']
            for metric_name, metric_data in metrics.items():
                assert 'slope' in metric_data
                assert 'direction' in metric_data
                assert 'current_value' in metric_data
                assert 'period_change' in metric_data
                assert metric_data['direction'] in ['improving', 'declining', 'stable']

    def test_generate_fleet_insights(self, analyzer):
        """Test fleet insights generation."""
        analyzer_instance, miner_id = analyzer
        
        # Generate fleet insights
        insights = analyzer_instance.generate_fleet_insights(days=2)
        
        # Verify result structure
        assert isinstance(insights, dict)
        assert 'summary' in insights
        assert 'performance_insights' in insights
        assert 'operational_insights' in insights
        assert 'financial_insights' in insights
        assert 'recommendations' in insights
        
        # Check that all insights are lists
        assert isinstance(insights['performance_insights'], list)
        assert isinstance(insights['operational_insights'], list)
        assert isinstance(insights['financial_insights'], list)
        assert isinstance(insights['recommendations'], list)
        
        # Check summary structure
        summary = insights['summary']
        assert 'total_miners' in summary
        assert 'avg_uptime' in summary
        assert 'total_hashrate' in summary

    def test_performance_grade_mapping(self, analyzer):
        """Test performance grade mapping function."""
        analyzer_instance, _ = analyzer
        
        # Test grade boundaries
        test_cases = [
            (95, 'A+'),
            (90, 'A+'),
            (87, 'A'),
            (82, 'B+'),
            (77, 'B'),
            (72, 'C+'),
            (67, 'C'),
            (62, 'D'),
            (50, 'F')
        ]
        
        for score, expected_grade in test_cases:
            grade = analyzer_instance._get_performance_grade(score)
            assert grade == expected_grade

    def test_linear_regression(self, analyzer):
        """Test linear regression function."""
        analyzer_instance, _ = analyzer
        
        # Test with known data
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # Perfect linear relationship: y = 2x
        
        slope, intercept = analyzer_instance._linear_regression(x, y)
        
        # Should get slope ~2 and intercept ~0
        assert abs(slope - 2.0) < 0.01
        assert abs(intercept - 0.0) < 0.01
        
        # Test with edge cases
        slope_empty, intercept_empty = analyzer_instance._linear_regression([], [])
        assert slope_empty == 0
        assert intercept_empty == 0
        
        slope_single, intercept_single = analyzer_instance._linear_regression([1], [2])
        assert slope_single == 0
        assert intercept_single == 0

    def test_recommendation_generation(self, analyzer):
        """Test recommendation generation logic."""
        analyzer_instance, _ = analyzer
        
        # Test with poor performance factors
        poor_factors = {
            'uptime': {'score': 0.5},
            'hashrate_stability': {'score': 0.6},
            'temperature': {'score': 0.4},
            'efficiency': {'score': 0.7},
            'rejection_rate': {'score': 0.3}
        }
        
        recommendations = analyzer_instance._generate_recommendations(poor_factors)
        
        # Should generate recommendations for poor scores
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Test with good performance factors
        good_factors = {
            'uptime': {'score': 0.95},
            'hashrate_stability': {'score': 0.90},
            'temperature': {'score': 0.85},
            'efficiency': {'score': 0.88},
            'rejection_rate': {'score': 0.92}
        }
        
        good_recommendations = analyzer_instance._generate_recommendations(good_factors)
        
        # Should generate fewer or no recommendations for good scores
        assert len(good_recommendations) <= len(recommendations)


class TestPredictiveAnalyzer:
    """Test suite for PredictiveAnalyzer class."""

    @pytest.fixture
    def temp_db_with_trends(self):
        """Create a database with trending data for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = BitaxeDatabase(db_path)
        miner_id = db.add_or_update_miner('192.168.1.45', 'test_miner', 934.3)
        
        # Insert trending performance data (declining over time)
        trends_data = []
        base_time = datetime.now() - timedelta(hours=168)  # 7 days ago
        
        for i in range(168):  # 168 hours of data
            hour_start = base_time + timedelta(hours=i)
            
            # Simulate declining performance over time
            degradation_factor = 1 - (i / 1000)  # Gradual decline
            temp_increase = i * 0.1  # Temperature increasing
            
            trends_data.append({
                'miner_id': miner_id,
                'hour_start': hour_start.strftime('%Y-%m-%d %H:%M:%S'),
                'samples_count': 10,
                'uptime_percent': 95.0 * degradation_factor,
                'avg_hashrate_ghs': 934 * degradation_factor,
                'avg_temp_asic_c': 60 + temp_increase,
                'avg_efficiency_j_th': 15 + (i * 0.01),  # Efficiency degrading
                'total_shares_accepted': 1000,
                'total_shares_rejected': max(1, int(i * 0.1)),  # Increasing rejections
                'rejection_rate_percent': min(10, i * 0.05)
            })
        
        # Insert data
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for data in trends_data:
                cursor.execute("""
                    INSERT INTO hourly_stats (
                        miner_id, hour_start, samples_count, uptime_percent,
                        avg_hashrate_ghs, min_hashrate_ghs, max_hashrate_ghs,
                        avg_temp_asic_c, max_temp_asic_c, avg_power_w, max_power_w,
                        avg_efficiency_j_th, total_shares_accepted, total_shares_rejected,
                        rejection_rate_percent, avg_wifi_rssi, status_distribution
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['miner_id'], data['hour_start'], data['samples_count'],
                    data['uptime_percent'], data['avg_hashrate_ghs'], 0, 0,
                    data['avg_temp_asic_c'], 0, 14, 15,
                    data['avg_efficiency_j_th'], data['total_shares_accepted'],
                    data['total_shares_rejected'], data['rejection_rate_percent'],
                    -50, '{"online": 10}'
                ))
            conn.commit()
        
        yield db, miner_id
        
        try:
            os.unlink(db_path)
        except OSError:
            pass

    @pytest.fixture
    def predictor(self, temp_db_with_trends):
        """Create a PredictiveAnalyzer instance for testing."""
        db, miner_id = temp_db_with_trends
        return PredictiveAnalyzer(db), miner_id

    def test_predict_maintenance_needs(self, predictor):
        """Test maintenance prediction functionality."""
        predictor_instance, miner_id = predictor
        
        # Predict maintenance needs
        prediction = predictor_instance.predict_maintenance_needs(miner_id)
        
        # Verify result structure
        assert isinstance(prediction, dict)
        assert 'maintenance_score' in prediction
        assert 'predicted_issues' in prediction
        assert 'recommendations' in prediction
        assert 'confidence' in prediction
        
        # Check score range
        assert 0 <= prediction['maintenance_score'] <= 100
        assert 0 <= prediction['confidence'] <= 1
        
        # Check predicted issues structure
        for issue in prediction['predicted_issues']:
            assert 'type' in issue
            assert 'probability' in issue
            assert 'timeframe' in issue
            assert 'description' in issue
            assert 0 <= issue['probability'] <= 1
        
        # Check recommendations is a list
        assert isinstance(prediction['recommendations'], list)

    def test_optimal_settings_recommendation(self, predictor):
        """Test optimal settings recommendation."""
        predictor_instance, miner_id = predictor
        
        # Need to insert some raw metrics with settings for this test
        db = predictor_instance.db
        
        # Insert sample raw metrics with different settings
        sample_metrics = []
        base_time = datetime.now() - timedelta(days=7)
        
        settings_combinations = [
            (1.000, 450, 930, 14.0, 60.0, 15.2),
            (1.010, 460, 940, 14.5, 62.0, 15.4),
            (1.020, 470, 950, 15.0, 65.0, 15.8),
            (0.990, 440, 920, 13.5, 58.0, 14.7)
        ]
        
        for i, (voltage, freq, hashrate, power, temp, efficiency) in enumerate(settings_combinations):
            for j in range(20):  # 20 samples per setting
                timestamp = base_time + timedelta(hours=i*24 + j)
                sample_metrics.append({
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'miner_ip': '192.168.1.45',
                    'hostname': 'test_miner',
                    'status': 'online',
                    'hashrate_ghs': hashrate + j,
                    'expected_hashrate_ghs': 934.3,
                    'hashrate_ratio_percent': 100.0,
                    'temp_asic_c': temp + j * 0.1,
                    'temp_vr_c': 53.0,
                    'power_w': power + j * 0.01,
                    'voltage_asic_set_v': voltage,
                    'voltage_asic_actual_v': voltage - 0.02,
                    'voltage_device_v': 5.0,
                    'frequency_set_mhz': freq,
                    'efficiency_j_th': efficiency + j * 0.01,
                    'shares_accepted': 1000,
                    'shares_rejected': 1,
                    'uptime_hours': 24.0,
                    'wifi_rssi': -50,
                    'fan_speed_percent': 50,
                    'fan_rpm': 4000,
                    'free_heap_bytes': 8000000,
                    'overclock_enabled': True,
                    'current_a': 9.0,
                    'pool_user': 'test_user',
                    'best_session_diff': '2M'
                })
        
        db.insert_raw_metrics(sample_metrics)
        
        # Get optimal settings recommendation
        recommendation = predictor_instance.optimal_settings_recommendation(miner_id)
        
        # Verify result structure
        assert isinstance(recommendation, dict)
        assert 'recommendation' in recommendation
        
        if recommendation['recommendation'] == 'optimized_settings':
            assert 'voltage' in recommendation
            assert 'frequency' in recommendation
            assert 'expected_performance' in recommendation
            assert 'confidence' in recommendation
            
            # Check performance structure
            performance = recommendation['expected_performance']
            assert 'hashrate_ghs' in performance
            assert 'power_w' in performance
            assert 'efficiency_j_th' in performance
            assert 'temperature_c' in performance

    def test_maintenance_scoring_logic(self, predictor):
        """Test maintenance scoring logic."""
        predictor_instance, miner_id = predictor
        
        # Test with current data (should have some maintenance issues due to trends)
        prediction = predictor_instance.predict_maintenance_needs(miner_id)
        
        # Should detect some issues due to declining trends
        assert prediction['maintenance_score'] > 0
        
        # Should have reasonable confidence with 168 hours of data
        assert prediction['confidence'] > 0.5

    def test_thermal_stress_prediction(self, predictor):
        """Test thermal stress prediction specifically."""
        predictor_instance, miner_id = predictor
        
        prediction = predictor_instance.predict_maintenance_needs(miner_id)
        
        # Check if thermal stress is detected (temperature was increasing in test data)
        thermal_issues = [issue for issue in prediction['predicted_issues'] 
                         if issue['type'] == 'thermal_stress']
        
        # Should detect thermal stress due to increasing temperature trend
        assert len(thermal_issues) > 0
        
        # Check thermal recommendations
        thermal_recommendations = [rec for rec in prediction['recommendations'] 
                                 if 'thermal' in rec.lower() or 'temperature' in rec.lower()]
        assert len(thermal_recommendations) > 0

    def test_performance_degradation_detection(self, predictor):
        """Test performance degradation detection."""
        predictor_instance, miner_id = predictor
        
        prediction = predictor_instance.predict_maintenance_needs(miner_id)
        
        # Check for performance degradation (hashrate was declining in test data)
        degradation_issues = [issue for issue in prediction['predicted_issues'] 
                            if issue['type'] == 'performance_degradation']
        
        # Should detect performance degradation
        assert len(degradation_issues) > 0
        
        # Verify degradation issue structure
        for issue in degradation_issues:
            assert issue['probability'] > 0
            assert 'week' in issue['timeframe'].lower()

    def test_efficiency_decline_detection(self, predictor):
        """Test efficiency decline detection."""
        predictor_instance, miner_id = predictor
        
        prediction = predictor_instance.predict_maintenance_needs(miner_id)
        
        # Check for efficiency decline (efficiency was degrading in test data)
        efficiency_issues = [issue for issue in prediction['predicted_issues'] 
                           if issue['type'] == 'efficiency_decline']
        
        # Should detect efficiency decline
        assert len(efficiency_issues) > 0

    def test_edge_cases(self, predictor):
        """Test edge cases in predictive analysis."""
        predictor_instance, _ = predictor
        
        # Test with non-existent miner
        empty_prediction = predictor_instance.predict_maintenance_needs(999)
        assert empty_prediction['maintenance_score'] == 0
        assert empty_prediction['confidence'] == 0
        assert len(empty_prediction['predicted_issues']) == 0
        
        # Test optimal settings with no data
        empty_recommendation = predictor_instance.optimal_settings_recommendation(999)
        assert empty_recommendation['recommendation'] == 'insufficient_data'


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics functionality."""

    @pytest.fixture
    def integrated_system(self):
        """Create a complete integrated analytics system for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = BitaxeDatabase(db_path)
        
        # Create realistic test scenario with multiple miners
        miners_data = [
            ('192.168.1.45', 'high_performer', 934.3),
            ('192.168.1.46', 'average_miner', 920.0),
            ('192.168.1.47', 'problem_miner', 900.0)
        ]
        
        miner_ids = []
        for ip, hostname, expected_hashrate in miners_data:
            miner_id = db.add_or_update_miner(ip, hostname, expected_hashrate)
            miner_ids.append(miner_id)
        
        # Insert realistic performance data
        base_time = datetime.now() - timedelta(days=7)
        metrics_data = []
        
        for day in range(7):
            for hour in range(24):
                timestamp = base_time + timedelta(days=day, hours=hour)
                
                for i, (miner_id, (ip, hostname, expected)) in enumerate(zip(miner_ids, miners_data)):
                    # Create different performance profiles
                    if hostname == 'high_performer':
                        hashrate = expected * (0.98 + 0.04 * (hour % 12) / 12)
                        temp = 55 + hour % 10
                        uptime = 99.5
                        efficiency = 14.5 + (hour % 6) * 0.1
                    elif hostname == 'average_miner':
                        hashrate = expected * (0.95 + 0.06 * (hour % 8) / 8)
                        temp = 60 + hour % 15
                        uptime = 95.0 + (hour % 10)
                        efficiency = 15.5 + (hour % 8) * 0.1
                    else:  # problem_miner
                        hashrate = expected * (0.85 + 0.10 * (hour % 6) / 6)
                        temp = 70 + hour % 20  # Running hot
                        uptime = 85.0 + (hour % 20)  # Poor uptime
                        efficiency = 17.0 + (hour % 10) * 0.2  # Poor efficiency
                    
                    metrics_data.append({
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'miner_ip': ip,
                        'hostname': hostname,
                        'status': 'online' if uptime > 90 else 'offline',
                        'hashrate_ghs': hashrate,
                        'expected_hashrate_ghs': expected,
                        'hashrate_ratio_percent': (hashrate / expected) * 100,
                        'temp_asic_c': temp,
                        'temp_vr_c': temp - 5,
                        'power_w': 14 + i * 0.5,
                        'voltage_asic_set_v': 1.0 + i * 0.01,
                        'voltage_asic_actual_v': 0.98 + i * 0.01,
                        'voltage_device_v': 5.0,
                        'frequency_set_mhz': 450 + i * 10,
                        'efficiency_j_th': efficiency,
                        'shares_accepted': 1000 + hour * 10,
                        'shares_rejected': max(1, int(temp - 60)),  # More rejects when hot
                        'uptime_hours': 24.0,
                        'wifi_rssi': -50 - i * 5,
                        'fan_speed_percent': min(100, int(temp)),
                        'fan_rpm': 3000 + int(temp) * 10,
                        'free_heap_bytes': 8000000,
                        'overclock_enabled': True,
                        'current_a': 9.0 + i * 0.2,
                        'pool_user': f'user_{i}',
                        'best_session_diff': f'{2 + i}M'
                    })
        
        db.insert_raw_metrics(metrics_data)
        db.generate_hourly_stats(start_time=base_time)
        
        analyzer = PerformanceAnalyzer(db)
        predictor = PredictiveAnalyzer(db)
        
        yield db, analyzer, predictor, miner_ids
        
        try:
            os.unlink(db_path)
        except OSError:
            pass

    def test_complete_analytics_workflow(self, integrated_system):
        """Test complete analytics workflow with realistic data."""
        db, analyzer, predictor, miner_ids = integrated_system
        
        # Test performance analysis for each miner
        for miner_id in miner_ids:
            # Calculate efficiency scores
            score = analyzer.calculate_efficiency_score(miner_id)
            assert isinstance(score, dict)
            assert 'score' in score
            assert 'grade' in score
            
            # Detect anomalies
            anomalies = analyzer.detect_anomalies(miner_id)
            assert isinstance(anomalies, list)
            
            # Calculate growth metrics
            growth = analyzer.calculate_growth_metrics(miner_id, days=7)
            assert isinstance(growth, dict)
            
            # Predict maintenance needs
            maintenance = predictor.predict_maintenance_needs(miner_id)
            assert isinstance(maintenance, dict)
            assert 'maintenance_score' in maintenance

    def test_fleet_analytics_comparison(self, integrated_system):
        """Test fleet analytics with multiple miners."""
        db, analyzer, predictor, miner_ids = integrated_system
        
        # Get fleet insights
        insights = analyzer.generate_fleet_insights(days=7)
        
        # Should have detected 3 miners
        assert insights['summary']['total_miners'] == 3
        
        # Should have performance insights about variations
        assert len(insights['performance_insights']) > 0
        
        # Should have fleet-wide recommendations
        assert len(insights['recommendations']) > 0

    def test_comparative_performance_analysis(self, integrated_system):
        """Test comparative performance analysis between miners."""
        db, analyzer, predictor, miner_ids = integrated_system
        
        scores = []
        for miner_id in miner_ids:
            score = analyzer.calculate_efficiency_score(miner_id)
            scores.append((miner_id, score['score'], score['grade']))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # High performer should have best score
        best_miner_id = scores[0][0]
        worst_miner_id = scores[-1][0]
        
        # Verify performance order matches expected
        assert scores[0][1] > scores[-1][1]  # Best > Worst
        
        # High performer should have A/B grade, problem miner should have lower grade
        best_grade = scores[0][2]
        worst_grade = scores[-1][2]
        
        grade_order = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']
        best_index = grade_order.index(best_grade) if best_grade in grade_order else 7
        worst_index = grade_order.index(worst_grade) if worst_grade in grade_order else 7
        
        assert best_index <= worst_index  # Better grade should have lower index

    def test_predictive_maintenance_alerts(self, integrated_system):
        """Test predictive maintenance alert generation."""
        db, analyzer, predictor, miner_ids = integrated_system
        
        maintenance_alerts = []
        
        for miner_id in miner_ids:
            prediction = predictor.predict_maintenance_needs(miner_id)
            if prediction['maintenance_score'] > 50:  # Needs attention
                maintenance_alerts.append((miner_id, prediction))
        
        # Problem miner should trigger maintenance alerts
        assert len(maintenance_alerts) > 0
        
        # Check alert details
        for miner_id, prediction in maintenance_alerts:
            assert len(prediction['predicted_issues']) > 0
            assert len(prediction['recommendations']) > 0

    def test_settings_optimization_workflow(self, integrated_system):
        """Test complete settings optimization workflow."""
        db, analyzer, predictor, miner_ids = integrated_system
        
        # Test optimal settings recommendation for each miner
        for miner_id in miner_ids:
            recommendation = predictor.optimal_settings_recommendation(miner_id)
            
            # Should provide some form of recommendation
            assert 'recommendation' in recommendation
            
            # If optimized settings available, should be reasonable
            if recommendation['recommendation'] == 'optimized_settings':
                assert 'voltage' in recommendation
                assert 'frequency' in recommendation
                assert 0.9 <= recommendation['voltage'] <= 1.1  # Reasonable voltage
                assert 400 <= recommendation['frequency'] <= 500  # Reasonable frequency

    def test_long_term_trend_analysis(self, integrated_system):
        """Test long-term trend analysis capabilities."""
        db, analyzer, predictor, miner_ids = integrated_system
        
        # Analyze trends for each miner
        for miner_id in miner_ids:
            trends = db.get_performance_trends(miner_id, hours=168)  # 7 days
            
            # Should have sufficient data points
            assert len(trends['hashrate']) > 100  # Should have many data points
            
            # Calculate growth metrics
            growth = analyzer.calculate_growth_metrics(miner_id, days=7)
            
            if growth['trend'] != 'insufficient_data':
                # Should classify trend appropriately
                assert growth['trend'] in ['improving', 'declining', 'stable']
                
                # Should have metrics for key performance indicators
                assert 'daily_hashrate' in growth['metrics']
                assert 'daily_efficiency' in growth['metrics']
                assert 'daily_uptime' in growth['metrics']