import asyncio
from trading_api_client import *
from trading_config_loader import *
from telegram_notifier import send_telegram_message, initialize_telegram
from trading_sequence_generator import *
from trading_classes import *
from financial_calculations import *
from pathlib import Path


async def log_message(file,message,type='log'):
    print(message)
    log_message = {
        "nonce": generate_nonce(),
        "type": type,
        "message": message
    }
    await send_telegram_message(message)
    file.write(str(log_message) + '\n')


# TODO : OPTIMIZE SPEED BASED ON REQUEST TYPE LIMITS
async def main():
    global PAUSE_TRADER
    with open(LOG_FILEPATH, 'a') as file:

        # Initialize bot and authentication
        print("Initializing telegram...")
        await initialize_telegram()

        # Create log file and directory if not existing
        Path(LOG_FILEPATH).parent.mkdir(parents=True, exist_ok=True)
        Path(LOG_FILEPATH).touch()

        open_orders = get_open_orders()
        for order in open_orders['order_list']:
            cancel_order(order['instrument_name'],order['order_id'])
            await log_message(file,f"Canceling order {order['order_id']} with instrument {order['instrument_name']}")
        
        # Initialize user accounts
        user = UserAccounts()
        user.update_accounts()
        user.display_accounts()



        #await log_message(file,"Starting trader...")

        # Update accounts balances
        user.update_accounts()

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
                    user.display_accounts()


                    sequences = get_trading_sequences(
                        ticker,
                        start_currencies=available_currencies,
                        end_currencies=END_CURRENCIES,
                    )

                    # Filter and order sequences by return
                    top_sequences = filter_and_order_by_return(
                        sequences, user.accounts, user.instruments_dict)
                    top_sequence = None

                    # Check if sequence is possible
                    if len(top_sequences) != 0:
                        # We take the first sequence as it is the best one
                        # top_sequence = top_sequences[0]
                        for sequence in top_sequences:
                            # 
                            #print(f"Sequence found with return of{sequence.percentage_return}")
                            if sequence.percentage_return >= MIN_PROFITS_PERCENTAGE:                                
                                sequence.display_infos()
                                top_sequence = sequence
                                break
                            
                    if top_sequence:
                        top_sequence.display_infos()
                        selected_sequence = top_sequence
                        await log_message(file,
                            f"Beginning trade sequence with return of : {top_sequence.percentage_return}%")
                        print(top_sequence.trade_infos)
                    else:
                        print("No top sequence available")
                
                # Sequence already selected, jump to next order placement
                else:
                    trade = selected_sequence.get_next_trade()

                    if trade == None:
                        await log_message(file,"No more trades in sequence, looking for new sequence")
                        selected_sequence = None
                        order_id = ""
                    else:
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
                        else:    
                            print('Response',response)
                            await log_message(file,f"Order created with trade order {selected_sequence.order_position}, {trade}")
                            order = response['result']
                            order_id = order['order_id']
                            wait_for_order = True

            
            # Waiting for order
            else:
                order_details = get_order_detail(order_id)
                status = order_details['result']['order_info']['status']
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
                    print(f"Waiting for order {order_id}",order_infos)
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
