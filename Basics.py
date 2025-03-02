# %%
# Import area
import pandas as pd
import pandas_datareader.data as web
import numpy as np
import sklearn
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# %%
#     Section Zero: Data, Dates, and initial config

AV_api_key = 'GO6INKUOGFPT2C05' # AlphaVantage API key

# format ---> datetime (yyyy, m, d, h, mm, ss)
start_time = datetime(2024, 1 ,1)    # 1st Jan 2024 9:30:00 AM NY Time
end_time = datetime(2025, 2, 28)    # 28th Feb 2025 4:00:00 PM NY TIME

# format ---> yf.download (symbol_list, start = datetime, end = datetime)
symbol_list = ['GGAL', 'BMA']
raw_data= yf.download(symbol_list, start_time , end_time) # Download a dataframe with high, low, open, close, etc.
clean_price_data = raw_data["Close"]  # Picks out only the  'Close' column out of the whole dataframe

# Plot the prices for each
plt.figure(figsize=(15,6))                     
plt.plot(clean_price_data)
plt.title(symbol_list)
plt.xlabel ('Date')
plt.ylabel ('Price')
plt.legend(clean_price_data.columns)
plt.show

# making them start at 100 and show the evolution in relative numbers (%)
relativeprices = clean_price_data/clean_price_data.iloc[0] * 100

plt.figure(figsize=(15,6))                     
plt.plot(relativeprices)
plt.title(f'relative change {symbol_list}')
plt.xlabel ('Date')
plt.ylabel ('Price')
plt.legend(clean_price_data.columns)
plt.show

# pct-change() calculates the change between rows,outputs dataframe with % changes 
daily_returns = clean_price_data.pct_change()*100       \

# More plotting
plt.figure(figsize= (15,6))
plt.plot (daily_returns)
plt.title('% daily returns')
plt.xlabel ('date')
plt.ylabel('% return')
plt.legend(daily_returns.columns)
plt.show()

## WE ALREADY HAVE OUR INITIAL DATA AND CONFIGURATION, NEXT STEP


# %%


#     Section A: Features needed for a simple pairs trading strategy. 


# Cointegration



# %%
