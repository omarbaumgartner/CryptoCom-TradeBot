import sys
import os
import csv
from pathlib import Path
import pandas as pd
import matplotlib.dates as mpdates
# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Get the absolute path of the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(parent_dir, '..'))
# Append the grandparent directory to sys.path
sys.path.append(grandparent_dir)
from cdc_trader.classes.account import UserAccounts
from cdc_trader.trader.trading_logic import apply_technical_analysis

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


# Selecting period and instruments
period = "5m"
instruments = ['ARKM_USD']

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
        user_accounts.accounts[available_currency]['balance'] = 0

# Adding missing instruments balances from fake data
for instrument in instruments:
    if instrument not in user_accounts.accounts:
        base, quote = instrument.split('_')
        user_accounts.accounts[base] = {'balance': 0, 'balance': 0}

print(f"Beginning balance with {user_accounts.accounts[quote]['balance']} USDT")
user_accounts.display_accounts()

# Now you have technical analysis results for all instruments in the 'data' dictionary
# You can iterate through the dictionary and implement your trading strategy logic

results = []

min_MA_short_window,max_MA_short_window = 1,5
min_MA_long_window,max_MA_long_window = 68,70
min_rsi_window,max_rsi_window = 7,14
min_macd_short,max_macd_short = 12,14
min_macd_long,max_macd_long = 26,28

#RSI
for rsi_window in range(min_rsi_window, max_rsi_window+1):
    # MACD
    for macd_short in range(min_macd_short, max_macd_short+1):
        for macd_long in range(min_macd_long, max_macd_long+1):
            # Moving Average
            for ma_long_window in reversed(range(min_MA_long_window, max_MA_long_window+1)):
                for ma_short_window in range(min_MA_short_window, max_MA_short_window+1):
                    
                    min_required_data_points = 0

                    num_trades = 0
                    user_accounts.accounts[quote]['balance'] = 100
                    user_accounts.accounts[base]['balance'] = 0
                    for instrument, df in data.items():
                        base, quote = instrument.split('_')
                        
                        for index, row in df.iterrows():
                            # Do we have enough data to apply technical analysis?
                            if index < min_required_data_points:
                                #print(f"Not enough data for {instrument} at {row['timestamp']}")
                                continue
                            
                            df = apply_technical_analysis(df,ma_short_window=ma_short_window, ma_long_window=ma_long_window, rsi_window=rsi_window, macd_short=macd_short, macd_long=macd_long)

                            # Example: Buy if the short moving average crosses above the long moving average and the available balance is greater than 0
                            if df.at[index, 'signal'] == 1 and user_accounts.accounts[quote]['balance'] > 0 :

                                base_price = row['close']
                                last_price = base_price
                                base_to_get = user_accounts.accounts[quote]['balance'] / base_price
                                num_trades +=1
                                #print(f"Buying {base_to_get} {base} at {row['close']} with available balance of {user_accounts.accounts[quote]['balance']} {quote}")
                                # Update user_accounts object after making a trade
                                user_accounts.accounts[base]['balance'] += base_to_get
                                user_accounts.accounts[quote]['balance'] -= user_accounts.accounts[quote]['balance']
                                #print(f"After trade, balances are : {user_accounts.accounts[base]['balance']} {base} and {user_accounts.accounts[quote]['balance']} {quote}")
                                #user_accounts.display_accounts()
                            
                            # Example: Sell if the short moving average crosses below the long moving average and the balance of the instrument is greater than 0
                            elif df.at[index, 'signal'] == -1 and user_accounts.accounts[base]['balance'] > 0 and row['close'] > last_price:
                                quote_price = row['close']
                                quote_to_get = user_accounts.accounts[base]['balance'] * quote_price
                                num_trades +=1
                                #last_price = quote_price
                                #print(f"Selling {user_accounts.accounts[base]['balance']} {base} at {row['close']} for {quote_to_get} {quote}")
                                # Update user_accounts object after making a trade
                                user_accounts.accounts[base]['balance'] -= user_accounts.accounts[base]['balance']
                                user_accounts.accounts[quote]['balance'] += quote_to_get
                                #print(f"After trade, balances are : {user_accounts.accounts[base]['balance']} {base} and {user_accounts.accounts[quote]['balance']} {quote}")

                                #user_accounts.display_accounts()
                            
                            else:
                                pass
                                #print(f"No trade for {instrument} at {row['close']}")
                            

                        
                    usdt_balance = user_accounts.accounts[quote]['balance']
                    base_balance_to_quote = user_accounts.accounts[base]['balance'] * df['close'].iloc[-1]
                    total = usdt_balance + base_balance_to_quote
                    print(f"{num_trades} Trades, Balance : {total} with MA {ma_short_window} and {ma_long_window} and RSI {rsi_window} and MACD {macd_short} and {macd_long}")
                    result = {
                        'short_window': ma_short_window,
                        'long_window': ma_long_window,
                        'balance': total
                    }
                    results.append(result)

# print best result based on balance
best_result = max(results, key=lambda x:x['balance'])
print(f"Best result : {best_result['balance']} with short window {best_result['short_window']} and long window {best_result['long_window']}")
