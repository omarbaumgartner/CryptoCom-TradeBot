import asyncio
from functions import *
from env import *
from telegram import send_telegram_message, initialize_telegram
from thinker import *
from classes import *
from calcul import *


# TODO : OPTIMIZE SPEED BASED ON REQUEST TYPE LIMITS
async def main():
    # Initialize user accounts
    user = UserAccounts()
    user.update_accounts()
    user.display_accounts()

    print("Starting trader...")
    # Initialize bot and authentication
    print("Initializing telegram...")
    await initialize_telegram()

    # Update accounts balances
    user.update_accounts()

    selected_sequence = None
    wait_for_order = False
    order_id = ""
    
    # Main loop, monitor market data and place orders
    while True:
        
        # Frequency monitoring depending on if we're waiting for an order to be filled
        if wait_for_order:
            sleep_time = 0.01
        else:
            sleep_time = 0.1

        # Consume commands sent by telegrams through a command queue
        if len(commands_queue) > 0:
            for command in commands_queue:
                if command == 'stop':
                    return

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
                print("Available currencies", available_currencies)
                
                print("Looking for top sequence...")

                sequences = get_trading_sequences(
                    ticker,
                    start_currencies=available_currencies,
                    end_currencies=END_CURRENCIES,
                )

                top_sequences = filter_and_order_by_return(
                    sequences, user.accounts, user.instruments_dict)
                top_sequence = None
                # Check if sequence is possible
                if len(top_sequences) != 0:
                    # We take the first sequence as it is the best one
                    # top_sequence = top_sequences[0]
                    print("########## TOP SEQUENCES ##########")
                    for sequence in top_sequences:
                        # sequence.display_infos()
                        if sequence.percentage_return >= MIN_PROFITS_PERCENTAGE:
                            sequence.display_infos()
                            print('Trades',sequence.trade_infos)
                            print("Percentage return",
                                  sequence.percentage_return)
                            top_sequence = sequence
                            break
  
                
                if top_sequence:
                    print("Top trade sequence with return of",
                          top_sequence.percentage_return)
                    selected_sequence = top_sequence
                    await send_telegram_message(
                        f"Top trade sequence with return of {top_sequence.percentage_return}")
                else:
                    print("No top sequence available")
            
            # Sequence already selected, jump to next order placement
            else:
                trade = selected_sequence.get_next_trade()
                if trade == None:
                    print("No more trades in sequence")
                    selected_sequence = None
                    order_id = ""

                print('Creating order with trade',selected_sequence.order_position, trade)
                await send_telegram_message(
                    f"Creating order with trade {selected_sequence.order_position} {trade}")
                
                # TODO : PYUSDT_USDT TOO STABLE TO TRADE WITH ADJUSTED PRICE, NEED TO ADJUST IT BASED ON MIN MAX OF LAST X TIME, OR USE AVERAGE, ORDER MIGHT NEVER BE FILLED
                response = create_order(**trade)
                
                # TODO : HANDLE ERROR UNOTHOZIED
                if(response['code'] == 10002):
                    print('Error creating order',response)
                    await send_telegram_message(
                        f"Error creating order {response}")
                    selected_sequence = None
                    order_id = ""
                else:    
                    print('Response',response)
                    order = response['result']
                    order_id = order['order_id']
                    wait_for_order = True

        else:
            order_details = get_order_detail(order_id)
            status = order_details['result']['order_info']['status']
            if status == 'ACTIVE':
                print("Waiting for order to be filled",order_details)
            elif status == 'FILLED': 
                print("Order filled")
                await send_telegram_message(
                    f"Order filled")
                wait_for_order = False

        # Sleep between iterations
        await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(main())
