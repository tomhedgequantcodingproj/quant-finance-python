"""
SMA Crossover Backtester
-------------------------
Backtests a 20/50 day Simple Moving Average crossover strategy on a given stock.

Strategy rules:
- BUY  when the 20-day SMA crosses above the 50-day SMA (Golden Cross)
- SELL when the 20-day SMA crosses below the 50-day SMA (Death Cross)

Results show each trade's entry/exit price and profit per share.
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
TICKER = "AGL.AX"
START_DATE = "2024-04-01"
END_DATE = "2026-04-09"

# --- Download data ---
df = yf.download(TICKER, start=START_DATE, end=END_DATE, progress=False)
close = df["Close"].squeeze()

# --- Calculate moving averages ---
sma20 = close.rolling(window=20).mean()   # short-term trend
sma50 = close.rolling(window=50).mean()   # long-term trend

# --- Build signals DataFrame ---
signals = pd.DataFrame()
signals["close"] = close
signals["sma20"] = sma20
signals["sma50"] = sma50

# 1 = sma20 above sma50 (uptrend), 0 = sma20 below sma50 (downtrend)
signals["signal"] = 0
signals.loc[signals["sma20"] > signals["sma50"], "signal"] = 1

# diff() detects changes: +1 = golden cross (buy), -1 = death cross (sell)
signals["crossover"] = signals["signal"].diff()

# --- Print crossover dates ---
buy_signals = signals[signals["crossover"] == 1]
sell_signals = signals[signals["crossover"] == -1]

print(f"\n--- Golden Cross — BUY Signals ({TICKER}) ---")
print(buy_signals[["close", "sma20", "sma50"]])

print(f"\n--- Death Cross — SELL Signals ({TICKER}) ---")
print(sell_signals[["close", "sma20", "sma50"]])

# --- Run backtest ---
# Track position state to avoid buying twice or selling without owning
buy_price = None
in_position = False
total_profit = 0

print(f"\n--- Trade Log ---")
for date, row in signals.iterrows():
    # Golden cross — enter position if not already holding
    if row["crossover"] == 1 and not in_position:
        buy_price = row["close"]
        in_position = True

    # Death cross — exit position if currently holding
    elif row["crossover"] == -1 and in_position:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        print(f"{date.date()} | Buy: ${buy_price:.2f} → Sell: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False

# --- Summary ---
print(f"\n--- Backtest Summary ({TICKER}) ---")
print(f"Strategy: 20/50 SMA Crossover")
print(f"Period:   {START_DATE} to {END_DATE}")
if total_profit > 0:
    print(f"Result:   Total Profit ${total_profit:.2f} per share")
else:
    print(f"Result:   Total Loss ${total_profit:.2f} per share")

# --- Plot price with moving averages ---
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(close, label="Close Price", alpha=0.5, color="steelblue")
ax.plot(sma20, label="20 Day SMA", color="orange")
ax.plot(sma50, label="50 Day SMA", color="red")
ax.set_title(f"{TICKER} — Price vs Moving Averages")
ax.set_ylabel("Price (AUD$)")
ax.legend()
plt.tight_layout()
plt.show()
