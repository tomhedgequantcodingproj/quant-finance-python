"""
Automated Stock Screener
-------------------------
Automatically downloads the last 12 months of data for a list of stocks
and ranks them across three key metrics:

1. Total return (highest to lowest)
2. Volatility (lowest to highest — safer stocks first)
3. Sharpe ratio (highest to lowest — best risk-adjusted return first)

Also generates a current buy/sell signal for each stock based on the
20/50 day SMA crossover strategy, and exports results to a CSV file.

No manual date entry required — dates are calculated automatically.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


# ─── Stock Class ─────────────────────────────────────────────────────────────

class Stock:
    RISK_FREE_RATE = 4 / 252  # Australian 10yr bond rate, converted to daily

    def __init__(self, ticker: str, start: str, end: str):
        self.ticker = ticker
        self.data = yf.download(ticker, start=start, end=end, progress=False)
        self.close = self.data["Close"].squeeze()
        self.returns = self.close.pct_change() * 100

    def total_return(self) -> float:
        return ((self.close.iloc[-1] - self.close.iloc[0]) / self.close.iloc[0]) * 100

    def volatility(self) -> float:
        return float(self.returns.std())

    def sharpe(self) -> float:
        return float((self.returns.mean() - self.RISK_FREE_RATE) / self.returns.std())

    def current_signal(self) -> str:
        sma20 = self.close.rolling(window=20).mean().iloc[-1]
        sma50 = self.close.rolling(window=50).mean().iloc[-1]
        if sma20 > sma50:
            return "BUY"
        elif sma20 < sma50:
            return "SELL"
        else:
            return "NEUTRAL"


# ─── Configuration ────────────────────────────────────────────────────────────

# Add or remove tickers here — supports ASX (.AX suffix), US, and other exchanges
TICKERS = [
    "AGL.AX", "BHP.AX", "LITE", "BE", "AAPL", "MSFT"
]

# Automatically calculate date range — always uses last 12 months
today = datetime.today()
one_year_ago = today - timedelta(days=365)
TODAY_STR = today.strftime("%Y-%m-%d")
ONE_YEAR_AGO_STR = one_year_ago.strftime("%Y-%m-%d")


# ─── Download Data ────────────────────────────────────────────────────────────

print(f"Downloading data from {ONE_YEAR_AGO_STR} to {TODAY_STR}...\n")
stocks = [Stock(ticker, ONE_YEAR_AGO_STR, TODAY_STR) for ticker in TICKERS]


# ─── Build Metric Dictionaries ───────────────────────────────────────────────

total_returns = {s.ticker: s.total_return() for s in stocks}
volatilities  = {s.ticker: s.volatility()   for s in stocks}
sharpes       = {s.ticker: s.sharpe()       for s in stocks}

sorted_returns = sorted(total_returns.items(), key=lambda x: x[1], reverse=True)
sorted_vols    = sorted(volatilities.items(),  key=lambda x: x[1])
sorted_sharpes = sorted(sharpes.items(),       key=lambda x: x[1], reverse=True)


# ─── Print Rankings ───────────────────────────────────────────────────────────

print("─── Best to Worst Total Return ───")
for i, (ticker, ret) in enumerate(sorted_returns, 1):
    print(f"  {i}. {ticker:<10} {ret:>8.2f}%")

print("\n─── Lowest to Highest Volatility ───")
for i, (ticker, vol) in enumerate(sorted_vols, 1):
    print(f"  {i}. {ticker:<10} {vol:>8.2f}%")

print("\n─── Best to Worst Sharpe Ratio ───")
for i, (ticker, sharpe) in enumerate(sorted_sharpes, 1):
    print(f"  {i}. {ticker:<10} {sharpe:>8.4f}")

print("\n─── Current Buy/Sell Signals ───")
for stock in stocks:
    print(f"  {stock.ticker:<10} {stock.current_signal()}")

print(f"\n✓ Best risk-adjusted return: {sorted_sharpes[0][0]}  (Sharpe: {sorted_sharpes[0][1]:.4f})")
print(f"✗ Worst risk-adjusted return: {sorted_sharpes[-1][0]} (Sharpe: {sorted_sharpes[-1][1]:.4f})")


# ─── Export to CSV ────────────────────────────────────────────────────────────

rows = [{
    "Ticker":           s.ticker,
    "Total Return (%)": round(s.total_return(), 2),
    "Volatility (%)":   round(s.volatility(),   2),
    "Sharpe Ratio":     round(s.sharpe(),        4),
    "Signal":           s.current_signal()
} for s in stocks]

results = pd.DataFrame(rows).sort_values("Sharpe Ratio", ascending=False)
results.to_csv("stock_screener.csv", index=False)
print(f"\nResults saved to stock_screener.csv")
