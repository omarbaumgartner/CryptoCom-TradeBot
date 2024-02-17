import yaml


def load_config(config_file):
    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


# Production or Sandbox
ENV = 'production'
RICH_MODE = False # Set to True to simulate a rich account
commands_queue = []

config = load_config("config.yaml")
api_config = config['api']
telegram_config = config['telegram']
LOG_FILEPATH = config['system']['log_file']

# Trader configuration
SLEEP_INTERVAL = 3 # seconds
MIN_VALUE_IN_CURRENCY = 4 # USDT 
MAX_INVESTMENT_PER_TRADE_IN_USDT = 5    # USDT
TRADING_FEE_PERCENTAGE = 0.0750 # %
# TODO : Reimplement min/max profit logic
MIN_PROFITS_PERCENTAGE = 0.09 # The minimum percentage of profit we want to make, will impact the bid and ask prices, the lower the percentage, the more likely the trade will be executed
MIN_DESIRED_PROFIT_PERCENTAGE = 0.01 # %
MAX_DESIRED_PROFIT_PERCENTAGE = 1 # %

END_CURRENCIES = ["USDT"]
MIN_SPREAD_PERCENTAGE = 0.0
PAUSE_TRADER = False
MAX_DEPTH = 4


# CDC API configuration
REST_BASE = api_config['rest_api'][ENV]
WS_MARKET = api_config['websocket_api'][ENV]['market_data']
WS_USER = api_config['websocket_api'][ENV]['user_data']
API_KEY = api_config['key']
API_SECRET = api_config['secret_key']

# Telegram configuration
TELEGRAM_MESSAGING_DISABLED = True
TEL_API_ID = telegram_config['app_api_id']
TEL_API_HASH = telegram_config['app_api_hash']
TEL_OWNER_USERNAME = telegram_config['owner_username']
TEL_BOT_TOKEN = telegram_config['bot_token']

