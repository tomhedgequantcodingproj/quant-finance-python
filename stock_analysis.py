"""
Stock Analysis Class
---------------------
A reusable Stock class that downloads historical price data and calculates
key financial metrics for any stock ticker supported by yfinance.

Metrics:
- Total return (%)
- Daily volatility (std of daily returns)
- Sharpe ratio (risk-adjusted return, risk-free rate = 4% annual)
- Best and worst single trading day
- Current SMA crossover signal (BUY / SELL / NEUTRAL)

Usage:
    stock = Stock("AAPL", "2025-01-01", "2026-01-01")
    stock.summary()
"""

import yfinance as yf
import pandas as pd


class Stock:
    # Risk-free rate — Australian 10yr government bond, annualised, converted to daily
    RISK_FREE_RATE = 4 / 252

    def __init__(self, ticker: str, start: str, end: str):
        """Download price data and calculate daily returns on initialisation."""
        self.ticker = ticker
        self.start = start
        self.end = end
        self.data = yf.download(ticker, start=start, end=end, progress=False)
        self.close = self.data["Close"].squeeze()       # daily closing prices
        self.returns = self.close.pct_change() * 100   # daily % returns

    def total_return(self) -> float:
        """Total percentage return over the full period."""
        return ((self.close.iloc[-1] - self.close.iloc[0]) / self.close.iloc[0]) * 100

    def volatility(self) -> float:
        """Standard deviation of daily percentage returns."""
        return float(self.returns.std())

    def sharpe(self) -> float:
        """Sharpe ratio — return per unit of risk, adjusted for risk-free rate."""
        return float((self.returns.mean() - self.RISK_FREE_RATE) / self.returns.std())

    def best_day(self):
        """Date of the highest single-day return."""
        return self.returns.idxmax().date()

    def worst_day(self):
        """Date of the lowest single-day return."""
        return self.returns.idxmin().date()

    def current_signal(self) -> str:
        """
        Current SMA crossover signal based on 20 and 50 day moving averages.
        BUY  = 20-day SMA above 50-day SMA (bullish trend)
        SELL = 20-day SMA below 50-day SMA (bearish trend)
        """
        sma20 = self.close.rolling(window=20).mean().iloc[-1]
        sma50 = self.close.rolling(window=50).mean().iloc[-1]
        if sma20 > sma50:
            return "BUY"
        elif sma20 < sma50:
            return "SELL"
        else:
            return "NEUTRAL"

    def summary(self):
        """Print a formatted summary of all key metrics."""
        print(f"\n--- {self.ticker} ({self.start} to {self.end}) ---")
        print(f"Total Return:  {self.total_return():.2f}%")
        print(f"Volatility:    {self.volatility():.2f}%")
        print(f"Sharpe Ratio:  {self.sharpe():.4f}")
        print(f"Best Day:      {self.best_day()} (+{self.returns.max():.2f}%)")
        print(f"Worst Day:     {self.worst_day()} ({self.returns.min():.2f}%)")
        print(f"Signal:        {self.current_signal()}")


# --- Example usage ---
if __name__ == "__main__":
    tickers = ["AGL.AX", "BHP.AX", "AAPL", "MSFT"]
    for ticker in tickers:
        stock = Stock(ticker, "2025-04-01", "2026-04-01")
        stock.summary()
