import ccxt
import time
import sys
import random
import numpy as np
import pandas as pd
from strategy import Strategy
from strategy_ml import MLStrategy
from backtesting import Backtest
from utils import load_config


class PaperTrading(Backtest):
    def __init__(self, config):
        super().__init__(config)
        print('*'*100)
        print('--------------STARTING DRY RUN--------------')
        print('*'*100)
        
        self.config = config
        self.balance = self.config['dry_run']['wallet']
        self.positions = []
        self.trade_history = []
        
        # Initialize Binance exchange
        self.exchange = ccxt.binance({
            'enableRateLimit': True,  # Enable rate limit to avoid hitting API limits
        })
        

        
    def fetch_ohlcv(self):
        bars= self.exchange.fetch_ohlcv(self.config['dry_run']['symbol'], self.config['dry_run']['timeframe'])
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df["close"] = pd.to_numeric(df["close"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["open"] = pd.to_numeric(df["open"])
        return df

    
    def run(self):
        order_in_progress = None
        
        n_trades = 0
        last_ath = 0
        sl_price = 0
        tp_price = 0
        long_liquidation_price = 0
        short_liquidation_price = 1e10
        
        self.wallet = self.config['dry_run']['wallet']
        
        # self.data['realised_pnl'] = 0.
        # self.data['unrealised_pnl'] = 0.
        # self.data['hodl'] = 0.
        # self.data['drawdown'] = 0.
        
        self.history = [] #pd.DataFrame(columns=['close', 'realised_pnl', 'unrealised_pnl', 'hodl', 'drawdown'])
        
        while True:
            df = self.fetch_ohlcv()
            strategy = Strategy(df)
            df = strategy.run()
            
            row = df.iloc[-1]
            # print('row', row)
            price = row['close']
            # print('Current Price: ', row['close'])
            
            # Update trades count
            if row['long_entry'] or row['short_entry']:
                n_trades += 1


            # check if it is time to close a long (LONG EXIT)
            if order_in_progress == 'long' and not self.config['dry_run']['ignore_longs']:
                if row['low'] < long_liquidation_price:
                    print(f' ! Your long was liquidated on the {row["timestamp"]} (price = {long_liquidation_price} {self.config['dry_run']['ignore_sl']})')
                    sys.exit()

                elif not self.config['dry_run']['ignore_sl'] and row['low'] <= sl_price:
                    pnl = self.calculate_pnl(entry_price, sl_price, quantity, order_in_progress)
                    fee_exit = quantity * sl_price * self.config['dry_run']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'long sl', sl_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                elif not self.config['dry_run']['ignore_tp'] and row['high'] >= tp_price:
                    pnl = self.calculate_pnl(entry_price, tp_price, quantity, order_in_progress)
                    fee_exit = quantity * tp_price * self.config['dry_run']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'long tp', tp_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                # elif not self.config['dry_run']['ignore_exit'] and row['long_exit']:
                elif not self.config['dry_run']['ignore_exit'] and np.random.random(1)[0] > 0.25:
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    pnl = self.calculate_pnl(entry_price, price, quantity, order_in_progress)
                    fee_exit = quantity * price * self.config['dry_run']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'long exit', price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                if self.wallet > last_ath:
                    last_ath = self.wallet


            # check if it is time to close a short (SHORT EXIT)
            elif order_in_progress == 'short' and not self.config['dry_run']['ignore_shorts']:
                if row['high'] > short_liquidation_price:
                    print(f'!Your short was liquidated on the {row["timestamp"]} (price = {short_liquidation_price} {self.config['dry_run']['ignore_sl']})')
                    sys.exit()

                elif not self.config['dry_run']['ignore_sl'] and row['high'] >= sl_price:
                    pnl = self.calculate_pnl(entry_price, sl_price, quantity, order_in_progress)
                    fee_exit = quantity * sl_price * self.config['dry_run']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'short sl', sl_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                elif not self.config['dry_run']['ignore_tp'] and row['low'] <= tp_price:
                    pnl = self.calculate_pnl(entry_price, tp_price, quantity, order_in_progress)
                    fee_exit = quantity * tp_price * self.config['dry_run']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'short tp', tp_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                # elif not self.config['dry_run']['ignore_exit'] and row['short_exit']:
                elif not self.config['dry_run']['ignore_exit'] and np.random.random(1)[0] > 0.25:
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    pnl = self.calculate_pnl(entry_price, price, quantity, order_in_progress)
                    fee_exit = quantity * price * self.config['dry_run']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'short exit', price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                if self.wallet > last_ath:
                    last_ath = self.wallet


            # check it is time to enter a long (LONG ENTRY)
            if not self.config['dry_run']['ignore_longs'] and order_in_progress == None:
                # if row['long_entry']:  
                if np.random.random(1)[0] > 0.5:
                    order_in_progress = 'long'
                    if not self.config['dry_run']['ignore_sl']:
                        sl_price = self.compute_long_sl_level(row, price)
                    if not self.config['dry_run']['ignore_tp']:
                        tp_price = self.compute_long_tp_level(row, price, sl_price)
                    long_liquidation_price = self.calculate_liquidation_price(price, order_in_progress)
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    entry_price = price
                    position = self.calculate_position_size(price, sl_price)
                    amount = position * self.config['dry_run']['leverage']
                    fee_entry = amount * self.config['dry_run']['trade_fees'] / 100
                    quantity = (amount - fee_entry) / price
                    if self.wallet > last_ath:
                        last_ath = self.wallet

                    self.wallet -= position
                    self.record_order(row['timestamp'], 'long entry', price, amount-fee_entry, -fee_entry, fee_entry)


            # check if it is time to enter a short (SHORT ENTRY)
            if not self.config['dry_run']['ignore_shorts'] and order_in_progress == None:
                if np.random.random(1)[0] > 0.5:
                # if row['short_entry']:
                    order_in_progress = 'short'
                    if not self.config['dry_run']['ignore_sl']:
                        sl_price = self.compute_short_sl_level(row, price)
                    if not self.config['dry_run']['ignore_tp']:
                        tp_price = self.compute_short_tp_level(row, price, sl_price)
                    short_liquidation_price = self.calculate_liquidation_price(price, order_in_progress)
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    entry_price = price
                    position = self.calculate_position_size(price, sl_price)
                    amount = position * self.config['dry_run']['leverage']
                    fee_entry = amount * self.config['dry_run']['trade_fees'] / 100
                    quantity = (amount - fee_entry) / price
                    self.wallet -= position
                    self.record_order(row['timestamp'], 'short entry', price, amount-fee_entry, -fee_entry, fee_entry)


            realised_pnl = self.wallet 
            unrealised_pnl = realised_pnl
            unrealised_pnl = realised_pnl if order_in_progress is None else (unrealised_pnl + position + self.calculate_pnl(entry_price, price, quantity, order_in_progress))

            # hodl = self.config['dry_run']['initial_capital'] / self.history["close"].iloc[0] * price
            # drawdown = 

            current_state = {'close': price,'realised_pnl': realised_pnl, 'unrealised_pnl': unrealised_pnl, 'hodl': 0, 'drawdown': 0}
            # self.history = self.history.append({'close': price,'realised_pnl': realised_pnl, 'unrealised_pnl': unrealised_pnl, 'hodl': 0, 'drawdown': 0})
            self.history.append(current_state) #= pd.concat([self.history, pd.DataFrame([1,1,1,1,1]).T], ignore_index=True)
            print('Orders \n', pd.DataFrame(self.orders))
            print('History \n', pd.DataFrame(self.history))
            # # updating wallet info
            # self.data.at[index, 'realised_pnl'] = self.wallet
            # self.data.at[index, 'unrealised_pnl'] = self.data.at[index, 'realised_pnl']
            # if order_in_progress != None:
            #     self.data.at[index, 'unrealised_pnl'] += position + self.calculate_pnl(entry_price, price, quantity, order_in_progress) #- fee
            # self.data.at[index, 'hodl'] = self.config['dry_run']['initial_capital'] / self.data["close"].iloc[0] * price
            # self.data.at[index, 'drawdown'] = (self.data.at[index, 'unrealised_pnl'] - last_ath) / last_ath if last_ath else 0
            
            time.sleep(10)
        



if __name__ == "__main__":
    config_file = '/home/tamal/projects/TradingBot/config.json'
    # historical_data = '/home/tamal/projects/TradingBot/BTC_USDT_500_days.csv'
    
    config = load_config(config_file)
    
    # Initialize the bot with an initial balance
    bot = PaperTrading(config)
    bot.run()

