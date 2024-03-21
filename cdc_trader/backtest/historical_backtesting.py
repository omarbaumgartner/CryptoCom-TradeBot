import sys
import os
import pandas as pd
import matplotlib.dates as mpdates

# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Get the absolute path of the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(parent_dir, ".."))
# Append the grandparent directory to sys.path
sys.path.append(grandparent_dir)
from cdc_trader.classes.account import UserAccounts
from cdc_trader.trader.trading_logic import apply_technical_analysis
from cdc_trader.utils.csv_utils import load_csv_files

# For printing purposes in order to see the right number of decimals without rounding
pd.set_option('display.precision', 10)

# Loading history data
def load_instruments_data_from_csvs(period, instruments):
    filepaths = load_csv_files("data", instruments=instruments, period=period)
    data = {}
    for file in filepaths:
        instrument = str(file).split("\\")[1]
        # extracting data
        df = pd.read_csv(file,float_precision='round_trip')
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].map(mpdates.date2num)
        df.loc[:, 'signal'] = None
        data[instrument] = df
    return data


def apply_historical_simulation(data, user_accounts, base, quote, analysis_params):
    """
    Apply historical simulation for trading strategy based on technical analysis.

    Parameters:
    - data (dict): Dictionary containing historical data for different instruments.
    - user_accounts (UserAccounts): Object representing user accounts.
    - base (str): Base currency symbol.
    - quote (str): Quote currency symbol.
    - analysis_params (dict): Dictionary containing parameters for technical analysis:
        - 'rsi_window' (int): Window size for RSI calculation.
        - 'macd_short' (int): Short window size for MACD calculation.
        - 'macd_long' (int): Long window size for MACD calculation.
        - 'ma_long_window' (int): Long window size for moving average calculation.
        - 'ma_short_window' (int): Short window size for moving average calculation.

    Returns:
    - dict: Dictionary containing simulation results.
    """
    min_required_data_points = max(
        analysis_params["ma_long_window"],
        analysis_params["ma_short_window"],
        analysis_params["macd_long"],
        analysis_params["macd_short"],
        analysis_params["rsi_window"],
    )
    
    num_trades = 0


    for instrument, df in data.items():
        base, quote = instrument.split("_")

        for index, row in df.iterrows():
            # Do we have enough data to apply technical analysis?
            if index < min_required_data_points:
                continue
            # TODO : Fix apply_technical_analysis, action is not correct, always hold
            # Coming from the change from row[signal] to iloc[index][signal]
            
            action,quantity,price = apply_technical_analysis(df.iloc[0:index], params=analysis_params)
            
            # TODO : integrate quantity
            if action == 'buy' and user_accounts.accounts[quote]["balance"] > 0 :
                last_price = price
                base_to_get = user_accounts.accounts[quote]["balance"] / price
                num_trades += 1
                user_accounts.accounts[base]["balance"] += base_to_get
                user_accounts.accounts[quote]["balance"] -= user_accounts.accounts[
                    quote
                ]["balance"]

            elif action == 'sell' and user_accounts.accounts[base]["balance"] > 0 and price > last_price :
                quote_price = price
                quote_to_get = user_accounts.accounts[base]["balance"] * quote_price
                num_trades += 1
                user_accounts.accounts[base]["balance"] -= user_accounts.accounts[base][
                    "balance"
                ]
                user_accounts.accounts[quote]["balance"] += quote_to_get

    quote_balance = user_accounts.accounts[quote]["balance"]
    base_balance_to_quote = (
        user_accounts.accounts[base]["balance"] * df["close"].iloc[-1]
    )
    total_quote_balance = quote_balance + base_balance_to_quote
    
    analysis_params["balance"] = total_quote_balance
    analysis_params["num_trades"] = num_trades

    print(
        f"Analysis Parameters: ",analysis_params
    )

    return analysis_params


# Selecting period and instruments
period = "1h"
instruments = ["BTC_USD"]
QUOTE_balance = 1000
print(f"Period set to {period}")
print(f"Loading instruments...")
data = load_instruments_data_from_csvs(period, instruments)

# Initialize empty row of signal in data
print(f"{len(data.keys())} instruments loaded")

user_accounts = UserAccounts()
# Adding missing base and quote balances to user accounts
for instrument in instruments:
    if instrument not in user_accounts.accounts:
        base, quote = instrument.split("_")
        user_accounts.add_account(
            {"currency": base, "balance": 0, "available": 0, "stake": 0, "order": 0}
        )
        user_accounts.add_account(
            {
                "currency": quote,
                "balance": QUOTE_balance,
                "available": QUOTE_balance,
                "stake": 0,
                "order": 0,
            }
        )

# Adding USDT balance to user accounts
# TODO : Improve code by using balance/available to simulate real use case instead of just balance
# TODO : Use GPU for faster computation = one simulation per kernel

print(f"Beginning balance with {user_accounts.accounts[quote]['balance']} USDT")
user_accounts.display_accounts()

# Hyperparameter optimization
# Moving Average
min_MA_short_window, max_MA_short_window = 1, 1
min_MA_long_window, max_MA_long_window = 40, 40
# RSI
min_rsi_overbought,max_rsi_overbought = 70,80
min_rsi_oversold,max_rsi_oversold = 30,40
min_rsi_window, max_rsi_window = 1, 5

# MACD
min_macd_short, max_macd_short = 14, 14
min_macd_long, max_macd_long = 28, 28


# Define the parameter ranges
parameter_ranges = {
    "rsi_window": range(min_rsi_window, max_rsi_window + 1),
    "macd_short": range(min_macd_short, max_macd_short + 1),
    "macd_long": range(min_macd_long, max_macd_long + 1),
    "rsi_overbought": range(min_rsi_overbought, max_rsi_overbought + 1),
    "rsi_oversold": range(min_rsi_oversold, max_rsi_oversold + 1),
    "ma_long_window": range(min_MA_long_window, max_MA_long_window + 1),
    "ma_short_window": range(min_MA_short_window, max_MA_short_window + 1),
}

results = []
# Iterate over parameter combinations
for rsi_window in parameter_ranges["rsi_window"]:
    for rsi_overbought in parameter_ranges["rsi_overbought"]:
        for rsi_oversold in parameter_ranges["rsi_oversold"]:
#    for macd_short in parameter_ranges["macd_short"]:
#        for macd_long in parameter_ranges["macd_long"]:
            for ma_long_window in parameter_ranges["ma_long_window"]:
                for ma_short_window in parameter_ranges["ma_short_window"]:
                    # Create analysis parameters dictionary
                    analysis_params = {
                        "rsi_window": rsi_window,
                        "rsi_overbought": rsi_overbought,
                        "rsi_oversold": rsi_oversold,
                        "macd_short": 0,
                        "macd_long": 0,
                        "ma_long_window": ma_long_window,
                        "ma_short_window": ma_short_window,
                    }


                    user_accounts.accounts[quote]["balance"] = QUOTE_balance
                    user_accounts.accounts[base]["balance"] = 0
                    
                    # Apply historical simulation with the current parameter combination
                    result = apply_historical_simulation(
                        data, user_accounts, base, quote, analysis_params
                    )

                    results.append(result)

# print best result based on balance
best_result = max(results, key=lambda x: x["balance"])
print(f"Best result: {best_result}")