// Dashboard JavaScript for Bitaxe Monitor

class BitaxeDashboard {
    constructor() {
        this.refreshInterval = null;
        this.refreshRate = 5000; // 5 seconds
        this.isRefreshing = true;
        
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
        try {
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
            this.updateLastUpdate();
            this.hideError();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError(`Failed to load data: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    updateFleetStats(stats) {
        document.getElementById('total-miners').textContent = stats.total_miners;
        document.getElementById('online-miners').textContent = stats.online_miners;
        document.getElementById('offline-miners').textContent = stats.offline_miners;
        document.getElementById('total-hashrate').textContent = stats.total_hashrate_ghs.toFixed(1);
        document.getElementById('total-power').textContent = stats.total_power_w.toFixed(1);
        document.getElementById('avg-temp').textContent = `${stats.average_temp_c.toFixed(1)}°C`;
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
                
                <div class="miner-metrics">
                    <div class="metric-item">
                        <div class="metric-label">Hashrate</div>
                        <div class="metric-value">
                            ${miner.hashrate_ghs.toFixed(1)} 
                            <span class="metric-unit">GH/s</span>
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
                        <div class="metric-label">ASIC Temp</div>
                        <div class="metric-value ${tempClass}">
                            ${miner.temp_asic_c.toFixed(1)}
                            <span class="metric-unit">°C</span>
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
                        <div class="metric-label">Frequency</div>
                        <div class="metric-value">
                            ${miner.frequency_set_mhz.toFixed(0)} 
                            <span class="metric-unit">MHz</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Voltage</div>
                        <div class="metric-value">
                            ${miner.voltage_asic_actual_v.toFixed(3)} 
                            <span class="metric-unit">V</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Shares A/R</div>
                        <div class="metric-value">
                            ${miner.shares_accepted}/${miner.shares_rejected}
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">Rejection Rate</div>
                        <div class="metric-value">
                            ${miner.rejection_rate_percent.toFixed(2)}
                            <span class="metric-unit">%</span>
                        </div>
                    </div>
                    
                    <div class="metric-item">
                        <div class="metric-label">WiFi Signal</div>
                        <div class="metric-value">
                            ${miner.wifi_rssi} 
                            <span class="metric-unit">dBm</span>
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
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BitaxeDashboard();
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