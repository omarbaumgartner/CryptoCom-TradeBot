import copy
from functions import *

class TradeSequences:
    def __init__(self):
        self.trade_sequences = []

    def add_trade_sequence(self, trade_sequence):
        self.trade_sequences.append(trade_sequence)

    def update_trade_sequences_tickers(self):
        ticker_all = get_ticker()
        instruments = []
        for ts in self.trade_sequences:
            ts_instruments = ts.get_instruments_names()
            instruments += ts_instruments
            # remove duplicates
            instruments = list(set(instruments))
        # keep in ticker only the instruments that are in instruments
        ticker = {

        }
        for tick in ticker_all:
            if tick['i'] in instruments:
                ticker[tick['i']] = tick
        # update tickers
        for ts in self.trade_sequences:
            ts.update_tickers(ticker)


class SingleTradeSequence:
    def __init__(self):
        self.instrument_names = []
        self.tickers = []
        self.order_of_trades = []

    def add_instrument_name(self, instrument_name):
        # print("Adding instrument name", instrument_name)
        self.instrument_names.append(instrument_name)
        self.tickers.append({})

    def get_instruments_names(self):
        return self.instrument_names

    def update_tickers(self, ticker):
        for i in range(len(self.instrument_names)):
            self.tickers[i] = ticker[self.instrument_names[i]]

    def display_tickers(self):
        for i in range(len(self.instrument_names)):
            print(self.instrument_names[i], self.tickers[i])

# Get instruments from ticker that could be used for trading
def get_usable_instruments(ticker):
    instruments = {}
    for tick in ticker:
        if 'PERP' not in tick["i"] and tick["a"] != "0" and tick["b"] != "0" and tick["k"] != "0" and tick["a"] != None and tick["b"] != None and tick["k"] != None:
            try:
                instruments[tick["i"]] = {
                    "instrument_name": tick["i"],
                }
            except:
                print("Error with tick", tick)
    return instruments

# Function to check if 'USD' and 'USDT' appear consecutively
# TODO : make it work for any number of currencies
def contains_consecutive_usd_usdt(pair):
    for i in range(len(pair) - 1):
        if (pair[i] == 'USD' and pair[i + 1] == 'USDT') or (pair[i] == 'USDT' and pair[i + 1] == 'USD'):
            return True
    return False

# Get possible trading sequences that start with start_currency and end with one of the possible end_currencies
# TODO : make start_currency also take one to many possible currencies
def generate_possible_trading_sequences(items, start_currency, end_currencies, max_depth=3):
    print("items", items)
    input()

    queue = [start_currency]
    cleaned_queue = []
    print("Looking for arbitrage opportunities...")
    stop_loop = False
    while True:
        if stop_loop:
            break
        length = len(queue)
        tmp_queue = copy.deepcopy(queue)

        for q in tmp_queue:
            currency = q[-1]
        # get items that contain currency
            currency_items = {}
            for item in items:
                if currency in item.split('_'):
                    currency_items[item] = items[item]

        # add items to queue
            for item in currency_items.keys():
                if item.split('_')[0] == currency:
                    queue.append(q[:-1]+item.split('_'))
                elif item.split('_')[1] == currency:
                    queue.append(q[:-1]+item.split('_')[::-1])

        # Remove loops in queue
            if len(q) < max_depth:
                for q in queue:
                    if len(q) > len(set(q)):
                        queue.remove(q)

            else:
                for q in queue:
                    # print("check if ", q[-1], " is in ", end_currencies)
                    if q[-1] in end_currencies:
                        # check if USD and USDT are not one after the other
                        if contains_consecutive_usd_usdt(q):
                            pass
                        else:
                            cleaned_queue.append(q)

                # break from loop and while
                stop_loop = True

        queue = queue[length:]
    cleaned_queue = list(set([tuple(q) for q in cleaned_queue]))
    return cleaned_queue


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
    # fix the order of the pairs
    # print('Fixing order of pairs...', len(c))
        for i in range(len(c)):
            ts.order_of_trades.append(c[i])
        # check if the pair is in the instrument names
        # if not, reverse the pair
            instrument_name = None
            if c[i] not in instrument_names:
                c[i] = c[i].split('_')[::-1]
            # join list to string
                c[i] = '_'.join(c[i])
            ts.add_instrument_name(c[i])
        ts_l.add_trade_sequence(ts)
    return ts_l


# Terminology :
# instrument : a tradable asset that can be bought or sold

print("Getting instruments...")
instruments, instruments_names = get_instruments()

print("Getting tickers...")
ticker = get_ticker()

print("Cleaning instruments...")
items = get_usable_instruments(ticker)

start_currency = ["USD"]
end_currencies = ["USD"]
max_depth = 3
print(
    f"Getting possible trading sequences with start currency {start_currency} and end currencies {end_currencies} and max depth of {max_depth} ...")
possible_trading_sequences = generate_possible_trading_sequences(
    items, start_currency, end_currencies, max_depth)
    
print(f"Sample of possible trading sequences: {possible_trading_sequences[:5]}")
input()
print("Generating readable instrument pairs...")
possible_instrument_pairs = generate_readable_instrument_pairs(
    possible_trading_sequences)
print(f"Sample of possible instrument pairs: {possible_instrument_pairs[:5]}")
input()
print("Creating trading sequences...")
ts_l = create_trading_sequences(possible_instrument_pairs, instruments_names)

print("Final trade sequences possible", len(ts_l.trade_sequences))
input()
# get instrument names
instrument_names = []
currency_names = []
for instrument in instruments:
    instrument_names.append(instrument['instrument_name'])
    base, quote = instrument['instrument_name'].split('_')
    if base not in currency_names:
        currency_names.append(base)
    if quote not in currency_names:
        currency_names.append(quote)

exit()

