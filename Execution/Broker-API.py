# API Basics
# We will start with Primary SA's Websocket API, using the free Remarkets account for realtime market data
#%%
import pyRofex
# pyrofex details --> https://github.com/matbarofex/pyRofex

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
