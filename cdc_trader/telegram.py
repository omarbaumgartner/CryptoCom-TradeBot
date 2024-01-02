from telethon import events, TelegramClient
from env import TEL_API_ID, TEL_API_HASH, TEL_OWNER_USERNAME, commands_queue, TELEGRAM_MESSAGING_DISABLED,PAUSE_TRADER
import asyncio
from functions import *

client = TelegramClient('bot', TEL_API_ID, TEL_API_HASH)


async def initialize_telegram():
    await client.start()
    print("Launching Bot")
    await send_telegram_message("Bot started")


@client.on(events.NewMessage(from_users=[TEL_OWNER_USERNAME]))
async def handle_messages(event):
    # You can add more logic to handle different commands
    if 'help' in event.raw_text.lower():
        await event.reply("Available commands:\n"
                          "ping - check if bot is alive\n"
                          "account - show account summary\n"
                          "queue - show commands queue\n"
                          "clear queue - clear commands queue\n"
                          "cancel all - cancel all orders\n"
                          "stop - stop the bot")

    elif 'stop' in event.raw_text.lower():
        await event.reply("Shutting down")
        print("Shutting down")
        commands_queue.append('stop')

    elif 'pause' or 'unpause' in event.raw_text.lower():
        PAUSE_TRADER = not PAUSE_TRADER
        await event.reply(f"Trader paused")

        # await bot.disconnect()
    elif 'ping' in event.raw_text.lower():
        commands_queue.append('ping')
        await event.reply("pong")

    elif 'account' in event.raw_text.lower():
        account_summary = get_account_summary()
        await event.reply(f"Account Summary: {account_summary}")

    elif 'queue' in event.raw_text.lower():
        await event.reply(f"Queue: {commands_queue}")

    elif 'clear queue' in event.raw_text.lower():
        commands_queue.clear()
        await event.reply(f"Queue cleared")

    elif 'cancel all' in event.raw_text.lower():
        await event.reply("Canceling all orders")
        _, instrument_names, _ = get_instruments()
        for instrument_name in instrument_names:
            response = cancel_all_orders(instrument_name)
            if response['code'] == 0:
                await event.reply(f"Orders for {instrument_name} canceled")
            else:
                pass
                #await event.reply(f"Error canceling orders for {instrument_name}")


async def send_telegram_message(message):
    if not TELEGRAM_MESSAGING_DISABLED:
        await client.send_message(TEL_OWNER_USERNAME, message)
    return


async def main_telegram():
    await initialize_telegram()
    print("Waiting")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main_telegram())
