
import time
import requests
import uuid
from cdc_trader.config.config_loader import REST_BASE, API_KEY
from cdc_trader.utils.api_signature_generator import generate_api_signature


def generate_unique_id():
    # Generate a UUID (Universally Unique Identifier)
    unique_id = str(uuid.uuid4())
    
    # Extract the first 36 characters to get a 36-character ID
    unique_id_36_chars = unique_id[:36]
    
    return unique_id_36_chars

def generate_nonce():
    return str(int(time.time() * 1000))


def generate_headers(params):
    signature = generate_api_signature(params)
    headers = {
        'Content-Type': 'application/json',
        'API-Signature': signature,
    }
    return headers


def get_instruments():
    # REST get instruments
    response = requests.get(REST_BASE + 'public/get-instruments')
    instruments = []
    instruments_names = []
    instruments_dict = {}
    for instrument in response.json()['result']['instruments']:
        instruments_dict[instrument['instrument_name']] = instrument
        instrument_formatted = {
            'instrument_name': instrument['instrument_name'],
            'base_currency': instrument['base_currency'],
            'quote_currency': instrument['quote_currency'],
            # Price
            'price_tick_size': instrument['price_tick_size'],
            'min_price': instrument['min_price'],
            'max_price': instrument['max_price'],
            'price_decimals': instrument['price_decimals'],
            # Quantity
            'quantity_tick_size': instrument['quantity_tick_size'],
            'min_quantity': instrument['min_quantity'],
            'max_quantity': instrument['max_quantity'],
            'quantity_decimals': instrument['quantity_decimals'],
            'last_update_date': instrument['last_update_date'],
        }

        instruments.append(instrument_formatted)
        instruments_names.append(instrument['instrument_name'])
    return instruments, instruments_names, instruments_dict


def get_orderbook(instrument_name, depth=10)->dict:
    '''Get orderbook for an instrument
    depth: Up to 50
    '''
    response = requests.get(REST_BASE + 'public/get-book',
                            params={'instrument_name': instrument_name, 'depth': depth})
    
    response.raise_for_status()  # raises exception when not a 2xx response
    if response.status_code == 200:
        try:
            return response.json()['result']
        except Exception as e:
                print(e)
                return None
         
    else:    
        return None


def get_candlesticks(instrument_name, interval)->dict:
    """
    Retrieves candlestick data for a specified instrument and interval.

    Args:
        instrument_name (str): Name of the trading instrument.
        interval (str): Time interval for the candlesticks.
                        period can be:
                        1m : one minute
                        5m : five minutes
                        15m : 15 minutes
                        30m: 30 minutes
                        1h : one hour
                        4h : 4 hours
                        6h : 6 hours
                        12h : 12 hours
                        1D : one day
                        7D : one week
                        14D : two weeks
                        1M : one month
    Returns:
        dict: Candlestick data for the specified instrument and interval.
    """
    response = requests.get(REST_BASE + 'public/get-candlestick',
                            params={'instrument_name': instrument_name, 'interval': interval})

    return response.json()['result']


# 24h
def get_ticker(instrument_name=None)->dict:
    if instrument_name is None:
        params = {}
    else:
        params = {'instrument_name': instrument_name}

    response = requests.get(REST_BASE + 'public/get-ticker',
                            params=params)
    return response.json()['result']['data']


def get_account_summary(currency=None)->dict:
    endpoint = 'private/get-account-summary'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 11,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {"currency": currency} if currency else {},
        "nonce": nonce
    }

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()['result']['accounts']


def create_order(instrument_name, side, type='LIMIT', price=None, quantity=None, notional=None,
                  time_in_force='GOOD_TILL_CANCEL', exec_inst='', trigger_price=None,**kwargs)->dict:
    """
    Creates a new order on the Exchange.

    :param instrument_name: The trading pair symbol, e.g., ETH_CRO, BTC_USDT.
    :param side: The order side, options are: BUY, SELL.
    :param type: The order type, options are: LIMIT, MARKET, STOP, STOP_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER.
    :param price: For LIMIT and STOP_LIMIT orders only: Unit price.
    :param quantity: For LIMIT Orders, MARKET, STOP_LOSS, TAKE_PROFIT orders only: Order Quantity to be Sold.
    :param notional: For MARKET (BUY), STOP_LOSS (BUY), TAKE_PROFIT (BUY) orders only: Amount to spend.
    :param client_oid: Optional Client Order ID (Maximum 36 characters). If not provided, it will be the nonce in the request.
    :param time_in_force: (Limit Orders Only) Options are: GOOD_TILL_CANCEL (Default if unspecified), FILL_OR_KILL, IMMEDIATE_OR_CANCEL.
    :param exec_inst: (Limit Orders Only) Options are: POST_ONLY or leave empty.
    :param trigger_price: Used with STOP_LOSS, STOP_LIMIT, TAKE_PROFIT, and TAKE_PROFIT_LIMIT orders. Dictates when the order will be triggered.

    :return: A JSON object containing information about the created order.
    """

    endpoint = 'private/create-order'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 11,
        "method": endpoint,
        "api_key": API_KEY, 
        "params": {
            "client_oid" : generate_unique_id(), #generate a unique id of 36 characters
            "instrument_name": instrument_name,
            "side": side.upper(),
            "type": type,
            "price": price,
            "quantity": quantity,
            "exec_inst": exec_inst,
        },
        "nonce": nonce
    }
    
    # TODO : add based on order type condition
    if trigger_price:
        params['params']['trigger_price'] = trigger_price
    
    if notional:
        params['params']['notional'] = notional 

    if time_in_force:
        params['params']['time_in_force'] = time_in_force

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()


def get_open_orders(instrument_name=None, page_size=20, page=0):
    """
    Retrieves all open orders for a particular instrument or all instruments.

    :param instrument_name: The trading pair symbol, e.g., ETH_CRO, BTC_USDT. Omit for "all".
    :param page_size: Page size (Default: 20, max: 200).
    :param page: Page number (0-based).

    :return: A JSON object containing information about open orders.
    """

    endpoint = 'private/get-open-orders'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 12,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "instrument_name": instrument_name,
            "page_size": page_size,
            "page": page
        },
        "nonce": nonce
    }

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
      
    return response.json()['result']


def get_order_detail(order_id:str):
    """
    Retrieves details for a particular order based on its order ID.

    :param order_id: The unique identifier of the order.

    :return: A JSON object containing details about the specified order.
    """

    endpoint = 'private/get-order-detail'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 12,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "order_id": order_id
        },
        "nonce": nonce
    }

    headers = generate_headers(params)

    response = requests.post(url, json=params, headers=headers)
    return response.json()


def cancel_order(instrument_name, order_id):
    """
    Cancels an existing order on the Exchange.

    :param instrument_name: The trading pair symbol, e.g., ETH_CRO, BTC_USDT.
    :param order_id: The unique identifier of the order to be canceled.

    :return: A JSON object confirming the request to cancel the order.
    """

    endpoint = 'private/cancel-order'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 11,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "instrument_name": instrument_name,
            "order_id": order_id
        },
        "nonce": nonce
    }

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()


def generate_order_params(instrument_name, side, order_type, price, quantity,
                          client_oid=None, time_in_force=None, exec_inst=None):
    """
    Generates a dictionary with order parameters.

    :param instrument_name: The trading pair symbol, e.g., ETH_CRO, BTC_USDT.
    :param side: BUY or SELL.
    :param order_type: LIMIT, MARKET, STOP_LOSS, STOP_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER.
    :param price: Unit price (For LIMIT and STOP_LIMIT orders only).
    :param quantity: Order Quantity to be Sold (For LIMIT Orders, MARKET, STOP_LOSS, TAKE_PROFIT orders only).
    :param client_oid: Optional Client order ID (Maximum 36 characters).
    :param time_in_force: (Limit Orders Only) Options are: GOOD_TILL_CANCEL, FILL_OR_KILL, IMMEDIATE_OR_CANCEL.
    :param exec_inst: (Limit Orders Only) Options are: POST_ONLY or leave empty.

    :return: A dictionary with order parameters.
    """
    order_params = {
        "instrument_name": instrument_name,
        "side": side,
        "type": order_type,
        "price": price,
        "quantity": quantity,
        "client_oid": client_oid,
        "time_in_force": time_in_force,
        "exec_inst": exec_inst
    }
    return order_params


def create_order_list(order_list):
    """
    Creates a list of orders on the Exchange.

    :param order_list: A list containing order details. Each order is a dictionary with required parameters.

    :return: A JSON object confirming the request to create the order list.
    """

    endpoint = 'private/create-order-list'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 12,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "contingency_type": "LIST",
            "order_list": order_list
        },
        "nonce": nonce
    }

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()


def cancel_order_list(order_list):
    """
    Cancels a list of orders on the Exchange.

    :param order_list: A list containing order details. Each order is a dictionary with required parameters.

    :return: A JSON object confirming the request to cancel the order list.
    """

    endpoint = 'private/cancel-order-list'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 13,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "order_list": order_list
        },
        "nonce": nonce
    }

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()


def cancel_all_orders(instrument_name):
    """
    Cancels all orders for a particular instrument/pair on the Exchange.

    :param instrument_name: The instrument name, e.g., ETH_CRO, BTC_USDT.

    :return: A JSON object confirming the request to cancel all orders for the specified instrument.
    """

    endpoint = 'private/cancel-all-orders'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 12,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "instrument_name": instrument_name
        },
        "nonce": nonce
    }

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()


def get_trades(instrument_name=None, page_size=20, page=0, start_ts=None, end_ts=None):
    """
    Gets all executed trades for a particular instrument.

    :param instrument_name: The instrument name, e.g., ETH_CRO, BTC_USDT. Omit for 'all'
    :param page_size: Page size (Default: 20, max: 200)
    :param page: Page number (0-based)
    :param start_ts: Start timestamp (milliseconds since the Unix epoch) - defaults to 24 hours ago
    :param end_ts: End timestamp (milliseconds since the Unix epoch) - defaults to 'now'

    :return: A JSON object containing executed trades for the specified instrument.
    """

    endpoint = 'private/get-trades'
    url = REST_BASE + endpoint

    nonce = generate_nonce()
    params = {
        "id": 11,
        "method": endpoint,
        "api_key": API_KEY,
        "params": {
            "page_size": page_size,
            "page": page,
            "start_ts": start_ts,
            "end_ts": end_ts
        },
        "nonce": nonce
    }

    if instrument_name:
        params['params']['instrument_name'] = instrument_name

    headers = generate_headers(params)
    response = requests.post(url, json=params, headers=headers)
    return response.json()


def cancel_all_open_orders():
    open_orders = get_open_orders()
    for order in open_orders['order_list']:
        cancel_order(order['instrument_name'],order['order_id'])
        print(f"Canceling order {order['order_id']} with instrument {order['instrument_name']}")
