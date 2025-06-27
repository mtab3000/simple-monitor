// Dashboard JavaScript for Bitaxe Monitor

class BitaxeDashboard {
    constructor() {
        this.refreshInterval = null;
        this.refreshRate = 30000; // 30 seconds
        this.isRefreshing = true;
        this.charts = {}; // Store chart instances
        this.historicalData = {}; // Store historical data for charts
        this.isLoading = false; // Prevent recursive loading
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        this.loadData();
    }
    
    setupEventListeners() {
        // Refresh toggle button
        const refreshToggle = document.getElementById('refresh-toggle');
        refreshToggle.addEventListener('click', () => this.toggleAutoRefresh());
        
        // Error message close button
        const errorClose = document.getElementById('error-close');
        errorClose.addEventListener('click', () => this.hideError());
    }
    
    toggleAutoRefresh() {
        const refreshToggle = document.getElementById('refresh-toggle');
        
        if (this.isRefreshing) {
            this.stopAutoRefresh();
            refreshToggle.innerHTML = '<i class="fas fa-play"></i> OFF';
            refreshToggle.classList.add('paused');
            this.isRefreshing = false;
        } else {
            this.startAutoRefresh();
            refreshToggle.innerHTML = '<i class="fas fa-pause"></i> ON';
            refreshToggle.classList.remove('paused');
            this.isRefreshing = true;
        }
    }
    
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadData();
        }, this.refreshRate);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    async loadData() {
        // Prevent recursive calls
        if (this.isLoading) {
            return;
        }
        
        try {
            this.isLoading = true;
            this.showLoading();
            
            // Load fleet stats and miner data in parallel
            const [fleetResponse, statusResponse] = await Promise.all([
                fetch('/api/fleet'),
                fetch('/api/status')
            ]);
            
            if (!fleetResponse.ok || !statusResponse.ok) {
                throw new Error('Failed to fetch data from server');
            }
            
            const fleetData = await fleetResponse.json();
            const statusData = await statusResponse.json();
            
            if (!fleetData.success || !statusData.success) {
                throw new Error(fleetData.error || statusData.error || 'Unknown error');
            }
            
            this.updateFleetStats(fleetData.data);
            this.updateMinersGrid(statusData.data.miners || []);
            this.updateCharts(statusData.data.miners || []);
            this.updateLastUpdate();
            this.hideError();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError(`Failed to load data: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    updateFleetStats(stats) {
        document.getElementById('total-miners').textContent = stats.total_miners;
        document.getElementById('online-miners').textContent = stats.online_miners;
        document.getElementById('offline-miners').textContent = stats.offline_miners;
        document.getElementById('total-hashrate').textContent = stats.total_hashrate_ghs.toFixed(1);
        document.getElementById('total-power').textContent = stats.total_power_w.toFixed(1);
        document.getElementById('fleet-efficiency').textContent = stats.average_efficiency_j_th.toFixed(1);
    }
    
    updateMinersGrid(miners) {
        const grid = document.getElementById('miners-grid');
        
        if (miners.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: #64748b;">
                    <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <div>No miners data available. Make sure the monitoring system is collecting data.</div>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = miners.map(miner => this.createMinerCard(miner)).join('');
    }
    
    createMinerCard(miner) {
        const statusClass = this.getStatusClass(miner.status);
        const performancePercent = miner.hashrate_ratio_percent;
        const performanceClass = this.getPerformanceClass(performancePercent);
        const tempClass = this.getTemperatureClass(miner.temp_asic_c);
        const offlineClass = miner.status !== 'online' ? 'offline' : '';
        
        return `
            <div class="miner-card ${offlineClass}">
                <div class="miner-header">
                    <div>
                        <div class="miner-title">${this.escapeHtml(miner.hostname)}</div>
                        <div class="miner-ip">${miner.ip}</div>
                    </div>
                    <div class="miner-status ${statusClass}">
                        ${this.getStatusText(miner.status)}
                    </div>
                </div>
                
                <div class="performance-bar">
                    <div class="performance-label">
                        <span>Hashrate Performance</span>
                        <span>${performancePercent.toFixed(1)}%</span>
                    </div>
                    <div class="performance-progress">
                        <div class="performance-fill ${performanceClass}" 
                             style="width: ${Math.min(performancePercent, 100)}%"></div>
                    </div>
                </div>
                
                <div class="miner-metrics extended">
                    <div class="metric-item">
                        <div class="metric-label">Input Voltage</div>
                        <div class="metric-value">
                            5.00 
                            <span class="metric-unit">V</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">ASIC Temp</div>
                        <div class="metric-value ${tempClass}">
                            ${miner.temp_asic_c.toFixed(1)}
                            <span class="metric-unit">°C</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">VR Temp</div>
                        <div class="metric-value ${this.getTemperatureClass(miner.temp_vr_c)}">
                            ${miner.temp_vr_c.toFixed(1)}
                            <span class="metric-unit">°C</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Hashrate</div>
                        <div class="metric-value">
                            ${miner.hashrate_ghs.toFixed(1)} 
                            <span class="metric-unit">GH/s</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Expected Hash</div>
                        <div class="metric-value">
                            ${miner.expected_hashrate_ghs.toFixed(1)} 
                            <span class="metric-unit">GH/s</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Efficiency</div>
                        <div class="metric-value">
                            ${miner.efficiency_j_th.toFixed(1)} 
                            <span class="metric-unit">J/TH</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Power</div>
                        <div class="metric-value">
                            ${miner.power_w.toFixed(1)} 
                            <span class="metric-unit">W</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Voltage Set</div>
                        <div class="metric-value">
                            ${miner.voltage_asic_set_v.toFixed(3)} 
                            <span class="metric-unit">V</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Voltage Actual</div>
                        <div class="metric-value">
                            ${miner.voltage_asic_actual_v.toFixed(3)} 
                            <span class="metric-unit">V</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Frequency</div>
                        <div class="metric-value">
                            ${miner.frequency_set_mhz.toFixed(0)} 
                            <span class="metric-unit">MHz</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Shares A/R</div>
                        <div class="metric-value">
                            ${miner.shares_accepted}/${miner.shares_rejected}
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Uptime</div>
                        <div class="metric-value">
                            ${miner.uptime_hours.toFixed(1)} 
                            <span class="metric-unit">hrs</span>
                        </div>
                    </div>
                </div>
                
                <div class="miner-charts">
                    <div class="chart-container">
                        <div class="chart-title">Hashrate vs Expected</div>
                        <canvas id="hashrate-chart-${miner.ip.replace(/\./g, '-')}" class="chart-canvas"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <div class="chart-title">Efficiency & ASIC Voltage</div>
                        <canvas id="efficiency-chart-${miner.ip.replace(/\./g, '-')}" class="chart-canvas"></canvas>
                    </div>
                </div>
            </div>
        `;
    }
    
    getStatusClass(status) {
        switch (status) {
            case 'online':
                return 'status-online';
            case 'offline':
            case 'connection_failed':
                return 'status-offline';
            default:
                return 'status-warning';
        }
    }
    
    getStatusText(status) {
        switch (status) {
            case 'online':
                return '🟢 Online';
            case 'offline':
            case 'connection_failed':
                return '🔴 Offline';
            case 'overheating':
                return '🔥 Hot';
            case 'no_hashrate':
                return '⚠️ No Hash';
            case 'high_rejection':
                return '❌ High Reject';
            case 'wifi_issues':
                return '📶 WiFi Issue';
            case 'timeout':
                return '⏰ Timeout';
            default:
                return '❓ Unknown';
        }
    }
    
    getPerformanceClass(percentage) {
        if (percentage >= 95) return '';
        if (percentage >= 80) return 'warning';
        return 'danger';
    }
    
    getTemperatureClass(temp) {
        if (temp >= 85) return 'temp-high';
        if (temp >= 80) return 'temp-warning';
        return '';
    }
    
    updateLastUpdate() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        document.getElementById('last-update').textContent = timeString;
    }
    
    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        
        errorText.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => this.hideError(), 10000);
    }
    
    hideError() {
        const errorElement = document.getElementById('error-message');
        errorElement.style.display = 'none';
    }
    
    showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }
    
    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateCharts(miners) {
        // Debounce chart updates to prevent excessive redraws
        if (this.chartUpdateTimeout) {
            clearTimeout(this.chartUpdateTimeout);
        }
        
        this.chartUpdateTimeout = setTimeout(() => {
            miners.forEach(miner => {
            const minerId = miner.ip.replace(/\./g, '-');
            
            // Update historical data
            if (!this.historicalData[minerId]) {
                this.historicalData[minerId] = {
                    timestamps: [],
                    hashrate: [],
                    expected_hashrate: [],
                    efficiency: [],
                    voltage_actual: []
                };
            }
            
            const data = this.historicalData[minerId];
            const now = new Date();
            
            // Keep only last 20 data points
            if (data.timestamps.length >= 20) {
                data.timestamps.shift();
                data.hashrate.shift();
                data.expected_hashrate.shift();
                data.efficiency.shift();
                data.voltage_actual.shift();
            }
            
            data.timestamps.push(now.toLocaleTimeString());
            data.hashrate.push(miner.hashrate_ghs);
            data.expected_hashrate.push(miner.expected_hashrate_ghs);
            data.efficiency.push(miner.efficiency_j_th);
            data.voltage_actual.push(miner.voltage_asic_actual_v);
            
            // Create or update charts
            this.createHashrateChart(minerId, data);
            this.createEfficiencyChart(minerId, data);
            });
        }, 100); // 100ms debounce
    }
    
    createHashrateChart(minerId, data) {
        const canvasId = `hashrate-chart-${minerId}`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            // Update existing chart
            this.charts[canvasId].data.labels = data.timestamps;
            this.charts[canvasId].data.datasets[0].data = data.hashrate;
            this.charts[canvasId].data.datasets[1].data = data.expected_hashrate;
            this.charts[canvasId].update('none');
        } else {
            // Create new chart
            this.charts[canvasId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps,
                    datasets: [{
                        label: 'Actual Hashrate',
                        data: data.hashrate,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1,
                        fill: true
                    }, {
                        label: 'Expected Hashrate',
                        data: data.expected_hashrate,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#e2e8f0'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            }
                        },
                        y: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            },
                            title: {
                                display: true,
                                text: 'GH/s',
                                color: '#94a3b8'
                            }
                        }
                    }
                }
            });
        }
    }
    
    createEfficiencyChart(minerId, data) {
        const canvasId = `efficiency-chart-${minerId}`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            // Update existing chart
            this.charts[canvasId].data.labels = data.timestamps;
            this.charts[canvasId].data.datasets[0].data = data.efficiency;
            this.charts[canvasId].data.datasets[1].data = data.voltage_actual;
            this.charts[canvasId].update('none');
        } else {
            // Create new chart
            this.charts[canvasId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps,
                    datasets: [{
                        label: 'Efficiency (J/TH)',
                        data: data.efficiency,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.1,
                        yAxisID: 'y',
                        fill: true
                    }, {
                        label: 'ASIC Voltage (V)',
                        data: data.voltage_actual,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        tension: 0.1,
                        yAxisID: 'y1',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#e2e8f0'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.1)'
                            },
                            title: {
                                display: true,
                                text: 'J/TH',
                                color: '#94a3b8'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            ticks: {
                                color: '#94a3b8'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                            title: {
                                display: true,
                                text: 'Volts',
                                color: '#94a3b8'
                            }
                        }
                    }
                }
            });
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new BitaxeDashboard();
});

// Handle page visibility change to pause/resume auto-refresh
document.addEventListener('visibilitychange', () => {
    const dashboard = window.dashboard;
    if (dashboard) {
        if (document.hidden) {
            dashboard.stopAutoRefresh();
        } else if (dashboard.isRefreshing) {
            dashboard.startAutoRefresh();
        }
    }
});