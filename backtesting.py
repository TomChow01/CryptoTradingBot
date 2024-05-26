import sys
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import wandb
from strategy import *


class Backtest:
    def __init__(self, config, data=None):
        print('*'*100)
        print('--------------STARTING BACKTESTING--------------')
        print('*'*100)
        
        self.config = config
        self.data = data
        self.orders = []
        
    def calculate_position_size(self, entry_price, stop_loss_price):
        if self.config['backtest']['exposure'] == 'all':
            return self.wallet
        risked_amount = self.wallet * (self.config['backtest']['exposure'] / 100)
        position = risked_amount * entry_price / abs(entry_price - stop_loss_price)
        return min(self.wallet, position)


    def calculate_liquidation_price(self, price, order_type):
            if order_type == 'long':
                return price * (1 - 1 / self.config['backtest']['leverage'])
            elif order_type == 'short':
                return price * (1 + 1 / self.config['backtest']['leverage'])


    def calculate_pnl(self, entry_price, exit_price, quantity, order_type):
        if order_type == 'long':
            return (exit_price - entry_price) * quantity
        elif order_type == 'short':
            return (entry_price - exit_price) * quantity
        
        

    def record_order(self, timestamp, type, price, amount, pnl, fee):
        order = {
            'timestamp': timestamp,
            'type': type,
            'amount': amount,
            'fee': fee,
            'pnl': pnl,
            'wallet': self.wallet,
        }
        self.orders.append(order)
        print(f"{type} at {price} {self.config['backtest']['symbol']} on {timestamp}, amount = {round(amount,2)} {self.config['backtest']['symbol']}, pnl = {round(pnl,2)} {self.config['backtest']['symbol']}, wallet = {round(self.wallet,2)} {self.config['backtest']['symbol']}")

    def check_short_entry_condition(self, row, previous_row):
        return row['close'] < row['Trend'] and row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs'] and row['RSI'] > 30


    def check_short_exit_condition(self, row, previous_row):
        return row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs']


    def compute_short_sl_level(self, row, entry_price):
        return entry_price + 2 * row['ATR']


    def compute_short_tp_level(self, row, entry_price, stop_loss_price):
        risk_reward_ratio = 4
        return entry_price * (1 - risk_reward_ratio * (stop_loss_price / entry_price - 1))

    def check_long_entry_condition(self, row, previous_row):
        return row['close'] > row['Trend'] and row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs'] and row['RSI'] < 70


    def check_long_exit_condition(self, row, previous_row):
        return row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs']


    def compute_long_sl_level(self, row, entry_price):
        return entry_price - 2 * row['ATR']


    def compute_long_tp_level(self, row, entry_price, stop_loss_price):
        risk_reward_ratio = 4
        return entry_price * (1 + risk_reward_ratio * (1 - stop_loss_price / entry_price))
        # return row['open'] * 1.1
        
        
    def analyze_backtest(self):
        ## Profits
        show_unrealised = True
        show_realised = True
        show_hodl = True

        profits_bot_realised = ((self.data['realised_pnl'] - self.config['backtest']['initial_capital'])/self.config['backtest']['initial_capital']) * 100
        profits_bot_unrealised = ((self.data['unrealised_pnl'] - self.config['backtest']['initial_capital'])/self.config['backtest']['initial_capital']) * 100
        profits_hodl = ((self.data['hodl'] - self.data.iloc[0]['hodl'])/self.data.iloc[0]['hodl']) * 100

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        if show_unrealised:
            ax1.plot(self.data['timestamp'], profits_bot_unrealised, color='gold', label='Bot')
        if show_realised:
            ax1.plot(self.data['timestamp'], profits_bot_realised, color='gold', label='Bot (realised)', ls= '--')
        if show_hodl:
            ax1.plot(self.data['timestamp'], profits_hodl, color='purple', label='Hodl')
        ax1.set_title('Net Profits', fontsize=20)
        ax1.set_ylabel('Net Profits (%)', fontsize=18)
        ax1.set_xticklabels([])
        ax1.legend(fontsize=16)
        if show_unrealised:
            ax2.plot(self.data['timestamp'], self.data['unrealised_pnl'], color='gold', label='Bot')
        if show_realised:
            ax2.plot(self.data['timestamp'], self.data['realised_pnl'], color='gold', label='Bot (realised)', ls= '--')
        if show_hodl:
            ax2.plot(self.data['timestamp'], self.data['hodl'], color='purple', label='Hodl')
            
        
        
        ax2.set_xlabel('Period', fontsize=18)
        ax2.set_ylabel('Net Profits (' + self.config['backtest']['name_quote'] + ')', fontsize=18)
        ax2.tick_params(axis='both', which='major', labelsize=12, rotation = 45)

        print(f" \n\n      ** Profits ** \n")
        print(f" > Period: {self.data['timestamp'].iloc[0]} -> {self.data['timestamp'].iloc[-1]} ")
        print(f" > Starting balance: {self.config['backtest']['initial_capital']} {self.config['backtest']['name_quote']}")
        print(f" > Final balance Bot: {round(self.data.iloc[-1]['unrealised_pnl'],2)} {self.config['backtest']['name_quote']}")
        print(f" > Final balance Hodl: {round(self.data.iloc[-1]['hodl'],2)} {self.config['backtest']['name_quote']}")
        print(f" > Bot net profits: {round(profits_bot_unrealised.iloc[-1],2)}%")
        print(f" > Hodl net profits: {round(profits_hodl.iloc[-1],2)}%")
        print(f" > Net profits ratio Bot / Hodl: {round(self.data.iloc[-1]['unrealised_pnl']/self.data.iloc[-1]['hodl'],2)}")
        # print(f' > SHARPE RATIO: {calculate_sharpe_ratio(self.data)}')
        
        if self.config['backtest']['log_wandb']:
            wandb.log({
                "Final balance Bot": round(self.data.iloc[-1]['unrealised_pnl'], 2),
                "Final balance Hodl": round(self.data.iloc[-1]['hodl'], 2),
                "Bot net profits (%)": round(profits_bot_unrealised.iloc[-1], 2),
                "Hodl net profits (%)": round(profits_hodl.iloc[-1], 2),
                "Net profits ratio Bot / Hodl": round(self.data.iloc[-1]['unrealised_pnl'] / self.data.iloc[-1]['hodl'], 2),
                # "Sharpe Ratio": calculate_sharpe_ratio(self.data)
            })

            # Log the plot as an image
            plt.savefig("net_profits.png")
            wandb.log({"Net Profits Plot": wandb.Image("net_profits.png")})


        ## Trades
        self.orders = pd.json_normalize(self.orders, sep='_')
        n_orders = len(self.orders.index)
        if not self.config['backtest']['ignore_longs']:
            n_longs = self.orders['type'].value_counts()['long entry']
        else:
            n_longs = 0
        if not self.config['backtest']['ignore_shorts']:
            n_shorts = self.orders['type'].value_counts()['short entry']
        else:
            n_shorts = 0
        n_entry_orders = 0
        if not self.config['backtest']['ignore_longs']:
            n_entry_orders += self.orders['type'].value_counts()['long entry']
        if not self.config['backtest']['ignore_shorts']:
            n_entry_orders += self.orders['type'].value_counts()['short entry']

        n_exit_orders = 0
        if 'long exit' in self.orders['type'].value_counts():
            n_exit_orders += self.orders['type'].value_counts()['long exit']
        if 'long tp' in self.orders['type'].value_counts():
            n_exit_orders += self.orders['type'].value_counts()['long tp']
        if 'long sl' in self.orders['type'].value_counts():
            n_exit_orders += self.orders['type'].value_counts()['long sl']
        if 'short exit' in self.orders['type'].value_counts():
            n_exit_orders += self.orders['type'].value_counts()['short exit']
        if 'short tp' in self.orders['type'].value_counts():
            n_exit_orders += self.orders['type'].value_counts()['short tp']
        if 'short sl' in self.orders['type'].value_counts():
            n_exit_orders += self.orders['type'].value_counts()['short sl']

        self.orders.loc[::2, 'pnl'] = np.nan
        self.orders['Win'] = ''
        self.orders.loc[self.orders['pnl']>0,'Win'] = 'Yes'
        self.orders.loc[self.orders['pnl']<=0,'Win'] = 'No'
        if 'Yes' in self.orders['Win'].value_counts():
            n_pos_trades = self.orders['Win'].value_counts()['Yes']
        else:
            n_pos_trades = 0
        if 'No' in self.orders['Win'].value_counts():
            n_neg_trades = self.orders['Win'].value_counts()['No']
        else:
            n_neg_trades = 0

        winrate = round(n_pos_trades / (n_pos_trades+n_neg_trades) * 100,2)
        self.orders['pnl%'] = self.orders['pnl'] / (self.orders['wallet'] - self.orders['pnl'])  * 100
        avg_trades = round(self.orders['pnl%'].mean(),2)
        avg_pos_trades = round(self.orders.loc[self.orders['Win'] == 'Yes']['pnl%'].mean(),2)
        avg_neg_trades = round(self.orders.loc[self.orders['Win'] == 'No']['pnl%'].mean(),2)
        best_trade = self.orders['pnl%'].max()
        when_best_trade = self.orders['timestamp'][self.orders.loc[self.orders['pnl%'] == best_trade].index.tolist()[0]]
        best_trade = round(best_trade,2)
        worst_trade = self.orders['pnl%'].min()
        when_worst_trade = self.orders['timestamp'][self.orders.loc[self.orders['pnl%'] == worst_trade].index.tolist()[0]]
        worst_trade = round(worst_trade,2)

        print(f" \n\n      ** Trades ** \n")
        print(f" > Orders: {n_orders} ({n_entry_orders} buys, {n_exit_orders} sells)")
        print(f" > Number of closed trades: {n_pos_trades+n_neg_trades}")
        print(f" > Winrate: {winrate}%")
        print(f" > Average trade profits: {avg_trades}%")
        print(f" > Number of winning trades: {n_pos_trades}")
        print(f" > Number of losing trades: {n_neg_trades}")
        print(f" > Average winning trades: {avg_pos_trades}%")
        print(f" > Average losing trades: {avg_neg_trades}%")
        print(f" > Best trade: {best_trade}% on the {when_best_trade}")
        print(f" > Worst trade: {worst_trade}% on the {when_worst_trade}")

        if self.config['backtest']['log_wandb']:
            wandb.log({
                "Buy Orders": n_entry_orders,
                "Sell Orders": n_exit_orders,
                "Winrate (%)": winrate,
                "Average trade profits (%)": avg_trades,
                "Average winning trades (%)": avg_pos_trades,
                "Average losing trades (%)": avg_neg_trades,
                "Best Trade": best_trade,
                "Worst Trade": worst_trade
            })


        ## Health
        worst_drawdown = round(self.data['drawdown'].min()*100,2)
        profit_factor = round(abs(self.orders.loc[self.orders['pnl'] > 0, 'pnl'].sum() / self.orders.loc[self.orders['pnl'] < 0, 'pnl'].sum()),2)
        return_over_max_drawdown = round(profits_bot_unrealised.iloc[-1] / abs(worst_drawdown),2)

        print(f" \n\n      ** Health ** \n")
        print(f" > Maximum drawdown: {worst_drawdown}%")
        print(f" > Profit factor: {profit_factor}")
        print(f" > Return over maximum drawdown: {return_over_max_drawdown}")
        
        
        if self.config['backtest']['log_wandb']:
            wandb.log({
                "Maximum Drawdown": worst_drawdown,
                "Profit Factor": profit_factor,
                "Return Over Maximum Drawdown": return_over_max_drawdown
            })



        ## fees
        total_fee = round(self.orders['fee'].sum(),2)
        biggest_fee = round(self.orders['fee'].max(),2)
        avg_fee = round(self.orders['fee'].mean(),2)

        print(f" \n\n      ** Fees ** \n")
        print(f" > Total: {total_fee} {self.config['backtest']['ignore_sl']}")
        print(f" > Biggest: {biggest_fee} {self.config['backtest']['ignore_sl']}")
        print(f" > Average: {avg_fee} {self.config['backtest']['ignore_sl']} \n")
        ax1.plot(self.data['timestamp'], self.data['drawdown']*100, color='blue', label='Drawdown')
        # plt.show()

    def run_backtest(self):

        # Initialize variables
        # print('Backtest data: ', self.data.shape, self.data.head())

        order_in_progress = None
        n_trades = 0
        last_ath = 0
        sl_price = 0
        tp_price = 0
        long_liquidation_price = 0
        short_liquidation_price = 1e10
        
        self.wallet = self.config['backtest']['initial_capital']
        
        self.data['realised_pnl'] = ''
        self.data['unrealised_pnl'] = ''
        self.data['hodl'] = ''
        self.data['drawdown'] = ''


        # Go through self.data and make trades
        for index, row in self.data.iterrows():
            price = row['close']
            # print(price)
            
            # Update trades count
            if row['long_entry'] or row['short_entry']:
                n_trades += 1


            # check if it is time to close a long (LONG EXIT)
            if order_in_progress == 'long' and not self.config['backtest']['ignore_longs']:
                if row['low'] < long_liquidation_price:
                    print(f' ! Your long was liquidated on the {row["timestamp"]} (price = {long_liquidation_price} {self.config['backtest']['ignore_sl']})')
                    sys.exit()

                elif not self.config['backtest']['ignore_sl'] and row['low'] <= sl_price:
                    pnl = self.calculate_pnl(entry_price, sl_price, quantity, order_in_progress)
                    fee_exit = quantity * sl_price * self.config['backtest']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'long sl', sl_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                elif not self.config['backtest']['ignore_tp'] and row['high'] >= tp_price:
                    pnl = self.calculate_pnl(entry_price, tp_price, quantity, order_in_progress)
                    fee_exit = quantity * tp_price * self.config['backtest']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'long tp', tp_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                elif not self.config['backtest']['ignore_exit'] and row['long_exit']:#check_long_exit_condition(row, previous_row):
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    pnl = self.calculate_pnl(entry_price, price, quantity, order_in_progress)
                    fee_exit = quantity * price * self.config['backtest']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    # if self.config['backtest']['latency']:
                    self.record_order(row['timestamp'], 'long exit', price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                if self.wallet > last_ath:
                    last_ath = self.wallet


            # check if it is time to close a short (SHORT EXIT)
            elif order_in_progress == 'short' and not self.config['backtest']['ignore_shorts']:
                if row['high'] > short_liquidation_price:
                    print(f'!Your short was liquidated on the {row["timestamp"]} (price = {short_liquidation_price} {self.config['backtest']['ignore_sl']})')
                    sys.exit()

                elif not self.config['backtest']['ignore_sl'] and row['high'] >= sl_price:
                    pnl = self.calculate_pnl(entry_price, sl_price, quantity, order_in_progress)
                    fee_exit = quantity * sl_price * self.config['backtest']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'short sl', sl_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                elif not self.config['backtest']['ignore_tp'] and row['low'] <= tp_price:
                    pnl = self.calculate_pnl(entry_price, tp_price, quantity, order_in_progress)
                    fee_exit = quantity * tp_price * self.config['backtest']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    self.record_order(row['timestamp'], 'short tp', tp_price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                elif not self.config['backtest']['ignore_exit'] and row['short_exit']:  #check_short_exit_condition(row, previous_row):
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    pnl = self.calculate_pnl(entry_price, price, quantity, order_in_progress)
                    fee_exit = quantity * price * self.config['backtest']['trade_fees'] / 100
                    self.wallet += position - fee_entry + pnl - fee_exit
                    # if self.config['backtest']['latency']:
                    self.record_order(row['timestamp'], 'short exit', price, 0, pnl - fee_exit - fee_entry, fee_exit)
                    order_in_progress = None

                if self.wallet > last_ath:
                    last_ath = self.wallet


            # check it is time to enter a long (LONG ENTRY)
            if not self.config['backtest']['ignore_longs'] and order_in_progress == None:
                if row['long_entry']:   #check_long_entry_condition(row, previous_row):
                    order_in_progress = 'long'
                    if not self.config['backtest']['ignore_sl']:
                        sl_price = self.compute_long_sl_level(row, price)
                    if not self.config['backtest']['ignore_tp']:
                        tp_price = self.compute_long_tp_level(row, price, sl_price)
                    long_liquidation_price = self.calculate_liquidation_price(price, order_in_progress)
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    entry_price = price
                    # if self.config['backtest']['latency']:
                    position = self.calculate_position_size(price, sl_price)
                    amount = position * self.config['backtest']['leverage']
                    fee_entry = amount * self.config['backtest']['trade_fees'] / 100
                    quantity = (amount - fee_entry) / price
                    if self.wallet > last_ath:
                        last_ath = self.wallet

                    self.wallet -= position
                    self.record_order(row['timestamp'], 'long entry', price, amount-fee_entry, -fee_entry, fee_entry)


            # check if it is time to enter a short (SHORT ENTRY)
            if not self.config['backtest']['ignore_shorts'] and order_in_progress == None:
                if row['short_entry']:  #check_short_entry_condition(row, previous_row):
                    order_in_progress = 'short'
                    if not self.config['backtest']['ignore_sl']:
                        sl_price = self.compute_short_sl_level(row, price)
                    if not self.config['backtest']['ignore_tp']:
                        tp_price = self.compute_short_tp_level(row, price, sl_price)
                    short_liquidation_price = self.calculate_liquidation_price(price, order_in_progress)
                    price += price * random.uniform(-self.config['backtest']['latency']/100., self.config['backtest']['latency']/100)
                    entry_price = price
                    # if self.config['backtest']['latency']:
                    position = self.calculate_position_size(price, sl_price)
                    amount = position * self.config['backtest']['leverage']
                    fee_entry = amount * self.config['backtest']['trade_fees'] / 100
                    quantity = (amount - fee_entry) / price
                    self.wallet -= position
                    self.record_order(row['timestamp'], 'short entry', price, amount-fee_entry, -fee_entry, fee_entry)


            # updating wallet info
            self.data.at[index, 'realised_pnl'] = self.wallet
            self.data.at[index, 'unrealised_pnl'] = self.data.at[index, 'realised_pnl']
            if order_in_progress != None:
                self.data.at[index, 'unrealised_pnl'] += position + self.calculate_pnl(entry_price, price, quantity, order_in_progress) #- fee
            self.data.at[index, 'hodl'] = self.config['backtest']['initial_capital'] / self.data["close"].iloc[0] * price
            self.data.at[index, 'drawdown'] = (self.data.at[index, 'unrealised_pnl'] - last_ath) / last_ath if last_ath else 0

        # return self.data, orders 