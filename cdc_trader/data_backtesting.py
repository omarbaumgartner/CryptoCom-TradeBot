from trading_api_client import *
import csv
from pathlib import Path
import pandas as pd
import matplotlib.dates as mpdates
from trading_classes import UserAccounts

# Load from csv
def load_csv(file_path):
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        data = list(reader)
    return data

# Load filepaths of csv files in a directory
def load_csv_files(folder_path,instruments=None, period='5m'):
    files = []
    for file in Path(folder_path).rglob("*.csv"):
        if period in str(file):
            # Load specific instruments
            if instruments!=None and str(file).split("\\")[1] in instruments:
                files.append(file)
            # Load all instruments
            elif not instruments:
                files.append(file)
    return files

def apply_technical_analysis(df):
    # Your technical analysis logic goes here
    # Modify the dataframe or extract relevant information
    # Example: Moving average crossover strategy
    short_window = 10
    long_window = 50
    df['short_mavg'] = df['close'].rolling(window=short_window, min_periods=1, center=False).mean()
    df['long_mavg'] = df['close'].rolling(window=long_window, min_periods=1, center=False).mean()
    df['signal'] = 0
    df.loc[df['short_mavg'] > df['long_mavg'], 'signal'] = 1
    df.loc[df['short_mavg'] < df['long_mavg'], 'signal'] = -1
    return df


# Selecting period and instruments
period = "5m"
instruments = ['BTC_USDT','ETH_USDT']

# Loading history data
filepaths = load_csv_files("data",instruments=instruments,period=period)

data = {

}

print(f"Period set to {period}")
print(f"Loading instruments...")
for file in filepaths:
    instrument = str(file).split("\\")[1]
    # extracting data
    df = pd.read_csv(file)
    # TODO : check this Assuming df has a DateTimeIndex
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].map(mpdates.date2num)
    data[instrument] = df
print(f"{len(data.keys())} instruments loaded")

# User account
user_accounts = UserAccounts()
user_accounts.update_accounts()
user_accounts.display_accounts()
# Setting balance to 0 for all currencies except USDT
for available_currency in user_accounts.accounts:
    if available_currency != 'USDT':
        user_accounts.accounts[available_currency]['balance'] = 0
        user_accounts.accounts[available_currency]['available'] = 0
    else : 
        user_accounts.accounts[available_currency]['balance'] = 100

print(f"Beginning balance with {user_accounts.accounts['USDT']['balance']} USDT")
user_accounts.display_accounts()
input("Press Enter to continue...")

# Now you have technical analysis results for all instruments in the 'data' dictionary
# You can iterate through the dictionary and implement your trading strategy logic

from data_technical_analysis import *

for instrument, df in data.items():
    for index, row in df.iterrows():
        print(f"Processing {instrument} at {row['timestamp']}")        
        
        # Do we have enough data to apply technical analysis?
        if index < 50:
            print(f"Not enough data for {instrument} at {row['timestamp']}")
            continue
        
        # Example: Buy if the short moving average crosses above the long moving average and the available balance is greater than 0
        if row['signal'] == 1 and user_accounts.accounts['USDT']['available'] > 0:
            print(f"Buying {instrument} at {row['close']} with available balance of {user_accounts.accounts['USDT']['available']} USDT")
            # Update user_accounts object after making a trade
            user_accounts.accounts[instrument]['balance'] += 1
            user_accounts.accounts['USDT']['available'] -= 1
            user_accounts.display_accounts()
        
        # Example: Sell if the short moving average crosses below the long moving average and the balance of the instrument is greater than 0
        elif row['signal'] == -1 and user_accounts.accounts[instrument]['balance'] > 0:
            print(f"Selling {instrument} at {row['close']} with balance of {user_accounts.accounts[instrument]['balance']}")
            # Update user_accounts object after making a trade
            user_accounts.accounts[instrument]['balance'] -= 1
            user_accounts.accounts['USDT']['available'] += 1
            user_accounts.display_accounts()
        
        else:
            print(f"No trade for {instrument} at {row['close']}")
        
        input("Press Enter to continue...")

# The loop above simulates time passing, and you can continuously update the data and make decisions in real-time.
