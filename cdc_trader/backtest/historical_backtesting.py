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


# Loading history data
def load_instruments_data_from_csvs(period, instruments):
    filepaths = load_csv_files("data", instruments=instruments, period=period)
    data = {}
    for file in filepaths:
        instrument = str(file).split("\\")[1]
        # extracting data
        df = pd.read_csv(file)
        # TODO : check this Assuming df has a DateTimeIndex
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].map(mpdates.date2num)
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
    min_required_data_points = 0
    num_trades = 0
    user_accounts.accounts[quote]["balance"] = 100
    user_accounts.accounts[base]["balance"] = 0

    for instrument, df in data.items():
        base, quote = instrument.split("_")

        for index, row in df.iterrows():
            # Do we have enough data to apply technical analysis?
            if index < min_required_data_points:
                continue

            df = apply_technical_analysis(df, params=analysis_params)

            # Example: Buy if the short moving average crosses above the long moving average and the available balance is greater than 0
            if (
                df.at[index, "signal"] == 1
                and user_accounts.accounts[quote]["balance"] > 0
            ):
                base_price = row["close"]
                last_price = base_price
                base_to_get = user_accounts.accounts[quote]["balance"] / base_price
                num_trades += 1
                user_accounts.accounts[base]["balance"] += base_to_get
                user_accounts.accounts[quote]["balance"] -= user_accounts.accounts[
                    quote
                ]["balance"]

            # Example: Sell if the short moving average crosses below the long moving average and the balance of the instrument is greater than 0
            elif (
                df.at[index, "signal"] == -1
                and user_accounts.accounts[base]["balance"] > 0
                and row["close"] > last_price
            ):
                quote_price = row["close"]
                quote_to_get = user_accounts.accounts[base]["balance"] * quote_price
                num_trades += 1
                user_accounts.accounts[base]["balance"] -= user_accounts.accounts[base][
                    "balance"
                ]
                user_accounts.accounts[quote]["balance"] += quote_to_get

    usdt_balance = user_accounts.accounts[quote]["balance"]
    base_balance_to_quote = (
        user_accounts.accounts[base]["balance"] * df["close"].iloc[-1]
    )
    total = usdt_balance + base_balance_to_quote
    print(
        f"Analysis Parameters: "
        f"RSI Window: {analysis_params['rsi_window']}, "
        f"MACD Short: {analysis_params['macd_short']}, "
        f"MACD Long: {analysis_params['macd_long']}, "
        f"MA Long Window: {analysis_params['ma_long_window']}, "
        f"MA Short Window: {analysis_params['ma_short_window']}, "
        f"Number of Trades: {num_trades}, "
        f"Final Balance: {total}"
    )

    result = {
        "short_window": analysis_params["ma_short_window"],
        "long_window": analysis_params["ma_long_window"],
        "balance": total,
    }

    return result


# Selecting period and instruments
period = "5m"
instruments = ["ARKM_USD"]
QUOTE_balance = 100
print(f"Period set to {period}")
print(f"Loading instruments...")
data = load_instruments_data_from_csvs(period, instruments)
print(f"{len(data.keys())} instruments loaded")

# User account
user_accounts = UserAccounts()

# Adding missing bases balance to user accounts
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
# TODO : Use GPU for faster computation

print(f"Beginning balance with {user_accounts.accounts[quote]['balance']} USDT")
user_accounts.display_accounts()

# Hyperparameter optimization
# Moving Average
min_MA_short_window, max_MA_short_window = 1, 5
min_MA_long_window, max_MA_long_window = 68, 70
# RSI
min_rsi_window, max_rsi_window = 7, 14
# MACD
min_macd_short, max_macd_short = 12, 14
min_macd_long, max_macd_long = 26, 28


# Define the parameter ranges
parameter_ranges = {
    "rsi_window": range(min_rsi_window, max_rsi_window + 1),
    "macd_short": range(min_macd_short, max_macd_short + 1),
    "macd_long": range(min_macd_long, max_macd_long + 1),
    "ma_long_window": range(min_MA_long_window, max_MA_long_window + 1),
    "ma_short_window": range(min_MA_short_window, max_MA_short_window + 1),
}

results = []
# Iterate over parameter combinations
for rsi_window in parameter_ranges["rsi_window"]:
    for macd_short in parameter_ranges["macd_short"]:
        for macd_long in parameter_ranges["macd_long"]:
            for ma_long_window in parameter_ranges["ma_long_window"]:
                for ma_short_window in parameter_ranges["ma_short_window"]:
                    # Create analysis parameters dictionary
                    analysis_params = {
                        "rsi_window": rsi_window,
                        "macd_short": macd_short,
                        "macd_long": macd_long,
                        "ma_long_window": ma_long_window,
                        "ma_short_window": ma_short_window,
                    }

                    # Apply historical simulation with the current parameter combination
                    result = apply_historical_simulation(
                        data, user_accounts, base, quote, analysis_params
                    )

                    results.append(result)

# print best result based on balance
best_result = max(results, key=lambda x: x["balance"])
print(
    f"Best result : {best_result['balance']} with short window {best_result['short_window']} and long window {best_result['long_window']}"
)
