#!/usr/bin/env python3
"""
Smart Bitaxe Gamma Monitor - Enhanced CLI Viewer
View collected metrics with detailed real-time information
"""

import csv
import argparse
import time
import yaml
import sys
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.text import Text
from rich.columns import Columns

console = Console()

def load_config():
    """Load configuration from config.yaml"""
    # Look for config in project root (parent directory)
    from pathlib import Path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / 'config.yaml'
    
    # Fallback to examples if no config exists
    if not config_path.exists():
        config_path = project_root / 'examples' / 'config.yaml'
    
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        console.print(f"[red]Error: config file not found at {config_path}[/red]")
        console.print("Run setup.py first to create configuration")
        sys.exit(1)

def load_csv_data(csv_path):
    """Load all data from CSV file"""
    # Handle relative paths from project root
    from pathlib import Path
    if not os.path.isabs(csv_path):
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        csv_path = project_root / csv_path
    
    if not os.path.exists(csv_path):
        console.print(f"[red]Error: CSV file {csv_path} not found[/red]")
        console.print("Run: python monitor.py first to generate data")
        sys.exit(1)
    
    data = []
    try:
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert numeric fields with better error handling
                numeric_fields = [
                    'hashrate_th', 'hashrate_ghs', 'expected_hashrate_ghs', 'hashrate_ratio_percent',
                    'temp_asic_c', 'temp_vr_c', 'power_w', 'voltage_device_v', 'voltage_asic_set_v', 
                    'voltage_asic_actual_v', 'current_a', 'frequency_set_mhz', 'efficiency_j_th', 
                    'shares_accepted', 'shares_rejected', 'uptime_seconds', 'uptime_hours', 'wifi_rssi', 
                    'fan_speed_percent', 'fan_rpm', 'free_heap_bytes', 'overclock_enabled'
                ]
                
                for field in numeric_fields:
                    if field in row:
                        try:
                            row[field] = float(row[field])
                        except (ValueError, TypeError):
                            row[field] = 0.0
                    else:
                        row[field] = 0.0
                
                data.append(row)
    except Exception as e:
        console.print(f"[red]Error reading CSV: {e}[/red]")
        sys.exit(1)
    
    return data

def get_latest_data_by_miner(data):
    """Get the latest data point for each miner"""
    latest_by_miner = {}
    for row in data:
        miner_ip = row['miner_ip']
        if miner_ip not in latest_by_miner:
            latest_by_miner[miner_ip] = row
        else:
            # Compare timestamps to keep the latest
            if row['timestamp'] > latest_by_miner[miner_ip]['timestamp']:
                latest_by_miner[miner_ip] = row
    return latest_by_miner

def create_main_table(latest_data, show_detailed=False):
    """Create main miners table"""
    if show_detailed:
        # For detailed view, just show a simple summary table - details are in the panels above
        table = Table(title="⚡ Fleet Summary", box=box.SIMPLE, border_style="blue")
        table.add_column("Miner", style="cyan bold", width=15)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Hashrate", justify="right", style="green", width=12)
        table.add_column("Performance", justify="right", style="yellow", width=12) 
        table.add_column("Temperature", justify="center", style="red", width=15)
        table.add_column("Power", justify="right", style="blue", width=10)
        table.add_column("Efficiency", justify="right", style="yellow", width=12)
    else:
        table = Table(title="⚡ Bitaxe Gamma Fleet Summary", box=box.ROUNDED, border_style="green")
        table.add_column("IP Address", style="cyan bold", width=15, no_wrap=True)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Hashrate\n(GH/s)", justify="right", style="green", width=10)
        table.add_column("Perf\n(%)", justify="right", style="yellow", width=6)
        table.add_column("ASIC T\n(°C)", justify="right", style="red", width=8)
        table.add_column("VR T\n(°C)", justify="right", style="bright_red", width=8)
        table.add_column("Power\n(W)", justify="right", style="blue", width=8)
        table.add_column("Voltage\n(V)", justify="right", style="magenta", width=9)
        table.add_column("Freq\n(MHz)", justify="right", style="cyan", width=8)
        table.add_column("Efficiency\n(J/TH)", justify="right", style="yellow", width=11)
        table.add_column("Uptime\n(hrs)", justify="right", style="dim", width=8)
    
    total_hashrate = 0
    total_power = 0
    online_count = 0
    
    for miner_ip, data in latest_data.items():
        status = data['status']
        
        # Status display with colors
        status_display = get_status_display(status)
        
        if status == 'online':
            online_count += 1
            total_hashrate += data.get('hashrate_ghs', 0)
            total_power += data.get('power_w', 0)
        
        # Format values
        hashrate = f"{data.get('hashrate_ghs', 0):.1f}" if data.get('hashrate_ghs', 0) > 0 else "-"
        perf_ratio = f"{data.get('hashrate_ratio_percent', 0):.0f}" if data.get('hashrate_ratio_percent', 0) > 0 else "-"
        temp_asic = f"{data.get('temp_asic_c', 0):.1f}" if data.get('temp_asic_c', 0) > 0 else "-"
        temp_vr = f"{data.get('temp_vr_c', 0):.1f}" if data.get('temp_vr_c', 0) > 0 else "-"
        power = f"{data.get('power_w', 0):.1f}" if data.get('power_w', 0) > 0 else "-"
        voltage_set = f"{data.get('voltage_asic_set_v', 0):.3f}" if data.get('voltage_asic_set_v', 0) > 0 else "-"
        voltage_actual = f"{data.get('voltage_asic_actual_v', 0):.3f}" if data.get('voltage_asic_actual_v', 0) > 0 else "-"
        freq_set = f"{data.get('frequency_set_mhz', 0)}" if data.get('frequency_set_mhz', 0) > 0 else "-"
        efficiency = f"{data.get('efficiency_j_th', 0):.1f}" if data.get('efficiency_j_th', 0) > 0 else "-"
        fan_speed = f"{data.get('fan_speed_percent', 0)}" if data.get('fan_speed_percent', 0) > 0 else "-"
        uptime_hrs = f"{data.get('uptime_hours', 0):.1f}" if data.get('uptime_hours', 0) > 0 else "-"
        hostname = str(data.get('hostname', 'Unknown'))[:7] if data.get('hostname') else 'Unknown'  # Truncate for display
        free_heap_mb = f"{data.get('free_heap_bytes', 0) / 1024 / 1024:.1f}" if data.get('free_heap_bytes', 0) > 0 else "-"
        overclock = "Y" if data.get('overclock_enabled', 0) else "N"
        current = f"{data.get('current_a', 0):.2f}" if data.get('current_a', 0) > 0 else "-"
        wifi_rssi = f"{data.get('wifi_rssi', 0)}" if data.get('wifi_rssi', 0) != 0 else "-"
        
        if show_detailed:
            miner_name = f"{miner_ip}\n({hostname})"
            temp_combined = f"{temp_asic}°C / {temp_vr}°C"
            hashrate_detailed = f"{hashrate} GH/s"
            perf_detailed = f"{perf_ratio}%"
            power_detailed = f"{power} W"
            efficiency_detailed = f"{efficiency} J/TH"
            
            table.add_row(
                miner_name, status_display, hashrate_detailed, perf_detailed, 
                temp_combined, power_detailed, efficiency_detailed
            )
        else:
            table.add_row(
                miner_ip, status_display, hashrate, perf_ratio, temp_asic, temp_vr, power,
                voltage_actual, freq_set, efficiency, uptime_hrs
            )
    
    # Add summary row
    total_miners = len(latest_data)
    avg_efficiency = total_power / (total_hashrate / 1000) if total_hashrate > 0 else 0  # J/TH
    
    table.add_section()
    if show_detailed:
        table.add_row(
            f"[bold]FLEET TOTAL[/bold]",
            f"[green]{online_count}/{total_miners} online[/green]",
            f"[bold]{total_hashrate:.1f} GH/s[/bold]",
            "-",
            "-",
            f"[bold]{total_power:.1f} W[/bold]",
            f"[bold]{avg_efficiency:.1f} J/TH[/bold]"
        )
    else:
        table.add_row(
            f"[bold]TOTAL ({online_count}/{total_miners})[/bold]",
            f"[green]{online_count} online[/green]",
            f"[bold]{total_hashrate:.1f}[/bold]", "-", "-", "-",
            f"[bold]{total_power:.1f}[/bold]", "-", "-",
            f"[bold]{avg_efficiency:.1f}[/bold]", "-"
        )
    
    return table

def get_status_display(status):
    """Get colored status display with Unicode icons"""
    status_map = {
        'online': '[green]🟢 ONLINE[/green]',
        'no_hashrate': '[yellow]⚠️  NO HASH[/yellow]',
        'overheating': '[red]🔥 HOT[/red]',
        'wifi_issues': '[bright_magenta]📶 WIFI[/bright_magenta]',
        'high_rejection': '[red]❌ REJECT[/red]',
        'timeout': '[red]⏰ TIMEOUT[/red]',
        'connection_failed': '[red]🔴 OFFLINE[/red]',
        'high_power': '[yellow]⚡ HI PWR[/yellow]',
        'low_power': '[yellow]🔋 LO PWR[/yellow]',
        'no_temp_sensor': '[yellow]🌡️  NO TEMP[/yellow]'
    }
    return status_map.get(status, f'[red]❓ {status.upper()}[/red]')

def create_fleet_stats_panel(latest_data):
    """Create fleet statistics panel"""
    total_miners = len(latest_data)
    online_miners = [m for m in latest_data.values() if m['status'] == 'online']
    online_count = len(online_miners)
    offline_count = total_miners - online_count
    
    if online_miners:
        total_hashrate = sum(m.get('hashrate_ghs', 0) for m in online_miners)
        total_power = sum(m.get('power_w', 0) for m in online_miners)
        avg_temp_asic = sum(m.get('temp_asic_c', 0) for m in online_miners) / len(online_miners)
        avg_temp_vr = sum(m.get('temp_vr_c', 0) for m in online_miners) / len(online_miners)
        avg_efficiency = total_power / (total_hashrate / 1000) if total_hashrate > 0 else 0  # J/TH
        total_shares = sum(m.get('shares_accepted', 0) for m in online_miners)
        total_rejected = sum(m.get('shares_rejected', 0) for m in online_miners)
        rejection_rate = (total_rejected / (total_shares + total_rejected) * 100) if (total_shares + total_rejected) > 0 else 0
    else:
        total_hashrate = total_power = avg_temp_asic = avg_temp_vr = avg_efficiency = 0
        total_shares = total_rejected = rejection_rate = 0
    
    # Create visual indicators
    online_percentage = (online_count / total_miners * 100) if total_miners > 0 else 0
    online_bar = "█" * int(online_percentage // 10) + "░" * (10 - int(online_percentage // 10))
    
    # Fleet health indicators
    fleet_health = "🟢 Excellent" if online_percentage >= 90 else "🟡 Good" if online_percentage >= 70 else "🔴 Poor"
    
    # Power efficiency rating
    if avg_efficiency <= 20:
        efficiency_rating = "🏆 Excellent"
    elif avg_efficiency <= 25:
        efficiency_rating = "🥈 Good"
    elif avg_efficiency <= 30:
        efficiency_rating = "🥉 Average"
    else:
        efficiency_rating = "⚠️ Poor"
    
    stats_text = f"""🏭 [bold blue]Fleet Overview[/bold blue]  {fleet_health}

📊 [bold cyan]Fleet Status[/bold cyan]
   Miners: [bold]{total_miners}[/bold] total  │  🟢 {online_count} online  │  🔴 {offline_count} offline
   Health: {online_bar} {online_percentage:.0f}%

⚡ [bold green]Performance Metrics[/bold green]
   🔗 Total Hashrate: [bold green]{total_hashrate:.1f} GH/s[/bold green] [dim]({total_hashrate/1000:.2f} TH/s)[/dim]
   ⚡ Total Power: [bold blue]{total_power:.1f} W[/bold blue]
   📊 Fleet Efficiency: [bold yellow]{avg_efficiency:.1f} J/TH[/bold yellow] {efficiency_rating}

🌡️ [bold red]Temperature Monitoring[/bold red]
   🔥 Average ASIC: [red]{avg_temp_asic:.1f}°C[/red]
   🌡️ Average VR: [bright_red]{avg_temp_vr:.1f}°C[/bright_red]

💎 [bold yellow]Mining Statistics[/bold yellow]
   ✅ Shares Accepted: [green]{total_shares:,}[/green]
   ❌ Shares Rejected: [red]{total_rejected:,}[/red]
   📈 Rejection Rate: [{'red' if rejection_rate > 5 else 'green'}]{rejection_rate:.2f}%[/{'red' if rejection_rate > 5 else 'green'}]
"""
    
    return Panel(stats_text.strip(), title="🏭 Fleet Dashboard", border_style="bright_blue", padding=(0, 1))

def create_individual_panels(latest_data):
    """Create individual miner panels for detailed view"""
    panels = []
    
    for miner_ip, data in latest_data.items():
        status = data['status']
        
        if status == 'online':
            panel_color = "bright_green"
            status_text = "[green]🟢 ONLINE[/green]"
        elif status in ['timeout', 'connection_failed']:
            panel_color = "bright_red"
            status_text = "[red]🔴 OFFLINE[/red]"
        else:
            panel_color = "bright_yellow"
            status_text = get_status_display(status)
        
        # Performance indicators
        perf_ratio = data.get('hashrate_ratio_percent', 0)
        perf_bar = "█" * int(perf_ratio // 10) + "░" * (10 - int(perf_ratio // 10))
        
        # Temperature warnings
        asic_temp = data.get('temp_asic_c', 0)
        vr_temp = data.get('temp_vr_c', 0)
        temp_warning = " 🔥" if asic_temp > 80 or vr_temp > 80 else ""
        
        content = f"""📊 {status_text}

🔗 [bold green]Mining Performance[/bold green]
   Hashrate: [green]{data.get('hashrate_ghs', 0):.1f} GH/s[/green] ({perf_ratio:.0f}% of target)
   Expected: [dim]{data.get('expected_hashrate_ghs', 0):.1f} GH/s[/dim]
   Performance: {perf_bar} {perf_ratio:.0f}%

🌡️ [bold red]Temperatures[/bold red]{temp_warning}
   ASIC: [red]{asic_temp:.1f}°C[/red]  │  VR: [bright_red]{vr_temp:.1f}°C[/bright_red]

⚡ [bold blue]Power & Voltage[/bold blue]
   Power: [blue]{data.get('power_w', 0):.1f}W[/blue]  │  Current: [purple]{data.get('current_a', 0):.2f}A[/purple]
   🔋 Set: [magenta]{data.get('voltage_asic_set_v', 0):.3f}V[/magenta]  │  Actual: [magenta]{data.get('voltage_asic_actual_v', 0):.3f}V[/magenta]
   📱 Device: [dim]{data.get('voltage_device_v', 0):.3f}V[/dim]

⚙️ [bold cyan]Configuration[/bold cyan]
   Frequency: [cyan]{data.get('frequency_set_mhz', 0)} MHz[/cyan]
   Efficiency: [yellow]{data.get('efficiency_j_th', 0):.1f} J/TH[/yellow]
   Overclock: {'[green]🚀 Enabled[/green]' if data.get('overclock_enabled', 0) else '[dim]❌ Disabled[/dim]'}

💎 [bold yellow]Mining Stats[/bold yellow]
   ✅ Accepted: [green]{data.get('shares_accepted', 0):,}[/green]
   ❌ Rejected: [red]{data.get('shares_rejected', 0):,}[/red]
   🏆 Best Session: [bold]{data.get('best_session_diff', '0')}[/bold]

🖥️ [bold dim]System Status[/bold dim]
   🌪️ Fan: {data.get('fan_speed_percent', 0)}% ([dim]{data.get('fan_rpm', 0)} RPM[/dim])
   💾 Memory: [cyan]{data.get('free_heap_bytes', 0) / 1024 / 1024:.1f} MB free[/cyan]
   📶 WiFi: [green]{data.get('wifi_rssi', 0)} dBm[/green]
   ⏰ Uptime: [dim]{data.get('uptime_hours', 0):.1f} hrs[/dim]"""
        
        if data.get('pool_user') and data.get('pool_user') != 'Unknown':
            pool_short = data['pool_user'][:15] + "..." if len(data['pool_user']) > 15 else data['pool_user']
            content += f"\n\n🏊 [bold cyan]Pool[/bold cyan]: [dim]{pool_short}[/dim]"
        
        # Create title with hostname and IP
        hostname = data.get('hostname', 'Unknown') or 'Unknown'
        if hostname.endswith('*'):
            hostname = f"({hostname})"
        title = f"⛏️ [bold white]{hostname}[/bold white] [dim]│ {miner_ip}[/dim]"
        
        panels.append(Panel(content, title=title, border_style=panel_color, padding=(1, 1)))
    
    return panels

def show_summary(config, detailed=False):
    """Show summary view"""
    csv_path = config['csv_path']
    console.print(f"\n[bold blue]Loading data from {csv_path}...[/bold blue]")
    
    data = load_csv_data(csv_path)
    if not data:
        console.print("[yellow]No data found in CSV file[/yellow]")
        return
    
    latest_data = get_latest_data_by_miner(data)
    console.print(f"[green]Loaded {len(data)} records for {len(latest_data)} miners[/green]\n")
    
    if detailed:
        # Show individual panels
        panels = create_individual_panels(latest_data)
        console.print(Columns(panels, equal=True, expand=True))
        console.print("\n")
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(create_fleet_stats_panel(latest_data), size=8),
        Layout(create_main_table(latest_data, show_detailed=detailed))
    )
    
    console.print(layout)

def show_live(config, detailed=False):
    """Show live updating view"""
    csv_path = config['csv_path']
    
    console.print("🚀 [bold green]Starting live monitor...[/bold green]")
    console.print("📊 [dim]Press Ctrl+C to exit - Updates every 5 seconds[/dim]\n")
    
    try:
        while True:
            # Clear screen and show current data
            console.clear()
            
            # Print header
            console.print("\n[bold bright_cyan]⚡ Smart Bitaxe Gamma Monitor ⚡[/bold bright_cyan]")
            console.print("[dim]Live Mode - Real-time Fleet Management[/dim]\n")
            
            try:
                data = load_csv_data(csv_path)
                if not data:
                    console.print("[yellow]No data available[/yellow]")
                else:
                    latest_data = get_latest_data_by_miner(data)
                    
                    # Show fleet stats
                    console.print(create_fleet_stats_panel(latest_data))
                    console.print()
                    
                    # Show main table
                    console.print(create_main_table(latest_data, show_detailed=detailed))
                    
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            # Show update time
            current_time = datetime.now().strftime("%H:%M:%S")
            console.print(f"\n[dim]Last updated: {current_time} | Press Ctrl+C to exit[/dim]")
            
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Live monitor stopped[/yellow]")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Smart Bitaxe Gamma Monitor - Enhanced CLI Viewer")
    parser.add_argument("--summary", action="store_true", help="Show summary of all miners")
    parser.add_argument("--live", action="store_true", help="Show live updating view")
    parser.add_argument("--detailed", action="store_true", help="Show detailed view with more metrics")
    
    args = parser.parse_args()
    
    if not args.summary and not args.live:
        parser.print_help()
        console.print("\n[yellow]Please specify either --summary or --live mode[/yellow]")
        console.print("[cyan]Examples:[/cyan]")
        console.print("  python cli_view.py --summary")
        console.print("  python cli_view.py --live")
        console.print("  python cli_view.py --summary --detailed")
        console.print("  python cli_view.py --live --detailed")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    console.print("\n[bold bright_cyan]⚡ Smart Bitaxe Gamma Monitor ⚡[/bold bright_cyan]")
    console.print("[dim]Enhanced CLI Viewer with Real-time Fleet Management[/dim]\n")
    
    if args.summary:
        show_summary(config, detailed=args.detailed)
    elif args.live:
        show_live(config, detailed=args.detailed)

if __name__ == "__main__":
    main()