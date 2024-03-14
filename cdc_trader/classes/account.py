from cdc_trader.api.cdc_api import *
from cdc_trader.config.config_loader import *

class UserAccounts:
    def __init__(self):
        """
        Initialize UserAccounts object.
        
        Initializes an empty dictionary to store user accounts and retrieves the instruments dictionary.
        """
        self.accounts = {}
        _, _, self.instruments_dict = get_instruments()

    def add_account(self, raw_account):
        """
        Add account to UserAccounts.

        Parameters:
        - raw_account (dict): Raw account data containing balance, available, stake, and order information.

        Returns:
        - None

        """
        self.accounts[raw_account['currency']] = {
            "balance": raw_account['balance'],
            "available": raw_account['available'],
            "stake": raw_account['stake'],
            "order": raw_account['order'],
        }

    def get_available_currencies(self, ticker_dict, min_value_in_usdt=0):
        """
        Get currencies with available balance > 0.

        Parameters:
        - ticker_dict (dict): Dictionary containing ticker information.
        - min_value_in_usdt (float): Minimum value in USDT required for currency to be considered.

        Returns:
        - available_currencies (list): List of currencies with available balance > min_value_in_usdt.
        """
        available_currencies = []
        for currency in self.accounts:
            if 'staked' in currency.lower():
                continue
            if currency != 'USDT' and currency != 'USD':
                equivalent_usdt = float(self.accounts[currency]['available']) * float(ticker_dict[currency+'_USDT']['a'])
            else:
                equivalent_usdt = float(self.accounts[currency]['available'])

            if equivalent_usdt > min_value_in_usdt:
                available_currencies.append(currency)
        
        return available_currencies

    def update_accounts(self):
        """
        Update user accounts.

        Fetches raw account data and updates the UserAccounts object with the latest account information.

        Returns:
        - None
        """
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
        """
        Display accounts summary.

        Prints a summary of the user accounts including currency and corresponding balance, available, stake, and order.

        Returns:
        - None
        """
        print(f"########## ACCOUNTS SUMMARY ##########", flush=True)
        for currency in self.accounts:
            print(currency, self.accounts[currency], flush=True)
        print(f"######################################", flush=True)
