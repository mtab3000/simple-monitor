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
        table = Table(title="Bitaxe Gamma Fleet - Detailed View", box=box.ROUNDED)
        table.add_column("Miner IP", style="cyan", no_wrap=True)
        table.add_column("Hostname", style="dim", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Hashrate\n(GH/s)", justify="right")
        table.add_column("Perf\n(%)", justify="right") 
        table.add_column("ASIC T\n(C)", justify="right") 
        table.add_column("VR T\n(C)", justify="right")
        table.add_column("Power\n(W)", justify="right")
        table.add_column("Set V\n(V)", justify="right")
        table.add_column("Actual V\n(V)", justify="right")
        table.add_column("Set Freq\n(MHz)", justify="right")
        table.add_column("Efficiency\n(J/TH)", justify="right")
        table.add_column("Uptime\n(hrs)", justify="right")
        table.add_column("Memory\n(MB)", justify="right")
        table.add_column("OC", justify="center")
    else:
        table = Table(title="Bitaxe Gamma Fleet Summary", box=box.ROUNDED)
        table.add_column("Miner IP", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Hashrate\n(GH/s)", justify="right")
        table.add_column("Perf\n(%)", justify="right")
        table.add_column("ASIC T\n(C)", justify="right")
        table.add_column("VR T\n(C)", justify="right")
        table.add_column("Power\n(W)", justify="right")
        table.add_column("Efficiency\n(J/TH)", justify="right")
        table.add_column("Fan\n(%)", justify="right")
        table.add_column("Uptime\n(hrs)", justify="right")
    
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
        hostname = str(data.get('hostname', 'Unknown'))[:8] if data.get('hostname') else 'Unknown'  # Truncate for display
        free_heap_mb = f"{data.get('free_heap_bytes', 0) / 1024 / 1024:.1f}" if data.get('free_heap_bytes', 0) > 0 else "-"
        overclock = "Y" if data.get('overclock_enabled', 0) else "N"
        
        if show_detailed:
            table.add_row(
                miner_ip, hostname, status_display, hashrate, perf_ratio, temp_asic, temp_vr, power,
                voltage_set, voltage_actual, freq_set, efficiency, uptime_hrs, free_heap_mb, overclock
            )
        else:
            table.add_row(
                miner_ip, status_display, hashrate, perf_ratio, temp_asic, temp_vr, power,
                efficiency, fan_speed, uptime_hrs
            )
    
    # Add summary row
    total_miners = len(latest_data)
    avg_efficiency = total_power / (total_hashrate / 1000) if total_hashrate > 0 else 0  # J/TH
    
    table.add_section()
    if show_detailed:
        table.add_row(
            f"[bold]TOTAL ({online_count}/{total_miners})[/bold]",
            "-",
            f"[green]{online_count} online[/green]",
            f"[bold]{total_hashrate:.1f}[/bold]", "-", "-", "-",
            f"[bold]{total_power:.1f}[/bold]", "-", "-", "-",
            f"[bold]{avg_efficiency:.1f}[/bold]", "-", "-", "-"
        )
    else:
        table.add_row(
            f"[bold]TOTAL ({online_count}/{total_miners})[/bold]",
            f"[green]{online_count} online[/green]",
            f"[bold]{total_hashrate:.1f}[/bold]", "-", "-", "-",
            f"[bold]{total_power:.1f}[/bold]",
            f"[bold]{avg_efficiency:.1f}[/bold]", "-", "-"
        )
    
    return table

def get_status_display(status):
    """Get colored status display"""
    status_map = {
        'online': '[green]ONLINE[/green]',
        'no_hashrate': '[yellow]NO HASH[/yellow]',
        'overheating': '[red]HOT[/red]',
        'wifi_issues': '[orange]WIFI[/orange]',
        'high_rejection': '[red]REJECT[/red]',
        'timeout': '[red]TIMEOUT[/red]',
        'connection_failed': '[red]OFFLINE[/red]',
        'high_power': '[yellow]HI PWR[/yellow]',
        'low_power': '[yellow]LO PWR[/yellow]',
        'no_temp_sensor': '[yellow]NO TEMP[/yellow]'
    }
    return status_map.get(status, f'[red]{status.upper()}[/red]')

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
    
    stats_text = f"""[bold green]Fleet Statistics[/bold green]

[cyan]Miners:[/cyan] {total_miners} total
[green]Online:[/green] {online_count}
[red]Offline:[/red] {offline_count}

[cyan]Performance:[/cyan]
Total Hashrate: {total_hashrate:.1f} GH/s ({total_hashrate/1000:.2f} TH/s)
Total Power: {total_power:.1f} W
Average ASIC Temperature: {avg_temp_asic:.1f} C
Average VR Temperature: {avg_temp_vr:.1f} C
Fleet Efficiency: {avg_efficiency:.1f} J/TH

[cyan]Mining Stats:[/cyan]
Shares Accepted: {total_shares:,}
Shares Rejected: {total_rejected:,}
Rejection Rate: {rejection_rate:.2f}%
"""
    
    return Panel(stats_text.strip(), title="Overview", border_style="blue")

def create_individual_panels(latest_data):
    """Create individual miner panels for detailed view"""
    panels = []
    
    for miner_ip, data in latest_data.items():
        status = data['status']
        
        if status == 'online':
            panel_color = "green"
            status_text = "[green]ONLINE[/green]"
        elif status in ['timeout', 'connection_failed']:
            panel_color = "red"
            status_text = "[red]OFFLINE[/red]"
        else:
            panel_color = "yellow"
            status_text = f"[yellow]{status.upper()}[/yellow]"
        
        content = f"""Status: {status_text}
Hashrate: {data.get('hashrate_ghs', 0):.1f} GH/s ({data.get('hashrate_ratio_percent', 0):.0f}% of expected)
Expected: {data.get('expected_hashrate_ghs', 0):.1f} GH/s
ASIC Temp: {data.get('temp_asic_c', 0):.1f}C
VR Temp: {data.get('temp_vr_c', 0):.1f}C
Power: {data.get('power_w', 0):.1f}W
Efficiency: {data.get('efficiency_j_th', 0):.1f} J/TH
Set Freq: {data.get('frequency_set_mhz', 0)} MHz
Set Voltage: {data.get('voltage_asic_set_v', 0):.3f}V
Actual Voltage: {data.get('voltage_asic_actual_v', 0):.3f}V
Best Session: {data.get('best_session_diff', '0')}
Memory Free: {data.get('free_heap_bytes', 0) / 1024 / 1024:.1f} MB
Overclock: {'Enabled' if data.get('overclock_enabled', 0) else 'Disabled'}
Uptime: {data.get('uptime_hours', 0):.1f} hrs"""
        
        if data.get('pool_user') and data.get('pool_user') != 'Unknown':
            pool_short = data['pool_user'][:15] + "..." if len(data['pool_user']) > 15 else data['pool_user']
            content += f"\nPool: {pool_short}"
        
        panels.append(Panel(content, title=f"[bold]{miner_ip} ({data.get('hostname', 'Unknown') or 'Unknown'})[/bold]", border_style=panel_color))
    
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
        Layout(create_fleet_stats_panel(latest_data), size=12),
        Layout(create_main_table(latest_data, show_detailed=detailed))
    )
    
    console.print(layout)

def show_live(config, detailed=False):
    """Show live updating view"""
    csv_path = config['csv_path']
    
    def generate_display():
        try:
            data = load_csv_data(csv_path)
            if not data:
                return Panel("[yellow]No data available[/yellow]", title="Live Monitor")
            
            latest_data = get_latest_data_by_miner(data)
            
            layout = Layout()
            layout.split_column(
                Layout(create_fleet_stats_panel(latest_data), size=12),
                Layout(create_main_table(latest_data, show_detailed=detailed))
            )
            return layout
        except Exception as e:
            return Panel(f"[red]Error: {e}[/red]", title="Live Monitor")
    
    console.print("[bold green]Starting live monitor...[/bold green]")
    console.print("Press Ctrl+C to exit\n")
    
    try:
        with Live(generate_display(), refresh_per_second=0.5) as live:
            while True:
                time.sleep(2)  # Update every 2 seconds
                live.update(generate_display())
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
    
    console.print("[bold blue]Smart Bitaxe Gamma Monitor - Enhanced CLI Viewer[/bold blue]")
    
    if args.summary:
        show_summary(config, detailed=args.detailed)
    elif args.live:
        show_live(config, detailed=args.detailed)

if __name__ == "__main__":
    main()