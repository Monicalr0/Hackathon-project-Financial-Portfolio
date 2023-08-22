# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: team11-nam-hackathon
#     language: python
#     name: python3
# ---

# %%
import yfinance as yf

# %%
tickers = yf.Tickers('msft aapl goog')

# %%
# access each ticker using (example)
tickers.tickers['MSFT'].info

# %%
# Create a Ticker object for the stock symbol you're interested in
stock = yf.Ticker("AAPL")

# Get general information about the stock
stock_info = stock.info

# Access the asset type information
asset_type = stock_info.get("quoteType", "N/A")

print("Asset Type:", asset_type)
