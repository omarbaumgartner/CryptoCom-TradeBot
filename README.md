# Cryptocurrency Trading Bot for Crypto.com Exchange

## Overview
This project is a sophisticated cryptocurrency trading bot specifically designed for the Crypto.com Exchange platform. It automates trading strategies by interacting with the exchange's APIs and is tailored for both new and experienced traders. The bot's trading logic and Telegram notifier behavior are highly customizable, offering a flexible approach to automated crypto trading.

## Features
- **Crypto.com Exchange API Integration**: Specifically designed for trading on the Crypto.com Exchange.
- **Customizable Trading Logic**: Flexible and adaptable trading strategies to suit various trading styles.
- **Telegram Integration**: Real-time notifications and remote control of the bot through Telegram.
- **Configurable Settings**: Easy configuration of API keys, trading parameters, and more.
- **User-Friendly Setup**: Quick and straightforward setup process using Poetry for dependency management.

## Modules
- `trading_api_client.py`: Manages interactions with the Crypto.com Exchange API.
- `trading_config_loader.py`: Loads configuration settings and parameters.
- `financial_calculations.py`: Performs financial calculations for trading decisions.
- `CryptoConversionGraph.py`: Analyzes cryptocurrency conversion paths using graph theory.
- `trading_classes.py`: Contains classes for various trading entities.
- `trading_sequence_generator.py`: Generates and manages trading sequences.
- `telegram_notifier.py`: Handles Telegram notifications and commands.

## Setup
### Prerequisites
- Python 3.x
- [Poetry](https://python-poetry.org/) for dependency management

### Installation
1. Clone the repository:
```sh
   git clone https://github.com/your-username/your-repository.git
```

2. Navigate to the cloned directory and install dependencies using Poetry:
```sh
    poetry install
```
## Configuration
1. Copy config_template.yaml to config.yaml and fill in your Crypto.com API keys and other necessary details.

2. Update the Telegram configuration in config.yaml with your bot credentials.

## Usage
Run the main script to start the bot:
```sh
   poetry run python trading_bot_main.py
```

## Telegram Commands
The bot can be controlled remotely via Telegram. Below are the available commands:

- `/help`: Displays a list of available commands.
- `/ping`: Checks if the bot is alive. Responds with "pong".
- `/account`: Shows a summary of the trading account.
- `/queue`: Displays the current command queue.
- `/clear queue`: Clears all commands in the queue.
- `/cancel all`: Cancels all open orders on the exchange.
- `/stop`: Stops the bot.
- `/pause` or `/unpause`: Toggles the bot's trading activity.

## Disclaimer
Trading cryptocurrencies involves significant risk and may not be suitable for all investors. Before trading, consider your experience level and risk appetite. This project is not liable for any potential damages or losses.

## Licence
This project is licensed under the MIT License.