#!/usr/bin/env python3
"""
Simple Bitaxe Gamma Monitor - CLI Viewer
View collected metrics with summary and live modes
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

console = Console()

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        console.print("[red]Error: config.yaml not found[/red]")
        sys.exit(1)

def load_csv_data(csv_path):
    """Load all data from CSV file"""
    if not os.path.exists(csv_path):
        console.print(f"[red]Error: CSV file {csv_path} not found[/red]")
        console.print("Run collector.py first to generate data")
        sys.exit(1)
    
    data = []
    try:
        with open(csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert numeric fields
                for field in ['hashrate_ghs', 'temperature_c', 'power_w', 'frequency_mhz', 'voltage_v', 'efficiency_ghj']:
                    try:
                        row[field] = float(row[field])
                    except (ValueError, TypeError):
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
def create_summary_table(latest_data):
    """Create a summary table of all miners"""
    table = Table(title="Bitaxe Gamma Miners Summary", box=box.ROUNDED)
    
    table.add_column("Miner IP", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Hashrate\n(GH/s)", justify="right")
    table.add_column("Temp\n(°C)", justify="right")
    table.add_column("Power\n(W)", justify="right")
    table.add_column("Efficiency\n(GH/J)", justify="right")
    table.add_column("Last Update", justify="center")
    
    total_hashrate = 0
    total_power = 0
    online_count = 0
    
    for miner_ip, data in latest_data.items():
        status = data['status']
        
        # Color coding for status
        if status == 'online':
            status_display = "[green]ON[/green]"
            online_count += 1
            total_hashrate += data['hashrate_ghs']
            total_power += data['power_w']
        elif status == 'offline':
            status_display = "[red]OFF[/red]"
        else:
            status_display = "[yellow]ERR[/yellow]"
        
        # Format values
        hashrate = f"{data['hashrate_ghs']:.1f}" if data['hashrate_ghs'] > 0 else "-"
        temp = f"{data['temperature_c']:.1f}" if data['temperature_c'] > 0 else "-"
        power = f"{data['power_w']:.1f}" if data['power_w'] > 0 else "-"
        efficiency = f"{data['efficiency_ghj']:.2f}" if data['efficiency_ghj'] > 0 else "-"        
        table.add_row(
            miner_ip,
            status_display,
            hashrate,
            temp,
            power,
            efficiency,
            data['timestamp']
        )
    
    # Add summary row
    total_miners = len(latest_data)
    avg_efficiency = total_hashrate / total_power if total_power > 0 else 0
    
    table.add_section()
    table.add_row(
        f"[bold]TOTAL ({online_count}/{total_miners})[/bold]",
        f"[green]{online_count} online[/green]",
        f"[bold]{total_hashrate:.1f}[/bold]",
        "-",
        f"[bold]{total_power:.1f}[/bold]",
        f"[bold]{avg_efficiency:.2f}[/bold]",
        "-"
    )
    
    return table

def create_stats_panel(latest_data):
    """Create statistics panel"""
    total_miners = len(latest_data)
    online_miners = sum(1 for data in latest_data.values() if data['status'] == 'online')
    offline_miners = total_miners - online_miners
    
    total_hashrate = sum(data['hashrate_ghs'] for data in latest_data.values() if data['status'] == 'online')
    total_power = sum(data['power_w'] for data in latest_data.values() if data['status'] == 'online')
    avg_temp = sum(data['temperature_c'] for data in latest_data.values() if data['status'] == 'online' and data['temperature_c'] > 0)
    avg_temp = avg_temp / online_miners if online_miners > 0 else 0
    
    avg_efficiency = total_hashrate / total_power if total_power > 0 else 0
    
    stats_text = f"""
[bold green]Fleet Statistics[/bold green]

Miners: {total_miners}
Online: {online_miners}
Offline: {offline_miners}

Total Hashrate: {total_hashrate:.1f} GH/s
Total Power: {total_power:.1f} W
Average Temperature: {avg_temp:.1f} C
Fleet Efficiency: {avg_efficiency:.2f} GH/J
"""
    
    return Panel(stats_text.strip(), title="Overview", border_style="blue")

def show_summary(config):
    """Show summary view"""
    csv_path = config['csv_path']
    console.print(f"\n[bold blue]Loading data from {csv_path}...[/bold blue]")
    
    data = load_csv_data(csv_path)
    if not data:
        console.print("[yellow]No data found in CSV file[/yellow]")
        return
    
    latest_data = get_latest_data_by_miner(data)    
    console.print(f"[green]Loaded {len(data)} records for {len(latest_data)} miners[/green]\n")
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(create_stats_panel(latest_data), size=10),
        Layout(create_summary_table(latest_data))
    )
    
    console.print(layout)

def show_live(config):
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
                Layout(create_stats_panel(latest_data), size=10),
                Layout(create_summary_table(latest_data))
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
    parser = argparse.ArgumentParser(description="Simple Bitaxe Gamma Monitor - CLI Viewer")
    parser.add_argument("--summary", action="store_true", help="Show summary of all miners")
    parser.add_argument("--live", action="store_true", help="Show live updating view")
    
    args = parser.parse_args()
    
    if not args.summary and not args.live:
        parser.print_help()
        console.print("\n[yellow]Please specify either --summary or --live mode[/yellow]")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    console.print("[bold blue]Simple Bitaxe Gamma Monitor - CLI Viewer[/bold blue]")
    
    if args.summary:
        show_summary(config)
    elif args.live:
        show_live(config)

if __name__ == "__main__":
    main()