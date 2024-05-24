import ta
import numpy as np
import pandas as pd 
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
# import talib
np.random.seed(42)



signal_to_int = {'long_entry': 1, 'long_exit': 2, 'short_entry': 3,'short_exit': 4}
int_to_signal = {v:k for k,v in signal_to_int.items()}


    







def label_data(row):
    
    if row['long_entry']:
        return 1  # Label for long_entry
    elif row['long_exit']:
        return 2  # Label for long_exit
    elif row['short_entry']:
        return 3  # Label for short_entry
    elif row['short_exit']:
        return 4  # Label for short_exit
    else:
        return 0  # Label for hold


# def 
def generate_signals():
    # print('generating Signals')
    pass
    

def populate_indicators(data:pd.DataFrame):
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
    

class MLStrategy:
    def __init__(self, data, strategy='s1'):
        self.data = data
        self.data = self.data.rename(columns={'date':'timestamp'})
        self.strategy = strategy
        
        self.data = populate_indicators(self.data)
        # print(self.data.tail())
        self.previous_row = self.data.iloc[0]
        # self.run()

    def check_short_entry_condition(self, row, previous_row):
        if self.strategy == 's1':
            return row['close'] < row['Trend'] and row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs'] and row['RSI'] > 30
        else:
            pass


    def check_short_exit_condition(self, row, previous_row):
        if self.strategy == 's1': 
            return row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs']
        else:
            pass


    def compute_short_sl_level(self, row, entry_price):
        if self.strategy == 's1': 
            return entry_price + 2 * row['ATR']
        else:
            pass


    def compute_short_tp_level(self, row, entry_price, stop_loss_price):
        risk_reward_ratio = 4
        if self.strategy == 's1':
            return entry_price * (1 - risk_reward_ratio * (stop_loss_price / entry_price - 1))
        else:
            pass

    def check_long_entry_condition(self, row, previous_row):
        if self.strategy == 's1':
            return row['close'] > row['Trend'] and row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs'] and row['RSI'] < 70
        else:
            pass


    def check_long_exit_condition(self, row, previous_row):
        if self.strategy == 's1':
            return row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs']
        else:
            pass


    def compute_long_sl_level(self, row, entry_price):
        return entry_price - 2 * row['ATR']


    def compute_long_tp_level(row, entry_price, stop_loss_price):
        risk_reward_ratio = 4
        return entry_price * (1 + risk_reward_ratio * (1 - stop_loss_price / entry_price))
    
    
    def create_labels(self, window=10):
        # data['labels'] = np.where(data['close'].shift(-1) > data['close'], 1, 0)
        # print(data.tail())
        self.data['pct_change'] = 0
        # percentage change over 'window' days
        pct_change = self.data["close"].shift(-window).rolling(window).mean() / self.data["close"] - 1
        self.data['pct_change'] = pct_change
        # print(self.data['pct_change'][:20])
        
        # Entry
        self.data['long_entry'] = np.where(self.data['pct_change'] > 0.01, True, False)
        self.data['short_entry'] = np.where(self.data['pct_change'] < 0.01, True, False)
        # Exit
        self.data['long_exit'] = np.where(self.data['pct_change'] < 0., True, False)
        self.data['short_exit'] = np.where(self.data['pct_change'] > 0, True, False)

        
        
        # # Entry
        # self.data['long_entry'] = np.where((self.data['close'].shift(-1) > self.data['close']) & (self.data['close'].shift(1) <= self.data['close']), 1, 0)
        # self.data['short_entry'] = np.where((self.data['close'].shift(-1) < self.data['close']) & (self.data['close'].shift(1) >= self.data['close']) , 1, 0)
        # # Exit
        # self.data['long_exit'] = np.where((self.data['close'].shift(-1) < self.data['close']) & (self.data['close'].shift(1) > self.data['close']) , 1, 0)
        # self.data['short_exit'] = np.where((self.data['close'].shift(-1) > self.data['close']) & (self.data['close'].shift(1) < self.data['close']), 1, 0)

        # Define conditions with shift
        # self.data['long_entry'] = (self.data['MA-st'] > self.data['MA-lt']) & (self.data['MA-st'].shift(1) <= self.data['MA-lt'].shift(1))
        # self.data['long_exit'] = (self.data['MA-st'] < self.data['MA-lt']) & (self.data['MA-st'].shift(1) >= self.data['MA-lt'].shift(1))
        # self.data['short_entry'] = (self.data['MA-st'] < self.data['MA-lt']) & (self.data['MA-st'].shift(1) > self.data['MA-lt'].shift(1))
        # self.data['short_exit'] = (self.data['MA-st'] > self.data['MA-lt']) & (self.data['MA-st'].shift(1) < self.data['MA-lt'].shift(1))

        # print('Long Entries: ', data['long_entry'].sum())
        # print('Long Exits: ', data['long_exit'].sum())
        # print('Short Entries: ', data['short_entry'].sum())
        # print('Short Exits: ', data['short_exit'].sum())

        # return data
    
    
    def prepare_data(self, test_split=0.2):
        # Drop NaN
        self.data['short_entry'] = False
        self.data['short_exit'] = False
        self.data['long_entry'] = False
        self.data['long_exit'] = False
        # print(self.data.head())
        # print(self.data['timestamp'])
        
        self.data.dropna(inplace=True)
        self.create_labels()
        # self.data['label'] = self.data.apply(label_data, axis=1)
        # print('labels: ', np.unique(self.data['label']))
        # Features and target
        features = ['open', 'high', 'low', 'close', 'RSI', 'ATR', 'Trend']
        X = self.data[['timestamp'] + features]
        y = self.data[['long_entry', 'long_exit', 'short_entry', 'short_exit']]  #['label']
        # y = self.data[['long_entry', 'long_exit', 'short_entry', 'short_exit']]
        
        

        test_size = int(len(X)*test_split)
        # Splitting the data into training and testing sets
        X_train, X_test, y_train, y_test = X.iloc[:len(X)-test_size], X.iloc[-test_size:], y.iloc[:len(y)-test_size], y.iloc[-test_size:]      #train_test_split(X, y, test_size=test_split, shuffle=False)

        
        # # Timeframes:
        train_timeframe = X_train['timestamp']
        test_timeframe = X_test['timestamp']
        X_train = X_train.drop(['timestamp'], axis=1)
        X_test = X_test.drop(['timestamp'], axis=1)
        # print('X_train',X_train.head())
        
        
        
        
        
        # Scaling the features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        # print('X_train scaled',X_train_scaled)
        return X_train_scaled, y_train, X_test_scaled, y_test, train_timeframe, test_timeframe

    def run(self):
        print('running')

        X_train, y_train, X_test, y_test, train_timeframe, test_timeframe = self.prepare_data(test_split=0.2)
        # print('Training data: ', X_train)

        #Train Model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate Model
        predictions = model.predict(X_test)
        # print('Predictions', predictions)
        
        ## Inference
        # input_data = X_test.copy()
        # outputs = model.predict(input_data) 
        # print('Outputs: ', outputs)
        # output_signals = [int_to_signal[output] if output != 0 else 'Hold' for output in outputs]
        # input_data = pd.DataFrame(input_data)
        # input_data['short_entry'] = False
        # input_data['short_exit'] = False
        # input_data['long_entry'] = False
        # input_data['long_exit'] = False
        # for i, pred in enumerate(output_signals):
        #     input_data.loc[i, pred] = True
        
        # print('Testing inf: ', input_data.loc[:20,['long_entry', 'long_exit', 'short_entry', 'short_exit']])
            
        
        
        # print(int_to_signal.keys(), type(predictions[0]))
        # prediction_signals = [int_to_signal[pred] if pred != 0 else 'Hold' for pred in predictions]
        # print('Predictions: ', predictions[:10])
        # print('Actual: ', y_test[:10])
        # print(classification_report(y_test, predictions))
        # print("Accuracy:", accuracy_score(y_test, predictions))
        
        test_preds = pd.DataFrame(predictions, columns=['long_entry', 'long_exit', 'short_entry', 'short_exit'])
        # print(test_preds.head())
        test_data = self.scaler.inverse_transform(X_test)
        # print('Test Data', test_data.shape, pd.DataFrame(test_timeframe).shape, test_preds.shape)
        test_data = pd.DataFrame(test_data, columns=['open', 'high', 'low', 'close', 'RSI', 'ATR', 'Trend']) #['open', 'high', 'low', 'close']
        # print(test_data.head())
        final_data = pd.concat([test_data, test_preds], axis=1)
        final_data.reset_index(drop=True, inplace=True)
        test_timeframe.reset_index(drop=True, inplace=True)

        final_data = pd.concat([test_timeframe, final_data], axis=1)
        # print(final_data.shape)
        return final_data



if __name__ == "__main__":
    historical_data = '/home/tamal/projects/TradingBot/BTC_USDT_500_days.csv'
    # historical_data = '/workspaces/CryptoTradingBot/BTC_USDT_500_days.csv'
    data = pd.read_csv(historical_data)
    # print(data)
    s = MLStrategy(data)
    final_data = s.run()
    print(final_data.head())
    # print(data)
    
    