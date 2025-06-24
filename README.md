# Simple Bitaxe Gamma Monitor

This tool collects metrics from Bitaxe Gamma miners and logs them to a CSV file.  
You can also view live stats in your terminal using a CLI.

## Usage

Run collector:
```
python collector.py
```

Run viewer:
```
python cli_view.py --summary
python cli_view.py --live
```

Configure miners in `config.yaml`.