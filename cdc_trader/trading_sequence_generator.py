import copy
from trading_api_client import *
from trading_config_loader import *
from trading_classes import *
from financial_calculations import *
from decimal import Decimal, ROUND_CEILING

# Get instruments from ticker that could be used for trading
def get_usable_instruments(ticker, min_spread_percentage):
    instruments = {}
    for tick in ticker:
        # print(tick)
        # input()
        # Cleaning based on tests
        if '-' not in tick['i'] and 'T_USD' not in tick["i"] and 'PERP' not in tick["i"] and tick["a"] != "0" and tick["b"] != "0" and tick["k"] != "0" and tick["a"] != None and tick["b"] != None and tick["k"] != None:
            # if quote or base is USD
            if 'USD' in tick["i"].split('_') or 'EUR' in tick["i"].split('_'):
                pass
            else:
                # if spread is greater than minimum_percentage_increase_decrease
                if 100*((float(tick["a"]) - float(tick["b"])) / float(tick["b"])) >= min_spread_percentage:
                    instruments[tick["i"]] = {
                        'instrument_name': tick['i'],
                        'verified_volume' : tick['vv'],
                        }

    
    
    # sort instruments dict by vv attribute inside each instrument
    instruments = dict(sorted(instruments.items(), key=lambda x: round(float(x[1]['verified_volume']),2), reverse=True))
    # slice instruments dict to keep only the first num_instruments instruments
    instruments = dict(list(instruments.items())[:50])
    return instruments.keys()

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
            if len(sequence) < max_depth: # +1 because we need to add the end currency
                # if it the trade loops before reaching depth, we remove it
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

        # check if base or quote
        initial_currency = sequence.order_of_trades[0].split("_")[0]

        start_currency = initial_currency
        initial_quantity = accounts[initial_currency]['available']
        if initial_quantity > MAX_INVESTMENT_PER_TRADE:
            initial_quantity = MAX_INVESTMENT_PER_TRADE

        # Loop through each trade
        for (i,(ticker, order_of_trade, instrument_name)) in enumerate(zip(sequence.tickers, sequence.order_of_trades, sequence.instrument_names)):
            dropped_trade = False
            # Check if first order
            if i == 0:
                # Get initial available quantity
                available_currency_quantity = initial_quantity

            #print('instrument_name', instrument_name)
            # Get base and quote of instrument
            base, quote = instrument_name.split("_")
            price_decimals = instruments_dict[instrument_name]['price_decimals']
            quantity_decimals = instruments_dict[instrument_name]['quantity_decimals']
            # Get initial currency
            initial_currency = order_of_trade.split("_")[0]

            # Get the minimum quantity needed for the trade
            min_quantity = float(
                instruments_dict[instrument_name]['min_quantity'])

            # Set side based on initial currency and instrument
            side = 'sell' if initial_currency == base else 'buy'
            ask_price = float(ticker['a'])
            bid_price = float(ticker['b'])
            # print("Ask price", ask_price)
            # print("Bid price", bid_price)
            # print("Side", side)
            # Buying order --> buy quote for base
            if side == 'buy':
                # This adjusted ask price is the price you are willing to pay per BTC to achieve a K% profit.
                adjusted_ask_price = ask_price * (1-profit_percentage_per_trade/100)
                # print("Adjusted ask price", adjusted_ask_price)
                # print("Price decimals", price_decimals)
                # Round to the lowest (floor) price_decimals
                adjusted_ask_price = floor_with_decimals(adjusted_ask_price, price_decimals)
                # print("Adjusted ask price", adjusted_ask_price)
                # print("Available currency quantity", available_currency_quantity)
                # Number of tokens to get after the trade with adjusted ask price
                base_quantity_to_get = available_currency_quantity / (adjusted_ask_price * (1 - TRADING_FEE_PERCENTAGE/100))

                # Round to the lowest (floor) quantity_decimals
                base_quantity_to_get = floor_with_decimals(base_quantity_to_get, quantity_decimals)

                # Resets initial quantity after adapting first trade quantity
                if i == 0:
                    initial_quantity = base_quantity_to_get * adjusted_ask_price

                price = adjusted_ask_price
                
                if base_quantity_to_get >= min_quantity:
                    #print(f"Buy {base_quantity_to_get} {base} for {available_currency_quantity} {quote}")
                    available_currency_quantity = base_quantity_to_get
                else:
                    dropped_trade = True
                    continue
                
                trade = {
                    "instrument_name": instrument_name,
                    "side": side,
                    "price": price,
                    "quantity": available_currency_quantity
                }

            # Selling order --> sell base for quote
                
            # Issue when it's the last trade
            # Trades [{'instrument_name': 'ETH_USDT', 'side': 'buy', 'price': 2307.4386734177156, 'quantity': 0.4337062451327935}, 
            #         {'instrument_name': 'ETH_PYUSD', 'side': 'sell', 'price': 2315.4, 'quantity': 0.4337062451327935}, 
            #         {'instrument_name': 'PYUSD_USDT', 'side': 'sell', 'price': 0.99949, 'quantity': 0.4337062451327935}]
            else:
                # This adjusted bid price is the price you are willing to sell per BTC to achieve a K% profit.
                adjusted_bid_price = bid_price * (1 + profit_percentage_per_trade/100)

                # Round to the highest (floor) price_decimals
                adjusted_bid_price = ceil_with_decimals(adjusted_bid_price, price_decimals)
                
                
                quote_quantity_to_get = available_currency_quantity * adjusted_bid_price * (1 - TRADING_FEE_PERCENTAGE/100)
                
                # Floor with quantity_decimals
                quote_quantity_to_get = floor_with_decimals(quote_quantity_to_get, quantity_decimals)

                price = adjusted_bid_price
                

                    
                            
                #sell_quantity = available_currency_quantity
                # We check that we have enough quantity to sell
                if available_currency_quantity >= min_quantity:
                    pass
                    #print(f"Sell {available_currency_quantity} {base} for {quote_quantity_to_get} {quote}")
                    #available_currency_quantity = quote_quantity_to_get
                else:
                    # We don't have enough quantity to sell, we skip the sequence
                    dropped_trade = True
                    continue

                trade = {
                    "instrument_name": instrument_name,
                    "side": side,
                    "price": price,
                    "quantity": available_currency_quantity
                }
                available_currency_quantity = quote_quantity_to_get
            sequence.add_trade_infos(trade)
        
        if not dropped_trade:
            end_currency = sequence.order_of_trades[-1].split("_")[1]
            end_quantity = round(sequence.trade_infos[-1]['quantity'] * sequence.trade_infos[-1]['price'] - (sequence.trade_infos[-1]['quantity'] * sequence.trade_infos[-1]['price'] * TRADING_FEE_PERCENTAGE/100),2)
            # TODO : make it work for any currencies instead of USDT -> ... -> USDT
            sequence.percentage_return = calculate_percentage_return(initial_quantity, end_quantity)
            # print("Start currency", start_currency, "Quantity", initial_quantity)
            # print("End currency", end_currency, "Quantity", end_quantity)        
            # print("Instruments of sequence", sequence.instrument_names)
            # print("Order of trades of sequence", sequence.order_of_trades)
            # print("Percentage return", sequence.percentage_return)
            # print("Trades",sequence.trade_infos)
            # input()
            kept_sequences.append(sequence)

    return sorted(kept_sequences, key=lambda x: x.percentage_return, reverse=True)


def get_trading_sequences(ticker,start_currencies: list[str], end_currencies: list[str]) -> list[SingleTradeSequence]:
    # Get all usable instruments with spread > MIN_SPREAD_PERCENTAGE
    instrument_names = get_usable_instruments(
        ticker, MIN_SPREAD_PERCENTAGE)

    
    # Getting possible trading sequences with start currency start_currencies and end currencies end_currencies
    possible_trading_sequences = generate_possible_trading_sequences(
        instrument_names, start_currencies, end_currencies, MAX_DEPTH)

    # Getting readable instrument pairs for each sequence
    possible_instrument_pairs = generate_readable_instrument_pairs(
        possible_trading_sequences)

    # print("Creating trading sequences...")
    ts_l = create_trading_sequences(
        possible_instrument_pairs, instrument_names)
    ts_l.update_trade_sequences_tickers()
    # print("Final trade sequences possible", len(ts_l.trade_sequences))

    # ordered_sequences = ts_l.order_trade_sequences_by_return()
    return ts_l.get_trade_sequences()