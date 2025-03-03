# %%
# Import area
import pandas as pd
import pandas_datareader.data as web
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import sklearn
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.stattools import adfuller
import matplotlib.dates as mdates

symbol_list = ['GGAL', 'BMA']
# format ---> yf.download (symbol_list, start = datetime, end = datetime)
#raw_data= yf.download(symbol_list, start_time , end_time) # Download a dataframe with high, low, open, close, etc.
raw_data = yf.download(tickers=symbol_list, period="7d", interval="5m")
raw_data.index = raw_data.index.tz_convert('America/New_York')
raw_data.index = raw_data.index.tz_localize(None)
raw_data.drop(raw_data[raw_data.index.date == pd.to_datetime('2025-02-27').date()].index, axis = 0 , inplace= True) # ---> dropping earnings outlier    

# %%

#     Section Zero: Data, Dates, and initial config


# format ---> datetime (yyyy, m, d, h, mm, ss)
start_time = datetime(2024, 1 ,1)    # 1st Jan 2024 9:30:00 AM NY Time
end_time = datetime(2025, 2, 28)    # 28th Feb 2025 4:00:00 PM NY TIME

clean_price_data = raw_data["Close"].dropna()  # Picks out only the  'Close' column out of the whole dataframe

# Plot the prices for each
plt.figure(figsize=(15,6))                     
plt.plot(range(len(clean_price_data.index)),clean_price_data)
plt.title(symbol_list)
plt.xlabel ('Date')
plt.ylabel ('Price')
plt.legend(clean_price_data.columns)

log_prices = np.log(clean_price_data)         # np.log log transforms the prices
log_returns = log_prices.diff().dropna()      # diff() takes the first difference of log prices (= log returns)

plt.figure(figsize=(15,6))                     
plt.plot(range(len(log_prices.index)),log_prices)
plt.title('Log Prices')
plt.xlabel ('Date')
plt.ylabel ('Log Price')
plt.legend(clean_price_data.columns)

plt.figure(figsize=(15,6))                     
plt.plot(range(len(log_returns.index)), log_returns)
plt.title('Log Returns')
plt.xlabel ('Date')
plt.ylabel ('Log Returns')
plt.legend(clean_price_data.columns)




# %% 

#     Section A: FEATURES NEEDED FOR A SIMPLE PAIRS TRADING STRATEGY. 


# Cointegration: We run an Engle-Granger Cointegration test for 2 time series, or a Johansen test for more

#               Testing if log prices are I(1)

# ADF for stationarity of first difference of log prices (log returns)
adf_ggal =adfuller (log_returns['GGAL'])
adf_bma =adfuller (log_returns['BMA'])

if adf_ggal[1] < 0.05:
    print('Reject H_0 at 5% significance level \nlog returns is stationary \nlog prices are I(1)]')
if adf_bma[1] > 0.05:
    print('Do NOT Reject H_0 at 5% significance level, \n log returns is NOT stationary, log prices are not I(1)')


# If ADF of log returns is stationary, proceed with cointegration test

# Engler and Granger test
score, p_value, critical_values = coint(log_prices['GGAL'],log_prices['BMA'] , trend= 'c')    # Coint() is the full engler and Granger test

print (f'ADF Cointegration score: {score} \n p-value: {p_value} \n critical values (1%,5%,10%): {critical_values}' )

if p_value < 0.05:
    print('Reject H_0 at 5% significance level, series is cointegrated, suitable for pairs trading')
if p_value > 0.05:
    print('Do NOT Reject H_0 at 5% significance level \nseries is NOT cointegrated \nNOT suitable for pairs trading')


# %%
#   Manually regressing one stock on another to see the residuals (manually verifying Engler and Granger)

X = log_prices['BMA']
Y = log_prices['GGAL']
X_with_constant = sm.add_constant(X)   # Add a constant to the Vector X for the constant in the regression
model_regression = sm.OLS(Y, X_with_constant).fit()   # Run an OLS regression
log_residuals = model_regression.resid                   # Save residuals

plt.plot(range(len(log_residuals.index)),log_residuals)
plt.title('log residuals')       # Plotting residuals
plt.ylabel('Log Residuals')
plt.show()

plt.figure()
plt.plot (range(len(Y.index)),Y)
plt.plot (range(len(Y.index)), model_regression.fittedvalues)
plt.title('GGAL Actual log price vs predicted')     # Plotting the OLS prediction of GGAL (on BMA) vs the actual price
plt.legend(['GGAL', 'GGAL predicted'])
plt.show()


#Testing for stationarity of the residuals
adf_result = adfuller(log_residuals) ## Uses 2 lags, 280ish sample size
print (f'ADF test statistic: {adf_result[0]} \np-value" {adf_result[1]} \nCritical Value: {adf_result[4]}') 
adf_result


# %%

#Section B: After we found a cointegrated pair....

log_returns_spread = log_returns['GGAL'] - log_returns['BMA']         
            

# Confirming that the spread is stationary
adf_log_returns_spread = adfuller(log_returns_spread)
print (f'adf test stat: {adf_log_returns_spread[0]} \n p-value: {adf_log_returns_spread[1]}')      #  ADF test for stationarity of log spread
if adf_log_returns_spread[1] < 0.05:
    print('p-value lower than 5%, spread is stationary')

#Calculating moments to Z transform
mean_spread = log_returns_spread.mean()
std_spread= log_returns_spread.std()

z_transformed_spread = (log_returns_spread - mean_spread) / std_spread    # Transformed

plt.figure()
plt.plot(range(len(log_returns_spread.index)), log_returns_spread, color = 'green')         # Raw log returns spread plot
plt.title('Log returns spread (GGAL-BMA)')
plt.show()


plt.hist(log_returns_spread, bins=70, color='skyblue', edgecolor='black') 
plt.title('Distribution of log spread')                                                     # Plotting distribution of spread
plt.axvline(mean_spread, color = 'purple', linestyle = '--', label = 'mean', linewidth = 2)
plt.axvline(std_spread, color = 'green', linestyle = '--', label = 'std', linewidth = 2)
plt.axvline(-std_spread, color = 'green', linestyle = '--', linewidth = 2)
plt.legend()
plt.show()


plt.figure()
plt.plot (range(len(z_transformed_spread.index)), z_transformed_spread, color = 'purple')
plt.title('Z-score of spread (GGAL-BMA)')
plt.axhline(mean_spread, color = 'blue', linestyle = '--', label= 'mean')       # Plotting Z scores with %5 significance level triggers
plt.axhline(1.96, color = 'green', linestyle = '--', label= '5% CV')
plt.axhline(-1.96, color = 'red', linestyle = '--', label= '5% CV')
plt.legend()
plt.show()


# %%
##              SECTION C: BUILDING THE STRATEGY

initial_cash = 1000
ggal_position = 0 
bma_position = 0
z_critical_values = 1.96
log_critical_values = z_critical_values * std_spread + mean_spread

entries_datetimes = []

for logspread in log_returns_spread:
    if logspread > log_critical_values  and ggal_position == 0:
        entrytime = log_returns_spread[log_returns_spread == logspread].index.item()
        entries_datetimes.append(entrytime)
        ggal_position = -1 
        bma_position = 1
        print('entry', entrytime)
    elif ggal_position < 0 and (logspread  - mean_spread) < (mean_spread * 0.01):
        ggal_position = 0
        bma_position = 0 
        exit_time = log_returns_spread[log_returns_spread == logspread].index.item()
        ggal_profit = clean_price_data['GGAL'].loc[entrytime] - clean_price_data['GGAL'].loc[exit_time]
        bma_profit = clean_price_data['BMA'].loc[exit_time] - clean_price_data['BMA'].loc[entrytime]
        initial_cash = initial_cash  + (ggal_profit + bma_profit)
        print  ('exit', initial_cash)



# %%


# 
# %%
log_returns_spread.idxmax()

# %%
