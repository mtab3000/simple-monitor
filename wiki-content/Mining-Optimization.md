# Mining Optimization

## Sweet Spot Analysis

The Mining Optimization Analyzer helps you find optimal voltage/frequency combinations that maximize both performance and stability.

### Basic Analysis
```bash
# Analyze voltage/frequency combinations for sweet spots
python src/optimization_analyzer.py --hours 24 --show-chart

# Analyze specific miner performance
python src/optimization_analyzer.py --miner-ip 192.168.1.45 --hours 48

# Export detailed analysis results
python src/optimization_analyzer.py --hours 168 --output weekly_optimization.json

# Custom CSV path and time window
python src/optimization_analyzer.py --csv-path custom_metrics.csv --hours 72 --show-chart
```

## Algorithm Details

### Performance Score (Higher = Better)

```
📈 Hashrate (40%)
   └─ Higher average preferred

⚡ Efficiency (30%) 
   └─ Lower J/TH preferred

🌡️ Temperature (20%)
   └─ Lower temps preferred  

💪 Power Ratio (10%)
   └─ GH/s per watt
```

### Stability Score (Lower = Better)

```
📈 Hashrate CV (50%)
   └─ Coefficient of variation

🌡️ Temp StdDev (30%)
   └─ Temperature consistency

⚡ Eff StdDev (20%)
   └─ Efficiency variation
```

### Sweet Spot Formula

```
🏆 Sweet Spot Score = 
   Performance Score ÷ 
   (1 + Stability Score/100)
```

**Perfect Balance:**
- High performance ✅
- Low variation ✅  
- Optimal efficiency ✅

## Key Features

### Smart Detection
- 🎯 **Sweet Spot Discovery** - Find optimal voltage/frequency balance
- 🔍 **Benchmark Detection** - Auto-identifies testing sessions  
- 📊 **Statistical Analysis** - Uses coefficient of variation
- 🏆 **Performance Ranking** - Ranks all combinations

### Intelligent Analysis
- 📈 **Stability Scoring** - Measures hashrate consistency
- 🌡️ **Temperature Monitoring** - Thermal analysis & warnings
- ⚡ **Efficiency Metrics** - J/TH optimization tracking
- 📋 **Smart Recommendations** - Actionable improvement suggestions

## Analysis Output

### Performance Reports
- 📊 **Ranked Settings** by sweet spot score
- 📈 **Statistical Metrics** for each combination  
- 📋 **Visual Charts** in beautiful text format
- 🎯 **Optimal Ranges** for voltage/frequency
- 🔍 **Benchmark Detection** with detailed analysis

### Export & Integration
- 📄 **JSON Export** for detailed analysis
- 📊 **CSV Compatibility** with existing data
- 🔗 **API Ready** for automation
- 📱 **Human Readable** summary reports
- ⚡ **Real-time Analysis** on live data

## Sample Output

```
🔍 Analyzing mining optimization data...
   Time window: 24 hours
   Data source: metrics.csv

📈 ANALYSIS SUMMARY
   Miners analyzed: 3
   Settings tested: 3
   Optimal settings found: 3

🏆 TOP OPTIMAL SETTINGS:
   1. 1.003V @ 463MHz
      Score: 375.59, Hashrate: 952.2 GH/s
      Stability: 5.2, Efficiency: 15.1 J/TH

📊 VOLTAGE/FREQUENCY PERFORMANCE COMPARISON
======================================================================
Rank Voltage  Freq    Score   Hashrate   Efficiency Stability
----------------------------------------------------------------------
1    1.003V   463MHz  375.59  952.2 GH/s 15.1 J/TH  5.2      
2    1.003V   458MHz  370.41  941.6 GH/s 15.0 J/TH  5.5      
3    1.027V   452MHz  353.36  894.5 GH/s 15.0 J/TH  5.3      
======================================================================
💡 Lower stability score is better (less variation)
🎯 Higher sweet spot score indicates optimal balance
```

## Best Practices

### Data Collection
- Run miners with different voltage/frequency settings
- Collect data for at least 24 hours per configuration
- Ensure stable network conditions during testing
- Monitor temperature and power consumption

### Analysis Tips
- Use longer time windows (48-168 hours) for more accurate results
- Compare multiple miners for fleet optimization
- Consider environmental factors (ambient temperature)
- Validate recommendations with extended testing

### Optimization Workflow
1. **Baseline** - Record current performance
2. **Test** - Try different voltage/frequency combinations
3. **Analyze** - Run optimization analyzer
4. **Implement** - Apply recommended settings
5. **Monitor** - Verify improvements over time