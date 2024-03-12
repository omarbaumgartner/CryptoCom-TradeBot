import asyncio
from pathlib import Path
import sys
import os
# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Get the absolute path of the grandparent directory
grandparent_dir = os.path.abspath(os.path.join(parent_dir, '..'))
# Append the grandparent directory to sys.path
sys.path.append(grandparent_dir)
from cdc_trader.config.config_loader import *
from cdc_trader.api.cdc_api import *
from cdc_trader.telegram.telegram_bot import initialize_telegram
from cdc_trader.utils.trading_sequence_generator import *
from cdc_trader.classes.trade import *
from cdc_trader.classes.account import *
from cdc_trader.utils.calculation_helpers import *
from cdc_trader.utils.trading_logger import log_message

# TODO : OPTIMIZE SPEED BASED ON REQUEST TYPE LIMITS
async def main():
    global PAUSE_TRADER
    trade = None
    timer = None
    # Create log file and directory if not existing
    Path(LOG_FILEPATH).parent.mkdir(parents=True, exist_ok=True)
    Path(LOG_FILEPATH).touch()

    with open(LOG_FILEPATH, 'a') as file:

        # Initialize bot and authentication
        await log_message(file,
                            f"Initializing telegram...",send_telegram=False)
        await initialize_telegram()


        # Cancel all open orders
        cancel_all_open_orders()
        await log_message(file,f"All open orders are cancelled")

        # Initialize user accounts
        user = UserAccounts()
        user.update_accounts()
        user.display_accounts()

        await log_message(file,"Starting trader...")

        selected_sequence = None
        wait_for_order = False
        order_id = ""

        # Main loop, monitor market data and place orders
        while True:
            # Consume commands sent by telegrams through a command queue
            if len(commands_queue) > 0:
                for command in commands_queue:
                    if command == 'stop':
                        # stop all async tasks
                        asyncio.get_event_loop().stop()
                    elif command == 'pause':
                        PAUSE_TRADER = True

                    elif command == 'resume':
                        PAUSE_TRADER = False
                        await log_message(file,f"Trader resumed")
                    
                    commands_queue.remove(command)

                
            if PAUSE_TRADER:
                await log_message(file,f"Trader paused with interval of {SLEEP_INTERVAL} seconds")
                await asyncio.sleep(SLEEP_INTERVAL)
                continue

            # Frequency monitoring depending on if we're waiting for an order to be filled
            if wait_for_order:
                sleep_time = 0.01
            else:
                sleep_time = 0.1

            # We're not waiting for an order to be filled, we can look for new trading sequences
            if not wait_for_order:
                
                # We look for best trading sequence
                if not selected_sequence:
                    # We get the available currencies we can trade
                    # TODO : Remove too low balance from available currencies
                    
                    ticker = get_ticker()
                    # to dict
                    ticker_dict = {t['i']: t for t in ticker}
                    available_currencies = user.get_available_currencies(ticker_dict, min_value_in_usdt=MIN_VALUE_IN_CURRENCY)
                    available_currencies.remove('USDT')

                    sequences = get_trading_sequences(
                        ticker,
                        start_currencies=available_currencies,
                        end_currencies=END_CURRENCIES,
                    )

                    # Filter and order sequences by return
                    top_sequences = filter_and_order_by_profit(
                        sequences, user.accounts, user.instruments_dict)
                    
                    # for sequence in top_sequences:
                    #     sequence.display_infos()
                    #     input("Press Enter to continue...")

                    # Check if sequence is possible
                    if len(top_sequences) != 0:
                        # We take the first sequence as it is the best one
                        # top_sequence = top_sequences[0]
                        for sequence in top_sequences:
                            sequence.display_infos()
                            #print(f"Sequence found with return of{sequence.percentage_return}")
                            if sequence.percentage_return >= MIN_PROFITS_PERCENTAGE:                                
                                top_sequence = sequence
                                break
         
                    if top_sequence:
                        top_sequence.display_infos()
                        selected_sequence = top_sequence                        
                        trade = selected_sequence.get_next_trade()
                        trade['id'] = selected_sequence.order_position-1
                        await log_message(file,
                            f"Beginning trade sequence with return of : {top_sequence.percentage_return}%")
                    else:
                        # if 3 second has passed, we print
                        if timer == None:
                            timer = time.time()
                        
                        if time.time() - timer > 3:
                            timer = time.time()
                            print("No top sequence available")
                
                # Sequence already selected, jump to next order placement
                else:

                    if trade == None:
                        await log_message(file,"No more trades in sequence, looking for new sequence")
                        selected_sequence = None
                        order_id = ""
                        wait_for_order = False
                    else:
                        
                        # update available balances
                        user.update_accounts()
                        trade['quantity'] = floor_with_decimals(trade['quantity'], trade['min_quantity_decimals'])
                        if trade['side'] == 'BUY':
                            trade['price'] = floor_with_decimals(trade['price'], trade['price_decimals'])
                        else:
                            trade['price'] = ceil_with_decimals(trade['price'], trade['price_decimals'])

                        print(f"Trade {trade}")

                        # TODO : PYUSDT_USDT TOO STABLE TO TRADE WITH ADJUSTED PRICE, NEED TO ADJUST IT BASED ON MIN MAX OF LAST X TIME, OR USE AVERAGE, ORDER MIGHT NEVER BE FILLED
                        response = create_order(**trade)

                        # TODO : HANDLE ERROR UNOTHOZIED
                        if(response['code'] == 10002):
                            await log_message(file,f"Error creating order {response}")
                            selected_sequence = None
                            order_id = ""
                        elif response['code'] == 20002:
                            await log_message(file,f"Order rejected {response}")
                            selected_sequence = None
                            order_id = ""
                        elif response['code'] == 30014:
                            await log_message(file,f"INVALID_QUANTITY_PRECISION {response}")
                            selected_sequence = None
                            order_id = ""
                        else:    
                            await log_message(file,f"Order created with trade order {selected_sequence.order_position}, {trade}")
                            order = response['result']
                            order_id = order['order_id']
                            wait_for_order = True
                            trade = selected_sequence.get_next_trade()

            
            # Waiting for order
            else:
                order_details = get_order_detail(order_id)
                try:
                    status = order_details['result']['order_info']['status']
                except:
                    print("ERROR",order_details)            
                
                order_infos = {
                    'order_id':order_id,
                    'status':status,
                    'instrument_name':order_details['result']['order_info']['instrument_name'],
                    'price':order_details['result']['order_info']['price'],
                    'quantity':order_details['result']['order_info']['quantity'],
                    'side':order_details['result']['order_info']['side'],
                    'type':order_details['result']['order_info']['type'],
                    'time_in_force':order_details['result']['order_info']['time_in_force'],
                }
                if status == 'ACTIVE':
                    # if 3 second has passed, we print
                    if timer == None:
                        timer = time.time()
                    
                    if time.time() - timer > 3:
                        timer = time.time()
                        print(f"Waiting for order {order_id} {order_infos['instrument_name']} {order_infos['side']} {order_infos['quantity']} @ {order_infos['price']} | {order_infos['type']} | {order_infos['time_in_force']}")
                
                elif status == 'FILLED': 
                    await log_message(file,f"Order {order_id} filled")
                    wait_for_order = False
                elif status == 'CANCELED':
                    await log_message(file,f"Order {order_id} canceled")
                    wait_for_order = False
                    
            # Sleep between iterations
            await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(main())
