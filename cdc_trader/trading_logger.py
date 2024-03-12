from trading_api_client import generate_nonce
from telegram_notifier import send_telegram_message
from datetime import datetime
# Make the writing in file be directly saved, because atm it only saves when the program stops.

# async def log_message(file,message,type='log',send_telegram=False,print_message=True):
#     if print_message:
#         print(message,flush=True)
#     log_message = {
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "type": type,
#         "message": message
#     }
#     if send_telegram:
#         await send_telegram_message(message)
#     file.write(str(log_message) + '\n')
#     file.flush()  # Flush the file to ensure immediate writing

def log_message(file,message,type='log',send_telegram=False,print_message=True):
    if print_message:
        print(message,flush=True)
    log_message = {
        "nonce": int(generate_nonce()),
        "type": type,
        "message": message
    }
    # if send_telegram:
    #     await send_telegram_message(message)
    file.write(str(log_message) + '\n')
    file.flush()  # Flush the file to ensure immediate writing
