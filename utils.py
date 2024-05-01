from urllib.request import urlopen
import re as r
import ccxt
import json

def getIP():
    d = str(urlopen('http://checkip.dyndns.com/')
            .read())

    return r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(d).group(1)


def log_in():
    try:
        with open('api_keys.json') as f:
                keys = json.load(f)

                #with open('addresses.json') as f:
                #    addresses = json.load(f)

                exchange = ccxt.binance({
                'apiKey': keys['binance']['api_key'],
                'secret': keys['binance']['api_secret'],
                })

                exchange.load_markets()
                print(f'Successfully logged into {exchange}')
                return exchange
    except:
            print('Log in Failed')

# def log_in2():
#         try:
#                 with open('api_keys.json') as f:
#                         keys = json.load(f)

#                         #with open('addresses.json') as f:
#                         #    addresses = json.load(f)

#                         exchange = ccxt.binance({
#                         'apiKey': keys['binance']['api_key'],
#                         'secret': keys['binance']['api_secret'],
#                         })

#                         exchange.load_markets()
#                         print('Log in Successfull')
#                         return exchange
#         except:
#                 print('Unable to Log in to Binance. Please Make sure Your IP address is whitelisted')
