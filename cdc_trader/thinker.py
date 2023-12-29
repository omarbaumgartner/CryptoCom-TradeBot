import copy
from functions import *
from env import *
from classes import *
from calcul import *

# Get instruments from ticker that could be used for trading


def get_usable_instruments(ticker, min_spread_percentage):
    instruments = {}
    for tick in ticker:
        # Cleaning based on tests
        if '-' not in tick['i'] and 'T_USD' not in tick["i"] and 'PERP' not in tick["i"] and tick["a"] != "0" and tick["b"] != "0" and tick["k"] != "0" and tick["a"] != None and tick["b"] != None and tick["k"] != None:
            # if quote or base is USD
            if 'USD' in tick["i"].split('_') or 'EUR' in tick["i"].split('_'):
                pass
            else:
                # if spread is greater than minimum_percentage_increase_decrease
                if 100*((float(tick["a"]) - float(tick["b"])) / float(tick["b"])) >= min_spread_percentage:
                    instruments[tick["i"]] = tick["i"]

    return dict(sorted(instruments.items()))

# Function to check if 'USD' and 'USDT' appear consecutively TODO : make it work for any number of currencies


def contains_consecutive_usd_usdt(pair):
    for i in range(len(pair) - 1):
        if (pair[i] == 'USD' and pair[i + 1] == 'USDT') or (pair[i] == 'USDT' and pair[i + 1] == 'USD'):
            return True
    return False

# Get possible trading sequences that start with start_currency and end with one of the possible end_currencies


def generate_possible_trading_sequences(usable_instruments, start_currencies, end_currencies, max_depth=3):
    sequences_queue = []
    for start_currency in start_currencies:
        # We start with a queue containing only the start currency
        sequences_queue.append([start_currency])

    final_queue = []

    # print("Looking for arbitrage opportunities...")
    stop_loop = False

    while stop_loop == False:
        num_parents = len(sequences_queue)
        for sequence in copy.deepcopy(sequences_queue):
            # depth still not reached, we add childs to sequence
            if len(sequence) < max_depth:
                # if it loops before reaching depth, we remove it
                if len(sequence) > len(set(sequence)):
                    sequences_queue.remove(sequence)
                    continue

                # Get last currency in sequence
                end_sequence_currency = sequence[-1]
                # get instruments that contain last currency in one of the two positions (base or quote)
                for instrument in usable_instruments:
                    # if last currency is in base or quote
                    if end_sequence_currency in instrument.split('_'):
                        # add parent with new currency to queue
                        if instrument.split('_')[0] == end_sequence_currency:
                            sequences_queue.append(
                                sequence[:-1]+instrument.split('_'))
                        elif instrument.split('_')[1] == end_sequence_currency:
                            sequences_queue.append(
                                sequence[:-1]+instrument.split('_')[::-1])

            # depth reached
            else:
                # if last currency is not in end_currencies, we remove the sequence
                if sequence[-1] not in end_currencies:
                    sequences_queue.remove(sequence)
        sequences_queue = list(map(list, set(tuple(inner_list)
                               for inner_list in sequences_queue)))
        if len(sequences_queue) == 0:
            stop_loop = True
            # print("No final sequences, stopping loop")

        elif len(sequences_queue) == num_parents:
            # print("No new parents added, stopping loop")
            stop_loop = True

        if stop_loop == True:
            # When we have no more possibilites, we check if the last currency is in the end_currencies
            # And we populate the final queue
            # Convert inner lists to tuples and then to a set to remove duplicates
            sequences_queue = set(tuple(inner_list)
                                  for inner_list in sequences_queue)

            # Convert the set of tuples back to a list of lists
            sequences_queue = [list(inner_tuple)
                               for inner_tuple in sequences_queue]
            sequences_queue = [
                lst for lst in sequences_queue if not has_duplicates_middle(lst)]

            for sequence in sequences_queue:
                if sequence not in final_queue and len(sequence) > 1 and sequence[-1] in end_currencies and len(sequence) == max_depth:
                    final_queue.append(sequence)
            break

    return final_queue

# Generate readable instrument pairs in order to create trade orders


def generate_readable_instrument_pairs(cleaned_queue):
    cleaned = []
    for q in cleaned_queue:
        pairs_to_trade = []
        for i in range(len(q)-1):
            pairs_to_trade.append(f"{q[i]}_{q[i+1]}")
        cleaned.append(pairs_to_trade)
    return cleaned

# Generate sequence of trades to execute


def create_trading_sequences(possible_instrument_pairs, instrument_names):
    ts_l = TradeSequences()
    for c in possible_instrument_pairs:
        ts = SingleTradeSequence()
        # Correct the order of the pairs
        for i in range(len(c)):
            ts.order_of_trades.append(c[i])
            # if the instrument name is not in instrument_names, this means that the pair is reversed, so we reverse it back
            if c[i] not in instrument_names:
                c[i] = c[i].split('_')[::-1]
                c[i] = '_'.join(c[i])

            ts.add_instrument_name(c[i])
        ts_l.add_trade_sequence(ts)
    return ts_l


def has_duplicates_middle(lst):
    seen = set()
    for item in lst[1:]:
        if item in seen:
            return True
        seen.add(item)
    return False


def filter_and_order_by_return(sequences: list[SingleTradeSequence], accounts, instruments_dict) -> list[SingleTradeSequence]:
    kept_sequences = []
    for sequence in sequences:
        # Getting number of trades
        num_trades = len(sequence.instrument_names)
        # Calculating profit percentage per trade
        profit_percentage_per_trade = (
            MIN_PROFITS_PERCENTAGE ** (1/num_trades) + TRADING_FEE_PERCENTAGE)
        available_quantities = []
        future_values = []
        # check if base or quote
        initial_currency = sequence.order_of_trades[0].split("_")[0]

        available_quantity = accounts[initial_currency]['available']
        available_quantities.append(available_quantity)
        future_values.append(available_quantity)
        min_quantity = float(
            instruments_dict[sequence.instrument_names[0]]['min_quantity'])

        min_decimals = int(instruments_dict[sequence.instrument_names[0]
                                            ]['quantity_decimals'])

        # Min price for buy order for one token
        ask_price = float(
            sequence.tickers[0]['a']) * (1 - profit_percentage_per_trade/100)
        # Max price for sell order for one token
        bid_price = float(
            sequence.tickers[0]['b']) * (1 + profit_percentage_per_trade/100)
        checks = []
        base, quote = sequence.instrument_names[0].split("_")
        if initial_currency == sequence.instrument_names[0].split("_")[0]:
            is_base = True
        else:
            is_base = False

        # BASE CURRENCY (CRYPTO)
        if is_base:
            side = 'sell'
            price = bid_price
            # If we have enough quantity
            if available_quantity >= min_quantity:
                # We convert it to quote currency
                # This calculates the quantity in terms of the token being sold.
                available_quantity = (
                    available_quantity / ask_price) * (1 - TRADING_FEE_PERCENTAGE/100)
                quantity_value = available_quantity * ask_price
                print(
                    f"Sell {available_quantity} {base} for {quantity_value} {quote}")

                # available_quantity = math.floor(
                #     available_quantity * 10**min_decimals) / 10**min_decimals
                checks.append([side, True])
            else:
                checks.append([side, False])

        # QUOTE CURRENCY (FIAT/STABLECOIN or CRYPTO)
        else:
            side = 'buy'
            price = ask_price
            # This calculates the quantity in terms of the token being bought.

            future_tokens_quantity = (
                available_quantity / bid_price) * (1 - TRADING_FEE_PERCENTAGE/100)
            # This calculates the value of the quantity in terms of the token being sold.
            # rounded_future_tokens_quantity = math.floor(
            #     future_tokens_quantity * 10**min_decimals) / 10**min_decimals

            if future_tokens_quantity >= min_quantity:
                checks.append([side, True])
                available_quantity = future_tokens_quantity
                quantity_value = available_quantity * bid_price
                print(
                    f"Buy {available_quantity} {quote} for {available_quantity} {base}")

            else:
                checks.append([side, False])
                # return checks, available_quantities

        available_quantities.append(available_quantity)
        future_values.append(quantity_value)

        # if side == 'sell':
        #     quantity =
        trade = {
            "instrument_name": sequence.instrument_names[0],
            "side": side,
            "price": price,
            "quantity": available_quantity
        }
        sequence.add_trade_infos(trade)

        # Check rest of the sequence
        for ticker, order_of_trade, instrument_name in zip(sequence.tickers[1:], sequence.order_of_trades[1:], sequence.instrument_names[1:]):
            base, quote = instrument_name.split("_")

            # invert side
            initial_currency = order_of_trade.split("_")[0]
            if initial_currency == instrument_name.split("_")[0]:
                is_base = True
                side = 'sell'
            else:
                is_base = False
                side = 'buy'

            min_quantity = float(
                instruments_dict[instrument_name]['min_quantity'])
            # Min price for buy order for one token
            ask_price = float(ticker['a']) * \
                (1-profit_percentage_per_trade/100)
            # Max price for sell order for one token
            bid_price = float(ticker['b']) * \
                (1 + profit_percentage_per_trade/100)

            initial_currency = order_of_trade.split("_")[0]
            min_decimals = int(
                instruments_dict[instrument_name]['quantity_decimals'])

            if side == 'sell':
                price = bid_price
                if available_quantity >= min_quantity:
                    available_quantity = (
                        available_quantity / ask_price) * (1 - TRADING_FEE_PERCENTAGE/100)
                    quantity_value = available_quantity * ask_price
                    print(
                        f"Sell {available_quantity} {base} for {quantity_value} {quote}")
                    # available_quantity = math.floor(
                    #     available_quantity * 10**min_decimals) / 10**min_decimals
                    checks.append([side, True])
                else:
                    checks.append([side, False])
                    # return checks, available_quantities
            else:
                price = ask_price
                future_tokens_quantity = (
                    available_quantity / bid_price) * (1 - TRADING_FEE_PERCENTAGE/100)
                future_tokens_quantity = future_tokens_quantity
                # rounded_future_tokens_quantity = math.floor(
                #     future_tokens_quantity * 10**min_decimals) / 10**min_decimals
                if future_tokens_quantity >= min_quantity:
                    checks.append([side, True])
                    available_quantity = future_tokens_quantity
                    quantity_value = available_quantity * bid_price
                    print(
                        f"Buy {available_quantity} {quote} for {available_quantity} {base}")
                else:
                    checks.append([side, False])
                    # return checks, available_quantities

            available_quantities.append(available_quantity)
            future_values.append(quantity_value)
            trade = {
                "instrument_name": instrument_name,
                "side": side,
                "price": price,
                "quantity": available_quantity
            }
            sequence.add_trade_infos(trade)

        has_false = any(False in sublist for sublist in checks)
        if not has_false:
            # TODO : make it work for any currencies instead of USDT -> ... -> USDT
            print("Instruments", sequence.instrument_names)
            print("Traders", sequence.order_of_trades)
            print("Checks", checks)
            print("Available quantities", available_quantities)
            print("Future values", future_values)
            input()
            sequence.percentage_return = calculate_percentage_return(
                available_quantities[0], available_quantities[-1])
            sequence.checks = checks
            sequence.available_quantities = available_quantities
            kept_sequences.append(sequence)
            # print(sequence.percentage_return)

    return sorted(kept_sequences, key=lambda x: x.percentage_return, reverse=True)


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

    # ordered_sequences = ts_l.order_trade_sequences_by_return()
    return ts_l.get_trade_sequences()
