import asyncio
from functions import *
from env import commands_queue
from telegram import send_telegram_message, initialize_telegram
from thinker import *
from classes import *
import math

# Add other necessary imports and functions here

# Method	Limit
# public/get-book
# public/get-ticker
# public/get-trades	100 requests per second each

# Method	Limit
# private/create-order
# private/cancel-order
# private/cancel-all-orders	15 requests per 100ms each
# private/get-order-detail	30 requests per 100ms
# private/get-trades	1 requests per second
# private/get-order-history	1 requests per second
# All others	3 requests per 100ms each
# Add other necessary imports and functions here
# trading method : crypto-to-crypto arbitrage

END_CURRENCIES = ["USDT"]
MIN_SPREAD_PERCENTAGE = 0.0
MIN_PROFITS_PERCENTAGE = 0.2 # TODO : integrate it
MAX_DEPTH = 4


user = UserAccounts()
user.update_accounts()
user.display_accounts()

# input()
# TODO : OPTIMIZE SPEED BASED ON REQUEST TYPE LIMITS
# TODO : Adapt ask and bid price to profit percentage !!!!!!!
def filter_and_order_by_return(sequences:list[SingleTradeSequence],accounts,instruments_dict):
    kept_sequences = []
    
    for sequence in sequences :
        available_quantities = []
        # check if base or quote
        initial_currency = sequence.order_of_trades[0].split("_")[0]
        available_quantity = accounts[initial_currency]['available']
        available_quantities.append(available_quantity)
        min_quantity = float(
            instruments_dict[sequence.instrument_names[0]]['min_quantity'])
        
        min_decimals = int(instruments_dict[sequence.instrument_names[0]
                                            ]['quantity_decimals'])

        # Min price for buy order for one token
        ask_price = float(sequence.tickers[0]['a'])
        # Max price for sell order for one token
        bid_price = float(sequence.tickers[0]['b'])
        checks = []
        if initial_currency == sequence.instrument_names[0].split("_")[0]:
            is_base = True
        else:
            is_base = False

        # CRYPTO
        if is_base:
            side = 'sell'
            if available_quantity >= min_quantity:
                available_quantity = available_quantity * ask_price
                # available_quantity = math.floor(
                #     available_quantity * 10**min_decimals) / 10**min_decimals
                checks.append([side, True])
            else:
                checks.append([side, False])

        # FIAT/STABLECOIN or CRYPTO
        else:
            side = 'buy'
            future_tokens_quantity = available_quantity / bid_price
            rounded_future_tokens_quantity = future_tokens_quantity
            # rounded_future_tokens_quantity = math.floor(
            #     future_tokens_quantity * 10**min_decimals) / 10**min_decimals
            if rounded_future_tokens_quantity >= min_quantity:
                checks.append([side, True])
                available_quantity = rounded_future_tokens_quantity
            else:
                checks.append([side, False])
                return checks,available_quantities

        available_quantities.append(available_quantity)
        # Check rest of the sequence
        for ticker, order_of_trade, instrument_name in zip(sequence.tickers[1:], sequence.order_of_trades[1:], sequence.instrument_names[1:]):
            # invert side
            initial_currency = order_of_trade.split("_")[0]
            if initial_currency == instrument_name.split("_")[0]:
                is_base = True
                side = 'sell'
            else:
                is_base = False
                side = 'buy'

            min_quantity = float(instruments_dict[instrument_name]['min_quantity'])
            ask_price = float(ticker['a'])  # Min price for buy order for one token
            # Max price for sell order for one token
            bid_price = float(ticker['b'])
            initial_currency = order_of_trade.split("_")[0]
            min_decimals = int(instruments_dict[instrument_name]['quantity_decimals'])

            if side == 'sell':
                if available_quantity >= min_quantity:
                    available_quantity = available_quantity * ask_price
                    # available_quantity = math.floor(
                    #     available_quantity * 10**min_decimals) / 10**min_decimals
                    checks.append([side, True])
                else:
                    checks.append([side, False])
                    return checks,available_quantities
            else:
                future_tokens_quantity = available_quantity / bid_price
                rounded_future_tokens_quantity = future_tokens_quantity
                # rounded_future_tokens_quantity = math.floor(
                #     future_tokens_quantity * 10**min_decimals) / 10**min_decimals
                if rounded_future_tokens_quantity >= min_quantity:
                    checks.append([side, True])
                    available_quantity = rounded_future_tokens_quantity
                else:
                    checks.append([side, False])
                    return checks,available_quantities

            available_quantities.append(available_quantity)

        has_false = any(False in sublist for sublist in checks)
        if not has_false:
            # TODO : make it work for any currencies instead of USDT -> ... -> USDT
            sequence.percentage_return = ((available_quantities[-1] / available_quantities[0])/ abs(available_quantities[0])) * 100
            sequence.checks = checks
            sequence.available_quantities = available_quantities
            kept_sequences.append(sequence)
            # kept_checks.append(checks)

    return sorted(kept_sequences, key=lambda x: x.percentage_return, reverse=True)
            


async def main():

    print("Starting trader...")
    # Initialize bot and authentication
    print("Initializing telegram...")
    await initialize_telegram()

    # Update accounts
    user.update_accounts()

    selected_sequence = None
    wait_for_order = False
    # Main trading loop
    while True:
        # High frequency monitoring when waiting for order
        if wait_for_order:
            sleep_time = 0.01
        else:
            sleep_time = 0.1

        # Consume commands from the queue
        if len(commands_queue) > 0:
            for command in commands_queue:
                if command == 'stop':
                    return

        if not wait_for_order:
            # Look for best trading sequence
            if not selected_sequence:
                available_currencies = user.get_available_currencies()
                print("Available currencies", available_currencies)
                print("Looking for top sequence...")
                sequences = get_trading_sequences(
                    start_currencies=available_currencies,
                    end_currencies=END_CURRENCIES,
                )
                top_sequences = filter_and_order_by_return(sequences,user.accounts,user.instruments_dict)
                # Need min_quantity for each instrument
                # accounts=user.accounts,
                # Need to check if available balance > min_quantity
                # instruments_dict=user.instruments_dict
                if len(top_sequences) != 0:
                    for sequence in top_sequences:
                        #sequence.display_infos()
                        print("Percentage return",sequence.percentage_return)

                        if sequence.percentage_return > MIN_PROFITS_PERCENTAGE:
                            sequence.display_infos()
                            print("Checks",sequence.checks)
                            print("Available quantities",sequence.available_quantities)
                            print("Percentage return",sequence.percentage_return)
                            input()
                    # is_possible,predicted_quantities = check_if_sequence_is_possible(
                    #     sequence, user.accounts, user.instruments_dict)
                    # has_false = any(False in sublist for sublist in is_possible)
                    # if not has_false:
                    #     sequence.display_infos()
                    #     print("Is possible", is_possible)
                    #     print("Predicted quantities",predicted_quantities)
                    #     input()
                    #     top_sequence = sequence
                        
                    
                top_sequence = None
                if top_sequence:
                    print("Top trade sequence with return of",
                          top_sequence.compound_return)
                    # TODO : take into account trading fee in compound calculator

                    selected_sequence = top_sequence
                    await send_telegram_message(
                        f"Top trade sequence with return of {top_sequence.compound_return}")
                else:
                    print("No top sequence available")
            # Sequence already selected, jump to next order placement
            else:
                print("Top sequence already selected, jumping to order placement")
                selected_sequence.display_infos()
                instrument, order_type, price = selected_sequence.get_next_order()
                print("Placing order of type", order_type,
                      "for instrument", instrument, "at price", price)
                wait_for_order = True

        else:
            print("Waiting for order to be filled")

            if False:
                print("Order filled")
                wait_for_order = False
                selected_sequence = None
                # TODO : send telegram message
                # send_telegram_message("Order filled")
                # Place order of top sequence

        # Monitor order execution

        # Telegram notifications (if needed)
        # send_telegram_message("Order placed successfully")

        # Sleep between iterations
        await asyncio.sleep(sleep_time)


def check_if_sequence_is_possible(sequence: SingleTradeSequence, accounts, instruments_dict):
    available_quantities = []
    # First order in sequence

    # check if base or quote
    initial_currency = sequence.order_of_trades[0].split("_")[0]
    available_quantity = accounts[initial_currency]['available']
    available_quantities.append(available_quantity)
    min_quantity = float(
        instruments_dict[sequence.instrument_names[0]]['min_quantity'])
    
    min_decimals = int(instruments_dict[sequence.instrument_names[0]
                                        ]['quantity_decimals'])

    # Min price for buy order for one token
    ask_price = float(sequence.tickers[0]['a'])
    # Max price for sell order for one token
    bid_price = float(sequence.tickers[0]['b'])
    checks = []
    if initial_currency == sequence.instrument_names[0].split("_")[0]:
        is_base = True
    else:
        is_base = False

    # CRYPTO
    if is_base:
        side = 'sell'
        if available_quantity >= min_quantity:
            available_quantity = available_quantity * ask_price
            # available_quantity = math.floor(
            #     available_quantity * 10**min_decimals) / 10**min_decimals
            checks.append([side, True])
        else:
            checks.append([side, False])
            return checks,available_quantities

    # FIAT/STABLECOIN or CRYPTO
    else:
        side = 'buy'
        future_tokens_quantity = available_quantity / bid_price
        rounded_future_tokens_quantity = future_tokens_quantity
        # rounded_future_tokens_quantity = math.floor(
        #     future_tokens_quantity * 10**min_decimals) / 10**min_decimals
        if rounded_future_tokens_quantity >= min_quantity:
            checks.append([side, True])
            available_quantity = rounded_future_tokens_quantity
        else:
            checks.append([side, False])
            return checks,available_quantities

    available_quantities.append(available_quantity)
    # Check rest of the sequence
    for ticker, order_of_trade, instrument_name in zip(sequence.tickers[1:], sequence.order_of_trades[1:], sequence.instrument_names[1:]):
        # invert side
        initial_currency = order_of_trade.split("_")[0]
        if initial_currency == instrument_name.split("_")[0]:
            is_base = True
            side = 'sell'
        else:
            is_base = False
            side = 'buy'

        min_quantity = float(instruments_dict[instrument_name]['min_quantity'])
        ask_price = float(ticker['a'])  # Min price for buy order for one token
        # Max price for sell order for one token
        bid_price = float(ticker['b'])
        initial_currency = order_of_trade.split("_")[0]
        min_decimals = int(instruments_dict[instrument_name]['quantity_decimals'])

        if side == 'sell':
            if available_quantity >= min_quantity:
                available_quantity = available_quantity * ask_price
                print("Available quantity", available_quantity)
                # available_quantity = math.floor(
                #     available_quantity * 10**min_decimals) / 10**min_decimals
                print("Available quantity", available_quantity)
                checks.append([side, True])
            else:
                checks.append([side, False])
                return checks,available_quantities
        else:
            future_tokens_quantity = available_quantity / bid_price
            rounded_future_tokens_quantity = future_tokens_quantity
            # rounded_future_tokens_quantity = math.floor(
            #     future_tokens_quantity * 10**min_decimals) / 10**min_decimals
            if rounded_future_tokens_quantity >= min_quantity:
                checks.append([side, True])
                available_quantity = rounded_future_tokens_quantity
            else:
                checks.append([side, False])
                return checks,available_quantities

        available_quantities.append(available_quantity)

    return checks,available_quantities

    print("Initial currency", initial_currency)
    initial_currency_available = accounts[initial_currency]['available']
    print("Initial currency available", initial_currency_available)
    # check if initial currency available > min_quantity
    input()

    if initial_currency_available > instruments_dict[sequence.order_of_trades[0]]['min_quantity']:
        print("Initial currency available > min_quantity")
        # check if initial currency available > min_quantity
        for i in range(len(sequence.order_of_trades)-1):
            print("Checking if", sequence.order_of_trades[i], "is possible")
            # check if initial currency available > min_quantity
            if accounts[sequence.order_of_trades[i]]['available'] > instruments_dict[sequence.order_of_trades[i]]['min_quantity']:
                print(sequence.order_of_trades[i], "is possible")
                return True
            else:
                print(sequence.order_of_trades[i], "is not possible")
                return False
    else:
        print("Initial currency available < min_quantity")
        return False

    input()
    # sequence.display_infos()

    pass


def get_trading_sequences(start_currencies: list[str], end_currencies: list[str]) -> list[SingleTradeSequence]:
    # Monitor market data
    ticker = get_ticker()

    # Get all usable instruments with spread > MIN_SPREAD_PERCENTAGE
    instrument_names = get_usable_instruments(
        ticker, MIN_SPREAD_PERCENTAGE)

    # print(f"Getting possible trading sequences with start currency {START_CURRENCIES} and end currencies {END_CURRENCIES} and max depth of {MAX_DEPTH} ...")
    possible_trading_sequences = generate_possible_trading_sequences(
        instrument_names, start_currencies, end_currencies, MAX_DEPTH)
    # print("Generating readable instrument pairs for each sequence")
    possible_instrument_pairs = generate_readable_instrument_pairs(
        possible_trading_sequences)

    # print("Creating trading sequences...")
    ts_l = create_trading_sequences(
        possible_instrument_pairs, instrument_names)
    ts_l.update_trade_sequences_tickers()
    # print("Final trade sequences possible", len(ts_l.trade_sequences))

    #ordered_sequences = ts_l.order_trade_sequences_by_return()
    return ts_l.get_trade_sequences()


if __name__ == "__main__":
    asyncio.run(main())
