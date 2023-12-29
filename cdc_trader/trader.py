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
    
    # Main loop, monitor market data and place orders
    while True:
        
        # High frequency monitoring when waiting for order
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
                available_currencies = user.get_available_currencies()
                print("Available currencies", available_currencies)
                print("Looking for top sequence...")

                sequences = get_trading_sequences(
                    start_currencies=available_currencies,
                    end_currencies=END_CURRENCIES,
                )

                top_sequences = filter_and_order_by_return(
                    sequences, user.accounts, user.instruments_dict)
                
                # Check if sequence is possible
                if len(top_sequences) != 0:
                    # We take the first sequence as it is the best one
                    # top_sequence = top_sequences[0]
                    for sequence in top_sequences:
                        # sequence.display_infos()
                        if sequence.percentage_return >= MIN_PROFITS_PERCENTAGE:
                            sequence.display_infos()
                            print("Percentage return",
                                  sequence.percentage_return)
                            print("Profit percentage per trade", (MIN_PROFITS_PERCENTAGE ** (
                                1/len(sequence.order_of_trades)) + TRADING_FEE_PERCENTAGE))
                            print("Checks", sequence.checks)
                            print("Available quantities",
                                  sequence.available_quantities)
                            print("Percentage return",
                                  sequence.percentage_return)
                            input()
                            top_sequence = sequence
                            break
                else:
                    top_sequence = None
                
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
                print("Top sequence already selected, jumping to order placement")
                trade = selected_sequence.get_next_trade()
                print("Trade",selected_sequence.order_position, trade)
                input()
                #wait_for_order = True

        else:
            print("Waiting for order to be filled")

        # Sleep between iterations
        await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(main())
