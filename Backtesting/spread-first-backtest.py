# %%
%matplotlib inline
import matplotlib.pyplot as plt
import backtrader as bt
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import math
# %% 
# Code to retrieve dataframes that take work to clean. 
import sys
sys.path.append('..') # Basics.py is a py file one level above
from Basics import log_returns_spread, clean_price_data

# Initializations and data downloads/appends



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
        compression = 1, 
        fromdate= df.index.min(), todate = df.index.max()
        )
    cerebro.adddata(data)
    print(f'{symbol} added to cerebro')

add_data('GGAL')
add_data('BMA')

# Global variables to be initiated in the class
global_pos_CV, global_neg_stoploss, global_pos_stoploss, global_mean_spread, global_std_spread = None, None, None, None, None


class GGAL_BMA_Spread_Strategy(bt.Strategy): 
    params = (                  # Parameters to be inputted by us, or take a default value
        ('spread', None),
        ('Z_pos_CV', 1.96), 
        ('Z_neg_CV', -1.96),
        ('Z_pos_stoploss', 4),
        ('Z_neg_stoploss', -4),        
    )

    def __init__(self):
        global global_pos_CV, global_neg_stoploss, global_pos_stoploss, global_mean_spread, global_std_spread       # initialize global vars inside class

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
        self.previous_position_GGAL, self.previous_position_BMA = 0, 0
        self.order_rejection_times = []
        self.trade_type = None
        self.trade_log = []
        self.ongoing_trades= {}

        # Spread-related instance variables
        self.mean_spread, self.std_spread = log_returns_spread.mean(),log_returns_spread.std()
        self.pos_CV= self.p.Z_pos_CV * self.std_spread + self.mean_spread
        self.neg_CV = self.p.Z_neg_CV * self.std_spread + self.mean_spread
        self.pos_stoploss_value = self.p.Z_pos_stoploss * self.std_spread + self.mean_spread
        self.neg_stoploss_value = self.p.Z_neg_stoploss * self.std_spread + self.mean_spread
        # Global Vars
        global_pos_CV = self.pos_CV
        global_pos_stoploss, global_neg_stoploss = self.pos_stoploss_value, self.neg_stoploss_value
        global_mean_spread, global_std_spread = self.mean_spread, self.std_spread
          
    def log(self, msg, dt=None):                         # logging a msg function
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {msg}')

  # END of static methods (that i dont change often)


  # Notify Order Section


    def notify_order(self, order):            # On each order submitted, accepted(by broker), and executed this method runs
        
        symbol = order.data._name
        buyorsell = 'buy' if order.isbuy() else 'sell'
        executed_price = order.executed.price
        size = order.executed.size


        # If order submitted:
        if order.status == order.Submitted:     # don't want to do anything when I submit them
          return
  
        # IF order accepted
        if order.status  == order.Accepted: 
            
            # Trade exit or stoploss
            if order.size == - self.previous_position_BMA or order.size == - self.previous_position_GGAL:
               buy_or_sell = 'Buy to cover' if order.isbuy() else 'sell to close'
               self.log(f'EXIT: {buy_or_sell} {symbol} order Accepted at price {order.created.price:.2f}, size: {order.size}')
                    #    f' PSG: {self.previous_position_GGAL} , PSB:{self.previous_position_BMA}')      TOGGLE # FOR DEBUGGING

            # Trade initiation
            else:
              buy_or_sell = 'Buy to open' if order.isbuy() else 'short'
              self.log(f'{buy_or_sell} {symbol} Accepted at price {order.created.price:.2f}, size: {order.size}')
                 #     f', PSG: {self.previous_position_GGAL} , PSB:{self.previous_position_BMA}')    TOGGLE # FOR DEBUGGING
            return
        
        # IF order is executed
        if order.status == order.Completed:
            
            if symbol == self.symbol_list[0]:
                self.order_GGAL = None     
            else:                                         # resetting orders to None
                self.order_BMA = None

            # Catching If it is a closing order (either take profit or stoploss)
            if order.size == - self.previous_position_GGAL or order.size == - self.previous_position_BMA:
               self.trade_type = 'close'

               if order.isbuy():
                self.log(f'EXIT: buy to cover {symbol} Executed, Price: {executed_price:.2f}, '
                          f'Position: {self.getposition(order.data).size} ')
                       #   f'Cost: {order.executed.value:.2f}, PSG: {self.previous_position_GGAL}, PSB: {self.previous_position_BMA}')  Toggle # for debugging
               elif order.issell():
                  self.log(f'EXIT: sell to close {symbol} Executed, Price: {executed_price:.2f}, '
                          f'Position: {self.getposition(order.data).size} ')
                       #   f'Cost: {order.executed.value:.2f}, PSG: {self.previous_position_GGAL}, PSB: {self.previous_position_BMA}') Toggle # for debugging
                  
            # Trade Entry orders
            elif order.isbuy():  # using elif is crucial, else it would execute if it meets the above condition too
                self.trade_type = 'open'
                self.log(f'ENTRY: buy {symbol} EXECUTED, Price: {executed_price:.2f}, '
                         f'Position: {self.getposition(order.data).size}, ')
                       #  f'Cost: {order.executed.value:.2f}, PSG: {self.previous_position_GGAL}, PSB: {self.previous_position_BMA}')  Toggle # for debugging
            elif order.issell(): # same than above
                self.trade_type = 'open'
                self.log(f'ENTRY: sell {symbol} EXECUTED, Price: {executed_price:.2f}, '
                         f'Position: {self.getposition(order.data).size}, ')
                      #   f'Cost: {order.executed.value:.2f}, PSG: {self.previous_position_GGAL}, PSB: {self.previous_position_BMA}')     Toggle # for debugging
                
            # Save the current position for the next orders
            self.previous_position_GGAL = self.getposition(order.data).size if symbol == self.symbol_list[0] else self.previous_position_GGAL
            self.previous_position_BMA = self.getposition(order.data).size if symbol == self.symbol_list[1] else self.previous_position_BMA
            
            if self.trade_type == 'open':
               self.trade_log.append({
                  'symbol': symbol,
                  'direction': 'buy' if order.isbuy() else 'short',
                  'size': size,
                  'type': 'to open',
                  'pnl' : None,
                  'execution time': self.datetime.datetime(0),
                  'price': executed_price
                  })
               
               
            elif self.trade_type == 'close':
               self.trade_log.append({
                  'symbol': symbol,
                  'direction': 'cover' if order.isbuy() else 'exit long',
                  'size': size,
                  'type': 'to close',
                  'pnl' : None,
                  'execution time': self.datetime.datetime(0),
                  'price': executed_price
                  })

            
            
            
            
            
            
            
            
            
            
            return

        if order.status not in [2,4]:    # check for rejections, not using elif because we have return at the end of every competing if statement
            print(f'order rejected? status: {order.status}')
            self.order_rejection_times.append(self.datetime.datetime(0))

  

    # NEXT method section


    def next(self):
      if len(self.dataclose_GGAL) < 1:
        return
      self.current_time = self.datetime.datetime(0)
      if self.current_time not in self.p.spread.index:                # staple vars, return if not atleast 1 datapoint.
         return
      self.current_spread = self.p.spread.loc[self.current_time]
      self.in_trade = self.getposition(self.datas[0]).size != 0 and self.getposition(self.datas[1]).size != 0          # Define being in a trade as having a position in both assets.

      # TRADE MANAGEMENT
      if self.in_trade:

        # Exit for profit
          if abs(self.current_spread - self.mean_spread) < abs(self.std_spread * 0.1):    # If the spread is very close to the mean (not exact since it is a very large decimal)
            if self.getposition(self.datas[0]).size > 0:
              self.order_GGAL = self.close(data=self.datas[0])               # Close if long GGAL
              self.order_BMA = self.close(data=self.datas[1])
              self.log(f'Exit long GGAL, cover short BMA at spread |{self.current_spread:.6f}| < |10% * STD| ({(self.std_spread * 0.1):.6f})')
            elif self.getposition(self.datas[0]).size < 0:
              self.order_BMA = self.close(data=self.datas[1])                 # Close if short GGAL
              self.order_GGAL = self.close(data=self.datas[0])
              self.log(f'cover short GGAL, exit long BMA at spread |{self.current_spread:.6f}| < |10% * STD| ({(self.std_spread * 0.1):.6f})')

        # Stopping Out
          elif (self.current_spread > self.pos_stoploss_value) or (self.current_spread < self.neg_stoploss_value):             # If we exceeded the stoploss in any direction
            if self.getposition(self.datas[0]).size < 0:                   # If we are short GGAL (positive spread, positive stoploss value)
              self.order_BMA = self.close(data=self.datas[1])
              self.order_GGAL = self.close(data=self.datas[0])
              self.log(f'STOPPED (cover GGAL, sell BMA) at spread {self.current_spread:.6f} > stoploss {self.pos_stoploss_value:.6f} Z-val: {self.p.Z_pos_stoploss}')
            elif self.getposition(self.datas[0]).size > 0:                 # If we are long GGAL (negative spread, negative stoploss value)
              self.order_GGAL = self.close(data=self.datas[0])
              self.order_BMA = self.close(data=self.datas[1])
              self.log(f'STOPPED (sell GGAL, cover BMA) at spread {self.current_spread:.6f} < stoploss {self.neg_stoploss_value:.6f} Z-val: {self.p.Z_neg_stoploss}')



            
      # ORDER NOT EXECUTED CASE            #  -------------> PENDING
      #elif not self.in_trade and (self.order_GGAL is not None or self.order_BMA is not None) :
          
    # TRADE ENTRY

      elif not self.in_trade and self.order_GGAL is None and self.order_BMA is None:       # Condition to not be in a trade and not have any pending orders waiting to be filled
       # print('h')                                                                        # For debugging, toggle #

        if self.current_spread > self.pos_CV:                                           # SHORT GGAL, LONG BMA CASE 
            size_GGAL = math.floor(self.broker.get_cash() / self.dataclose_GGAL[0])
            size_BMA = math.floor(self.broker.get_cash() / self.dataclose_BMA[0])         # Position sizing 
            self.order_GGAL = self.sell(data=self.datas[0], size=size_GGAL)
            self.order_BMA = self.buy(data=self.datas[1], size=size_BMA)                  # setting orders
            self.log(f'SHORT GGAL, LONG BMA at spread {self.current_spread:.6f} > trigger: {self.pos_CV:.6f}')

      
        elif self.current_spread < self.neg_CV:                                        # LONG GGAL, SHORT BMA CASE
            size_GGAL = math.floor(self.broker.get_cash() / self.dataclose_GGAL[0])
            size_BMA = math.floor(self.broker.get_cash() / self.dataclose_BMA[0])
            self.order_BMA = self.sell(data=self.datas[1], size=size_BMA)                  # same thing
            self.order_GGAL = self.buy(data=self.datas[0], size=size_GGAL)
            self.log(f'LONG GGAL, SHORT BMA at spread {self.current_spread:.6f} < trigger: {self.neg_CV:.6f}')

      
# Parameters to run the strat 

cerebro.broker.setcommission(commission=0.000)                                    # set commision in decimal form (0.1% = 0.001)
cerebro.addsizer(bt.sizers.PercentSizer, percents = 95)                           # size of port %, leave a 5% for commisions / slippage
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
cerebro.addwriter(bt.WriterFile, out=None, csv=False)

cerebro.addstrategy(GGAL_BMA_Spread_Strategy,
                    spread= log_returns_spread,   # Pass the spread series here
                    Z_pos_CV=  1,
                    Z_neg_CV= -1,
                    Z_pos_stoploss=  4,
                    Z_neg_stoploss= -4,               
                  )                            

results = cerebro.run()
cerebro.plot(iplot=False)
final_value = cerebro.broker.getvalue()
starting_cash = cerebro.broker.startingcash
gain_percentage = (final_value / starting_cash - 1) * 100
gain_dollars = final_value - starting_cash
print(f'Final Value: ${final_value:.2f}\nReturn: ${gain_dollars:.2f} --> %{gain_percentage:.2f}')
trade_analyzer = results[0].analyzers.tradeanalyzer.get_analysis()

# %%


triggerchecks = log_returns_spread.copy().to_frame(name='spread')
triggerchecks['ABS CV'] = abs(global_pos_CV)
triggerchecks['pos stoploss'] = global_pos_stoploss
triggerchecks['neg stoploss'] = global_neg_stoploss
triggerchecks['mean spread'] = global_mean_spread
triggerchecks['above trigger?'] = abs(triggerchecks['spread']) > triggerchecks['ABS CV']
triggerchecks['stopped out?'] = (triggerchecks['spread'] > global_pos_stoploss) | (triggerchecks['spread'] < global_neg_stoploss)
triggerchecks['exit profit trigger?'] = abs(triggerchecks['spread'] - global_mean_spread) < abs(global_std_spread * 0.1 )



# %%
trades_raw = pd.DataFrame(results[0].trade_log)
trades_raw.set_index(trades_raw['execution time'], inplace= True)
trades = trades_raw.pivot_table(index = trades_raw.index, columns = ['symbol'], values = ['direction', 'size', 'type', 'pnl', 'price'], aggfunc = 'first', dropna= False)
trades.columns.names = ['metrics', 'symbols']


for symbol in ['GGAL', 'BMA']:
  symbol_data = trades.xs(symbol, level = 'symbols', axis = 1)
  #print (symbol_data)      # Toggle for debug
  long_position = None
  short_position = None
  
  for idx, row in symbol_data.iterrows():
      if row['type'] == 'to open':
        if row['direction'] == 'buy':
          long_position = row
          
        elif row['direction'] == 'short':
          short_position = row
          
      elif row['type'] == 'to close' and (long_position is not None or short_position is not None):
        if row['direction'] == 'exit long':
          pnl = (row['price'] - long_position['price']) * abs(row['size'])  # abs row size, since order is to close
          #print (idx, pnl)          # Toggle for debug
          trades.loc[idx,('pnl', symbol)] = pnl
          long_position = None
        elif row['direction'] == 'cover' and short_position is not None:
          pnl = (short_position['price'] - row['price'] ) * abs(row['size'])
          #print (idx, pnl)       # Toggle for debug
          trades.loc[idx,('pnl', symbol)] = pnl
          short_position = None
        
pnls = trades.xs('pnl', level = ('metrics'), axis =1).dropna()
pnls['total pnl'] = pnls['BMA'] + pnls['GGAL']
total_pnl = pnls['total pnl'].sum()
total_pnl

trades.head(50)
print(f'total pnl: ${total_pnl:.2f}')
# %%
