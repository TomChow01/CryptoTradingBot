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

# def buy_condition(row): #entry
#         if row['MA-st'] > row['MA-lt']:
#             return True
#         else:
#             return False
        
#     #     return row['MA-st'] > row['MA-lt']:

# def sell_condition(row): #exit
#     if row['MA-st'] < row['MA-lt']:
#         return True
#     else:
#         return False

signal_to_int = {
        'long_entry': 1,
        'long_exit': 2,
        'short_entry': 3,
        'short_exit': 4,
        # 'hold' : 0
    }
int_to_signal = {v:k for k,v in signal_to_int.items()}


    
def create_labels(data):
    # data['labels'] = np.where(data['close'].shift(-1) > data['close'], 1, 0)
    # print(data.tail())

    # Define conditions with shift
    data['long_entry'] = (data['MA-st'] > data['MA-lt']) & (data['MA-st'].shift(1) <= data['MA-lt'].shift(1))
    data['long_exit'] = (data['MA-st'] < data['MA-lt']) & (data['MA-st'].shift(1) >= data['MA-lt'].shift(1))
    data['short_entry'] = (data['MA-st'] < data['MA-lt']) & (data['MA-st'].shift(1) > data['MA-lt'].shift(1))
    data['short_exit'] = (data['MA-st'] > data['MA-lt']) & (data['MA-st'].shift(1) < data['MA-lt'].shift(1))

    # print('Long Entries: ', data['long_entry'].sum())
    # print('Long Exits: ', data['long_exit'].sum())
    # print('Short Entries: ', data['short_entry'].sum())
    # print('Short Exits: ', data['short_exit'].sum())

    return data

def prepare_data(data, test_split=0.2):
    # Drop NaN
    data.dropna(inplace=True)
    data = create_labels(data)
    data['label'] = data.apply(label_data, axis=1)
    # Features and target
    features = ['close', 'RSI', 'ATR', 'Trend']
    X = data[features]
    y = data['label']
    # y = data[['long_entry', 'long_exit', 'short_entry', 'short_exit']]

    # Splitting the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Scaling the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, y_train, X_test_scaled, y_test




def label_data(row):
    
    # print(int_to_signal)

    for condition, label in signal_to_int.items():
        if row[condition]:
            return label
    
    # Default case if no conditions are met
    # return 0



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
    
# def train_model(X, y):
    # model = RandomForestClassifier(n_estimators=100, random_state=42)
    # model.fit


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
    

class Strategy:
    def __init__(self, data, strategy='s1'):
        self.data = data
        self.strategy = strategy
        
        self.data = populate_indicators(self.data)
        self.previous_row = self.data.iloc[0]
        self.run()
        
        # self.data['short_entry'] = ''
        # self.data['short_exit'] = ''
        # self.data['long_entry'] = ''
        # self.data['long_exit'] = ''
        
        
        # X_train, y_train, X_test, y_test = prepare_data(self.data)
        # print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)
        
    
    
    
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
    
    def run(self):
        print('running')

        self.data['short_entry'] = ''
        self.data['short_exit'] = ''
        self.data['long_entry'] = ''
        self.data['long_exit'] = ''
        
        
        X_train, y_train, X_test, y_test = prepare_data(self.data)

        #Train Model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate Model
        predictions = model.predict(X_test)
        print(int_to_signal.keys(), type(predictions[0]))
        prediction_signals = [int_to_signal[pred] if pred != 0 else 'Hold' for pred in predictions]
        print('Predictions: ', prediction_signals)
        print('Actual: ', y_test.tolist())
        print(classification_report(y_test, predictions))
        print("Accuracy:", accuracy_score(y_test, predictions))

        
        # for index, row in self.data.iterrows():
        #     price = row['close']
        #     self.data.at[index, 'long_exit'] = self.check_long_exit_condition(row, self.previous_row)    
        #     self.data.at[index, 'short_exit'] = self.check_short_exit_condition(row, self.previous_row)
        #     self.data.at[index, 'long_entry'] = self.check_long_entry_condition(row, self.previous_row)
        #     self.data.at[index, 'short_entry'] = self.check_short_entry_condition(row, self.previous_row)
        #     self.previous_row = row
        # return self.data
        # pass
        

if __name__ == "__main__":
    # historical_data = '/home/tamal/projects/TradingBot/BTC_USDT_500_days.csv'
    historical_data = '/workspaces/CryptoTradingBot/BTC_USDT_500_days.csv'
    data = pd.read_csv(historical_data)
    # print(data)
    s = Strategy(data)
    data = s.data
    # print(data.head())
    # print(data)
    
    