import asyncio
from functions import *
from env import commands_queue, TRADING_FEE_PERCENTAGE, DESIRED_PROFIT_PERCENTAGE, MIN_SPREAD_PERCENTAGE, START_CURRENCIES, END_CURRENCIES, MAX_DEPTH
from telegram import send_telegram_message, initialize_telegram
from thinker import *
# Add other necessary imports and functions here

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
# Add other necessary imports and functions here
# trading method : crypto-to-crypto arbitrage


async def main():
    try:
        # Initialize bot and authentication
        await initialize_telegram()

        # Get initial account summary
        account_summary = get_account_summary()

        # Main trading loop
        while True:
            # Consume commands from the queue
            if len(commands_queue) > 0:
                for command in commands_queue:
                    if command == 'stop':
                        return

            # Monitor market data (tickers, candlesticks)
            ticker = get_ticker()

            # print("Getting sorted usable instruments...")
            instrument_names = get_usable_instruments(
                ticker, MIN_SPREAD_PERCENTAGE)

            # print(f"Getting possible trading sequences with start currency {START_CURRENCIES} and end currencies {END_CURRENCIES} and max depth of {MAX_DEPTH} ...")
            possible_trading_sequences = generate_possible_trading_sequences(
                instrument_names, START_CURRENCIES, END_CURRENCIES, MAX_DEPTH)
            # print("Generating readable instrument pairs for each sequence")
            possible_instrument_pairs = generate_readable_instrument_pairs(
                possible_trading_sequences)

            # print("Creating trading sequences...")
            ts_l = create_trading_sequences(
                possible_instrument_pairs, instrument_names)

            # print("Final trade sequences possible", len(ts_l.trade_sequences))

            top_sequence = ts_l.get_top_trade_sequence()
            if top_sequence:
                print("Top trade sequence with return of", top_sequence.compound_return)
                # TODO : take into account trading fee in compound calculator
                await send_telegram_message(
                    f"Top trade sequence with return of {top_sequence.compound_return}")
            else:
                print("No top sequence")

            # Place orders if conditions are met
            # Example: create_order("BTC_USDT", "BUY", "LIMIT", price=50000, quantity=0.001)

            # Monitor order execution

            # Telegram notifications (if needed)
            # send_telegram_message("Order placed successfully")

            # Sleep between iterations
            await asyncio.sleep(0.5)

    except Exception as e:
        # send_telegram_message(f"Error: {e}")
        pass


if __name__ == "__main__":
    asyncio.run(main())
