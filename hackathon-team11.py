import time
from datetime import datetime
import pandas as pd
import numpy as np

dt = datetime(2023, 1, 1)
start_date = int(round(dt.timestamp()))

dt = datetime(2023, 7, 31)
end_date = int(round(dt.timestamp()))

stock = 'SPY'
stock2 = 'AAPL'
stock3 = '^TNX'

df_spy = pd.read_csv(f"https://query1.finance.yahoo.com/v7/finance/download/{stock}?period1={start_date}&period2={end_date}&interval=1d&events=history&includeAdjustedClose=true",
    parse_dates = ['Date'], index_col='Date')

df_apple =  pd.read_csv(f"https://query1.finance.yahoo.com/v7/finance/download/{stock2}?period1={start_date}&period2={end_date}&interval=1d&events=history&includeAdjustedClose=true",
    parse_dates = ['Date'], index_col='Date')

df_bonds =  pd.read_csv(f"https://query1.finance.yahoo.com/v7/finance/download/{stock3}?period1={start_date}&period2={end_date}&interval=1d&events=history&includeAdjustedClose=true",
    parse_dates = ['Date'], index_col='Date')

df_spy = pd.DataFrame(df_spy)
# print(df_bonds)
# print(df_spy)
# print(df_apple)

#Create a df containing all ticker info
ticker_list = ['SPY', 'AAPL', '^TNX']
port = df_spy[['Close']].merge(df_apple[['Close']], on = 'Date').merge(df_bonds[['Close']], on = 'Date')
port.columns = ticker_list

returns = np.log(port / port.shift(1))
returns_mean = returns.mean() * 143

print(returns.cov()*143)
print(returns.corr())

client = {'total_inv': 300000,
          'spy_shares':15, 'app_shares':30, 'bonds_shares': 60}
totalshare = client[]
#asset_price = 
spy_asset = client['spy_shares']*port['SPY'][-1]
#print(returns_mean)

#client_cash = pd.DataFrame()

# client.cash

#port = pd.concat([df_spy[['Close']], df_apple[['Close']]], df_bonds[['Close']], axis=2)
