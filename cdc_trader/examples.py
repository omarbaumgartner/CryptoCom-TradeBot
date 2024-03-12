from trading_api_client import *

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


# Example to create a LIMIT order
order_params = {
    "instrument_name": "IOTX_USD",
    "side": "SELL",
    "type": "LIMIT",
    "price": 0.5,
    "quantity": 10,
    "client_oid": "my_order_0002",
    "time_in_force": "GOOD_TILL_CANCEL",
    "exec_inst": "POST_ONLY",
}

trade = {
    "instrument_name": "BTC_USDT",
    "side": "buy",
    "type": "LIMIT",
    "price": 46628.28,
    "quantity": 0.0001,
    "time_in_force": "GOOD_TILL_CANCEL",
    "exec_inst": "POST_ONLY",
}

print(get_ticker('CRO_USDT'))
exit()

trade = {'instrument_name': 'BTC_USDT', 
          'side': 'BUY', 
          'price': 51593.79, 
          'quantity': 0.0001}

trade = {'instrument_name': 'CRO_BTC', 'side': 'sell', 'price': 1.7439e-06, 'quantity': 48.6, 'min_quantity': 1.0, 'price_decimals': 10}
trade = {'instrument_name': 'CRO_BTC', 'side': 'sell', 'price': 0.0000017439, 'quantity': 48.6, 'min_quantity': 1.0, 'price_decimals': 10}
trade = {'instrument_name': 'ETH_CRO', 'side': 'buy', 'price': 30823.0, 'quantity': 0.0015, 'min_quantity_decimals': 4, 'price_decimals': 0}
trade =  {'instrument_name': 'ETH_CRO', 'side': 'BUY', 'price': 30754, 'quantity': 0.0001}
trade = {'instrument_name': 'MANA_BTC', 'side': 'buy', 'price': 0.000008900, 'quantity': 8.8}
created_order = create_order(**trade)
print('Order:', created_order)
trade = {'instrument_name': 'MANA_BTC', 'side': 'buy', 'price': 0.0000089, 'quantity': 8}
created_order = create_order(**trade)
print('Order:', created_order)
exit()

# if created_order['code'] == 10004:
#     print(f"ERROR {created_order['detail_message']}")
# else:
#     print(f"Created Order: {created_order}")

# Example to create a STOP_LIMIT order
stop_limit_params = {
    "instrument_name": "BTC_USDT",
    "side": "BUY",
    "type": "STOP_LIMIT",
    "quantity": 1,
    "trigger_price": 9000,
    "price": 9100,
    "client_oid": "my_stop_limit_order_0015",
    "time_in_force": "GOOD_TILL_CANCEL",
}
# created_stop_limit_order = create_order(**stop_limit_params)
# print('Created Stop-Limit Order:', created_stop_limit_order)


# while True:
#     response = get_ticker('BTC_USDT')

#     print('ticker', response)
#     time.sleep(1)


# Example to create a list of orders
order_list_to_create = [
    {
        "instrument_name": "IOTX_USD",
        "side": "SELL",
        "type": "LIMIT",
        "price": 0.5,
        "quantity": 10,
        "client_oid": "my_order_0002",
        "time_in_force": "GOOD_TILL_CANCEL",
        "exec_inst": "POST_ONLY",
    },
    {
        "instrument_name": "IOTX_USD",
        "side": "SELL",
        "type": "LIMIT",
        "price": 0.45,
        "quantity": 10,
        "client_oid": "my_order_0003",
        "time_in_force": "GOOD_TILL_CANCEL",
        "exec_inst": "POST_ONLY",
    },
]


# created_order_list = create_order_list(order_list_to_create)
# exit()

# Example to get open orders for a specific instrument
# instrument_to_check = 'ETH_CRO'
# open_orders_data = get_open_orders(instrument_name=instrument_to_check)
# print(f'Open Orders for {instrument_to_check}:', open_orders_data)

# # Example to get open orders for all instruments
all_open_orders_data = get_open_orders()
print("All Open Orders:")

# Example to cancel a list of orders
# order_list_to_cancel = []
# for order in all_open_orders_data['order_list']:
#     print(get_order_detail(order['order_id']))
#     order_list_to_cancel.append(
#         {"order_id": order['order_id'], "instrument_name": order['instrument_name']})
#     print('------------------------')

# print("Cancelling Orders...")
# canceled_order_list = cancel_order_list(order_list_to_cancel)
# if canceled_order_list['code'] == 0:
#     print(f"Orders cancelled successfully for {order_list_to_cancel}")

#     response = cancel_order(order['instrument_name'], order['order_id'])
#     if response['code'] == 0:
#         print(f"Order {order['order_id']} cancelled")

#     print(response)
#     time.sleep(1)
