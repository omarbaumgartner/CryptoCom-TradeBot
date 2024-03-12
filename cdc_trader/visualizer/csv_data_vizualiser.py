from cdc_trader.api.cdc_api import *
import csv
from pathlib import Path 
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd
import matplotlib.dates as mpdates
 
# Load from csv 
def load_csv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)
    return data

# Load filepaths of csv files in a directory
def load_csv_files(folder_path):
    files = []
    for file in Path(folder_path).rglob('*.csv'):
        files.append(file)
    return files

filepaths = load_csv_files('data')

# extracting Data for plotting
df = pd.read_csv("data/CRO_USDT/CRO_USDT_12h_candles_2024-02-28_00-16-45.csv")

# convert into datetime object
df['timestamp'] = pd.to_datetime(df['timestamp'])

# apply map function
df['timestamp'] = df['timestamp'].map(mpdates.date2num)


plt.style.use('dark_background')
# creating Subplots
fig, ax = plt.subplots()

width = 0.001 * (df.index[1] - df.index[0])

# plotting the data
candlestick_ohlc(ax, df.values, width = width,
                colorup = 'green', colordown = 'red', 
                alpha = 0.8)

# allow grid
ax.grid(True)

# Setting labels 
ax.set_xlabel('Date')
ax.set_ylabel('Price')

# setting title
plt.title('Prices For the Period 01-07-2020 to 15-07-2020')

# Formatting Date
date_format = mpdates.DateFormatter('%d-%m-%Y')
ax.xaxis.set_major_formatter(date_format)
fig.autofmt_xdate()

fig.tight_layout()

# show the plot
plt.show()