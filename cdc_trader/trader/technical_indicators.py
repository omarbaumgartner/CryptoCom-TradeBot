# coding: utf-8
import numpy as np
import talib # pip install + follow this guide https://github.com/ta-lib/ta-lib-python
import statistics

# Relative Strength Index
def getRSIs(closes, period):
    if len(closes) < period:
        return [None]
    else:
        closes = [float(i) for i in closes]
        rsis = talib.RSI(np.array(closes), timeperiod=period)
        return rsis

# Single Moving Average
def getSMA(closes, period):
    if len(closes) < period:
        return [None]
    else:
        closes = [float(i) for i in closes]
        sma = talib.SMA(np.array(closes), timeperiod=period)
        return sma


# Bolinger Bands Percentage
def getBBPs(closes, period):
    if len(closes) < period:
        return [None]
    else:
        closes = [float(i) for i in closes]
        up, mid, low = talib.BBANDS(
            np.array(closes), timeperiod=period, nbdevup=2, nbdevdn=2, matype=0
        )
        bbp = (closes - low) / (up - low)
        return bbp


# On Balance Volume
def getOBVS(closes, volumes, period):
    closes = [float(x) for x in closes]
    volumes = [float(x) for x in volumes]
    obvs = talib.OBV(np.array(closes), np.array(volumes))
    a = obvs[len(obvs) - period :]
    mean = statistics.mean(a)
    return a, mean
