"""
Volatility Screener
--------------------
Downloads 1 year of ASX stock data and ranks stocks from least to most volatile.
Volatility is measured as the standard deviation of daily percentage returns.
"""

import yfinance as yf
import pandas as pd

# --- Configuration ---
# Add or remove tickers here to change which stocks are screened
TICKERS = ["BHP.AX", "RIO.AX", "NAB.AX", "GYG.AX", "TLS.AX"]
START_DATE = "2025-04-01"
END_DATE = "2026-04-08"

# --- Download and calculate volatility for each stock ---
vols = {}

for ticker in TICKERS:
    df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
    close = df["Close"].squeeze()
    returns = close.pct_change() * 100       # daily % returns
    vols[ticker] = float(returns.std())      # volatility = std of daily returns

# --- Sort from least to most volatile ---
sorted_vols = sorted(vols.items(), key=lambda x: x[1])

# --- Print results ---
print("\n--- Volatility Ranking (Least to Most Risky) ---")
for i, (ticker, vol) in enumerate(sorted_vols, 1):
    print(f"{i}. {ticker}: {vol:.2f}%")

print(f"\nSafest Stock:   {sorted_vols[0][0]} ({sorted_vols[0][1]:.2f}% daily volatility)")
print(f"Riskiest Stock: {sorted_vols[-1][0]} ({sorted_vols[-1][1]:.2f}% daily volatility)")
