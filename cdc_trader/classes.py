from functions import *
from env import *

class UserAccounts:
    def __init__(self):
        self.accounts = {}
        _, _, self.instruments_dict = get_instruments()

    def add_account(self, raw_account):
        self.accounts[raw_account['currency']] = {
            "balance": raw_account['balance'],
            "available": raw_account['available'],
            "stake": raw_account['stake'],
            "order": raw_account['order'],
        }

    # Get currencies with available balance > 0, still need if instrument min_quantity < available balance so that we can place order
    def get_available_currencies(self,ticker_dict,min_value_in_usdt=0):
        available_currencies = []
        for currency in self.accounts:
            if currency != 'USDT' and currency != 'USD' and 'staked' not in currency :
                equivalent_usdt = float(self.accounts[currency]['available']) * float(ticker_dict[currency+'_USDT']['b'])
            else:
                equivalent_usdt = float(self.accounts[currency]['available'])

            if equivalent_usdt > min_value_in_usdt:
                available_currencies.append(currency)
        
        return available_currencies


    def update_accounts(self):
        raw_accounts = get_account_summary()
        self.accounts = {}
        for raw_account in raw_accounts:
            if RICH_MODE:
                # For testing purposes, we set available balance to 1000 USDT
                if raw_account['currency'] == 'USDT':
                    raw_account['available'] = 1000
                    self.add_account(raw_account)
            self.add_account(raw_account)

    def display_accounts(self):
        print(f"########## ACCOUNTS SUMMARY ##########")
        for currency in self.accounts:
            print(currency, self.accounts[currency])
        print(f"######################################")


class OrdersManager:
    def __init__(self):
        self.orders = {}


class SingleTradeSequence:
    def __init__(self):
        self.instrument_names = []
        self.order_of_trades = []
        self.percentage_spreads = []
        self.percentage_return = 0

        # Contain sides
        self.checks = []
        # Contain quantities
        self.available_quantities = []
        # Contain 
        self.tickers = []
        self.trade_infos = []
        self.orders_ids = []
        self.order_position = 0
        self.order_status = None

    def add_instrument_name(self, instrument_name):
        # print("Adding instrument name", instrument_name)
        self.instrument_names.append(instrument_name)
        self.tickers.append({})

    def add_trade_infos(self, trade):
        self.trade_infos.append(trade)
        
    def get_next_trade(self):
        if self.order_position < len(self.trade_infos):
            trade_to_return = self.trade_infos[self.order_position]
            self.order_position += 1
            return trade_to_return
        else:
            return None

    def get_instruments_names(self):
        return self.instrument_names

    def calculate_compound_return(self, returns):
        compound_return = 1
        for r in returns:
            compound_return *= 1 + (r / 100)  # Convert percentage to decimal
        return (compound_return - 1)*100

    def update_tickers(self, ticker):
        for i in range(len(self.instrument_names)):
            self.tickers[i] = ticker[self.instrument_names[i]]
            self.tickers[i]['a'] = float(self.tickers[i]['a'])
            self.tickers[i]['b'] = float(self.tickers[i]['b'])
            self.percentage_spreads.append(
                100*((self.tickers[i]['a'] - self.tickers[i]['b']) / self.tickers[i]['b']))


    def display_tickers(self):
        print("Instrument name Ticker Order of trades")
        for i in range(len(self.instrument_names)):
            print(
                f"{self.order_of_trades[i]} {self.percentage_spreads[i]}%")

    def display_infos(self,show_tickers=False):
        print("########## TRADE SEQUENCE ##########")
        print("Instrument names", self.instrument_names)
        print("Order of trades", self.order_of_trades)
        # print("Percentage spreads", self.percentage_spreads)
        # print("Compound return", self.compound_return)
        print("Side", self.checks)
        print("Orders ids", self.orders_ids)
        if show_tickers:
            print("Tickers", self.tickers)
        print("#####################################")



class TradeSequences:
    def __init__(self):
        self.trade_sequences = []

    def add_trade_sequence(self, trade_sequence):
        self.trade_sequences.append(trade_sequence)

    def get_trade_sequences(self) -> list[SingleTradeSequence]:
        return self.trade_sequences

    # Update ticker of each instrument in each trade sequence contained in self.trade_sequences
    def update_trade_sequences_tickers(self):
        ticker_all = get_ticker()
        instruments = []
        for ts in self.get_trade_sequences():
            ts_instruments = ts.get_instruments_names()
            instruments += ts_instruments
            # remove duplicates
            instruments = list(set(instruments))

        # keep in ticker only the instruments that are in instruments
        ticker = {}
        for tick in ticker_all:
            if tick['i'] in instruments:
                ticker[tick['i']] = tick
        # update tickers
        for ts in self.get_trade_sequences():
            ts.update_tickers(ticker)

    # def order_trade_sequences_by_return(self) -> SingleTradeSequence:
    #     self.update_trade_sequences_tickers()
    #     if len(self.trade_sequences) == 0:
    #         return []
    #     else:
    #         return sorted(self.trade_sequences, key=lambda x: x.compound_return, reverse=True)
