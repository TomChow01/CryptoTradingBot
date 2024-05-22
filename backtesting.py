import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategy import *

name_base = "BTC"
name_quote = "USDT"

ignore_shorts = False
ignore_longs = False
ignore_tp = False
ignore_sl = False
ignore_exit = False

timeframe = "1d"
starting_date_backtest = "01 january 2019"
ending_date_backtest =  "01 january 2022"
starting_date_dl = "01 january 2018"
ending_date_dl = "01 january 2022"


initial_capital = 1000 # in quote
exposure = 2           # position size in percent
# exposure = 'all'       # use this instead if you want 100% of your portfolio to be used for each trade
trade_fees = 0.1       # in percent
leverage = 5



def calculate_position_size(balance, exposure, entry_price, stop_loss_price):
    if exposure == 'all':
        return balance
    risked_amount = balance * (exposure / 100)
    position = risked_amount * entry_price / abs(entry_price - stop_loss_price)
    return min(balance, position)


def calculate_liquidation_price(price, leverage, order_type):
        if order_type == 'long':
            return price * (1 - 1 / leverage)
        elif order_type == 'short':
            return price * (1 + 1 / leverage)


def calculate_pnl(entry_price, exit_price, quantity, order_type):
    if order_type == 'long':
        return (exit_price - entry_price) * quantity
    elif order_type == 'short':
        return (entry_price - exit_price) * quantity
    
def calculate_sharpe_ratio(data, risk_free_rate=0.0):
    # Calculate daily returns
    data['daily_return'] = data['realised_pnl'].pct_change()

    # Calculate average daily return
    avg_daily_return = data['daily_return'].mean()

    # Calculate daily return standard deviation
    daily_return_std = data['daily_return'].std()

    # Calculate Sharpe Ratio (assuming risk-free rate is zero)
    sharpe_ratio = (avg_daily_return - risk_free_rate) / daily_return_std * np.sqrt(365)

    return sharpe_ratio

# # Assuming your DataFrame is named `data` and has a 'realised_pnl' column
# sharpe_ratio = calculate_sharpe_ratio(data)
    

def record_order(timestamp, type, price, amount, pnl, wallet, fee, orders):
    order = {
        'timestamp': timestamp,
        'type': type,
        'amount': amount,
        'fee': fee,
        'pnl': pnl,
        'wallet': wallet,
    }
    orders.append(order)
    print(f"{type} at {price} {name_quote} on {timestamp}, amount = {round(amount,2)} {name_quote}, pnl = {round(pnl,2)} {name_quote}, wallet = {round(wallet,2)} {name_quote}")

def check_short_entry_condition(row, previous_row):
    return row['close'] < row['Trend'] and row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs'] and row['RSI'] > 30


def check_short_exit_condition(row, previous_row):
    return row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs']


def compute_short_sl_level(row, entry_price):
    return entry_price + 2 * row['ATR']


def compute_short_tp_level(row, entry_price, stop_loss_price):
    risk_reward_ratio = 4
    return entry_price * (1 - risk_reward_ratio * (stop_loss_price / entry_price - 1))

def check_long_entry_condition(row, previous_row):
    return row['close'] > row['Trend'] and row['EMAf'] > row['EMAs'] and previous_row['EMAf'] < previous_row['EMAs'] and row['RSI'] < 70


def check_long_exit_condition(row, previous_row):
    return row['EMAf'] < row['EMAs'] and previous_row['EMAf'] > previous_row['EMAs']


def compute_long_sl_level(row, entry_price):
    return entry_price - 2 * row['ATR']


def compute_long_tp_level(row, entry_price, stop_loss_price):
    risk_reward_ratio = 4
    return entry_price * (1 + risk_reward_ratio * (1 - stop_loss_price / entry_price))
    return row['open'] * 1.1
    

def analyze_backtest(data, backtest_orders):
    ## Profits
    show_unrealised = True
    show_realised = True
    show_hodl = True

    profits_bot_realised = ((data['realised_pnl'] - initial_capital)/initial_capital) * 100
    profits_bot_unrealised = ((data['unrealised_pnl'] - initial_capital)/initial_capital) * 100
    profits_hodl = ((data['hodl'] - data.iloc[0]['hodl'])/data.iloc[0]['hodl']) * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    if show_unrealised:
        ax1.plot(data['timestamp'], profits_bot_unrealised, color='gold', label='Bot')
    if show_realised:
        ax1.plot(data['timestamp'], profits_bot_realised, color='gold', label='Bot (realised)', ls= '--')
    if show_hodl:
        ax1.plot(data['timestamp'], profits_hodl, color='purple', label='Hodl')
    ax1.set_title('Net Profits', fontsize=20)
    ax1.set_ylabel('Net Profits (%)', fontsize=18)
    ax1.set_xticklabels([])
    ax1.legend(fontsize=16)
    if show_unrealised:
        ax2.plot(data['timestamp'], data['unrealised_pnl'], color='gold', label='Bot')
    if show_realised:
        ax2.plot(data['timestamp'], data['realised_pnl'], color='gold', label='Bot (realised)', ls= '--')
    if show_hodl:
        ax2.plot(data['timestamp'], data['hodl'], color='purple', label='Hodl')
    ax2.set_xlabel('Period', fontsize=18)
    ax2.set_ylabel('Net Profits (' + name_quote + ')', fontsize=18)
    ax2.tick_params(axis='both', which='major', labelsize=12, rotation = 45)

    print(f" \n\n      ** Profits ** \n")
    print(f" > Period: {data['timestamp'].iloc[0]} -> {data['timestamp'].iloc[-1]} ")
    print(f" > Starting balance: {initial_capital} {name_quote}")
    print(f" > Final balance Bot: {round(data.iloc[-1]['unrealised_pnl'],2)} {name_quote}")
    print(f" > Final balance Hodl: {round(data.iloc[-1]['hodl'],2)} {name_quote}")
    print(f" > Bot net profits: {round(profits_bot_unrealised.iloc[-1],2)}%")
    print(f" > Hodl net profits: {round(profits_hodl.iloc[-1],2)}%")
    print(f" > Net profits ratio Bot / Hodl: {round(data.iloc[-1]['unrealised_pnl']/data.iloc[-1]['hodl'],2)}")
    print(f' > SHARPE RATIO: {calculate_sharpe_ratio(data)}')


    ## Trades
    orders = pd.json_normalize(backtest_orders, sep='_')
    n_orders = len(orders.index)
    if not ignore_longs:
        n_longs = orders['type'].value_counts()['long entry']
    else:
        n_longs = 0
    if not ignore_shorts:
        n_shorts = orders['type'].value_counts()['short entry']
    else:
        n_shorts = 0
    n_entry_orders = 0
    if not ignore_longs:
        n_entry_orders += orders['type'].value_counts()['long entry']
    if not ignore_shorts:
        n_entry_orders += orders['type'].value_counts()['short entry']

    n_exit_orders = 0
    if 'long exit' in orders['type'].value_counts():
        n_exit_orders += orders['type'].value_counts()['long exit']
    if 'long tp' in orders['type'].value_counts():
        n_exit_orders += orders['type'].value_counts()['long tp']
    if 'long sl' in orders['type'].value_counts():
        n_exit_orders += orders['type'].value_counts()['long sl']
    if 'short exit' in orders['type'].value_counts():
        n_exit_orders += orders['type'].value_counts()['short exit']
    if 'short tp' in orders['type'].value_counts():
        n_exit_orders += orders['type'].value_counts()['short tp']
    if 'short sl' in orders['type'].value_counts():
        n_exit_orders += orders['type'].value_counts()['short sl']

    orders.loc[::2, 'pnl'] = np.nan
    orders['Win'] = ''
    orders.loc[orders['pnl']>0,'Win'] = 'Yes'
    orders.loc[orders['pnl']<=0,'Win'] = 'No'
    if 'Yes' in orders['Win'].value_counts():
        n_pos_trades = orders['Win'].value_counts()['Yes']
    else:
        n_pos_trades = 0
    if 'No' in orders['Win'].value_counts():
        n_neg_trades = orders['Win'].value_counts()['No']
    else:
        n_neg_trades = 0

    winrate = round(n_pos_trades / (n_pos_trades+n_neg_trades) * 100,2)
    orders['pnl%'] = orders['pnl'] / (orders['wallet'] - orders['pnl'])  * 100
    avg_trades = round(orders['pnl%'].mean(),2)
    avg_pos_trades = round(orders.loc[orders['Win'] == 'Yes']['pnl%'].mean(),2)
    avg_neg_trades = round(orders.loc[orders['Win'] == 'No']['pnl%'].mean(),2)
    best_trade = orders['pnl%'].max()
    when_best_trade = orders['timestamp'][orders.loc[orders['pnl%'] == best_trade].index.tolist()[0]]
    best_trade = round(best_trade,2)
    worst_trade = orders['pnl%'].min()
    when_worst_trade = orders['timestamp'][orders.loc[orders['pnl%'] == worst_trade].index.tolist()[0]]
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


    ## Health
    worst_drawdown = round(data['drawdown'].min()*100,2)
    profit_factor = round(abs(orders.loc[orders['pnl'] > 0, 'pnl'].sum() / orders.loc[orders['pnl'] < 0, 'pnl'].sum()),2)
    return_over_max_drawdown = round(profits_bot_unrealised.iloc[-1] / abs(worst_drawdown),2)

    print(f" \n\n      ** Health ** \n")
    print(f" > Maximum drawdown: {worst_drawdown}%")
    print(f" > Profit factor: {profit_factor}")
    print(f" > Return over maximum drawdown: {return_over_max_drawdown}")


    ## fees
    total_fee = round(orders['fee'].sum(),2)
    biggest_fee = round(orders['fee'].max(),2)
    avg_fee = round(orders['fee'].mean(),2)

    print(f" \n\n      ** Fees ** \n")
    print(f" > Total: {total_fee} {name_quote}")
    print(f" > Biggest: {biggest_fee} {name_quote}")
    print(f" > Average: {avg_fee} {name_quote} \n")
    # plt.show()

def run_backtest(data):

    # Initialize variables
    orders = []
    order_in_progress = None
    n_trades = 0
    last_ath = 0
    sl_price = 0
    tp_price = 0
    long_liquidation_price = 0
    short_liquidation_price = 1e10
    wallet = initial_capital
    data['realised_pnl'] = ''
    data['unrealised_pnl'] = ''
    data['hodl'] = ''
    data['drawdown'] = ''
    # previous_row = data.iloc[0]


    # Go through data and make trades
    for index, row in data.iterrows():
        price = row['close']
        # print(price)
        
        # Update trades count
        if row['long_entry'] or row['short_entry']:
            n_trades += 1


        # check if it is time to close a long (LONG EXIT)
        if order_in_progress == 'long' and not ignore_longs:
            if row['low'] < long_liquidation_price:
                print(f' ! Your long was liquidated on the {row["timestamp"]} (price = {long_liquidation_price} {name_quote})')
                sys.exit()

            elif not ignore_sl and row['low'] <= sl_price:
                pnl = calculate_pnl(entry_price, sl_price, quantity, order_in_progress)
                fee_exit = quantity * sl_price * trade_fees / 100
                wallet += position - fee_entry + pnl - fee_exit
                record_order(row['timestamp'], 'long sl', sl_price, 0, pnl - fee_exit - fee_entry, wallet, fee_exit, orders)
                order_in_progress = None

            elif not ignore_tp and row['high'] >= tp_price:
                pnl = calculate_pnl(entry_price, tp_price, quantity, order_in_progress)
                fee_exit = quantity * tp_price * trade_fees / 100
                wallet += position - fee_entry + pnl - fee_exit
                record_order(row['timestamp'], 'long tp', tp_price, 0, pnl - fee_exit - fee_entry, wallet, fee_exit, orders)
                order_in_progress = None

            elif not ignore_exit and row['long_exit']:#check_long_exit_condition(row, previous_row):
                pnl = calculate_pnl(entry_price, price, quantity, order_in_progress)
                fee_exit = quantity * price * trade_fees / 100
                wallet += position - fee_entry + pnl - fee_exit
                record_order(row['timestamp'], 'long exit', price, 0, pnl - fee_exit - fee_entry, wallet, fee_exit, orders)
                order_in_progress = None

            if wallet > last_ath:
                last_ath = wallet


        # check if it is time to close a short (SHORT EXIT)
        elif order_in_progress == 'short' and not ignore_shorts:
            if row['high'] > short_liquidation_price:
                print(f'!Your short was liquidated on the {row["timestamp"]} (price = {short_liquidation_price} {name_quote})')
                sys.exit()

            elif not ignore_sl and row['high'] >= sl_price:
                pnl = calculate_pnl(entry_price, sl_price, quantity, order_in_progress)
                fee_exit = quantity * sl_price * trade_fees / 100
                wallet += position - fee_entry + pnl - fee_exit
                record_order(row['timestamp'], 'short sl', sl_price, 0, pnl - fee_exit - fee_entry, wallet, fee_exit, orders)
                order_in_progress = None

            elif not ignore_tp and row['low'] <= tp_price:
                pnl = calculate_pnl(entry_price, tp_price, quantity, order_in_progress)
                fee_exit = quantity * tp_price * trade_fees / 100
                wallet += position - fee_entry + pnl - fee_exit
                record_order(row['timestamp'], 'short tp', tp_price, 0, pnl - fee_exit - fee_entry, wallet, fee_exit, orders)
                order_in_progress = None

            elif not ignore_exit and row['short_exit']:  #check_short_exit_condition(row, previous_row):
                pnl = calculate_pnl(entry_price, price, quantity, order_in_progress)
                fee_exit = quantity * price * trade_fees / 100
                wallet += position - fee_entry + pnl - fee_exit
                record_order(row['timestamp'], 'short exit', price, 0, pnl - fee_exit - fee_entry, wallet, fee_exit, orders)
                order_in_progress = None

            if wallet > last_ath:
                last_ath = wallet


        # check it is time to enter a long (LONG ENTRY)
        if not ignore_longs and order_in_progress == None:
            if row['long_entry']:   #check_long_entry_condition(row, previous_row):
                order_in_progress = 'long'
                if not ignore_sl:
                    sl_price = compute_long_sl_level(row, price)
                if not ignore_tp:
                    tp_price = compute_long_tp_level(row, price, sl_price)
                entry_price = price
                position = calculate_position_size(wallet, exposure, price, sl_price)
                amount = position * leverage
                fee_entry = amount * trade_fees / 100
                quantity = (amount - fee_entry) / price
                long_liquidation_price = calculate_liquidation_price(price, leverage, order_in_progress)
                if wallet > last_ath:
                    last_ath = wallet

                wallet -= position
                record_order(row['timestamp'], 'long entry', price, amount-fee_entry, -fee_entry, wallet, fee_entry, orders)


        # check if it is time to enter a short (SHORT ENTRY)
        if not ignore_shorts and order_in_progress == None:
            if row['short_entry']:  #check_short_entry_condition(row, previous_row):
                order_in_progress = 'short'
                if not ignore_sl:
                    sl_price = compute_short_sl_level(row, price)
                if not ignore_tp:
                    tp_price = compute_short_tp_level(row, price, sl_price)
                entry_price = price
                position = calculate_position_size(wallet, exposure, price, sl_price)
                amount = position * leverage
                fee_entry = amount * trade_fees / 100
                quantity = (amount - fee_entry) / price
                short_liquidation_price = calculate_liquidation_price(price, leverage, order_in_progress)
                wallet -= position
                record_order(row['timestamp'], 'short entry', price, amount-fee_entry, -fee_entry, wallet, fee_entry, orders)


        # updating wallet info
        data.at[index, 'realised_pnl'] = wallet
        data.at[index, 'unrealised_pnl'] = data.at[index, 'realised_pnl']
        if order_in_progress != None:
            data.at[index, 'unrealised_pnl'] += position + calculate_pnl(entry_price, price, quantity, order_in_progress) #- fee
        data.at[index, 'hodl'] = initial_capital / data["close"].iloc[0] * price
        data.at[index, 'drawdown'] = (data.at[index, 'unrealised_pnl'] - last_ath) / last_ath if last_ath else 0

        # previous_row = row

    return data, orders