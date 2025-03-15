#%%
import requests
import pandas as pd

# Step 1: Get the Authentication Token
def get_auth_token(username, password):
    url = "https://api.remarkets.primary.com.ar/auth/getToken"
    
    headers = {
        'X-Username': 'pridagia20974',
        'X-Password': 'dpdgpG4$' 
    }
    
    response = requests.post(url, headers=headers)
    

    if response.status_code == 200:
        # Extract the token from the response headers
        token = response.headers.get('X-Auth-Token')
        if token:
            print("Token received successfully.")
            return token
        else:
            print("Error: No token found in response.")
            return None
    else:
        print(f"Error in auth: {response.status_code}, {response.text}")
        return None

# Step 2: Use the Token to Get Historical Market Data
def get_historical_trades(token):
    url = "https://api.remarkets.primary.com.ar/rest/data/getTrades"
    
    # Define the request parameters
    params = {
        "marketId": "ROFX",  # Identificador del Mercado (ROFX para Matba Rofex)
        "symbol": "DLR/MAR25",  # Símbolo del contrato (Ejemplo: GGAL/JUN25)
        "date": '2025-03-15',
      #  "dateFrom": "2025-03-13",  # Fecha desde (YYYY-MM-DD)
       # "dateTo": "2025-03-14",    # Fecha hasta (YYYY-MM-DD)
      #  "external": 'false',       # Para consultar información de mercados externos, use "true"
        "environment": "REMARKETS"  # Indicar el entorno (REMARKETS o PRIMARY)
    }
    
    # Define the request headers with the token
    headers = {
        'Authorization': f'Bearer {token}',  # Bearer token in the Authorization header
        'Content-Type': 'application/json'
    }
    
    # Send the GET request with the token in the headers
    response = requests.get(url, params=params, headers=headers)
    print(response.url)
    # Print the raw response to debug
    print("Response Status Code:", response.status_code)
    print("Raw Response Text:", response.text)
    
    if response.status_code == 200:

        try:
            # Parse the JSON response
            trade_data = response.json()
            
            # Check if there are trades in the response
            if "trades" in trade_data:
                # Convert the trade data into a Pandas DataFrame
                df = pd.DataFrame(trade_data["trades"])
                
                # Convert timestamps to datetime format
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                # Display first rows
                print(df.head())
                
            else:
                print("No trades found for the given date range.")
        except ValueError as e:
            print("Error parsing JSON:", e)
    else:
        print(f"Error: {response.status_code}, {response.text}")

# Main Program Execution
if __name__ == "__main__":
    # Replace with your actual credentials
    username = "pridagia20974"
    password = "dpdgpG4$"
    
    # Step 1: Get the Auth Token
    token = get_auth_token(username, password)
    
    if token:
        # Step 2: Use the token to get historical trade data
        get_historical_trades(token)

# %%
