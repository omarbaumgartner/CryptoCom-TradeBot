import time
import numpy as np
import datetime
import sys
import os
# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Get the absolute path of the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(parent_dir, '..'))
# Append the grandparent directory to sys.path
sys.path.append(grandparent_dir)

from cdc_trader.classes.account import UserAccounts
from cdc_trader.utils.trading_logger import log_message
from cdc_trader.api.cdc_api import generate_nonce
from cdc_trader.api.cdc_api import get_orderbook, get_ticker


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

# Initialize user accounts
user = UserAccounts()
user.update_accounts()
#user.display_accounts()

instrument = 'LINK_USD'
base,quote = instrument.split('_')

available_Base = 0
available_Quote = 1000

waiting_for_order = False
bid_order_count_values = []  # Store historical bid order count values
ask_order_count_values = []  # Store historical ask order count values

today_date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
backtesting_filename = f'data/backtesting/trader/backtesting_{today_date}.txt'
orderbook_filename = f'data/backtesting/orderbook/orderbook_data_{today_date}.txt'

# TODO:Optimize realtime efficiency because lags impact by using WebSockets
# Asynchronous Programming

sleep_time_order_seconds = 1
sleep_time_no_order_seconds = 0.2 # 200ms
wait_time_order_minutes = 1

while True:
    orderbook = get_orderbook(instrument, 150)
    if orderbook is None:
        print('Error getting orderbook data. Retrying in 5 seconds...')
        time.sleep(5)
        continue
    ticker = get_ticker(instrument)
    # 100 requests per second each public method
    current_ask_price = float(ticker[0]['k'])
    current_bid_price = float(ticker[0]['b'])

    orderbook['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Append the orderbook data to a file
    with open(orderbook_filename, 'a') as file:
        file.write(str(orderbook) + '\n')
        file.flush()  # Flush the file to ensure immediate writing

    instrument = orderbook['instrument_name']
    depth = orderbook['depth']
    data = orderbook['data'][0]
    
            # Get bid and ask order counts
    bid_order_count = data['bids'][0][2]
    ask_order_count = data['asks'][0][2]

    # Store bid and ask order counts for dynamic threshold adjustment
    bid_order_count_values.append(bid_order_count)
    ask_order_count_values.append(ask_order_count)

    # Adjust the threshold dynamically based on bid and ask moving averages
    order_count_threshold = dynamic_threshold_adjustment(
        bid_order_count_values, ask_order_count_values,window_size=20, sensitivity_factor=2
    )

    # Use the dynamically adjusted threshold in the trading strategy
    side, quantity, price = trend_following_strategy_with_order_count(
        data, available_Base,available_Quote, 0.00075, order_count_threshold
    )

    with open(backtesting_filename, 'a') as log_file:
        log_message(log_file, f"Signal: {side} Quantity: {quantity} Price: {price}\n Available {base}: {available_Base} Available {quote}: {available_Quote}",print_message=False)

    # Looking for trade
    if not waiting_for_order:

        if side == 'buy' and available_Quote > 0:
            # Place a buy order
            with open(backtesting_filename, 'a') as log_file:
                log_message(log_file, f"Placing buy order for {quantity} {base} at {price} {quote}")
            order_price = price
            order_side = side
            order_quantity = quantity
            order_nonce = int(generate_nonce())
            waiting_for_order = True
            
        elif side == 'sell' and available_Base > 0:
            with open(backtesting_filename, 'a') as log_file:
                log_message(log_file, f"Placing sell order for {quantity} {base} at {price} {quote}")
            order_price = price
            order_side = side
            order_quantity = quantity
            order_nonce = int(generate_nonce())
            waiting_for_order = True
        
        else :
            with open(backtesting_filename, 'a') as log_file:
                log_message(log_file, f"Signal: {side}")
        time.sleep(sleep_time_no_order_seconds)
    else:
        with open(backtesting_filename, 'a') as log_file:
            log_message(log_file, f"Waiting for order {order_side} to be filled. Current ask price: {current_ask_price} Current bid price: {current_bid_price} Order price: {order_price} Order quantity: {order_quantity}")
        if order_side == 'buy' and current_ask_price <= order_price:
            available_Base += order_quantity
            available_Quote -= order_quantity * order_price
            
            with open(backtesting_filename, 'a') as log_file:
                log_message(log_file, f"Order {order_side} filled. Now I have {available_Base} {base} and {available_Quote} {quote}")

            waiting_for_order = False
            order_price = None
            order_quantity = None
            order_nonce = None
            order_side = None

        elif order_side == 'sell' and current_bid_price >= order_price:
            available_Base -= order_quantity
            available_Quote += order_quantity * order_price
            with open(backtesting_filename, 'a') as log_file:
                log_message(log_file, f"Order {order_side} filled. Now I have {available_Base} {base} and {available_Quote} {quote}")
            waiting_for_order = False
            order_price = None
            order_quantity = None
            order_nonce = None
            order_side = None
        
        if waiting_for_order :
            if abs((int(generate_nonce()) - order_nonce) / (1000 * 60)) > wait_time_order_minutes:
                # Cancel the order if it's been waiting for more than wait_time_order minutes
                with open(backtesting_filename, 'a') as log_file:
                    log_message(log_file, f"Cancelling order {order_side} after {wait_time_order_minutes} minutes")
                waiting_for_order = False
                order_price = None
                order_quantity = None
                order_nonce = None
                order_side = None    
        time.sleep(sleep_time_order_seconds)
        