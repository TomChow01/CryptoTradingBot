import ta
import pandas as pd 

class Strategy:
    def __init__(self, data, strategy='s1'):
        self.data = data
        self.strategy = strategy
        
        self.data = self.populate_indicators(self.data)
        self.previous_row = self.data.iloc[0]

    
    def populate_indicators(self, data:pd.DataFrame):
        data['MA-st'] = ta.trend.sma_indicator(data['close'], 10)
        data['MA-lt'] = ta.trend.sma_indicator(data['close'], 40)
        data['EMAf'] = ta.trend.ema_indicator(data['close'], 10)
        data['EMAs'] = ta.trend.ema_indicator(data['close'], 30)
        data['Trend'] = ta.trend.sma_indicator(data['close'], 50)
        data['RSI'] = ta.momentum.rsi(data['close'])
        data['ATR'] = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=14)

        # MACD = ta.trend.MACD(data['close'], window_slow=26, window_fast=12, window_sign=9)
        # data['MACD'] = MACD.macd()
        # data['MACD_histo'] = MACD.macd_diff()
        # data['MACD_signal'] = MACD.macd_signal()

        # BB = ta.volatility.BollingerBands(close=data['close'], window=100, window_dev=2)
        # data["BB_lower"] = BB.bollinger_lband()
        # data["BB_upper"] = BB.bollinger_hband()
        # data["BB_avg"] = BB.bollinger_mavg()
        return data
    
    
    ## Entry Conditions
    def check_long_entry_condition(self, row, previous_row):
        if self.strategy == 's1':
            return row['close'] > row['Trend'] and row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs'] and row['RSI'] < 70
        else:
            pass
            
    def check_short_entry_condition(self, row, previous_row):
        if self.strategy == 's1':
            return row['close'] < row['Trend'] and row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs'] and row['RSI'] > 30
        else:
            pass

    ## Exit Conditions
    def check_long_exit_condition(self, row, previous_row):
        if self.strategy == 's1':
            return row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs']
        else:
            pass
        
    def check_short_exit_condition(self, row, previous_row):
        if self.strategy == 's1': 
            return row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs']
        else:
            pass
    
    def run(self):
        
        for index, row in self.data.iterrows():
            price = row['close']
            self.data.at[index, 'long_exit'] = self.check_long_exit_condition(row, self.previous_row)    
            self.data.at[index, 'short_exit'] = self.check_short_exit_condition(row, self.previous_row)
            self.data.at[index, 'long_entry'] = self.check_long_entry_condition(row, self.previous_row)
            self.data.at[index, 'short_entry'] = self.check_short_entry_condition(row, self.previous_row)
            self.previous_row = row
        
        return self.data
        # pass