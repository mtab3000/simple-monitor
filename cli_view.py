#!/usr/bin/env python3
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

console = Console()

def load_csv_data(csv_path):
    """Load data from CSV file"""
    if not Path(csv_path).exists():
        return []
    
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['hashrate_gh'] = float(row['hashrate_gh'])
            row['temperature'] = float(row['temperature'])
            row['power_w'] = float(row['power_w'])
            row['uptime_s'] = int(row['uptime_s'])
            row['accepted_shares'] = int(row['accepted_shares'])
            row['rejected_shares'] = int(row['rejected_shares'])
            row['pool_difficulty'] = int(row['pool_difficulty'])
            data.append(row)
    
    return data

def get_latest_metrics(data):
    """Get the latest metrics for each miner"""
    if not data:
        return {}
    
    latest = {}
    for row in data:
        miner_ip = row['miner_ip']
        if miner_ip not in latest or row['timestamp'] > latest[miner_ip]['timestamp']:
            latest[miner_ip] = row
    
    return latest

def create_summary_table(latest_metrics):
    """Create a summary table showing latest metrics for all miners"""
    table = Table(title="Bitaxe Gamma Miners - Current Status")
    
    table.add_column("Miner IP", style="cyan", no_wrap=True)
    table.add_column("Hashrate (GH/s)", style="green")
    table.add_column("Temperature (°C)", style="yellow")
    table.add_column("Power (W)", style="blue")
    table.add_column("Uptime", style="magenta")
    table.add_column("Shares (A/R)", style="white")
    table.add_column("Last Update", style="dim")
    
    total_hashrate = 0
    total_power = 0
    
    for miner_ip, metrics in latest_metrics.items():
        uptime_hours = metrics['uptime_s'] // 3600
        uptime_minutes = (metrics['uptime_s'] % 3600) // 60
        uptime_str = f"{uptime_hours}h {uptime_minutes}m"
        
        shares_str = f"{metrics['accepted_shares']}/{metrics['rejected_shares']}"
        
        # Parse timestamp
        timestamp = datetime.fromisoformat(metrics['timestamp'])
        time_ago = datetime.now() - timestamp
        
        if time_ago < timedelta(minutes=1):
            last_update = "Just now"
        elif time_ago < timedelta(hours=1):
            last_update = f"{int(time_ago.total_seconds() // 60)}m ago"
        else:
            last_update = f"{int(time_ago.total_seconds() // 3600)}h ago"
        
        # Color code temperature
        temp_style = "red" if metrics['temperature'] > 80 else "yellow" if metrics['temperature'] > 70 else "green"
        
        table.add_row(
            miner_ip,
            f"{metrics['hashrate_gh']:.1f}",
            f"[{temp_style}]{metrics['temperature']:.1f}[/{temp_style}]",
            f"{metrics['power_w']:.1f}",
            uptime_str,
            shares_str,
            last_update
        )
        
        total_hashrate += metrics['hashrate_gh']
        total_power += metrics['power_w']
    
    # Add totals row
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold green]{total_hashrate:.1f}[/bold green]",
        "-",
        f"[bold blue]{total_power:.1f}[/bold blue]",
        "-",
        "-",
        "-"
    )
    
    return table

def create_live_display(latest_metrics):
    """Create a live updating display layout"""
    layout = Layout()
    
    # Main content
    main_table = create_summary_table(latest_metrics)
    
    # Stats panel
    total_miners = len(latest_metrics)
    total_hashrate = sum(m['hashrate_gh'] for m in latest_metrics.values())
    avg_temp = sum(m['temperature'] for m in latest_metrics.values()) / total_miners if total_miners > 0 else 0
    total_power = sum(m['power_w'] for m in latest_metrics.values())
    
    stats_text = Text()
    stats_text.append(f"Fleet Overview\n", style="bold cyan")
    stats_text.append(f"Active Miners: {total_miners}\n")
    stats_text.append(f"Total Hashrate: {total_hashrate:.1f} GH/s\n", style="green")
    stats_text.append(f"Average Temp: {avg_temp:.1f}°C\n", style="yellow")
    stats_text.append(f"Total Power: {total_power:.1f}W\n", style="blue")
    stats_text.append(f"Efficiency: {total_hashrate/total_power:.1f} GH/W\n", style="magenta")
    
    stats_panel = Panel(stats_text, title="Fleet Stats", border_style="green")
    
    layout.split_column(
        Layout(main_table, name="main", size=15),
        Layout(stats_panel, name="stats", size=8)
    )
    
    return layout

def show_summary(csv_path):
    """Show summary of current miner status"""
    data = load_csv_data(csv_path)
    if not data:
        console.print("[red]No data found. Run collector.py first.[/red]")
        return
    
    latest_metrics = get_latest_metrics(data)
    table = create_summary_table(latest_metrics)
    console.print(table)

def show_live(csv_path):
    """Show live updating view"""
    console.print("[green]Starting live view... Press Ctrl+C to exit[/green]")
    
    with Live(console=console, refresh_per_second=1) as live:
        try:
            while True:
                data = load_csv_data(csv_path)
                if data:
                    latest_metrics = get_latest_metrics(data)
                    display = create_live_display(latest_metrics)
                    live.update(display)
                else:
                    live.update(Panel("No data available. Run collector.py first.", 
                                    title="Waiting for data", border_style="red"))
                time.sleep(2)
        except KeyboardInterrupt:
            console.print("\n[yellow]Live view stopped.[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="Bitaxe Gamma Monitor CLI Viewer")
    parser.add_argument("--summary", action="store_true", help="Show current summary")
    parser.add_argument("--live", action="store_true", help="Show live updating view")
    parser.add_argument("--csv", default="metrics.csv", help="CSV file path (default: metrics.csv)")
    
    args = parser.parse_args()
    
    if args.live:
        show_live(args.csv)
    elif args.summary:
        show_summary(args.csv)
    else:
        console.print("[yellow]Use --summary or --live flag. See --help for options.[/yellow]")

if __name__ == "__main__":
    main()