from trading_api_client import generate_nonce
from telegram_notifier import send_telegram_message


async def log_message(file,message,type='log',send_telegram=True):
    print(message)
    log_message = {
        "nonce": generate_nonce(),
        "type": type,
        "message": message
    }
    if send_telegram:
        await send_telegram_message(message)
    file.write(str(log_message) + '\n')