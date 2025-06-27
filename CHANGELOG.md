# Changelog

## [Debug Branch] - 2025-06-27

### Fixed
- **Efficiency Calculation Formula**: Corrected the efficiency calculation in `enhanced_collector.py` to properly display J/TH (Joules per Terahash) values instead of showing 0.0
  - **Previous formula**: `(power_w * 1000) / (hashrate_ghs * 1000)` = `power_w / hashrate_ghs` (incorrect, resulted in W/GH)
  - **Corrected formula**: `power_w / (hashrate_ghs / 1000)` (correct, results in J/TH)
  - **Impact**: Web dashboard now correctly displays efficiency values like "22.2 J/TH" instead of "0.0 J/TH"
  - **Example**: For a miner with 900 GH/s hashrate and 20W power consumption:
    - Old result: 0.02 (displayed as 0.0 J/TH)
    - New result: 22.22 J/TH (correct efficiency)

### Added
- **Test Coverage**: Added specific test case `test_efficiency_calculation_formula` to verify correct efficiency calculations
- **Edge Case Handling**: Verified zero hashrate scenarios properly return 0 efficiency

### Technical Details
- **File Modified**: `src/enhanced_collector.py` line 139
- **Formula**: Efficiency (J/TH) = Power (W) ÷ (Hashrate (GH/s) ÷ 1000)
- **Units**: Converts power from Watts to Joules per second, hashrate from GH/s to TH/s
- **Verification**: All core modules still import and function correctly