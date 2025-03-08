# %%
%matplotlib inline
import backtrader as bt
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# %%
%matplotlib inline
        # Backtrader Basics: defining prices, initializing cerebro
        # adding the data, running cerebro and plotting the results
GGAL = yf.download('GGAL', start='2024-01-01')
GGAL.columns = ['open', 'high', 'low', 'close', 'volume'] # Rename for Cerebro
cerebro = bt.Cerebro() # Create a cerebro entity
feed = bt.feeds.PandasData(dataname=GGAL) # Create a data feed
cerebro.adddata(feed) # Add the data feed



class miprimeraestretegia(bt.Strategy): # Create a Strategy class
    def __init__(self): # init the strategy and define close price as self.dataclose
        self.dataclose = self.datas[0].close

        #instances of pending orders and commissions, etc. 
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sellprice = None
        self.sellcomm = None
        self.bar_executed = None
        
    def log(self, msg, dt =None): # Logging function. dt stands for datetime, set to None as default (if not provided)
        dt = dt or self.datas[0].datetime.date(0) # If dt is not provided, set it to current datetime
        print(f'{dt.isoformat()}, {msg}')
                 # to call this function we use self.log('our message in quotes')


    def notify_order(self, order): # Notify order status method
          if order.status in [order.Submitted, order.Accepted]:
              buy_orsell = 'BUY' if order.isbuy() else 'SELL'
              self.log(f'{buy_orsell} order Submitted/Accepted at price {order.created.price}')
        
              return
          if order.status in [order.Completed]:
              self.bar_executed = len(self)
              if order.isbuy():
                  self.log(f'BUY EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
                  self.buyprice = order.executed.price
                  self.buycomm = order.executed.comm
              elif order.issell():
                  self.log(f'SELL EXECUTED, Price: {order.executed.price}, Cost: {order.executed.value}, Comm: {order.executed.comm}')
                  self.sellprice = order.executed.price
                  self.sellcomm = order.executed.comm
                

    
    def next(self): # Method that executed with each price, i.e. most of the strategy
        if len(self.dataclose) < 3:
             return

        if not self.position:
                if self.dataclose[0] > self.dataclose[-3] and self.dataclose[-2] > self.dataclose[-3]:
                        if self.dataclose[-1] > self.dataclose[-2]:
                                self.order = self.buy()
                               
        elif self.position:
                execution_bar_index =  self.bar_executed - len(self)
                if self.dataclose[0] < self.dataclose[execution_bar_index - 3 ] * 0.90:
                        self.order  = self.sell()
                

cerebro.addstrategy(miprimeraestretegia) # Add the strategy to cerebro
cerebro.broker.setcommission(commission=0.001) # Set the commission to 0.1%
cerebro.addsizer(bt.sizers.PercentSizer, percents = 95) # Set position size to 95% of the cash
cerebro.run() # Run the strategy
cerebro.plot(iplot=False) # Plot the results
final_value = cerebro.broker.getvalue()
starting_cash = cerebro.broker.startingcash
gain_percentage = (final_value / starting_cash - 1) * 100
gain_dollars = final_value - starting_cash
print(f'Final Value: ${final_value:.2f}\nReturn: ${gain_dollars:.2f} --> %{gain_percentage:.2f}')
# %%
