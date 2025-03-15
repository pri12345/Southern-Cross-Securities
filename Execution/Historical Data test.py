#%%
import requests
import pandas as pd
#%%
# API endpoint for historical market data
url = "https://api.remarkets.primary.com.ar/rest/data/getTrades"

# Define the request parameters
params = {
    "marketId": "ROFX",  # Identificador del Mercado (ROFX para Matba Rofex)
    "symbol": "GGAL/JUN25",  # Símbolo del contrato (Ejemplo: GGAL/JUN25)
    "dateFrom": "2024-03-10",  # Fecha desde (YYYY-MM-DD)
    "dateTo": "2024-03-15",    # Fecha hasta (YYYY-MM-DD)
    "external": "false",       # Para consultar información de mercados externos, use "true"
    "environment": "REMARKETS"  # Indicar el entorno (REMARKETS o PRIMARY)
}

# Send the GET request
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    trade_data = response.json()
    
    # Check if there are trades in the response
    if "trades" in trade_data:
        # Convert the trade data into a Pandas DataFrame
        df = pd.DataFrame(trade_data["trades"])
        
        # Convert timestamps to datetime format
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Display the first rows of the DataFrame
        print(df.head())
        
        # Optionally, save the data to a CSV file
        df.to_csv("historical_trades.csv", index=False)
        print("Data saved to historical_trades.csv")
    else:
        print("No trades found for the given date range.")
else:
    print(f"Error: {response.status_code}, {response.text}")

# %%
