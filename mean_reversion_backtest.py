import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
TICKER = "AAPL"
START_DATE = "2024-04-01"
END_DATE = "2026-04-09"

# --- Download price data ---
df = yf.download(TICKER, start=START_DATE, end=END_DATE)
spy = yf.download("SPY", start=START_DATE, end=END_DATE)

close = df["Close"].squeeze()
spy_close = spy["Close"].squeeze()

# --- Bollinger Bands (20 day, 2 standard deviations) ---
middle = close.rolling(window=20).mean()
std = close.rolling(window=20).std()
upper = middle + (2 * std)
lower = middle - (2 * std)

# --- Trend filters ---
spy_sma50 = spy_close.rolling(window=50).mean()   # market regime filter
AAPL_sma50 = close.rolling(window=50).mean()       # individual stock trend filter

# --- Plot price with Bollinger Bands ---
fig, ax1 = plt.subplots(figsize=(12, 8))
close.plot(ax=ax1, label="Close Price", color="steelblue", alpha=0.5)
upper.plot(ax=ax1, label="Upper Band", color="red")
lower.plot(ax=ax1, label="Lower Band", color="green")
middle.plot(ax=ax1, label="20 Day SMA", color="orange")
ax1.set_title(f"{TICKER} - Price with Bollinger Bands")
ax1.set_ylabel("Price (USD)")
ax1.legend()
plt.tight_layout()
plt.show()

# --- Build signals DataFrame ---
signals = pd.DataFrame()
signals["close"] = close
signals["middle"] = middle
signals["lower"] = lower
signals["upper"] = upper
signals["spy"] = spy_close
signals["spy_sma50"] = spy_sma50
signals["AAPLsma50"] = AAPL_sma50
signals["AAPLsma50_rising"] = signals["AAPLsma50"] > signals["AAPLsma50"].shift(5)

# --- Backtest ---
# Entry: price touches lower band + SPY above 50 SMA + stock in uptrend
# Exit: price reverts to mean, stop loss triggered, or take profit hit
buy_price = None
in_position = False
total_profit = 0
trade_profits = []

print(f"\n--- Trade Log ({TICKER}) ---")
for date, row in signals.iterrows():
    # Buy when oversold and both trend filters confirm uptrend
    if row["close"] <= row["lower"] and not in_position and row["spy"] > row["spy_sma50"] and row["AAPLsma50_rising"]:
        buy_price = row["close"]
        stop_loss = buy_price * (1 - 0.02)
        take_profit = buy_price * (1 + 0.03)
        in_position = True
        print(f"Buy  on {date.date()} at: ${buy_price:.2f}")

    elif in_position and row["close"] >= take_profit:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        trade_profits.append(profit)
        print(f"Take Profit on {date.date()} at: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False

    elif in_position and row["close"] >= row["middle"]:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        trade_profits.append(profit)
        print(f"Sell on {date.date()} at: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False

    elif in_position and row["close"] < stop_loss:
        sell_price = row["close"]
        profit = sell_price - buy_price
        total_profit += profit
        trade_profits.append(profit)
        print(f"Stop Loss on {date.date()} | Buy: ${buy_price:.2f} → Sell: ${sell_price:.2f} | Profit: ${profit:.2f}")
        in_position = False

# --- Summary ---
print(f"\n--- Backtest Summary ---")
result = "Profit" if total_profit > 0 else "Loss"
print(f"Total {result}: ${total_profit:.2f} per share")

# --- Kelly Criterion ---
def kelly_criterion(trade_profits):
    wins = [p for p in trade_profits if p > 0]
    losses = [abs(p) for p in trade_profits if p < 0]
    if not trade_profits or not wins or not losses:
        print("Not enough data for Kelly Criterion.")
        return
    win_rate = len(wins) / len(trade_profits)
    avg_win = sum(wins) / len(wins)
    avg_loss = sum(losses) / len(losses)
    kelly = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
    print(f"Win Rate: {win_rate:.2%} | Avg Win: ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
    print(f"Kelly %:  {kelly:.2%}")
    if kelly > 0.25:
        print("Verdict: Strong bet.")
    elif kelly > 0:
        print("Verdict: Modest bet.")
    else:
        print("Verdict: Don't trade this strategy.")

kelly_criterion(trade_profits)