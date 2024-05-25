import ta
import numpy as np
import pandas as pd 
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
np.random.seed(42)


class MLStrategy:
    def __init__(self, data, strategy='s1'):
        self.data = data
        self.data = self.data.rename(columns={'date':'timestamp'})
        self.strategy = strategy
        
        self.data = self.populate_indicators(self.data)

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


    def create_labels(self, window=10):        
        # percentage change over 'window' days
        pct_change = self.data["close"].shift(-window).rolling(window).mean() / self.data["close"] - 1
        self.data['pct_change'] = pct_change
        
        ## Entry Exit: Logic 1
        # Entry
        self.data['long_entry'] = np.where(self.data['pct_change'] > 0.01, True, False)
        self.data['short_entry'] = np.where(self.data['pct_change'] < 0.01, True, False)
        # Exit
        self.data['long_exit'] = np.where(self.data['pct_change'] < 0., True, False)
        self.data['short_exit'] = np.where(self.data['pct_change'] > 0, True, False)

        ## Entry Exit: Logic 2
        # # Entry
        # self.data['long_entry'] = np.where((self.data['close'].shift(-1) > self.data['close']) & (self.data['close'].shift(1) <= self.data['close']), 1, 0)
        # self.data['short_entry'] = np.where((self.data['close'].shift(-1) < self.data['close']) & (self.data['close'].shift(1) >= self.data['close']) , 1, 0)
        # # Exit
        # self.data['long_exit'] = np.where((self.data['close'].shift(-1) < self.data['close']) & (self.data['close'].shift(1) > self.data['close']) , 1, 0)
        # self.data['short_exit'] = np.where((self.data['close'].shift(-1) > self.data['close']) & (self.data['close'].shift(1) < self.data['close']), 1, 0)


        # print('Long Entries: ', data['long_entry'].sum())
        # print('Long Exits: ', data['long_exit'].sum())
        # print('Short Entries: ', data['short_entry'].sum())
        # print('Short Exits: ', data['short_exit'].sum())

    
    
    def prepare_data(self, test_split=0.2):
        # Drop NaN
        self.data.dropna(inplace=True)
        
        # Create Labels
        self.create_labels(window=10)

        # Features and target
        features = ['open', 'high', 'low', 'close', 'RSI', 'ATR', 'Trend']
        
        X = self.data[['timestamp'] + features]
        y = self.data[['long_entry', 'long_exit', 'short_entry', 'short_exit']]  #['label']
        
        
        # Splitting the data into training and testing sets
        test_size = int(len(X)*test_split)
        X_train, X_test, y_train, y_test = X.iloc[:len(X)-test_size], X.iloc[-test_size:], y.iloc[:len(y)-test_size], y.iloc[-test_size:]      #train_test_split(X, y, test_size=test_split, shuffle=False)

        
        # # Timeframes:
        train_timeframe = X_train['timestamp']
        test_timeframe = X_test['timestamp']
        X_train = X_train.drop(['timestamp'], axis=1)
        X_test = X_test.drop(['timestamp'], axis=1)

        # Scaling the features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        # print('X_train scaled',X_train_scaled)
        return X_train_scaled, y_train, X_test_scaled, y_test, train_timeframe, test_timeframe

    def run(self):
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
    data = pd.read_csv(historical_data)
    s = MLStrategy(data)
    final_data = s.run()
    print(final_data.head())
    # print(data)
    
    