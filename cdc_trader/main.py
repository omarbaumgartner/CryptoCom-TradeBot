import signal
import multiprocessing
import asyncio
from telegram import main_telegram
from draft.cdc import main_trade

async def run_main_telegram():
    try:
        print("telegram")
        await main_telegram()
    except Exception as e:
        print(f"Error in run_main_telegram: {e}")

async def run_main_trade():
    try:
        print('trade')
        await main_trade()
    except Exception as e:
        print(f"Error in run_main_trade: {e}")

def wrapper_main_telegram():
    asyncio.run(run_main_telegram())

def wrapper_main_trade():
    asyncio.run(run_main_trade())

def main():
    #process_telegram = multiprocessing.Process(target=wrapper_main_telegram)
    process_trade = multiprocessing.Process(target=wrapper_main_trade)

    try:
        #process_telegram.start()
        process_trade.start()

        #process_telegram.join()
        process_trade.join()
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Stopping...")

def signal_handler(sig, frame):
    print("Ctrl+C pressed. Stopping...")
    exit()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    try:
        main()
    except KeyboardInterrupt:
        pass
