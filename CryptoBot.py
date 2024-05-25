import os
import sys
# import cv2

import math

 
import time
import datetime
from datetime import datetime, timezone
 
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import mplfinance as mpf

import ccxt

import ta
import json
import wandb

from utils import getIP, log_in, load_config

from strategy import Strategy
from backtesting import Backtest
from strategy_ml import MLStrategy



class TradingBot:
    def __init__(self, config:str= 'config.json'):
        print('*'*100)
        print('--------------STARTING THE BOT--------------')
        print('*'*100)
        
        
        self.config = config #load_config(config)
        print(f'Hi I am {self.config['bot_name']}, Your Personal Crypto Trading Bot')
        self.log_wandb = self.config['backtest']['log_wandb']
        
        # if self.exchange:
        try:
            self.exchange = log_in() #exchange
            self.exchange.load_markets()
            print('Successfully Logged into Binance')
        except:
            self.exchange = ccxt.binance()
            print('WARNING: Unable to Log into Binance')
                # print('working only with the historical data')

        
    def get_historical_prices(self, symbols:str='BTC/USDT', timeframe:str='1d', days:int = None, start: datetime = None, end: datetime = None, save:bool=False)-> pd.DataFrame:
        if self.exchange:
            
            
            if days:
                # print(f'Fetching {symbols} Data of last {days} days')
                from_timestamp = self.exchange.milliseconds() - days * 86400 * 1000
                to_timestamp = self.exchange.milliseconds() - (days-10) * 86400 * 1000
                print(f'Fetching past {days} days data for {symbols} || Timeframe: {timeframe}')
                bars = self.exchange.fetch_ohlcv(symbols, timeframe=timeframe, since=from_timestamp, limit=1000)
            
            
            elif start and end:
                print(f'Fetching {symbols} Data from {start} to {end}')
                start_timestamp = int(self.exchange.parse8601(start))
                end_timestamp = int(self.exchange.parse8601(end))

                bars = []

                # Fetch data in batches
                while start_timestamp < end_timestamp:
                    ohlcv = self.exchange.fetch_ohlcv(symbols, timeframe, since=start_timestamp, )
                    if not ohlcv:
                        break
                    bars.extend(ohlcv)
                    start_timestamp = ohlcv[-1][0] + 1
                

            # bars = exchange.fetch_ohlcv(symbols, timeframe=timeframe, since=from_timestamp,  params={'until': to_timestamp}, limit=1000)
            df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df["close"] = pd.to_numeric(df["close"])
            df["high"] = pd.to_numeric(df["high"])
            df["low"] = pd.to_numeric(df["low"])
            df["open"] = pd.to_numeric(df["open"])
            
            if save:
                filename = f'{symbols}_{len(df)+1}_days.csv' #'test.csv'
                print('Data Saved As: ', filename)
                df.to_csv(filename)
            
            return df
        return None
    
    def fetch_coin_balance(self, symbol:str='BTC') -> float:
        balances = pd.DataFrame(self.exchange.fetch_balance()['info']['balances'])
        pair_balance = float(balances[balances['asset']==symbol]['free'].values[0])
        return pair_balance
    

    def plot_data(self, data:pd.DataFrame):
        df = data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Set the timestamp as the index
        df.set_index('timestamp', inplace=True)

        # Plot the data using mplfinance
        fig, ax = mpf.plot(df, type='candle', style='charles', title='BTC/USDT OHLCV', volume=True, figsize=(20, 10), figratio=(20, 10), figscale=1.5, returnfig=True)
        plot_filename = 'btc_usdt_ohlcv.png'
        fig.savefig(plot_filename)

        plt.close(fig)

    
    def run(self, historical_data=None):
        if self.exchange:
            try:
                data = self.get_historical_prices(symbols=self.config['symbol'], timeframe='1d', days=500, save=True)
                # df = self.get_historical_prices(symbols=self.config['symbol'], timeframe='1d', start='2019-01-01 00:00:00', end='2022-12-31 00:00:00', save=True)
                # print(data.shape)
                
            except:
                print('Unable to fetch historical Data. Falling back to historical data')
        else:
            if historical_data:
                data = pd.read_csv(historical_data)
            else:
                raise ValueError('Data could not be fetched.')

        
        # Plot the Data
        self.plot_data(data)

        # Apply Strategy on Data
        strategy_1 = Strategy(data)
        data = strategy_1.run()
        
        # Backtest The Strategy
        backtest = Backtest(self.config, data)
        backtest.run_backtest()
        backtest.analyze_backtest()
        
    

if __name__ == '__main__':
    config_file = '/home/tamal/projects/TradingBot/config.json'
    historical_data = '/home/tamal/projects/TradingBot/BTC_USDT_500_days.csv'
    
    config = load_config(config_file)
    
    
    if config['backtest']['log_wandb']:
        wandb.init(project="backtest_project",
                entity= 'tomchow',
                name='test')
    
    
    bot = TradingBot(config)
    bot.run(historical_data)
    # data, orders = bot.run(historical_data)
    # analyze_backtest(data, orders)
    # print(orders)
    
    
   