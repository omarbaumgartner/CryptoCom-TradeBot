import yaml


def load_config(config_file):
    with open(config_file, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


# Production or Sandbox
ENV = 'production'

commands_queue = []

config = load_config("config.yaml")
api_config = config['api']
telegram_config = config['telegram']


TRADING_FEE_PERCENTAGE = 0.0750
DESIRED_PROFIT_PERCENTAGE = 1




REST_BASE = api_config['rest_api'][ENV]
WS_MARKET = api_config['websocket_api'][ENV]['market_data']
WS_USER = api_config['websocket_api'][ENV]['user_data']
API_KEY = api_config['key']
API_SECRET = api_config['secret_key']

TEL_API_ID = telegram_config['app_api_id']
TEL_API_HASH = telegram_config['app_api_hash']
TEL_OWNER_USERNAME = telegram_config['owner_username']
TEL_BOT_TOKEN = telegram_config['bot_token']
TELEGRAM_MESSAGING_DISABLED = True