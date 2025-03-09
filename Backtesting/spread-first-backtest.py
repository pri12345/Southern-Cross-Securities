# %%
%matplotlib inline
import matplotlib.pyplot as plt
import backtrader as bt
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# %% 
# Code to retrieve dataframes that take work to clean. 
import sys
sys.path.append('..') # Basics.py is a py file one level above
from Basics import log_returns_spread, clean_price_data

mean_spread = log_returns_spread.mean()
std_spread = log_returns_spread.std()
pos_CV= 1.96 * std_spread + mean_spread
neg_CV = -1.96 * std_spread + mean_spread

log_returns_spread.loc['2025-02-28 09:35:00']

# %%
%matplotlib inline

cerebro = bt.Cerebro()
def add_data(symbol):
    df = clean_price_data[symbol].to_frame(name = 'close')
    df['open'] = df['high'] =df['low'] = df['close']
    df['volume'] = 0

    data = bt.feeds.PandasData(
        dataname = df,
        name =symbol,
        timeframe = bt.TimeFrame.Minutes,
        compression = 5, 
        fromdate= df.index.min(), todate = df.index.max()
        )
    cerebro.adddata(data)
    print(f'{symbol} added to cerebro')

add_data('GGAL')
add_data('BMA')

class GGAL_BMA_Spread_Strategy(bt.Strategy):
    params = (
        ('spread', None),
        ('pos_CV', pos_CV),
        ('neg_CV', neg_CV),
        ('Z_neg_stoploss', 4),
        ('Z_pos_stoploss', -4),        
    )

    def __init__(self):
        self.symbol_list = [i._name for i in self.datas]
        self.current_time = None
        self.current_spread = None
        self.in_trade = False
        self.dataclose_GGAL = self.datas[0].close
        self.dataclose_BMA = self.datas[1].close
        self.order_GGAL, self.order_BMA = None, None
        self.buyprice_GGAL, self.buyprice_BMA = None, None
        self.buycomm_GGAL, self.buycomm_BMA = None, None
        self.sellprice_GGAL, self.sellprice_BMA = None, None
        self.sellcomm_GGAL, self.sellcomm_BMA = None, None
        self.bar_executed_GGAL, self.bar_executed_BMA = None, None

    def log(self, msg, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {msg}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            buy_or_sell = 'BUY' if order.isbuy() else 'SELL'
            self.log(f'{buy_or_sell} {order.data._name} order Submitted/Accepted at price {order.created.price}')
            return
        if order.status in [order.Completed]:
            if order.data._name == self.symbol_list[0]:
                self.bar_executed_GGAL, self.buyprice_GGAL = len(self), order.executed.price
                self.buycomm_GGAL = order.executed.comm
                self.order_GGAL = None     
            elif order.data._name == self.symbol_list[1]:
                self.bar_executed_BMA, self.buyprice_BMA = len(self), order.executed.price
                self.buycomm_BMA = order.executed.comm
                self.order_BMA = None
            if order.isbuy():
                self.log(f'''BUY {order.data._name} EXECUTED, Price: {order.executed.price}, 
                         Cost: {order.executed.value}, Comm: {order.executed.comm}''')
            elif order.issell():
                self.log(f'''SELL {order.data._name} EXECUTED, Price: {order.executed.price}, 
                         Cost: {order.executed.value}, Comm: {order.executed.comm}''')

    def next(self):
      if len(self.dataclose_GGAL) < 1:
        return
      self.current_time = self.datetime.datetime(0)
      if self.current_time not in self.p.spread.index:
         return
      self.current_spread = self.p.spread.loc[self.current_time]
      self.in_trade = self.getposition(self.datas[0]) != 0 and self.getposition(self.datas[1]).size != 0

      # TRADE MANAGEMENT
      if self.in_trade:

          # Exit for profit
          if self.current_spread - mean_spread < mean_spread * 0.01:
            if self.getposition(self.datas[0]).size > 0:
              self.order_GGAL = self.sell(data = self.datas[0])
              self.order_BMA = self.buy(data = self.datas[1])
              self.log(f'Exit long GGAL, cover short BMA at spread {self.current_spread} ~= mean spread: {mean_spread}')
            elif self.getposition(self.datas[0]).size < 0:
              self.order_GGAL = self.buy(data = self.datas[0])
              self.order_BMA = self.sell(data = self.datas[1])
              self.log(f'cover short GGAL, exit long BMA at spread {self.current_spread} ~= mean spread: {mean_spread}')

          # Risk Management
          elif self.current_spread > self.p.Z_pos_stoploss:
            if self.getposition(self.datas[0]).size < 0:
              self.order_GGAL = self.buy(data = self.datas[0])
              self.order_BMA = self.sell(data = self.datas[1])
              self.log(f'STOPPED (cover GGAL, sell BMA) at spread {self.current_spread} > stoploss Z: {self.p.Z_pos_stoploss}')
            elif self.getposition(self.datas[0]).size < 0:
              self.order_GGAL = self.buy(data = self.datas[0])
              self.order_BMA = self.sell(data = self.datas[1])
              self.log(f'STOPPED (sell GGAL, cover BMA) at spread {self.current_spread} < stoploss -Z: {self.p.Z_neg_stoploss}')



            
      # ORDER NOT EXECUTED CASE
      #elif not self.in_trade and (self.order_GGAL is not None or self.order_BMA is not None) :
          

      # TRADE ENTRY
      elif not self.in_trade and self.order_GGAL is None and self.order_BMA is None:
          
      # SHORT GGAL, LONG BMA CASE 
        if self.current_spread > self.p.pos_CV:
            self.order_GGAL = self.buy(data = self.datas[0])
            self.order_BMA = self.sell(data = self.datas[1])
            self.log(f'SHORT GGAL, LONG BMA at spread {self.current_spread} > {self.p.pos_CV}')

      # LONG GGAL, SHORT BMA CASE
        elif self.current_spread < self.p.neg_CV:
            self.order_GGAL = self.sell(data = self.datas[0])
            self.order_BMA = self.buy(data = self.datas[1])
            self.log(f'LONG GGAL, SHORT BMA at spread {self.current_spread} < {self.p.neg_CV}')

      
cerebro.addstrategy(GGAL_BMA_Spread_Strategy, spread = log_returns_spread)
cerebro.broker.setcommission(commission=0.000)
cerebro.addsizer(bt.sizers.PercentSizer, percents = 95)
cerebro.run()
cerebro.plot(iplot=False)

final_value = cerebro.broker.getvalue()
starting_cash = cerebro.broker.startingcash
gain_percentage = (final_value / starting_cash - 1) * 100
gain_dollars = final_value - starting_cash
print(f'Final Value: ${final_value:.2f}\nReturn: ${gain_dollars:.2f} --> %{gain_percentage:.2f}')






# %%

# %%

# %%
