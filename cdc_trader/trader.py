import asyncio
from functions import *
from env import commands_queue
from telegram import send_telegram_message, initialize_telegram

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
        # await send_telegram_message(f"Initial Account Summary: {account_summary}")
        # asyncio.run(main_telegram())

        # send_telegram_message(f"Initial Account Summary: {account_summary}")
        # await send_telegram_message(f"Initial Account Summary: {account_summary}")
        # Start the Telegram thread
        # await main_telegram()
        # Main trading loop
        while True:

            # Consume commands from the queue
            if len(commands_queue) > 0:
                for command in commands_queue:
                    if command == 'stop':
                        return

            # Monitor market data (tickers, candlesticks)
            tickers = get_ticker()
            # print('Tick', commands_queue)
            # await send_telegram_message(f"Tick")

            # print(tickers)
            # send_telegram_message(f"Tickers: {tickers}")

            # Implement trading decision logic

            # Risk management

            # Place orders if conditions are met
            # Example: create_order("BTC_USDT", "BUY", "LIMIT", price=50000, quantity=0.001)

            # Monitor order execution

            # Telegram notifications (if needed)
            # send_telegram_message("Order placed successfully")

            # Sleep between iterations
            await asyncio.sleep(1)

    except Exception as e:
        # send_telegram_message(f"Error: {e}")
        pass


if __name__ == "__main__":
    asyncio.run(main())
