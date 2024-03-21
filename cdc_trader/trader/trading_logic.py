from cdc_trader.trader.technical_indicators import *
from ta.momentum import rsi
from ta.trend import macd
import numpy as np

# TODO : add type hints to all functions
# TODO : make all trading logics return the same format of signals for easy integration

def apply_technical_analysis(df, params=None):
    """
    Apply technical analysis to a DataFrame containing financial data.

    Args:
        df (pandas.DataFrame): The DataFrame containing financial data.
        params (dict, optional): A dictionary containing parameters for technical analysis.
            Default is None. If None, default parameters are used:
            {'ma_short_window': 10,
             'ma_long_window': 50,
             'rsi_window': 14,
             'macd_short': 12,
             'macd_long': 26}

    Returns:
        tuple: A tuple containing the action to take ('buy', 'sell', or 'hold'), quantity, and price.

    Notes:
        This function calculates moving averages, RSI (Relative Strength Index), and MACD (Moving Average
        Convergence Divergence) indicators based on the given DataFrame. It then combines these indicators
        to generate buy and sell signals.

    Example:
        >>> parameters = {
        ...     'ma_short_window': 10,
        ...     'ma_long_window': 50,
        ...     'rsi_window': 14,
        ...     'rsi_overbought': 70,
        ...     'rsi_oversold': 30,
        ...     'macd_short': 12,
        ...     'macd_long': 26
        ... }
        >>> result = apply_technical_analysis(df, params=parameters) 
    """

    
    # Moving averages
    short_ma_val = df['close'].rolling(window=params['ma_short_window'], min_periods=1, center=False).mean()
    long_ma_val = df['close'].rolling(window=params['ma_long_window'], min_periods=1, center=False).mean()

    # RSI
    rsi_val = rsi(df['close'], window=params['rsi_window']).iloc[-1]

    # MACD : TODO integrate
    #macd_val = macd(close=df['close'], window_fast=params['macd_short'], window_slow=params['macd_long'])

    # TODO : Add weights to each indicator  
    
    # Combine signals
    combined_signal = 0
    combined_signal += 1 if (short_ma_val > long_ma_val).iloc[-1] else -1
    combined_signal += 1 if rsi_val < params["rsi_overbought"] else (-1 if rsi_val > params["rsi_overbought"] else 0)

    # Interpret combined signal
    #df['signal'] = 0
    signal = 0
    if combined_signal > 1:
        signal = 1
    elif combined_signal < -1:
        signal = -1
    
    # Determine action based on signal
    action = 'hold'
    # TODO : Integrate quantity and price to match order book trading logic
    quantity = 0
    price = 0
    
    if signal == 1:
        action = 'buy'
        price = df['close'].iloc[-1]
    elif signal == -1:
        action = 'sell'
        price = df['close'].iloc[-1]
    else:
        action = 'hold'

    df.loc[df.index[-1], 'signal'] = signal


    return action, quantity, price

# market depth analysis based on order books

def dynamic_threshold_adjustment(bid_order_count_values, ask_order_count_values, params=None):
    """
    Adjust the threshold dynamically based on moving averages of bid and ask order count values.

    Parameters:
        bid_order_count_values (list): List of bid order count values.
        ask_order_count_values (list): List of ask order count values.
        params (dict, optional): A dictionary containing parameters for threshold adjustment.
            Default is None. If None, default parameters are used:
            {'window_size': 10, 'sensitivity_factor': 1.5}

    Returns:
        int: Adjusted threshold value.
    """
    
    if params is None:
        params = {'window_size': 10, 'sensitivity_factor': 1.5}

    # Convert bid and ask order count values to numeric type
    bid_order_count_values = np.array(bid_order_count_values, dtype=float)
    ask_order_count_values = np.array(ask_order_count_values, dtype=float)

    window_size = params.get('window_size', 10)
    sensitivity_factor = params.get('sensitivity_factor', 1.5)

    if len(bid_order_count_values) < window_size or len(ask_order_count_values) < window_size:
        return 1  # Default threshold if there's not enough data yet

    # Calculate moving averages for bid and ask order counts
    bid_moving_average = np.mean(bid_order_count_values[-window_size:])
    ask_moving_average = np.mean(ask_order_count_values[-window_size:])

    # Use the maximum moving average as the basis for adjustment
    max_moving_average = max(bid_moving_average, ask_moving_average)

    adjusted_threshold = int(max_moving_average * sensitivity_factor)

    return max(1, adjusted_threshold)  # Ensure the threshold is at least 1


def trend_following_strategy_with_order_count(order_book_data, available_Base, available_Quote, params=None):
    """
    Implement a trend-following trading strategy based on order count thresholds.

    Parameters:
        order_book_data (dict): A dictionary containing order book data, including bids and asks.
        available_Base (float): Amount of the base currency available for trading.
        available_Quote (float): Amount of the quote currency available for trading.
        params (dict, optional): A dictionary containing parameters for the trading strategy.
            Default is None. If None, default parameters are used:
            {'transaction_fee': 0.00075, 'order_count_threshold': 10}

    Returns:
        tuple: A tuple containing the action to take ('buy', 'sell', or 'hold'), quantity, and price.

    Notes:
        This function implements a trend-following trading strategy based on the order count thresholds.
        It evaluates the order book data, available base and quote currencies, and adjusts the buy and sell
        prices based on the transaction fee. It then decides whether to place a buy order, a sell order, or
        hold position based on the calculated conditions.

    """
    if params is None:
        params = {'transaction_fee': 0.00075, 'order_count_threshold': 10}

    bids = np.array(order_book_data['bids'])
    asks = np.array(order_book_data['asks'])

    bid_prices = bids[:, 0].astype(float)
    ask_prices = asks[:, 0].astype(float)

    bid_volume = bids[:, 1].astype(float)
    ask_volume = asks[:, 1].astype(float)

    bid_order_count = bids[:, 2].astype(int)
    ask_order_count = asks[:, 2].astype(int)

    # Calculate the mid-price between the highest bid and lowest ask
    mid_price = (ask_prices[0] + bid_prices[0]) / 2.0

    # Extract parameters from the params dictionary
    transaction_fee = params.get('transaction_fee', 0.00075)
    order_count_threshold = params.get('order_count_threshold', 10)

    # Simulate slippage by adjusting the buy and sell prices
    adjusted_bid_price = bid_prices[0] * (1 + transaction_fee)
    adjusted_ask_price = ask_prices[0] * (1 - transaction_fee)

    action = 'hold'
    quantity = 0
    price = 0

    if mid_price > adjusted_ask_price and bid_order_count[0] > order_count_threshold and available_Quote > 0:
        # Place a buy order as the mid-price is higher than adjusted ask price and order count is above the threshold
        ask_quantity = min(available_Quote / adjusted_ask_price, float(ask_volume[0]))
        if ask_quantity > 0:
            action = 'buy'
            quantity = ask_quantity
            price = adjusted_ask_price
    elif mid_price < adjusted_bid_price and ask_order_count[0] > order_count_threshold and available_Base > 0:
        # Place a sell order as the mid-price is lower than adjusted bid price and order count is above the threshold
        bid_quantity = min(float(bid_volume[0]), available_Base)
        if bid_quantity > 0:
            action = 'sell'
            quantity = bid_quantity
            price = adjusted_bid_price
    
    return action,quantity,price
