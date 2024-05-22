import os
import sys
# import cv2

import math

 
import time
import datetime
from datetime import timezone
 
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

import ccxt

import ta
import json

from utils import getIP, log_in, load_config
from strategy import populate_indicators, Strategy
from backtesting import *


class TradingBot:
    def __init__(self, config:str= 'config.json', exchange=None, name='Freedom 25'):
        
        print(f'Hi I am {name}, To your service')
        self.config = load_config(config)
        self.exchange = exchange
        
        if self.exchange:
            try:
                self.exchange = log_in() #exchange
                self.exchange.load_markets()
                print('Successfully Connected to the Exchange')
            except:
                self.exchange = None
                print('Unable to Connect to the Exchange')
                print('working only with the historical data')
        
        # else
        # os.system('pwd')
        
    def get_historical_prices(self, symbols:str='BTC/USDT', timeframe:str='1d', days:int = 500, start: datetime = None, end: datetime = None, save:bool=False)-> pd.DataFrame:
        if self.exchange:
            from_timestamp = self.exchange.milliseconds() - days * 86400 * 1000
            to_timestamp = self.exchange.milliseconds() - (days-10) * 86400 * 1000
            # bars = exchange.fetch_ohlcv(symbols, timeframe)
            
            if days:
                print(f'Fetching past {days} days data for {symbols} || Timeframe: {timeframe}')
                bars = self.exchange.fetch_ohlcv(symbols, timeframe=timeframe, since=from_timestamp, limit=1000)
            
            #TODO: from-to timestamp data fetch
            if start:
                if end:
                    pass
                else:
                    pass
                

            # bars = exchange.fetch_ohlcv(symbols, timeframe=timeframe, since=from_timestamp,  params={'until': to_timestamp}, limit=1000)
            df = pd.DataFrame(bars[:-1], columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['date'], unit='ms')
            df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df["close"] = pd.to_numeric(df["close"])
            df["high"] = pd.to_numeric(df["high"])
            df["low"] = pd.to_numeric(df["low"])
            df["open"] = pd.to_numeric(df["open"])
            
            if save:
                filename = f'{symbols}_{days}_days.csv' #'test.csv'
                print(filename)
                df.to_csv(filename)
            
            return df
        return None
    
    def fetch_coin_balance(self, symbol:str='BTC') -> float:
        balances = pd.DataFrame(self.exchange.fetch_balance()['info']['balances'])
        pair_balance = float(balances[balances['asset']==symbol]['free'].values[0])
        return pair_balance
    
    
    
    
    def load_config():
        pass
    
     
    def plot_data(self, dataframe:pd.DataFrame):
        pass
    
    def create_trade(self):
        pass
    
    def execute_signals(self):
        pass
    
    def execute_trades(self):
        pass
    
    def run(self, historical_data=None):
        if self.exchange:
            try:
                df = self.get_historical_prices(symbols=self.config['symbol'], timeframe='1d', days=500)
            except:
                print('Unable to fetch historical Data. Falling back to historical data')
        else:
            if historical_data:
                df = pd.read_csv(historical_data)
            else:
                raise ValueError('Data could not be fetched.')
            
        # print(df.head())
        # print(df.tail())
        # data = populate_indicators(df)
        data = df.rename(columns={'date':'timestamp'})
        strategy_1 = Strategy(data, strategy='s1')
        data = strategy_1.data
        print('Long Entries: ', data['long_entry'].sum())
        print('Long Exits: ', data['long_exit'].sum())
        print('Short Entries: ', data['short_entry'].sum())
        print('Short Exits: ', data['short_exit'].sum())
        print(data.tail())
        data, backtest_orders = run_backtest(data)
        analyze_backtest(data, backtest_orders)
        # print(data)
        # print(backtest_orders)
        # return data, backtest_orders
    

if __name__ == '__main__':
    config_file = '/workspaces/CryptoTradingBot/config.json' #'/home/tamal/projects/TradingBot/config.json'
    historical_data = '/workspaces/CryptoTradingBot/BTC_USDT_500_days.csv' #'/home/tamal/projects/TradingBot/BTC_USDT_500_days.csv'
    
    bot = TradingBot(config_file, exchange='binance', name='Willi')
    bot.run(historical_data)
    # data, orders = bot.run(historical_data)
    # analyze_backtest(data, orders)
    # print(orders)
    
    
   