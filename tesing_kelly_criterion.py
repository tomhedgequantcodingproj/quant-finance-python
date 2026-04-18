import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
TICKER = "AAPL"
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
trade_profits = []

print(f"\n--- Trade Log ---")
for date, row in signals.iterrows():
    # Golden cross — enter position if not already holding
    if row["crossover"] == 1 and not in_position:
        buy_price = row["close"]
        stop_loss = (buy_price * (1-0.02))
        take_profit = (buy_price * (1+0.03))
        in_position = True
    elif in_position and row["close"] > take_profit:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        trade_profits.append(profit)
        print(f"Take Profit Triggered on {date.date()} | Buy: ${buy_price:.2f} -> Sell: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False
    elif in_position and row["close"] < stop_loss:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        trade_profits.append(profit)
        print(f"Stop Loss Triggered on {date.date()} | Buy: ${buy_price:.2f} -> Sell: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False
    # Death cross — exit position if currently holding
    elif row["crossover"] == -1 and in_position:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        trade_profits.append(profit)
        print(f"{date.date()} | Buy: ${buy_price:.2f} -> Sell: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False
    
# --- Summary ---
print(f"\n--- Backtest Summary ({TICKER}) ---")
print(f"Strategy: 20/50 SMA Crossover")
print(f"Period:   {START_DATE} to {END_DATE}")
if total_profit > 0:
    print(f"Result:   Total Profit ${total_profit:.2f} per share")
else:
    print(f"Result:   Total Loss ${total_profit:.2f} per share")

wins = []
losses = []

for p in trade_profits:
    if p > 0:
        wins.append(p)
    else:
        losses.append(abs(p))
def kelly_criterion(trade_profits, wins, losses):
    if not trade_profits or not wins or not losses:
        return 0.0, 0.0, 0.0, 0.0
    win_rate = len(wins) / len(trade_profits)
    loss_rate = 1 - win_rate
    avg_win = sum(wins) / len(wins)
    avg_loss = sum(losses) / len(losses)
    win_loss_ratio = avg_win / avg_loss
    kelly = win_rate - (loss_rate / win_loss_ratio)
    return win_rate, avg_win, avg_loss, kelly

win_rate, avg_win, avg_loss, kelly = kelly_criterion(trade_profits, wins, losses)

print(f"Win Rate: {win_rate:.2%}")
print(f"Avg Win: ${avg_win:.2f}")
print(f"Avg Loss: ${avg_loss:.2f}") 
print(f"Kelly %: {kelly:.2%}")
if kelly > 0.25:
    print(f"Strong bet should be made.")
elif kelly > 0: 
    print(f"Moderate bet should be made.")
elif kelly <= 0:
    print(f"Dont trade this strategy.")
