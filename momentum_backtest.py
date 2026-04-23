import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configuration
TICKERS = ["AGL.AX", "LITE", "BE", "AAPL", "BHP.AX", "MSFT", "DAO", "ETH"]
START = "2024-01-01"
END = "2026-04-01"
CAPITAL = 10000
LOOKBACK = 182  # 6 months in days

#  Download all data upfront as its more efficient than downloading inside the loop 
all_data = {}
for ticker in TICKERS:
    df = yf.download(ticker, start=START, end=END, progress=False)
    all_data[ticker] = df["Close"].squeeze()

# Generate monthly rebalance dates 
# Start July 2024 so there is a full 6 months of lookback data available
months = pd.date_range(start="2024-07-01", end=END, freq="MS")

portfolio_value = CAPITAL
held_stocks = []
buy_prices = {}
shares_held = {}        # tracks actual number of shares owned per stock
prev_portfolio_value = CAPITAL
portfolio_history = []  # stores monthly portfolio value for drawdown calculation

print(f"Starting Capital: ${CAPITAL:,.2f}\n")
print(f"{'Date':<12} {'Holdings':<20} {'Portfolio Value':>16} {'Monthly Return':>15}")
print("-" * 67)

for month in months:
    lookback_start = month - timedelta(days=LOOKBACK)

    # Calculate 6 month return for each stock using a sliding window
    returns = {}
    for ticker in TICKERS:
        price_slice = all_data[ticker].loc[lookback_start:month]
        if len(price_slice) < 2:
            continue  # skip if insufficient data
        return_pct = (price_slice.iloc[-1] - price_slice.iloc[0]) / price_slice.iloc[0] * 100
        returns[ticker] = float(return_pct)

    # Rank stocks by 6 month return and select top 2
    sorted_returns = sorted(returns.items(), key=lambda x: x[1], reverse=True)
    top2_list = [sorted_returns[0][0], sorted_returns[1][0]]

    # Get current prices for this month
    current_prices = {}
    for ticker in TICKERS:
        price_data = all_data[ticker].loc[:month]
        if len(price_data) > 0:
            current_prices[ticker] = float(price_data.iloc[-1])

    # Mark portfolio to market to update value based on current prices
    if held_stocks:
        portfolio_value = sum(
            shares_held[t] * current_prices[t]
            for t in held_stocks
            if t in current_prices
        )

    # Sell stocks that dropped out of top 2
    trades = []
    for ticker in held_stocks[:]:
        if ticker not in top2_list:
            sell_price = current_prices[ticker]
            proceeds = shares_held[ticker] * sell_price
            profit = proceeds - (shares_held[ticker] * buy_prices[ticker])
            trades.append(f"SELL {ticker} at ${sell_price:.2f} P&L ${profit:+.2f}")
            held_stocks.remove(ticker)
            del buy_prices[ticker]
            del shares_held[ticker]

    # Calculate available cash after sells
    cash = portfolio_value - sum(
        shares_held.get(t, 0) * current_prices[t]
        for t in held_stocks
    )

    # Buy stocks new to top 2 to split cash equally between new positions
    new_buys = [t for t in top2_list if t not in held_stocks]
    if new_buys:
        allocation = cash / len(new_buys)
        for ticker in new_buys:
            buy_price = current_prices[ticker]
            shares = allocation / buy_price
            trades.append(f"BUY  {ticker} at ${buy_price:.2f} for {shares:.2f} shares")
            held_stocks.append(ticker)
            buy_prices[ticker] = buy_price
            shares_held[ticker] = shares

    # Calculate and print monthly return
    monthly_return = ((portfolio_value - prev_portfolio_value) / prev_portfolio_value) * 100
    prev_portfolio_value = portfolio_value
    portfolio_history.append(portfolio_value)

    holdings_str = " & ".join(held_stocks)
    print(f"{str(month.date()):<12} {holdings_str:<20} ${portfolio_value:>14,.2f} {monthly_return:>+14.2f}%")
    for trade in trades:
        print(f"  → {trade}")

# Final summary
print("-" * 67) # 67
print(f"\nFinal Portfolio Value: ${portfolio_value:,.2f}")
print(f"Total Return:          {((portfolio_value - CAPITAL) / CAPITAL * 100):+.2f}%")

# Maximum drawdown calculation
# Tracks rolling peak and finds worst sequential drop from any peak to subsequent trough
peak = portfolio_history[0]
max_drawdown = 0

for value in portfolio_history:
    if value > peak:
        peak = value
    drawdown = (value - peak) / peak * 100
    if drawdown < max_drawdown:
        max_drawdown = drawdown

print(f"Maximum Drawdown:      {max_drawdown:.2f}%")
