# API Basics
# We will start with Primary SA's Websocket API, using the free Remarkets account for realtime market data
#%%
import pyRofex
# pyrofex details --> https://github.com/matbarofex/pyRofex
import pandas as pd

# %%

pyRofex.initialize(
    user="pridagia20974",
    password="dpdgpG4$",
    account="REM20974",
    environment=pyRofex.Environment.REMARKET  # Change to PRIMARY if using live trading
)


# Define handlers
def market_data_handler(message):
    print("Market Data:", message)

def error_handler(message):
    print("Error:", message)

def exception_handler(exception):
    print("Exception:", exception)



# Initialize WebSocket
pyRofex.init_websocket_connection(
    market_data_handler=market_data_handler,
    error_handler=error_handler,
    exception_handler=exception_handler
)

# Subscribe to bid/ask data
pyRofex.market_data_subscription(
    tickers=["MERV - XMEV - GGALD - CI"],  # Replace with desired instruments
    entries=[pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]
)


# %%
# Seccion Datos Historicos, consultar documentacion API, esta ahi
response = pyRofex.get_trade_history(
    ticker="MERV - XMEV - GGALD - CI",   # Instrument symbol
    start_date="2025-03-13", # Start date (YYYY-MM-DD)
    end_date="2024-03-14"    # End date (YYYY-MM-DD)
)

response

# if "trades" in response:
#     # Convert JSON response to Pandas DataFrame
#     df = pd.DataFrame(response["trades"])
#     df["timestamp"] = pd.to_datetime(df["timestamp"])  # Convert timestamp to datetime
    
#     # Print first rows
#     print(df.head())
# else:
#     print('error: ', response)
# %%
