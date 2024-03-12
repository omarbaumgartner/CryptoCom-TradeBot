from telethon import events, TelegramClient
from cdc_trader.config.config_loader import TEL_API_ID, TEL_API_HASH, TEL_OWNER_USERNAME, commands_queue, TELEGRAM_MESSAGING_DISABLED,PAUSE_TRADER
import asyncio
from cdc_trader.api.cdc_api import *

client = TelegramClient('bot', TEL_API_ID, TEL_API_HASH)

async def initialize_telegram():
    await client.start()
    print("Launching Bot")
    await send_telegram_message("Bot started")


@client.on(events.NewMessage(from_users=[TEL_OWNER_USERNAME]))
async def handle_messages(event):
    global PAUSE_TRADER
    # You can add more logic to handle different commands
    if 'help' in event.raw_text.lower():
        await event.reply(  "Available commands:\n"
                            "ping - check if bot is alive\n"
                            "account - show account summary\n"
                            "orders - show open orders\n"
                            "queue - show commands queue\n"
                            "pause - pause the bot\n"
                            "resume - resume the bot\n"
                            "clear queue - clear commands queue\n"
                            "cancel all - cancel all orders\n"
                            "stop - stop the bot")


    elif 'orders' in event.raw_text.lower():
        open_orders = get_open_orders()
        await event.reply(f"Open orders: {open_orders}")

    elif 'stop' in event.raw_text.lower():
        await event.reply("Shutting down")
        commands_queue.append('stop')

    elif 'pause' in event.raw_text.lower():
        commands_queue.append('pause')
        

    elif 'resume' in event.raw_text.lower():
        commands_queue.append('resume')

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
        open_orders = get_open_orders()
        for order in open_orders['order_list']:
            cancel_order(order['instrument_name'],order['order_id'])
            await event.reply(f"Canceling order {order['order_id']} with instrument {order['instrument_name']}")


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
