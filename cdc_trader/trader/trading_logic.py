from cdc_trader.trader.technical_indicators import *
import ta
from ta.momentum import rsi
from ta.trend import macd


def apply_technical_analysis(df, ma_short_window=10, ma_long_window=50, rsi_window=14, macd_short=12, macd_long=26):
    # Moving averages
    df['short_mavg'] = df['close'].rolling(window=ma_short_window, min_periods=1, center=False).mean()
    df['long_mavg'] = df['close'].rolling(window=ma_long_window, min_periods=1, center=False).mean()

    # RSI
    df['rsi'] = rsi(df['close'], window=rsi_window)

    # MACD
    df['macd'] = macd(close=df['close'], window_fast=macd_short, window_slow=macd_long)

    # Combine signals
    df['combined_signal'] = 0
    df['combined_signal'] += (df['short_mavg'] > df['long_mavg']).astype(int)
    df['combined_signal'] += (df['rsi'] < 30).astype(int)
    df['combined_signal'] += (df['rsi'] > 70).astype(int)
    df['combined_signal'] += (df['macd'] > 0).astype(int)
    
    # Interpret combined signal
    df['signal'] = 0
    df.loc[df['combined_signal'] > 1, 'signal'] = 1  # Buy if more than one indicator is positive
    df.loc[df['combined_signal'] < -1, 'signal'] = -1  # Sell if more than one indicator is negative

    return df

# market depth analysis based on order books

def dynamic_threshold_adjustment(bid_order_count_values, ask_order_count_values, window_size=10, sensitivity_factor=1.5):
    """
    Adjust the threshold dynamically based on moving averages of bid and ask order count values.

    Parameters:
    - bid_order_count_values: List of bid order count values.
    - ask_order_count_values: List of ask order count values.
    - window_size: Size of the moving average window.
    - sensitivity_factor: A factor to control the sensitivity of the adjustment.

    Returns:
    - Adjusted threshold value.
    """
    # Convert bid and ask order count values to numeric type
    bid_order_count_values = np.array(bid_order_count_values, dtype=float)
    ask_order_count_values = np.array(ask_order_count_values, dtype=float)

    if len(bid_order_count_values) < window_size or len(ask_order_count_values) < window_size:
        return 1  # Default threshold if there's not enough data yet

    # Calculate moving averages for bid and ask order counts
    bid_moving_average = np.mean(bid_order_count_values[-window_size:])
    ask_moving_average = np.mean(ask_order_count_values[-window_size:])

    # Use the maximum moving average as the basis for adjustment
    max_moving_average = max(bid_moving_average, ask_moving_average)

    adjusted_threshold = int(max_moving_average * sensitivity_factor)

    return max(1, adjusted_threshold)  # Ensure the threshold is at least 1


def trend_following_strategy_with_order_count(
    order_book_data, available_Base, available_Quote, transaction_fee=0.00075, order_count_threshold=10
):
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

    # Simulate slippage by adjusting the buy and sell prices
    adjusted_bid_price = bid_prices[0] * (1 + transaction_fee)
    adjusted_ask_price = ask_prices[0] * (1 - transaction_fee)

    if mid_price > adjusted_ask_price and bid_order_count[0] > order_count_threshold and available_Quote > 0:
        # Place a buy order as the mid-price is higher than adjusted ask price and order count is above the threshold
        print('buy', available_Quote / adjusted_ask_price, float(ask_volume[0]))
        ask_quantity = min(available_Quote / adjusted_ask_price, float(ask_volume[0]))
        if ask_quantity > 0:
            return 'buy', ask_quantity, adjusted_ask_price
        else:
            return 'hold', 0, 0
    elif mid_price < adjusted_bid_price and ask_order_count[0] > order_count_threshold and available_Base > 0:
        # Place a sell order as the mid-price is lower than adjusted bid price and order count is above the threshold
        bid_quantity = min(float(bid_volume[0]), available_Base)
        if bid_quantity > 0:
            return 'sell', bid_quantity, adjusted_bid_price
        else:
            return 'hold', 0, 0
    else:
        return 'hold', 0, 0
