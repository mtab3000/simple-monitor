# 📊 Database & Analytics Documentation

Advanced data storage and analytics system for Bitaxe Gamma Monitor with SQLite database, performance analysis, and predictive insights.

## 🏗️ Database Architecture

### Database Schema

The enhanced system uses SQLite for robust data storage with the following tables:

#### Core Tables

**`miners`** - Miner configuration and metadata
- `id` - Primary key
- `ip_address` - Unique miner IP address
- `hostname` - Miner hostname/name
- `expected_hashrate_ghs` - Expected performance baseline
- `created_at` / `updated_at` - Timestamps
- `is_active` - Status flag

**`raw_metrics`** - Time-series data (detailed measurements)
- All original CSV fields plus optimized storage
- JSON field for extensibility
- Foreign key to miners table
- Indexes for performance

**`hourly_stats`** - Aggregated hourly performance data
- Statistical summaries (avg, min, max)
- Uptime percentages
- Status distribution
- Rejection rates

**`daily_stats`** - Daily performance summaries
- Growth trend analysis
- Revenue estimates
- Peak performance tracking

**`fleet_stats`** - Fleet-wide metrics
- Total fleet performance
- Cross-miner comparisons
- Efficiency tracking

**`alerts`** - Performance alerts and anomalies
- Automated alert generation
- Severity levels
- Resolution tracking

### Performance Optimizations

- **Write-Ahead Logging (WAL)** for concurrent access
- **Strategic indexes** on timestamp and miner_id columns
- **Batch processing** for efficient data insertion
- **Automatic cleanup** of old raw data (30-day retention)
- **Database vacuum** for optimization

## 📈 Analytics Engine

### Performance Analysis

#### Efficiency Scoring System
Comprehensive performance scoring based on weighted factors:

- **Uptime (25% weight)** - Target: 95%+ uptime
- **Hashrate Stability (30% weight)** - Consistent performance
- **Temperature Management (20% weight)** - Optimal 60-75°C range
- **Energy Efficiency (15% weight)** - Lower J/TH is better
- **Share Rejection (10% weight)** - Target: <2% rejection rate

**Grade Scale:**
- A+ (90-100%): Excellent performance
- A (85-89%): Very good performance  
- B+ (80-84%): Good performance
- B (75-79%): Acceptable performance
- C+ (70-74%): Below average
- C (65-69%): Poor performance
- D (60-64%): Very poor performance
- F (<60%): Critical issues

#### Anomaly Detection
Statistical analysis to identify:
- **Hashrate anomalies** - Deviations beyond 2 standard deviations
- **Temperature spikes** - Above 85°C warning, 90°C critical
- **Power consumption anomalies** - Unusual power draw patterns

#### Growth Metrics
- **Linear regression** trend analysis over 30-day periods
- **Performance trajectory** prediction
- **Improvement/degradation** tracking

### Predictive Analytics

#### Maintenance Prediction
Machine learning-style analysis for:
- **Thermal stress prediction** - Based on temperature trends
- **Performance degradation** - Hashrate decline detection
- **Efficiency decline** - Power consumption increases
- **Maintenance scoring** - 0-100 urgency scale

#### Optimization Recommendations
Data-driven suggestions for:
- **Voltage/frequency optimization** - Best settings based on historical data
- **Cooling improvements** - Temperature management
- **Performance tuning** - Efficiency optimization

## 🔄 Data Migration

### CSV to Database Migration

```bash
# Migrate existing CSV data
python src/data_migration.py --action migrate

# Verify migration
python src/data_migration.py --action verify

# Export back to CSV (backup)
python src/data_migration.py --action export
```

### Migration Features
- **Automatic backup** of original CSV files
- **Data validation** and cleaning during migration
- **Progress tracking** for large datasets
- **Verification tools** to ensure data integrity
- **Rollback capability** via CSV export

## 🚀 Enhanced Collector

### New Features

#### Database Integration
- **Dual storage** - Both CSV and database (configurable)
- **Batch processing** - Efficient data insertion
- **Error recovery** - Graceful handling of database issues

#### Background Analytics
- **Scheduled analytics** - Hourly performance analysis
- **Automated alerts** - Anomaly detection and notification
- **Maintenance scheduling** - Predictive maintenance alerts

#### Advanced Configuration

```yaml
# Enhanced collector configuration
database_path: "data/bitaxe_monitor.db"
enable_database: true
enable_analytics: true
analytics_interval: 3600      # 1 hour
maintenance_interval: 86400   # 24 hours

alert_thresholds:
  temp_critical: 90
  temp_warning: 85
  hashrate_drop_percent: 20
  rejection_rate_percent: 5
  efficiency_threshold: 20

log_level: "INFO"
log_file: "data/collector.log"
```

## 📊 Usage Examples

### Running Enhanced Monitoring

```bash
# Start enhanced monitoring with database
python enhanced_monitor.py

# Custom configuration
python enhanced_monitor.py --config my_config.yaml --log-level DEBUG

# Analytics interval override
python enhanced_monitor.py --analytics-interval 1800  # 30 minutes
```

### Data Analysis Examples

#### Python API Usage

```python
from src.database import BitaxeDatabase
from src.analytics import PerformanceAnalyzer

# Initialize
db = BitaxeDatabase()
analyzer = PerformanceAnalyzer(db)

# Get miner efficiency score
score = analyzer.calculate_efficiency_score(miner_id=1)
print(f"Performance Grade: {score['grade']}")
print(f"Score: {score['score']}%")

# Get performance trends
trends = db.get_performance_trends(miner_id=1, hours=24)
print(f"Average hashrate: {sum(trends['hashrate'])/len(trends['hashrate']):.1f} GH/s")

# Fleet analytics
fleet_data = db.get_fleet_analytics(days=7)
print(f"Fleet efficiency: {fleet_data['fleet_stats']['avg_efficiency']:.1f} J/TH")
```

#### SQL Queries

```sql
-- Top performing miners last 24 hours
SELECT 
    m.hostname,
    AVG(hs.avg_hashrate_ghs) as avg_hashrate,
    AVG(hs.uptime_percent) as uptime,
    AVG(hs.avg_efficiency_j_th) as efficiency
FROM miners m
JOIN hourly_stats hs ON m.id = hs.miner_id
WHERE hs.hour_start >= datetime('now', '-24 hours')
GROUP BY m.id
ORDER BY uptime DESC, avg_hashrate DESC;

-- Alert summary
SELECT 
    alert_type,
    severity,
    COUNT(*) as count
FROM alerts 
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY alert_type, severity
ORDER BY count DESC;
```

## 🔧 Advanced Features

### Performance Monitoring

#### Real-time Metrics
- **Collection statistics** - Success rates, timing
- **Background task status** - Analytics and maintenance
- **Thread monitoring** - Concurrent operation tracking

#### Alert System
- **Automated detection** - Statistical anomaly detection
- **Severity levels** - Info, warning, critical
- **Alert resolution** - Manual and automatic resolution
- **Alert history** - Complete audit trail

### Data Retention

#### Automatic Cleanup
- **Raw data** - 30-day retention (configurable)
- **Hourly stats** - 1-year retention
- **Daily stats** - Permanent retention
- **Alerts** - 6-month retention

#### Backup Strategy
- **Database backups** - Automatic SQLite backups
- **CSV exports** - Regular data exports
- **Migration tools** - Easy data portability

## 🔍 Troubleshooting

### Common Issues

#### Database Problems
```bash
# Check database integrity
sqlite3 data/bitaxe_monitor.db "PRAGMA integrity_check;"

# Manual vacuum
sqlite3 data/bitaxe_monitor.db "VACUUM;"

# Reset database (WARNING: destroys data)
rm data/bitaxe_monitor.db
```

#### Migration Issues
```bash
# Re-run migration with verbose logging
python src/data_migration.py --action migrate --log-level DEBUG

# Verify specific data
python src/data_migration.py --action verify
```

#### Analytics Problems
```bash
# Check analytics logs
tail -f data/collector.log | grep analytics

# Manual analytics run
python -c "
from src.database import BitaxeDatabase
from src.analytics import PerformanceAnalyzer
db = BitaxeDatabase()
db.generate_hourly_stats()
print('Analytics completed')
"
```

### Performance Optimization

#### Large Datasets
- **Batch size tuning** - Adjust batch_size in database.py
- **Index optimization** - Custom indexes for specific queries
- **Cleanup frequency** - Adjust retention periods

#### Memory Usage
- **Connection pooling** - SQLite handles this automatically
- **Query optimization** - Use appropriate LIMIT clauses
- **Background tasks** - Monitor thread memory usage

## 🔮 Future Enhancements

### Planned Features
- **Machine learning models** - Advanced predictive analytics
- **Custom alert rules** - User-defined alert conditions
- **Historical comparison** - Year-over-year performance
- **Export formats** - JSON, Parquet, InfluxDB integration
- **REST API** - External system integration
- **Dashboard widgets** - Configurable monitoring displays

### Extensibility
- **Plugin system** - Custom analytics modules
- **External databases** - PostgreSQL, InfluxDB support
- **Cloud storage** - S3, GCS integration
- **Notification systems** - Email, Slack, webhooks

## 📝 Technical Notes

### Database Design Principles
- **Normalization** - Proper relational design
- **Performance first** - Optimized for time-series data
- **Extensibility** - JSON fields for future data
- **Backwards compatibility** - CSV export maintains compatibility

### Analytics Algorithms
- **Statistical methods** - Standard deviation, linear regression
- **Time-series analysis** - Trend detection, seasonality
- **Anomaly detection** - Threshold-based and statistical
- **Predictive modeling** - Pattern recognition for maintenance

### Security Considerations
- **Local storage** - No external data transmission
- **File permissions** - Restricted database access
- **Input validation** - Sanitized data insertion
- **SQL injection protection** - Parameterized queries

---

For technical support or feature requests, see the main [README.md](../README.md) or create an issue on GitHub.