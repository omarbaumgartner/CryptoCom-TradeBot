import copy
from functions import *
from env import TRADING_FEE_PERCENTAGE, DESIRED_PROFIT_PERCENTAGE
from classes import *

# Terminology :
# instrument : a tradable asset that can be bought or sold

# for ts in ts_l.trade_sequences:
#     ts.display_tickers()
#     input()


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
