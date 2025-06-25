#!/usr/bin/env python3
"""
Tuning Process Monitor
Tracks miner restarts and uptime changes during 20h tuning process
"""

import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def monitor_tuning_process():
    """Monitor the tuning process and track restarts"""
    db_path = "data/bitaxe_monitor.db"
    
    print(f"🔧 Starting tuning process monitor at {datetime.now()}")
    print("Monitoring 20h tuning process with expected restarts every ~10min")
    print("Script changes frequency/voltage → triggers miner restarts")
    print("Press Ctrl+C to stop monitoring\n")
    
    last_uptimes = {}
    restart_count = {}
    
    try:
        while True:
            try:
                conn = sqlite3.connect(db_path, timeout=10.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get latest uptime for each miner
                cursor.execute("""
                    SELECT r.uptime_hours, r.timestamp, m.ip_address, m.hostname,
                           r.hashrate_ghs, r.temp_asic_c, r.frequency_set_mhz, r.voltage_asic_set_v
                    FROM raw_metrics r
                    JOIN miners m ON r.miner_id = m.id
                    WHERE r.timestamp = (
                        SELECT MAX(timestamp) FROM raw_metrics r2 
                        WHERE r2.miner_id = r.miner_id
                    )
                    ORDER BY m.ip_address
                """)
                
                rows = cursor.fetchall()
                conn.close()
                
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] Miner Status:")
                
                for row in rows:
                    ip = row['ip_address']
                    hostname = row['hostname']
                    uptime = row['uptime_hours']
                    hashrate = row['hashrate_ghs']
                    temp = row['temp_asic_c']
                    freq = row['frequency_set_mhz']
                    voltage = row['voltage_asic_set_v']
                    
                    # Check for restart (uptime decreased significantly)
                    # During tuning: expect restarts every ~10 minutes due to script changes
                    if ip in last_uptimes:
                        if uptime < (last_uptimes[ip] - 0.1):  # 6 minute threshold for tuning
                            restart_count[ip] = restart_count.get(ip, 0) + 1
                            restart_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"  🔄 TUNING RESTART: {hostname} ({ip})")
                            print(f"     Uptime: {last_uptimes[ip]:.2f}h → {uptime:.2f}h")
                            print(f"     Restart #{restart_count[ip]} at {restart_time}")
                            print(f"     Expected: Script changing freq/voltage every ~10min")
                            
                            # Log restart to file
                            with open('tuning_restarts.log', 'a') as f:
                                f.write(f"{restart_time},{ip},{hostname},{last_uptimes[ip]:.2f},{uptime:.2f},{restart_count[ip]}\n")
                    
                    last_uptimes[ip] = uptime
                    
                    # Display current status
                    print(f"  {hostname:12} ({ip:13}) | "
                          f"Uptime: {uptime:5.1f}h | "
                          f"Hash: {hashrate:6.1f} GH/s | "
                          f"Temp: {temp:4.1f}°C | "
                          f"Freq: {freq:3.0f}MHz | "
                          f"Volt: {voltage:.3f}V | "
                          f"Restarts: {restart_count.get(ip, 0)}")
                
                # Summary
                total_restarts = sum(restart_count.values())
                print(f"\n💡 Total restarts detected: {total_restarts}")
                
                if total_restarts > 0:
                    print("📋 Restart log saved to: tuning_restarts.log")
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Tuning monitor stopped at {datetime.now()}")
        if restart_count:
            print("\n📊 Final restart summary:")
            for ip, count in restart_count.items():
                print(f"  {ip}: {count} restarts")
        else:
            print("✅ No restarts detected during monitoring period")

if __name__ == "__main__":
    monitor_tuning_process()