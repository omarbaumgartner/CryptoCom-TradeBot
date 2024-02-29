from trading_api_client import *
from datetime import datetime
import csv
from pathlib import Path
# Pull candlesticks of instrument based on a specific interval, save it to csv
# It will then be used for vizualisation and backtesting
def candles_to_csv(output_folder,timestamp, instrument_name, period, candles):
    f = open(f"{output_folder}/{instrument_name}_{period}_candles_{timestamp}.csv", "a+",newline='')
    writer = csv.writer(f)
    writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
    for candle in candles:
        candle["t"] = datetime.fromtimestamp(candle["t"] / 1000)
        writer.writerow(
            [
                candle["t"],
                candle["o"],
                candle["h"],
                candle["l"],
                candle["c"],
                candle["v"],
            ]
        )

# Get instruments from ticker that could be used for trading
def get_usable_instruments(ticker):
    instruments = []
    for tick in ticker:
        if '-' not in tick['i'] and 'T_USD' not in tick["i"] and 'PERP' not in tick["i"]:
            if 'USD' in tick["i"].split('_') or 'EUR' in tick["i"].split('_'):
                pass
            else:
                instruments.append(tick['i'])
    return instruments

data_folder = "data"
ticker = get_ticker()

periods = ["1m", "5m", "15m", "30m", "1h", "4h", "6h", "12h"]
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
instruments = get_usable_instruments(ticker)

for instrument_name in instruments:
    output_folder = f"{data_folder}/{instrument_name}"
    
    # Create a folder for each instrument
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    for period in periods:
        data = get_candlesticks(instrument_name, period)
        candles = data["data"]
        candles_to_csv(output_folder,timestamp, instrument_name, period, candles)